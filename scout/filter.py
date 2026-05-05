"""
Scout Filter — two-pass relevance gate before expensive Exa fetches.

Pass 1 (title_filter):   Fast regex/keyword match on job title.
Pass 2 (haiku_filter):   Haiku model pass — confirms relevance given title +
                         company name without paying for full JD fetch.

Both passes are conservative: when in doubt, let the job through.
"""

import json
import re
import anthropic
from .models import MODELS

# ---------------------------------------------------------------------------
# Pass 1 — title keyword filter
# ---------------------------------------------------------------------------

# Titles that are a clear "yes"
_INCLUDE_PATTERNS = re.compile(
    r"""
    \b(
        product\s+manager |
        product\s+management |
        technical\s+product |
        senior\s+pm |
        staff\s+pm |
        principal\s+pm |
        director\s+of\s+product |
        vp\s+of\s+product |
        head\s+of\s+product |
        ai\s+product |
        ml\s+product |
        product\s+lead |
        product\s+owner
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Titles that are clearly irrelevant (avoid false positives from generic PM-adjacent words)
_EXCLUDE_PATTERNS = re.compile(
    r"""
    \b(
        software\s+engineer |
        data\s+scientist |
        data\s+engineer |
        machine\s+learning\s+engineer |
        ml\s+engineer |
        devops |
        site\s+reliability |
        accountant |
        lawyer |
        legal |
        marketing\s+manager |
        sales\s+rep |
        hr\s+manager |
        recruiter |
        executive\s+assistant |
        finance\s+manager
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


def title_filter(jobs: list[dict]) -> list[dict]:
    """
    Keep jobs whose title matches an include pattern AND does not match an
    exclude pattern. Jobs with ambiguous titles pass through.
    """
    kept = []
    for job in jobs:
        title = job.get("title", "")
        if _EXCLUDE_PATTERNS.search(title):
            continue
        if _INCLUDE_PATTERNS.search(title):
            kept.append(job)
        # titles without any match are dropped — too noisy for Haiku spend
    return kept


# ---------------------------------------------------------------------------
# Pass 2 — Haiku keyword relevance check
# ---------------------------------------------------------------------------

_HAIKU_SYSTEM = """You are a job relevance classifier for Austin Stretz, a Technical Product Architect specializing in AI-driven computer vision, biomechanics, and real-time systems. His target roles are Technical Product Manager or Senior PM positions in AI, computer vision, sports technology, video analytics, or related ML product domains. He is open to remote work or roles in the Kansas City metro area, with a salary range of $100K–$160K.

Respond ONLY with valid JSON: {"relevant": true|false, "reason": "<one sentence>"}"""


def haiku_filter(jobs: list[dict], client: anthropic.Anthropic | None = None) -> list[dict]:
    """
    Use Haiku to confirm relevance for each job that passed title_filter.
    Jobs where the model returns relevant=true (or on API error) are kept.
    """
    if not jobs:
        return []

    if client is None:
        client = anthropic.Anthropic()

    kept = []
    for job in jobs:
        prompt = (
            f"Job title: {job.get('title', '')}\n"
            f"Company: {job.get('company_name', '')}\n"
            f"Location: {job.get('location', '') or 'Unknown'}\n\n"
            "Is this job potentially relevant for Austin?"
        )
        try:
            response = client.messages.create(
                model=MODELS["orchestration"],
                max_tokens=64,
                system=[
                    {
                        "type": "text",
                        "text": _HAIKU_SYSTEM,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            # Strip markdown code fences if present
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
            result = json.loads(text)
            if result.get("relevant", True):
                job["_filter_reason"] = result.get("reason", "")
                kept.append(job)
            else:
                print(f"[filter] Haiku dropped: {job['title']} @ {job['company_name']} — {result.get('reason','')}")
        except Exception as e:
            # On error, let the job through rather than silently drop it
            print(f"[filter] Haiku error for {job['title']}: {e}")
            kept.append(job)

    return kept
