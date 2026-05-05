"""
Scout Fetch — retrieve full job description text via Exa.

Uses exa.get_contents() to pull the rendered page for each job URL.
Content is truncated to ~300-350 words to keep scoring prompts lean.
"""

import os
from typing import Optional

_MAX_CHARS = 2_000  # ~300-350 words, fits comfortably in a Sonnet context window


def _get_exa_client():
    """Lazy import so the module loads even without exa-py installed."""
    try:
        from exa_py import Exa
    except ImportError as e:
        raise ImportError(
            "exa-py is required for fetch. Install with: pip install exa-py"
        ) from e
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        raise ValueError("EXA_API_KEY environment variable is not set")
    return Exa(api_key=api_key)


def truncate(text: str, max_chars: int = _MAX_CHARS) -> str:
    """Hard-truncate text and append a marker if trimmed."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[truncated]"


def fetch_job_content(url: str, exa=None) -> Optional[str]:
    """
    Fetch and return the text content of a job posting URL.
    Returns None if fetch fails or content is empty.
    """
    if not url:
        return None

    if exa is None:
        exa = _get_exa_client()

    try:
        results = exa.get_contents([url], text={"max_characters": _MAX_CHARS})
        if not results or not results.results:
            return None
        item = results.results[0]
        raw = getattr(item, "text", None) or ""
        if not raw.strip():
            return None
        return truncate(raw)
    except Exception as e:
        print(f"[fetch] Exa error for {url}: {e}")
        return None


def fetch_jobs(jobs: list[dict], exa=None) -> list[dict]:
    """
    Fetch content for each job dict (must have 'url' key).
    Adds 'content' key to each job in-place; skips jobs without a URL.
    Returns the same list with content populated where available.
    """
    if exa is None:
        try:
            exa = _get_exa_client()
        except (ImportError, ValueError) as e:
            print(f"[fetch] Cannot initialize Exa client: {e}")
            return jobs

    for job in jobs:
        url = job.get("url")
        if not url:
            continue
        content = fetch_job_content(url, exa=exa)
        if content:
            job["content"] = content
            print(f"[fetch] Fetched {len(content)} chars: {job.get('title','')} @ {job.get('company_name','')}")
        else:
            print(f"[fetch] No content: {job.get('title','')} @ {job.get('company_name','')}")

    return jobs
