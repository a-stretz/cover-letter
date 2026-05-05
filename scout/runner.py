"""
Scout Runner — full pipeline orchestration.

Pipeline:
  1. Load company list
  2. Poll Greenhouse / Lever for each company
  3. Dedup against registry
  4. Pass 1: title_filter
  5. Pass 2: haiku_filter (Haiku model)
  6. Fetch full content via Exa
  7. Score each job via Sonnet
  8. Persist to registry
  9. Save run record + return summary

Entry point: run_scout()
"""

import time
import anthropic
from typing import Optional

from .companies import get_companies
from .registry import init_db, save_posting, update_content, update_score, save_run
from .search import search_company, filter_new
from .filter import title_filter, haiku_filter
from .fetch import fetch_jobs, _get_exa_client
from .score import score_jobs


def _accumulate_cost(totals: dict, job: dict) -> None:
    """Add per-job token usage into a running totals dict."""
    tokens = job.get("_score_tokens", {})
    totals["input"]        += tokens.get("input", 0)
    totals["output"]       += tokens.get("output", 0)
    totals["cache_read"]   += tokens.get("cache_read", 0)
    totals["cache_create"] += tokens.get("cache_create", 0)


def run_scout(
    tier_filter: Optional[int] = None,
    skip_fetch: bool = False,
    skip_score: bool = False,
    min_score_to_return: float = 5.0,
) -> dict:
    """
    Execute the full scout pipeline.

    Args:
        tier_filter:          Only poll companies at this tier (1, 2, or 3).
                              None = all tiers.
        skip_fetch:           Skip Exa content fetch (useful for dry runs).
        skip_score:           Skip Sonnet scoring (useful for dry runs).
        min_score_to_return:  Minimum score threshold for results returned
                              to the caller. Lower-scoring jobs are still
                              saved to registry.

    Returns dict with:
        run_id, companies_polled, new_jobs_found, jobs_filtered_in,
        jobs_scored, results (list of scored job dicts), cost_info, elapsed_s
    """
    init_db()
    start = time.time()

    client = anthropic.Anthropic()
    exa = None
    if not skip_fetch:
        try:
            exa = _get_exa_client()
        except Exception as e:
            print(f"[runner] Exa unavailable, skipping fetch: {e}")
            skip_fetch = True

    companies = get_companies(tier=tier_filter)
    print(f"[runner] Polling {len(companies)} companies (tier={tier_filter or 'all'})")

    # ── Step 1–3: search + dedup ──────────────────────────────────────────
    all_raw: list[dict] = []
    for company in companies:
        raw = search_company(company)
        new = filter_new(raw)
        print(f"[runner] {company['name']}: {len(raw)} total, {len(new)} new")
        all_raw.extend(new)

    new_jobs_found = len(all_raw)
    print(f"[runner] Total new postings: {new_jobs_found}")

    if not all_raw:
        run_id = save_run(
            companies_polled=len(companies),
            new_jobs_found=0,
            jobs_filtered_in=0,
            jobs_scored=0,
            summary={"message": "No new postings found"},
        )
        return {
            "run_id": run_id,
            "companies_polled": len(companies),
            "new_jobs_found": 0,
            "jobs_filtered_in": 0,
            "jobs_scored": 0,
            "results": [],
            "cost_info": None,
            "elapsed_s": round(time.time() - start, 1),
        }

    # ── Step 4–5: filter ──────────────────────────────────────────────────
    after_title = title_filter(all_raw)
    print(f"[runner] After title filter: {len(after_title)}/{new_jobs_found}")

    after_haiku = haiku_filter(after_title, client=client)
    print(f"[runner] After Haiku filter: {len(after_haiku)}/{len(after_title)}")
    jobs_filtered_in = len(after_haiku)

    # Persist filtered-in jobs to registry before scoring
    for job in after_haiku:
        row_id = save_posting(
            company_name=job["company_name"],
            job_id=job["job_id"],
            title=job["title"],
            source=job["source"],
            url=job.get("url"),
            location=job.get("location"),
        )
        job["_db_id"] = row_id

    # Also save filtered-out jobs so we don't re-poll them next run
    filtered_out = [j for j in all_raw if j not in after_haiku]
    for job in filtered_out:
        save_posting(
            company_name=job["company_name"],
            job_id=job["job_id"],
            title=job["title"],
            source=job["source"],
            url=job.get("url"),
            location=job.get("location"),
        )

    if not after_haiku:
        run_id = save_run(
            companies_polled=len(companies),
            new_jobs_found=new_jobs_found,
            jobs_filtered_in=0,
            jobs_scored=0,
            summary={"message": "No jobs passed filter"},
        )
        return {
            "run_id": run_id,
            "companies_polled": len(companies),
            "new_jobs_found": new_jobs_found,
            "jobs_filtered_in": 0,
            "jobs_scored": 0,
            "results": [],
            "cost_info": None,
            "elapsed_s": round(time.time() - start, 1),
        }

    # ── Step 6: fetch ─────────────────────────────────────────────────────
    if not skip_fetch and exa:
        after_haiku = fetch_jobs(after_haiku, exa=exa)
        for job in after_haiku:
            if job.get("content") and job.get("_db_id"):
                update_content(job["_db_id"], job["content"])

    # ── Step 7: score ─────────────────────────────────────────────────────
    token_totals = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0}
    jobs_scored = 0

    if not skip_score:
        after_haiku = score_jobs(after_haiku, client=client)
        for job in after_haiku:
            if job.get("_db_id") and "score" in job:
                update_score(
                    job["_db_id"],
                    job["score"],
                    {
                        "tier":           job.get("tier"),
                        "strengths":      job.get("strengths"),
                        "concerns":       job.get("concerns"),
                        "auto_reject":    job.get("auto_reject"),
                        "priority":       job.get("priority"),
                        "recommendation": job.get("recommendation"),
                    },
                )
                _accumulate_cost(token_totals, job)
                jobs_scored += 1

    # ── Step 8: build cost summary ────────────────────────────────────────
    cost_info = None
    if token_totals["input"] > 0:
        # Rough Sonnet 4.6 pricing: $3/M input, $15/M output, $0.30/M cache read
        input_cost   = (token_totals["input"]        / 1_000_000) * 3.00
        output_cost  = (token_totals["output"]       / 1_000_000) * 15.00
        cached_cost  = (token_totals["cache_read"]   / 1_000_000) * 0.30
        create_cost  = (token_totals["cache_create"] / 1_000_000) * 3.75
        total_cost   = input_cost + output_cost + cached_cost + create_cost
        cache_savings = (token_totals["cache_read"]  / 1_000_000) * (3.00 - 0.30)
        cost_info = {
            "total_cost":    round(total_cost, 4),
            "cache_savings": round(cache_savings, 4),
            **token_totals,
        }

    # ── Step 9: save run + return ─────────────────────────────────────────
    results = [
        {k: v for k, v in j.items() if not k.startswith("_")}
        for j in after_haiku
        if j.get("score", 0) >= min_score_to_return or not skip_score is False
    ]
    results.sort(key=lambda j: j.get("score", 0), reverse=True)

    summary = {
        "top_job": results[0]["title"] + " @ " + results[0]["company_name"] if results else None,
        "apply_count": sum(1 for j in results if j.get("tier") == "APPLY"),
        "consider_count": sum(1 for j in results if j.get("tier") == "CONSIDER"),
    }

    run_id = save_run(
        companies_polled=len(companies),
        new_jobs_found=new_jobs_found,
        jobs_filtered_in=jobs_filtered_in,
        jobs_scored=jobs_scored,
        cost_info=cost_info,
        summary=summary,
    )

    elapsed = round(time.time() - start, 1)
    print(f"[runner] Done in {elapsed}s — run_id={run_id}, {len(results)} results returned")

    return {
        "run_id":            run_id,
        "companies_polled":  len(companies),
        "new_jobs_found":    new_jobs_found,
        "jobs_filtered_in":  jobs_filtered_in,
        "jobs_scored":       jobs_scored,
        "results":           results,
        "cost_info":         cost_info,
        "elapsed_s":         elapsed,
    }
