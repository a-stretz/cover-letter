"""
Scout Search — poll Greenhouse and Lever APIs for new job postings.

Greenhouse boards API:  GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs
Lever postings API:     GET https://api.lever.co/v0/postings/{company}?mode=json

Returns raw job dicts; registry dedup is handled by the caller (runner.py)
so that fetch counts are accurate. is_seen() is exposed for pre-filtering.
"""

import requests
from typing import Optional
from .registry import is_seen

_GH_BASE = "https://boards-api.greenhouse.io/v1/boards"
_LEVER_BASE = "https://api.lever.co/v0/postings"
_TIMEOUT = 15  # seconds


def _get(url: str, params: dict | None = None) -> Optional[dict | list]:
    try:
        r = requests.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"[search] HTTP error for {url}: {e}")
        return None


# ---------------------------------------------------------------------------
# Greenhouse
# ---------------------------------------------------------------------------

def poll_greenhouse(board_token: str, company_name: str) -> list[dict]:
    """
    Fetch all active jobs from a Greenhouse board.

    Returns list of normalized job dicts:
      job_id, title, url, location, company_name, source='greenhouse'
    """
    data = _get(f"{_GH_BASE}/{board_token}/jobs", params={"content": "true"})
    if not data or "jobs" not in data:
        return []

    results = []
    for job in data["jobs"]:
        job_id = str(job.get("id", ""))
        if not job_id:
            continue
        location = ""
        if job.get("location"):
            location = job["location"].get("name", "")
        results.append({
            "job_id": job_id,
            "title": job.get("title", ""),
            "url": job.get("absolute_url", ""),
            "location": location,
            "company_name": company_name,
            "source": "greenhouse",
        })
    return results


# ---------------------------------------------------------------------------
# Lever
# ---------------------------------------------------------------------------

def poll_lever(lever_company: str, company_name: str) -> list[dict]:
    """
    Fetch all active postings from Lever.

    Returns list of normalized job dicts:
      job_id, title, url, location, company_name, source='lever'
    """
    data = _get(f"{_LEVER_BASE}/{lever_company}", params={"mode": "json"})
    if not isinstance(data, list):
        return []

    results = []
    for job in data:
        job_id = job.get("id", "")
        if not job_id:
            continue
        categories = job.get("categories", {})
        location = categories.get("location", "") or categories.get("allLocations", [""])[0]
        results.append({
            "job_id": str(job_id),
            "title": job.get("text", ""),
            "url": job.get("hostedUrl", ""),
            "location": location,
            "company_name": company_name,
            "source": "lever",
        })
    return results


# ---------------------------------------------------------------------------
# Company dispatcher
# ---------------------------------------------------------------------------

def search_company(company: dict) -> list[dict]:
    """
    Poll all configured APIs for a company and return raw job list.
    Does NOT deduplicate against registry — caller handles that.
    """
    jobs: list[dict] = []

    if company.get("greenhouse_board_token"):
        gh_jobs = poll_greenhouse(company["greenhouse_board_token"], company["name"])
        print(f"[search] {company['name']} (Greenhouse): {len(gh_jobs)} postings")
        jobs.extend(gh_jobs)

    if company.get("lever_company"):
        lv_jobs = poll_lever(company["lever_company"], company["name"])
        print(f"[search] {company['name']} (Lever): {len(lv_jobs)} postings")
        jobs.extend(lv_jobs)

    return jobs


def filter_new(jobs: list[dict]) -> list[dict]:
    """Remove jobs already in the registry."""
    return [j for j in jobs if not is_seen(j["source"], j["job_id"])]
