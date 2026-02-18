"""
Batch Job Screener - Stage 1 Quick Screening
Processes large volumes of job postings using lightweight API calls.
Designed for high throughput: ~25-30 jobs/minute at ~$1-3 per 1,000 jobs.
"""

import os
import json
import csv
import io
import uuid
import time
from datetime import datetime
from anthropic import Anthropic

# Optional Excel support
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


def get_client():
    """Get Anthropic API client"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return Anthropic(api_key=api_key)


# Screening thresholds by mode
SCREEN_MODES = {
    "conservative": {
        "min_score": 6,
        "description": "Only screen in strong matches (score >= 6)"
    },
    "balanced": {
        "min_score": 4,
        "description": "Screen in moderate and strong matches (score >= 4)"
    },
    "aggressive": {
        "min_score": 2,
        "description": "Screen in almost everything except obvious mismatches (score >= 2)"
    }
}

# Hard reject patterns for local pre-filtering (no API needed)
HARD_REJECT_TITLES = [
    "software engineer", "data engineer", "devops", "sre",
    "marketing manager", "sales manager", "account executive",
    "graphic designer", "ux designer", "ui designer",
    "data scientist", "ml engineer", "machine learning engineer",
    "frontend engineer", "backend engineer", "full stack",
    "qa engineer", "test engineer", "security engineer",
    "hr manager", "recruiter", "talent acquisition",
    "finance", "accounting", "legal", "counsel",
    "customer success", "support engineer",
]

# Title patterns that are strong matches
STRONG_MATCH_TITLES = [
    "product manager", "product owner", "technical product",
    "ai product", "platform product", "senior product",
    "director of product", "vp product", "head of product",
    "program manager",
]

# KC metro locations
KC_METRO = [
    "kansas city", "overland park", "shawnee", "lenexa", "olathe",
    "independence", "blue springs", "belton", "liberty", "de soto",
    "leawood", "prairie village", "mission", "merriam",
]

SCREEN_PROMPT = """You are a job screening assistant for Austin Stretz, an AI Product Manager.

CANDIDATE PROFILE (brief):
- Current: AI Product Manager at NeoSavant.ai (edge-AI computer vision, sports analytics)
- Previous: Product Lead / Co-Founder at 1872 Consulting (HR Tech, B2B SaaS, Fortune 100)
- Skills: Product strategy, computer vision, Python, AI/ML products, B2B SaaS
- Certs: A-CSPO, AI PM (IBM), CSPO
- Wants: Remote preferred, KC metro acceptable, $100k+ salary
- Target roles: AI/ML PM, Technical PM, Platform PM, B2B SaaS PM, Product Owner

SCREENING CRITERIA:
Auto-REJECT if ANY:
1. Onsite required outside KC metro
2. Max salary < $100k (if stated)
3. Requires 10+ years experience explicitly
4. Not a PM/PO/TPM role (engineering IC, marketing, sales, etc.)
5. Requires specific skills Austin lacks (hardware eng, deep ML research)

SCORING (1-10):
9-10: Dream role (AI PM, sports tech, remote, strong alignment)
7-8: Strong match (good PM role, relevant domain, good location)
5-6: Moderate match (PM role, some alignment, acceptable terms)
3-4: Weak match (tangential PM role, some concerns)
1-2: Poor match (minimal relevance, multiple concerns)

Screen these {count} jobs. For EACH job, output a JSON object.

JOBS TO SCREEN:
{jobs}

OUTPUT: Return a JSON array with one object per job:
[
  {{
    "index": 0,
    "decision": "SCREEN_IN" or "SCREEN_OUT",
    "match_score": 1-10,
    "confidence": "HIGH" or "MEDIUM" or "LOW",
    "primary_reject_reason": "reason string" or null,
    "quick_notes": "1-2 sentence summary of fit"
  }},
  ...
]

