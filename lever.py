import re
from typing import List, Optional

import bs4
from playwright.async_api._generated import Page

from data_model import JobPost


def lever_job_link_filter(link: Optional[str]) -> Optional[str]:

    def extra_process_lever(link):
        if len(link.split("/")) == 5:
            link = "/".join(link.split("/")[:-1])
        if link == "https://jobs.lever.co" or link == "https://jobs.lever.co/":
            return None
        return link

    if link is None:
        return None
    if not link.startswith("https://jobs.lever.co"):
        return None
    pattern = r"https://jobs\.lever\.co/([a-zA-Z0-9_-]+)$"
    if re.match(pattern, link):
        return extra_process_lever(link)
    link = "/".join(link.split("/")[:-1])
    return extra_process_lever(link)


async def get_company_lever_links(page: Page, company_link: str) -> List[JobPost]:

    def process_job_post(soup):
        job_link = soup.find("a")
        job_title = soup.find("h5")
        job_location = soup.find("span", class_="location")
        job_commitment = soup.find("span", class_="commitment")
        if job_link:
            job_link = job_link.get("href")
        if job_title:
            job_title = job_title.get_text()
        if job_location:
            job_location = job_location.get_text()
        if job_commitment:
            job_commitment = job_commitment.get_text()
        return dict(
            job_link=job_link,
            job_title=job_title,
            job_location=job_location,
            job_commitment=job_commitment,
        )

    await page.goto(company_link)
    soup = bs4.BeautifulSoup(await page.content(), "html.parser")
    footer = soup.find("div", class_="main-footer-text").find("a")
    company_website = footer.get("href")
    company_name = footer.get_text().replace("Home Page", "").rstrip()
    job_posts = [process_job_post(x) for x in soup.find_all("div", class_="posting")]
    for job_post in job_posts:
        job_post["company_name"] = company_name
        job_post["company_website"] = company_website
        job_post["company_job_website"] = company_link
    return [JobPost.model_validate(x) for x in job_posts]
