import json
import time
from pathlib import Path
from typing import Dict, List, Optional

import bs4
from data_model import JobProvider
from greenhouse import get_company_greenhouse_links, greenhouse_link_filter
from lever import get_company_lever_links, lever_job_link_filter
from playwright.async_api._generated import Page
from ranker import generate_intersting_job_csv
from tqdm import tqdm
from utils import async_write_json_stream, get_datetime, init_browser_page
from workday import get_company_workday_links, workday_link_filter


async def get_all_duckduckgo_links(page: Page, search_query: str) -> List[str]:
    """Opens duckduckgo search engine and retrieves all links from the search results"""
    max_page_per_search = 40
    wait_after_typing = 1
    wait_after_enter = 4
    wait_on_paging = 2

    async def scroll_down():
        await page.evaluate("window.scrollBy(0, window.innerHeight)")

    async def load_n_times(n):
        for i in tqdm(list(range(n))):
            await scroll_down()
            await page.locator('text="More results"').last.click(timeout=5000)
            time.sleep(wait_on_paging)

    await page.goto("https://duckduckgo.com/")
    await page.locator("#searchbox_input").type(search_query)
    time.sleep(wait_after_typing)
    await page.keyboard.press("Enter")
    time.sleep(wait_after_enter)
    try:
        await load_n_times(max_page_per_search)
    except:
        pass
    soup = bs4.BeautifulSoup(await page.content(), "html.parser")
    links = [x.get("href") for x in soup.find_all("a")]
    return links


async def parse_provider_links(
    page: Page,
    provider: JobProvider,
    provider_name: str,
    job_queries: List[str],
    provider_rundir: Path,
):
    """
    Given provider such as Greenhouse, extracts all links to it from duckduckgo search engine,
    filters garbage then saves to a json file
    """
    links_dir = provider_rundir / "links"
    links_dir.mkdir(parents=True, exist_ok=True)

    for job_query in job_queries:
        print("Retrieving links for", job_query, "from", provider_name, "provider")
        links = await get_all_duckduckgo_links(
            page, f"{provider.duckduckgo_query} {job_query}"
        )
        links = [provider.job_link_filter(x) for x in links]
        links = [x for x in links if x is not None]
        links = list(set(links))
        with open(links_dir / f"{job_query}.json", "w", encoding="utf-8") as f:
            json.dump(links, f)


async def source_links(
    registry: Dict[str, JobProvider], rundir: Path, job_queries: List[str]
):
    """Calls parse_provider_links for all provides"""
    async with init_browser_page() as page:
        for provider_name, provider in registry.items():
            provider_rundir = rundir / provider_name
            provider_rundir.mkdir(parents=True, exist_ok=True)
            await parse_provider_links(
                page, provider, provider_name, job_queries, provider_rundir
            )


def consolidate_links(link_dir):
    """Reads all links from a link directory and return a list of unique links"""
    link_dir = Path(link_dir)
    link_files = list(link_dir.glob("*.json"))
    all_links = []
    for link_file in link_files:
        with open(link_file, "r", encoding="utf-8") as f:
            links = json.load(f)
            all_links += links
    all_links = list(set(all_links))
    return all_links


async def get_all_company_links(registry: Dict[str, JobProvider], rundir: Path):
    """
    Goes to each provider website and extracts all job posts for every company in the list
    """
    async with init_browser_page() as page:
        for provider_name, provider in registry.items():
            provider_rundir = rundir / provider_name
            output_path = provider_rundir / "jobs.tjson"
            links = consolidate_links(provider_rundir / "links")
            await async_write_json_stream(
                lambda link: provider.source_company_jobs(page, link),
                links,
                output_path,
            )


async def process_provider_registry(
    job_queries: List[str],
    registry: Dict[str, JobProvider],
    cache_dir: str = "./cache_dir",
    checkpoint: Optional[str] = None,
):
    """Top-level method: does everything"""
    if checkpoint:
        rundir = Path(checkpoint)
    else:
        cache_dir = Path(cache_dir)
        rundir: Path = cache_dir / get_datetime()
        rundir.mkdir(parents=True, exist_ok=True)
    await source_links(registry, rundir, job_queries)
    await get_all_company_links(registry, rundir)
    generate_intersting_job_csv(rundir, "interesting_jobs.csv")


if __name__ == "__main__":
    import asyncio

    job_provider_registry = {
        "lever": JobProvider(
            duckduckgo_query="site:jobs.lever.co",
            job_link_filter=lever_job_link_filter,
            source_company_jobs=get_company_lever_links,
        ),
        "greenhouse": JobProvider(
            duckduckgo_query="site:boards.greenhouse.io",
            job_link_filter=greenhouse_link_filter,
            source_company_jobs=get_company_greenhouse_links,
        ),
        # Workaday takes a while (like 4 hours or so) to load so comment out for now
        # "workday": JobProvider(
        #    duckduckgo_query="site:myworkdayjobs.com",
        #    job_link_filter=workday_link_filter,
        #    source_company_jobs=get_company_workday_links,
        # ),
    }

    asyncio.run(
        process_provider_registry(
            ["machine learning", "data scientist"],
            job_provider_registry,
        )
    )