Respond with ONLY valid JSON array, no markdown."""


def parse_xlsx(file_content: bytes) -> list:
    """Parse Excel (.xlsx) file into list of job dicts."""
    if not HAS_OPENPYXL:
        raise ImportError("openpyxl is required for Excel file support. Install with: pip install openpyxl")

    wb = openpyxl.load_workbook(io.BytesIO(file_content), read_only=True, data_only=True)
    ws = wb.active

    jobs = []
    headers = None

    for row_idx, row in enumerate(ws.iter_rows(values_only=True)):
        if row_idx == 0:
            # First row is headers - normalize them
            headers = []
            for cell in row:
                if cell is None:
                    headers.append(None)
                else:
                    headers.append(str(cell).strip().lower().replace(' ', '_'))
            continue

        if not headers:
            continue

        # Build job dict from row
        job = {}
        for col_idx, cell in enumerate(row):
            if col_idx >= len(headers) or headers[col_idx] is None:
                continue
            clean_key = headers[col_idx]
            if not clean_key:
                continue
            job[clean_key] = str(cell).strip() if cell is not None else ''

        # Skip completely empty rows
        if not any(job.values()):
            continue

        # Map common column variations (same as CSV)
        normalized = {
            'job_title': job.get('job_title') or job.get('title') or job.get('position') or '',
            'company_name': job.get('company_name') or job.get('company') or job.get('employer') or '',
            'location': job.get('location') or job.get('city') or job.get('job_location') or '',
            'job_url': job.get('job_url') or job.get('url') or job.get('link') or job.get('apply_url') or job.get('job_linkedin_url') or '',
            'job_snippet': job.get('job_snippet') or job.get('snippet') or job.get('description') or job.get('summary') or '',
            'salary_range': job.get('salary_range') or job.get('salary') or job.get('compensation') or job.get('pay') or '',
            'posted_date': job.get('posted_date') or job.get('date') or job.get('date_posted') or job.get('posted_on') or '',
        }

        # Skip rows with no title or company
        if not normalized['job_title'] and not normalized['company_name']:
            continue

        jobs.append(normalized)

    wb.close()
    return jobs


def parse_csv(csv_text: str) -> list:
    """Parse CSV or TSV text into list of job dicts. Auto-detects delimiter."""
    # Auto-detect delimiter (tab vs comma)
    first_line = csv_text.split('\n')[0] if csv_text else ''
    if '\t' in first_line:
        delimiter = '\t'
    else:
        delimiter = ','

    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delimiter)
    jobs = []
    for row in reader:
        # Normalize column names (handle various CSV formats)
        # Guard against None keys from blank/trailing CSV column headers
        job = {}
        for key, value in row.items():
            if key is None:
                continue
            clean_key = key.strip().lower().replace(' ', '_')
            if not clean_key:
                continue
            job[clean_key] = (value or '').strip()

        # Skip completely empty rows
        if not any(job.values()):
            continue

        # Map common column variations
        normalized = {
            'job_title': job.get('job_title') or job.get('title') or job.get('position') or '',
            'company_name': job.get('company_name') or job.get('company') or job.get('employer') or '',
            'location': job.get('location') or job.get('city') or job.get('job_location') or '',
            'job_url': job.get('job_url') or job.get('url') or job.get('link') or job.get('apply_url') or job.get('job_linkedin_url') or '',
            'job_snippet': job.get('job_snippet') or job.get('snippet') or job.get('description') or job.get('summary') or '',
            'salary_range': job.get('salary_range') or job.get('salary') or job.get('compensation') or job.get('pay') or '',
            'posted_date': job.get('posted_date') or job.get('date') or job.get('date_posted') or job.get('posted_on') or '',
        }

        # Skip rows with no title or company (not useful for screening)
        if not normalized['job_title'] and not normalized['company_name']:
            continue

        jobs.append(normalized)

    return jobs


def local_prefilter(job: dict) -> dict:
    """
    Fast local pre-filtering before API call.
    Returns None if job should pass to API, or a reject result if hard-rejected.
    """
    title = job.get('job_title', '').lower()
    location = job.get('location', '').lower()

    # Check for hard reject titles
    for reject_title in HARD_REJECT_TITLES:
        if reject_title in title and 'product' not in title:
            return {
                "decision": "SCREEN_OUT",
                "match_score": 1,
                "confidence": "HIGH",
                "primary_reject_reason": f"Role type mismatch: '{job.get('job_title', '')}'",
                "quick_notes": "Not a product management role."
            }

    # Check for onsite outside KC
    if location and 'remote' not in location:
        is_kc = any(kc in location for kc in KC_METRO)
        # Only hard-reject if location is clearly specified and not KC
        # Don't reject if location is vague
        if not is_kc and any(word in location.lower() for word in ['onsite', 'on-site', 'in-office', 'in office']):
            return {
                "decision": "SCREEN_OUT",
                "match_score": 1,
                "confidence": "HIGH",
                "primary_reject_reason": f"Onsite required: {job.get('location', '')}",
                "quick_notes": "Onsite outside KC metro."
            }

    return None  # Pass to API screening


def format_job_for_prompt(job: dict, index: int) -> str:
    """Format a single job for the screening prompt."""
    parts = [f"Job {index}:"]
    if job.get('job_title'):
        parts.append(f"  Title: {job['job_title']}")
    if job.get('company_name'):
        parts.append(f"  Company: {job['company_name']}")
    if job.get('location'):
        parts.append(f"  Location: {job['location']}")
    if job.get('salary_range'):
        parts.append(f"  Salary: {job['salary_range']}")
    if job.get('job_snippet'):
        # Truncate snippet to save tokens
        # Also escape curly braces so they don't interfere with .format()
        snippet = job['job_snippet'][:300].replace('{', '{{').replace('}', '}}')
        parts.append(f"  Snippet: {snippet}")
    return '\n'.join(parts)


def screen_batch_api(jobs: list, batch_size: int = 20) -> list:
    """
    Screen jobs using Claude API in batches.
    Processes batch_size jobs per API call for efficiency.
    """
    client = get_client()
    all_results = []

    for i in range(0, len(jobs), batch_size):
        batch = jobs[i:i + batch_size]

        # Format jobs for prompt
        jobs_text = '\n\n'.join(
            format_job_for_prompt(job, idx)
            for idx, job in enumerate(batch)
        )

        prompt = SCREEN_PROMPT.format(
            count=len(batch),
            jobs=jobs_text
        )

        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Guard against None response (e.g. max_tokens hit or API anomaly)
            raw_text = message.content[0].text if message.content else None
            if not raw_text:
                raise ValueError(f"Empty API response (stop_reason={message.stop_reason})")
            response_text = raw_text.strip()

            # Parse JSON
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]
                if lines[-1].strip() == '```':
                    lines = lines[:-1]
                response_text = '\n'.join(lines)

            batch_results = json.loads(response_text)

            # Ensure we have results for all jobs in batch
            if len(batch_results) < len(batch):
                # Pad with default results
                for j in range(len(batch_results), len(batch)):
                    batch_results.append({
                        "index": j,
                        "decision": "SCREEN_IN",
                        "match_score": 5,
                        "confidence": "LOW",
                        "primary_reject_reason": None,
                        "quick_notes": "Screening incomplete, defaulting to screen-in."
                    })

            all_results.extend(batch_results)

        except Exception as e:
            # On API failure, default all jobs in batch to SCREEN_IN
            for j in range(len(batch)):
                all_results.append({
                    "index": j,
                    "decision": "SCREEN_IN",
                    "match_score": 5,
                    "confidence": "LOW",
                    "primary_reject_reason": None,
                    "quick_notes": f"API error, defaulting to screen-in: {str(e)[:80]}"
                })

        # Brief delay between batches to avoid rate limits
        if i + batch_size < len(jobs):
            time.sleep(0.5)

    return all_results


def screen_jobs(jobs: list, mode: str = "balanced") -> list:
    """
    Main screening function. Combines local pre-filtering with API screening.

    Args:
        jobs: List of job dicts with job_title, company_name, location, etc.
        mode: Screening mode - 'conservative', 'balanced', or 'aggressive'

    Returns:
        List of job dicts with screening results added.
    """
    min_score = SCREEN_MODES.get(mode, SCREEN_MODES["balanced"])["min_score"]

    # Phase 1: Local pre-filtering
    api_jobs = []  # Jobs that need API screening
    api_job_indices = []  # Original indices for API jobs
    results = [None] * len(jobs)  # Pre-allocate results array

    for i, job in enumerate(jobs):
        local_result = local_prefilter(job)
        if local_result:
            results[i] = {**job, **local_result}
        else:
            api_jobs.append(job)
            api_job_indices.append(i)

    # Phase 2: API screening for remaining jobs
    if api_jobs:
        api_results = screen_batch_api(api_jobs)

        for j, api_result in enumerate(api_results):
            if j < len(api_job_indices):
                orig_idx = api_job_indices[j]
                job = jobs[orig_idx]

                # Apply mode threshold
                score = api_result.get('match_score', 5)
                if score < min_score:
                    api_result['decision'] = 'SCREEN_OUT'
                    if not api_result.get('primary_reject_reason'):
                        api_result['primary_reject_reason'] = f'Score {score} below {mode} threshold ({min_score})'

                results[orig_idx] = {**job, **api_result}

    # Fill any gaps
    for i in range(len(results)):
        if results[i] is None:
            results[i] = {
                **jobs[i],
                "decision": "SCREEN_IN",
                "match_score": 5,
                "confidence": "LOW",
                "primary_reject_reason": None,
                "quick_notes": "Unscreened, defaulting to screen-in."
            }

    return results


def generate_batch_summary(results: list) -> dict:
    """Generate summary statistics for a completed batch screening."""
    screen_in = [r for r in results if r.get('decision') == 'SCREEN_IN']
    screen_out = [r for r in results if r.get('decision') == 'SCREEN_OUT']

    scores = [r.get('match_score', 0) for r in screen_in]
    avg_score = sum(scores) / len(scores) if scores else 0

    # Reject reason breakdown
    reject_reasons = {}
    for r in screen_out:
        reason = r.get('primary_reject_reason', 'Unknown')
        # Categorize
        if 'role type' in reason.lower() or 'not a product' in reason.lower():
            key = 'Role Mismatch'
        elif 'onsite' in reason.lower() or 'location' in reason.lower():
            key = 'Location'
        elif 'salary' in reason.lower() or 'compensation' in reason.lower():
            key = 'Compensation'
        elif 'score' in reason.lower() and 'threshold' in reason.lower():
            key = 'Below Score Threshold'
        else:
            key = 'Other'
        reject_reasons[key] = reject_reasons.get(key, 0) + 1

    return {
        "total": len(results),
        "screen_in": len(screen_in),
        "screen_out": len(screen_out),
        "screen_in_rate": f"{len(screen_in)/len(results)*100:.1f}%" if results else "0%",
        "avg_match_score": round(avg_score, 1),
        "high_priority": len([r for r in screen_in if r.get('match_score', 0) >= 8]),
        "reject_breakdown": reject_reasons,
        "score_distribution": {
            "9-10": len([r for r in results if r.get('match_score', 0) >= 9]),
            "7-8": len([r for r in results if 7 <= r.get('match_score', 0) <= 8]),
            "5-6": len([r for r in results if 5 <= r.get('match_score', 0) <= 6]),
            "3-4": len([r for r in results if 3 <= r.get('match_score', 0) <= 4]),
            "1-2": len([r for r in results if r.get('match_score', 0) <= 2]),
        }
    }
