from typing import List, Optional

from playwright.async_api._generated import Page

from data_model import JobPost


def workday_link_filter(link: Optional[str]) -> Optional[str]:
    def extra_process_workday(link):
        if (
            link.startswith("https://duckduckgo.com")
            or "login?redirect" in link
            or "/page/" in link
        ):
            return None
        if link.endswith("/introduceYourself") or link.endswith("/introduceYourself/"):
            return None
        if link.endswith("/login"):
            return link[:-6]

        link = link.split("/details/")[0]
        return link

    def shorten_link(link):
        splitter = link.split("/")
        if "job" in splitter:
            return "/".join(splitter[: splitter.index("job")])
        else:
            return link

    if link is None:
        return None
    if "myworkdayjobs.com" in link and link.startswith("https://"):
        return extra_process_workday(shorten_link(link))
    else:
        return None


async def get_company_workday_links(page: Page, company_link: str) -> List[JobPost]:

    def query_dict(d, key):
        if key in d:
            return d[key]
        else:
            return None

    def remap_fields(x):
        return JobPost(
            job_link=query_dict(x, "externalPath"),
            job_title=query_dict(x, "title"),
            job_location=query_dict(x, "locationsText"),
            job_commitment=None,
            company_name=None,
            company_website=None,
            company_job_website=query_dict(x, "companyPath"),
            posted_on=query_dict(x, "postedOn"),
        )

    def event_filter(event):
        request = event.request
        request_url = request.url
        if request_url.endswith("/jobs"):
            return True

    async def await_event():
        response = await page.wait_for_event("response", event_filter, timeout=5000)
        response_json = await response.json()
        return response_json["jobPostings"]

    results = []
    await page.goto(company_link)
    results += await await_event()
    while True:
        try:
            await page.locator('button[aria-label="next"]').click(timeout=5000)
            results += await await_event()
        except:
            break
    for res in results:
        try:
            res["companyPath"] = company_link
            res["externalPath"] = company_link + res["externalPath"]
        except:
            continue
    return [remap_fields(x) for x in results]
