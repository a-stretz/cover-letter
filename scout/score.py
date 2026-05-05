"""
Scout Score — Sonnet-powered job scoring against Austin's candidate profile.

Each call is isolated (one job per API call) so failures don't cascade.
Prompt caching applied to the static system prompt + profile block.

Scoring rubric (0–10):
  0–3   Poor fit / auto-reject criteria present
  4–5   Marginal fit, significant gaps
  6–7   Good fit, worth applying
  8–9   Strong fit, prioritize
  10    Perfect fit (rare — reserved for exact match)
"""

import json
import re
import sys
import os
import anthropic

# Allow running from repo root or from scout/
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from profile import PROFILE, REJECT_CRITERIA, PRIORITY_TRIGGERS
from .models import MODELS

# ---------------------------------------------------------------------------
# Static prompt blocks — cached once per session
# ---------------------------------------------------------------------------

_PROFILE_TEXT = f"""# Candidate Profile

**Name:** {PROFILE['contact']['name']}
**Location:** {PROFILE['contact']['location']}
**Target title:** {PROFILE['identity']['title']}
**Specialization:** {PROFILE['identity']['specialization']}

## Identity
{PROFILE['identity']['one_liner']}

## Compensation range
Min: ${PROFILE['compensation']['min']:,} | Target: ${PROFILE['compensation']['target']:,} | Max: ${PROFILE['compensation']['max']:,}
Contract min: ${PROFILE['compensation']['contract_min_hourly']}/hr

## Location
Preferred: {PROFILE['location_preferences']['preferred']}
Acceptable KC metro: {', '.join(PROFILE['location_preferences']['acceptable'])}
Reject onsite outside KC: {PROFILE['location_preferences']['reject_onsite_outside_kc']}

## Current role
{PROFILE['experience']['current']['title']} at {PROFILE['experience']['current']['company']} ({PROFILE['experience']['current']['dates']})

## Key skills
- AI/ML/CV: {', '.join(PROFILE['skills']['ai_ml_cv'][:4])}
- Product: {', '.join(PROFILE['skills']['product_ux'][:4])}
- Biomechanics: {', '.join(PROFILE['skills']['biomechanics'][:3])}

## Target roles
{chr(10).join('- ' + r for r in PROFILE['target_roles'])}

## Domains
{chr(10).join('- ' + d for d in PROFILE['domains'])}

## Auto-reject criteria
{REJECT_CRITERIA}

## Priority triggers
{PRIORITY_TRIGGERS}
"""

_SYSTEM_PROMPT = """You are a job fit analyst for Austin Stretz. Given a job description, score the fit and return a structured JSON assessment.

Return ONLY valid JSON with this exact structure:
{
  "score": <float 0-10>,
  "tier": "APPLY" | "CONSIDER" | "SKIP",
  "strengths": [<up to 4 short strings>],
  "concerns": [<up to 4 short strings>],
  "auto_reject": false | "<reason if auto-reject criteria triggered>",
  "priority": false | "<reason if priority triggers apply>",
  "recommendation": "<one sentence action recommendation>"
}

Scoring guide:
  8–10  Strong / perfect fit — APPLY
  6–7   Good fit, some gaps — APPLY or CONSIDER
  4–5   Marginal fit — CONSIDER
  0–3   Poor fit or auto-reject — SKIP
"""


def _build_messages(job: dict) -> list[dict]:
    content = job.get("content") or f"[No full description available — title only: {job.get('title','')}]"
    return [
        {
            "role": "user",
            "content": (
                f"Company: {job.get('company_name', 'Unknown')}\n"
                f"Title: {job.get('title', 'Unknown')}\n"
                f"Location: {job.get('location', 'Unknown') or 'Not specified'}\n\n"
                f"--- JOB DESCRIPTION ---\n{content}"
            ),
        }
    ]


def score_job(job: dict, client: anthropic.Anthropic | None = None) -> dict:
    """
    Score a single job posting against Austin's profile.

    Returns the job dict with added keys:
      score, tier, strengths, concerns, auto_reject, priority, recommendation
    On error, returns the job dict unchanged plus 'score_error'.
    """
    if client is None:
        client = anthropic.Anthropic()

    try:
        response = client.messages.create(
            model=MODELS["reasoning"],
            max_tokens=512,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT + "\n\n" + _PROFILE_TEXT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=_build_messages(job),
        )

        text = response.content[0].text.strip()
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
        result = json.loads(text)

        # Attach scoring results to job dict
        job.update({
            "score":          float(result.get("score", 0)),
            "tier":           result.get("tier", "SKIP"),
            "strengths":      result.get("strengths", []),
            "concerns":       result.get("concerns", []),
            "auto_reject":    result.get("auto_reject", False),
            "priority":       result.get("priority", False),
            "recommendation": result.get("recommendation", ""),
            "_score_tokens":  {
                "input":        response.usage.input_tokens,
                "output":       response.usage.output_tokens,
                "cache_read":   getattr(response.usage, "cache_read_input_tokens", 0) or 0,
                "cache_create": getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
            },
        })

        print(
            f"[score] {job['score']:.1f}/10 ({job['tier']}) — "
            f"{job.get('title','')} @ {job.get('company_name','')}"
        )

    except Exception as e:
        print(f"[score] Error scoring {job.get('title','')} @ {job.get('company_name','')}: {e}")
        job["score_error"] = str(e)

    return job


def score_jobs(jobs: list[dict], client: anthropic.Anthropic | None = None) -> list[dict]:
    """Score a list of jobs and return them sorted by score descending."""
    if client is None:
        client = anthropic.Anthropic()

    scored = [score_job(job, client=client) for job in jobs]
    scored.sort(key=lambda j: j.get("score", 0), reverse=True)
    return scored
