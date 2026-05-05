"""
Scout Registry — SQLite persistence for job postings and run history.

DB lives at scout/registry.db relative to this file.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "registry.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS job_postings (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name    TEXT NOT NULL,
            job_id          TEXT,
            title           TEXT NOT NULL,
            url             TEXT,
            location        TEXT,
            source          TEXT NOT NULL,
            content         TEXT,
            score           REAL,
            score_summary   TEXT,
            seen_at         TEXT NOT NULL DEFAULT (datetime('now')),
            scored_at       TEXT,
            UNIQUE(source, job_id)
        );

        CREATE TABLE IF NOT EXISTS scout_runs (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at              TEXT NOT NULL DEFAULT (datetime('now')),
            companies_polled    INTEGER DEFAULT 0,
            new_jobs_found      INTEGER DEFAULT 0,
            jobs_filtered_in    INTEGER DEFAULT 0,
            jobs_scored         INTEGER DEFAULT 0,
            cost_info           TEXT,
            summary             TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_postings_company
            ON job_postings(company_name);
        CREATE INDEX IF NOT EXISTS idx_postings_score
            ON job_postings(score DESC);
        CREATE INDEX IF NOT EXISTS idx_postings_seen
            ON job_postings(seen_at DESC);
    """)
    conn.commit()
    conn.close()


def is_seen(source: str, job_id: str) -> bool:
    """Return True if this (source, job_id) pair is already in the registry."""
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM job_postings WHERE source = ? AND job_id = ?",
        (source, job_id)
    ).fetchone()
    conn.close()
    return row is not None


def save_posting(
    company_name: str,
    job_id: str,
    title: str,
    source: str,
    url: Optional[str] = None,
    location: Optional[str] = None,
    content: Optional[str] = None,
) -> Optional[int]:
    """
    Insert a new job posting. Returns the new row id, or None if it was
    already present (INSERT OR IGNORE).
    """
    conn = get_db()
    cur = conn.execute(
        """INSERT OR IGNORE INTO job_postings
               (company_name, job_id, title, source, url, location, content)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (company_name, job_id, title, source, url, location, content)
    )
    conn.commit()
    row_id = cur.lastrowid if cur.rowcount else None
    conn.close()
    return row_id


def update_score(db_id: int, score: float, score_summary: dict) -> None:
    """Persist scoring results for a posting."""
    conn = get_db()
    conn.execute(
        """UPDATE job_postings
           SET score = ?, score_summary = ?, scored_at = datetime('now')
           WHERE id = ?""",
        (score, json.dumps(score_summary), db_id)
    )
    conn.commit()
    conn.close()


def update_content(db_id: int, content: str) -> None:
    """Store fetched full-text content for a posting."""
    conn = get_db()
    conn.execute(
        "UPDATE job_postings SET content = ? WHERE id = ?",
        (content, db_id)
    )
    conn.commit()
    conn.close()


def save_run(
    companies_polled: int,
    new_jobs_found: int,
    jobs_filtered_in: int,
    jobs_scored: int,
    cost_info: Optional[dict] = None,
    summary: Optional[dict] = None,
) -> int:
    """Record a completed scout run. Returns the run id."""
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO scout_runs
               (companies_polled, new_jobs_found, jobs_filtered_in,
                jobs_scored, cost_info, summary)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            companies_polled,
            new_jobs_found,
            jobs_filtered_in,
            jobs_scored,
            json.dumps(cost_info) if cost_info else None,
            json.dumps(summary) if summary else None,
        )
    )
    conn.commit()
    run_id = cur.lastrowid
    conn.close()
    return run_id


def get_recent_postings(limit: int = 50, min_score: Optional[float] = None) -> list[dict]:
    """Return recent postings, optionally filtered by minimum score."""
    conn = get_db()
    if min_score is not None:
        rows = conn.execute(
            """SELECT * FROM job_postings
               WHERE score >= ?
               ORDER BY score DESC, seen_at DESC
               LIMIT ?""",
            (min_score, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM job_postings
               ORDER BY seen_at DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_run_history(limit: int = 10) -> list[dict]:
    """Return recent scout runs."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM scout_runs ORDER BY run_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    print(f"Registry initialized at {DB_PATH}")

    # Insert a test posting
    rid = save_posting(
        company_name="Test Co",
        job_id="test-001",
        title="Senior PM",
        source="greenhouse",
        url="https://example.com/jobs/test-001",
        location="Remote",
    )
    print(f"Inserted posting id={rid}")

    # Duplicate should return None
    rid2 = save_posting(
        company_name="Test Co",
        job_id="test-001",
        title="Senior PM",
        source="greenhouse",
    )
    print(f"Duplicate insert returned id={rid2}  (expected None)")

    # is_seen check
    print(f"is_seen('greenhouse','test-001') = {is_seen('greenhouse','test-001')}")
    print(f"is_seen('greenhouse','missing')  = {is_seen('greenhouse','missing')}")

    # Score update
    if rid:
        update_score(rid, 8.2, {"strengths": ["CV", "PM"], "concerns": [], "recommendation": "APPLY"})
        print("Score updated")

    # Run record
    run_id = save_run(3, 12, 5, 5, summary={"top_job": "Senior PM @ Test Co"})
    print(f"Run saved id={run_id}")

    postings = get_recent_postings(limit=5)
    print(f"Recent postings: {len(postings)}")
    print("registry.py OK")
