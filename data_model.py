from typing import Callable, Optional, Union

import pydantic


class JobProvider(pydantic.BaseModel):
    duckduckgo_query: str
    job_link_filter: Callable[[Optional[str]], Optional[str]]
    source_company_jobs: Callable[[str], Union[dict, list]]


class JobPost(pydantic.BaseModel):
    job_link: str
    job_title: str
    job_location: Optional[str]
    job_commitment: Optional[str]
    company_name: Optional[str]
    company_website: Optional[str]
    company_job_website: str
    posted_on: Optional[str] = None
    provider: Optional[str] = None
