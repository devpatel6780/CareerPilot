"""Greenhouse Job Board API client + normalization to a common raw-job shape.

Public, unauthenticated endpoint: https://boards-api.greenhouse.io
"""

import httpx

from .errors import CompanyNotFound
from .text_utils import strip_html


def fetch_greenhouse_jobs(company: str, limit: int = 20) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    try:
        response = httpx.get(url, params={"content": "true"}, timeout=15)
    except httpx.HTTPError as exc:
        raise CompanyNotFound(f"Could not reach Greenhouse for company '{company}': {exc}") from exc

    if response.status_code == 404:
        raise CompanyNotFound(f"No Greenhouse board found for company '{company}'")
    response.raise_for_status()

    jobs = response.json().get("jobs", [])[:limit]

    return [
        {
            "title": job.get("title", ""),
            "company": company,
            "location": (job.get("location") or {}).get("name", ""),
            "source": "greenhouse",
            "source_url": job.get("absolute_url", ""),
            "raw_description": strip_html(job.get("content", "")),
        }
        for job in jobs
    ]
