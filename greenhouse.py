from typing import List, Optional

import bs4
from playwright.async_api._generated import Page

from data_model import JobPost


def greenhouse_link_filter(link: Optional[str]) -> Optional[str]:
    def extra_process_greenhouse(link: str):
        link = link.replace("embed/job_board?for=", "")
        link = link.replace("embed/job_app?for=", "")
        link: str = link.split("/jobs/")[0]
        link = link.split("?")[0]
        if link.endswith("embed/job_app") or link.endswith("embed/job_app/"):
            return None
        return link

    def process_job_link(x):
        if x.split("/")[-2] != "jobs":
            return x
        else:
            return "/".join(x.split("/")[:-2])

    if link is None:
        return None
    if not link.startswith("https://boards.greenhouse.io"):
        return None
    return extra_process_greenhouse(process_job_link(link))


async def get_company_greenhouse_links(page: Page, company_link: str) -> List[JobPost]:

    def process_opening(x):
        job_link = x.find("a")
        if job_link:
            job_link = job_link.get("href")
        job_title = x.find("a")
        if job_title:
            job_title = job_title.get_text()
        job_location = x.find("span", class_="location")
        if job_location:
            job_location = job_location.get_text()
        job_commitment = None
        return dict(
            job_link="https://boards.greenhouse.io" + job_link,
            job_title=job_title,
            job_location=job_location,
            job_commitment=job_commitment,
        )

    await page.goto(company_link)
    soup = bs4.BeautifulSoup(await page.content(), "html.parser")
    company_link = soup.find("a").get("href")
    company_name = soup.find("h1").get_text()
    job_posts = [process_opening(x) for x in soup.find_all("div", class_="opening")]
    for job_post in job_posts:
        job_post["company_name"] = company_name
        job_post["company_website"] = company_link
        job_post["company_job_website"] = company_link
    return [JobPost.model_validate(x) for x in job_posts]
