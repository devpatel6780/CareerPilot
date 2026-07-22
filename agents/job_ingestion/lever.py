"""Lever Postings API client + normalization to a common raw-job shape.

Public, unauthenticated endpoint: https://api.lever.co/v0/postings/{company}
"""

import httpx

from .errors import CompanyNotFound
from .text_utils import strip_html


def fetch_lever_jobs(company: str, limit: int = 20) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{company}"
    try:
        response = httpx.get(url, params={"mode": "json"}, timeout=15)
    except httpx.HTTPError as exc:
        raise CompanyNotFound(f"Could not reach Lever for company '{company}': {exc}") from exc

    if response.status_code == 404:
        raise CompanyNotFound(f"No Lever postings found for company '{company}'")
    response.raise_for_status()

    postings = response.json()[:limit]

    normalized = []
    for posting in postings:
        sections = "\n\n".join(
            f"{lst.get('text', '')}\n{strip_html(lst.get('content', ''))}"
            for lst in posting.get("lists", [])
        )
        raw_description = "\n\n".join(
            part for part in [posting.get("descriptionPlain", ""), sections] if part
        )
        normalized.append(
            {
                "title": posting.get("text", ""),
                "company": company,
                "location": (posting.get("categories") or {}).get("location", ""),
                "source": "lever",
                "source_url": posting.get("hostedUrl", ""),
                "raw_description": raw_description,
            }
        )
    return normalized
