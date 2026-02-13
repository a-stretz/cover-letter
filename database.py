"""
Database module for SQLite operations
Enhanced with new columns for detailed tracking
"""

import sqlite3
import json
from flask import g, current_app

DATABASE = 'job_applications.db'


def get_db():
    """Get database connection for current request"""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database with schema"""
    db = get_db()

    # Create the main table with ALL columns defined upfront
    db.execute('''
        CREATE TABLE IF NOT EXISTS jobs_analyzed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_description TEXT NOT NULL,
            company_name TEXT,
            job_title TEXT,
            additional_context TEXT,

            -- Decision outputs
            decision TEXT NOT NULL CHECK(decision IN ('APPLY', 'REJECT')),
            decision_summary TEXT,
            priority_level TEXT CHECK(priority_level IN ('PRIORITY', 'STANDARD', 'REJECT')),

            -- Resume selection (selects from 3 pre-built variants, does NOT generate)
            selected_resume TEXT CHECK(selected_resume IN ('AI Product Manager', 'Platform Product Manager', 'B2B SaaS Product Manager')),
            resume_confidence TEXT CHECK(resume_confidence IN ('Low', 'Medium', 'High')),
            resume_reasoning TEXT,
            resume_key_signals TEXT,

            -- Location & Compensation
            location_type TEXT,
            location_details TEXT,
            compensation_range TEXT,
            compensation_fit TEXT,

            -- Company info
            company_domain TEXT,

            -- Experience Match (Enhanced)
            experience_score INTEGER,
            experience_label TEXT,
            experience_summary TEXT,
            responsibility_alignment TEXT,
            domain_experience_notes TEXT,
            technical_skills_match TEXT,
            requirements_fit_notes TEXT,

            -- Keywords and reasons
            keywords_detected TEXT,
            reject_reasons_json TEXT,
            priority_reasons_json TEXT,
            resume_rationale TEXT,

            -- Cover letter (metadata only, not full text)
            cover_letter_filepath TEXT,
            cover_letter_generated INTEGER DEFAULT 0,

            -- Follow-up messages
            messages_json TEXT,

            -- Role summary
            role_summary TEXT,

            -- JD file path
            jd_filepath TEXT,

            -- Tracking
            status TEXT DEFAULT 'analyzed' CHECK(status IN ('analyzed', 'applied', 'interview_scheduled', 'interview_completed', 'rejected', 'offer')),
            status_updated_at TIMESTAMP,
            notes TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create indexes separately (after table exists with all columns)
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_jobs_decision ON jobs_analyzed(decision)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs_analyzed(priority_level)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs_analyzed(status)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs_analyzed(company_name)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs_analyzed(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_resume ON jobs_analyzed(selected_resume)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs_analyzed(location_type)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_comp_fit ON jobs_analyzed(compensation_fit)",
    ]

    for index_sql in indexes:
        try:
            db.execute(index_sql)
        except sqlite3.OperationalError:
            pass  # Index might already exist or column missing in old DB

    db.commit()

    # Migration: Add new columns to existing tables if they don't exist
    cursor = db.execute("PRAGMA table_info(jobs_analyzed)")
    existing_columns = [row[1] for row in cursor.fetchall()]

    new_columns = [
        ("decision_summary", "TEXT"),
        ("location_type", "TEXT"),
        ("location_details", "TEXT"),
        ("compensation_range", "TEXT"),
        ("compensation_fit", "TEXT"),
        ("company_domain", "TEXT"),
        ("experience_score", "INTEGER"),
        ("experience_label", "TEXT"),
        ("experience_summary", "TEXT"),
        ("responsibility_alignment", "TEXT"),
        ("domain_experience_notes", "TEXT"),
        ("technical_skills_match", "TEXT"),
        ("requirements_fit_notes", "TEXT"),
        ("keywords_detected", "TEXT"),
        ("cover_letter_generated", "INTEGER DEFAULT 0"),
        ("messages_json", "TEXT"),
        ("role_summary", "TEXT"),
        ("jd_filepath", "TEXT"),
        ("selected_resume", "TEXT"),
        ("resume_confidence", "TEXT"),
        ("resume_reasoning", "TEXT"),
        ("resume_key_signals", "TEXT"),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            try:
                db.execute(f"ALTER TABLE jobs_analyzed ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass  # Column might already exist

    db.commit()

    # Create batch_jobs table for batch processing
    db.execute('''
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT NOT NULL,
            job_url TEXT,
            job_title TEXT,
            company_name TEXT,
            location TEXT,
            job_snippet TEXT,
            job_description_full TEXT,
            posted_date TEXT,
            salary_range TEXT,

            -- Stage 1: Screening
            screen_decision TEXT CHECK(screen_decision IN ('SCREEN_IN', 'SCREEN_OUT', 'PENDING')),
            screen_match_score INTEGER,
            screen_confidence TEXT CHECK(screen_confidence IN ('HIGH', 'MEDIUM', 'LOW')),
            screen_reject_reason TEXT,
            screen_notes TEXT,
            screened_at TIMESTAMP,

            -- Stage 2: Full analysis (links to jobs_analyzed table)
            analysis_id INTEGER,
            analyzed_at TIMESTAMP,

            -- Application tracking
            application_status TEXT DEFAULT 'NOT_APPLIED' CHECK(application_status IN ('NOT_APPLIED', 'APPLIED', 'INTERVIEW', 'REJECTED', 'OFFER')),
            applied_at TIMESTAMP,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (analysis_id) REFERENCES jobs_analyzed(id)
        )
    ''')

    batch_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_batch_screen_decision ON batch_jobs(screen_decision)",
        "CREATE INDEX IF NOT EXISTS idx_batch_match_score ON batch_jobs(screen_match_score DESC)",
        "CREATE INDEX IF NOT EXISTS idx_batch_id ON batch_jobs(batch_id)",
        "CREATE INDEX IF NOT EXISTS idx_batch_app_status ON batch_jobs(application_status)",
    ]

    for index_sql in batch_indexes:
        try:
            db.execute(index_sql)
        except sqlite3.OperationalError:
            pass

    # Create batch_runs table to track batch imports
    db.execute('''
        CREATE TABLE IF NOT EXISTS batch_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id TEXT UNIQUE NOT NULL,
            name TEXT,
            total_jobs INTEGER DEFAULT 0,
            screen_in_count INTEGER DEFAULT 0,
            screen_out_count INTEGER DEFAULT 0,
            analyzed_count INTEGER DEFAULT 0,
            screen_mode TEXT DEFAULT 'balanced',
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'screening', 'screened', 'analyzing', 'complete')),
            summary_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.commit()
    current_app.teardown_appcontext(close_db)


def save_job_analysis(job_description, additional_context, analysis_result, cover_letter_filepath=None, jd_filepath=None, selected_resume=None, resume_confidence=None, resume_reasoning=None):
    """Save job analysis to database and return the job ID"""
    db = get_db()

    analysis = analysis_result.get('analysis', {})
    experience = analysis.get('experience_match', {})
    resume_selection = analysis_result.get('resume_selection', {})

    # Get key signals as JSON string
    key_signals = resume_selection.get('key_signals', [])
    key_signals_json = json.dumps(key_signals) if key_signals else None

    cursor = db.execute(
        '''INSERT INTO jobs_analyzed (
            job_description,
            additional_context,
            company_name,
            job_title,
            decision,
            decision_summary,
            priority_level,
            selected_resume,
            resume_confidence,
            resume_reasoning,
            resume_key_signals,
            location_type,
            location_details,
            compensation_range,
            compensation_fit,
            company_domain,
            experience_score,
            experience_label,
            experience_summary,
            responsibility_alignment,
            domain_experience_notes,
            technical_skills_match,
            requirements_fit_notes,
            keywords_detected,
            reject_reasons_json,
            priority_reasons_json,
            cover_letter_filepath,
            cover_letter_generated,
            role_summary,
            jd_filepath
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            job_description,
            additional_context,
            analysis_result.get('company_name'),
            analysis_result.get('job_title'),
            analysis_result.get('decision'),
            analysis_result.get('decision_summary'),
            analysis_result.get('priority_level'),
            selected_resume or resume_selection.get('selected_resume'),
            resume_confidence or resume_selection.get('confidence'),
            resume_reasoning or resume_selection.get('reasoning'),
            key_signals_json,
            analysis.get('location_type'),
            analysis.get('location_details'),
            analysis.get('compensation_range'),
            analysis.get('compensation_fit'),
            analysis.get('company_domain'),
            experience.get('score') if isinstance(experience, dict) else None,
            experience.get('label') if isinstance(experience, dict) else None,
            experience.get('summary') if isinstance(experience, dict) else None,
            experience.get('responsibility_alignment') if isinstance(experience, dict) else None,
            experience.get('domain_experience') if isinstance(experience, dict) else None,
            experience.get('technical_skills') if isinstance(experience, dict) else None,
            experience.get('requirements_fit') if isinstance(experience, dict) else None,
            analysis.get('keywords_detected'),
            json.dumps(analysis.get('reject_reasons', [])),
            json.dumps(analysis.get('priority_reasons', [])),
            cover_letter_filepath,
            1 if cover_letter_filepath else 0,
            analysis.get('role_summary'),
            jd_filepath
        )
    )

    db.commit()
    return cursor.lastrowid


def update_job_cover_letter(job_id, filepath):
    """Update job with cover letter filepath"""
    db = get_db()
    db.execute(
        '''UPDATE jobs_analyzed
           SET cover_letter_filepath = ?, cover_letter_generated = 1, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?''',
        (filepath, job_id)
    )
    db.commit()


def save_follow_up_message(job_id, message_type, message_text, filepath):
    """Save a follow-up message for a job"""
    db = get_db()
    from datetime import datetime

    # Get existing messages
    job = db.execute('SELECT messages_json FROM jobs_analyzed WHERE id = ?', (job_id,)).fetchone()
    messages = json.loads(job['messages_json']) if job and job['messages_json'] else []

    # Add new message
    messages.append({
        'type': message_type,
        'text': message_text,
        'filepath': filepath,
        'created_at': datetime.now().isoformat()
    })

    db.execute(
        '''UPDATE jobs_analyzed
           SET messages_json = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?''',
        (json.dumps(messages), job_id)
    )
    db.commit()


def get_jobs_history(filters=None, search=None, limit=100, offset=0):
    """Get job history with optional filters and search"""
    db = get_db()

    query = '''SELECT id, company_name, job_title, decision, selected_resume,
                      resume_confidence, priority_level, location_type, compensation_fit, status, created_at
               FROM jobs_analyzed WHERE 1=1'''
    params = []

    if filters:
        if filters.get('decision'):
            query += ' AND decision = ?'
            params.append(filters['decision'])
        if filters.get('resume'):
            query += ' AND selected_resume = ?'
            params.append(filters['resume'])
        if filters.get('priority'):
            if filters['priority'] == 'Yes':
                query += ' AND priority_level = ?'
                params.append('PRIORITY')
            else:
                query += ' AND priority_level != ?'
                params.append('PRIORITY')
        if filters.get('location'):
            query += ' AND location_type = ?'
            params.append(filters['location'])
        if filters.get('compensation'):
            query += ' AND compensation_fit = ?'
            params.append(filters['compensation'])

    if search:
        query += ''' AND (company_name LIKE ? OR job_title LIKE ?
                    OR company_domain LIKE ? OR keywords_detected LIKE ?)'''
        search_term = f'%{search}%'
        params.extend([search_term, search_term, search_term, search_term])

    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    return db.execute(query, params).fetchall()


def get_job_details(job_id):
    """Get full details for a specific job"""
    db = get_db()
    return db.execute('SELECT * FROM jobs_analyzed WHERE id = ?', (job_id,)).fetchone()


# --- Batch Processing Functions ---

def create_batch_run(batch_id, name, total_jobs, screen_mode="balanced"):
    """Create a new batch run record."""
    db = get_db()
    db.execute(
        '''INSERT INTO batch_runs (batch_id, name, total_jobs, screen_mode, status)
           VALUES (?, ?, ?, ?, 'pending')''',
        (batch_id, name, total_jobs, screen_mode)
    )
    db.commit()


def update_batch_run(batch_id, **kwargs):
    """Update batch run fields."""
    db = get_db()
    sets = []
    params = []
    for key, value in kwargs.items():
        sets.append(f"{key} = ?")
        params.append(value)
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(batch_id)
    db.execute(f"UPDATE batch_runs SET {', '.join(sets)} WHERE batch_id = ?", params)
    db.commit()


def save_batch_jobs(batch_id, jobs):
    """Save a list of jobs for a batch. Jobs should have screening results."""
    db = get_db()
    for job in jobs:
        db.execute(
            '''INSERT INTO batch_jobs (
                batch_id, job_url, job_title, company_name, location,
                job_snippet, posted_date, salary_range,
                screen_decision, screen_match_score, screen_confidence,
                screen_reject_reason, screen_notes, screened_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
            (
                batch_id,
                job.get('job_url'),
                job.get('job_title'),
                job.get('company_name'),
                job.get('location'),
                job.get('job_snippet', '')[:500],
                job.get('posted_date'),
                job.get('salary_range'),
                job.get('decision', 'PENDING'),
                job.get('match_score'),
                job.get('confidence'),
                job.get('primary_reject_reason'),
                job.get('quick_notes'),
            )
        )
    db.commit()


def get_batch_runs(limit=50):
    """Get all batch runs, newest first."""
    db = get_db()
    return db.execute(
        '''SELECT * FROM batch_runs ORDER BY created_at DESC LIMIT ?''',
        (limit,)
    ).fetchall()


def get_batch_run(batch_id):
    """Get a single batch run by ID."""
    db = get_db()
    return db.execute(
        'SELECT * FROM batch_runs WHERE batch_id = ?', (batch_id,)
    ).fetchone()


def get_batch_jobs(batch_id, decision_filter=None, sort_by="screen_match_score", limit=500):
    """Get jobs for a batch with optional filtering."""
    db = get_db()
    query = 'SELECT * FROM batch_jobs WHERE batch_id = ?'
    params = [batch_id]

    if decision_filter:
        query += ' AND screen_decision = ?'
        params.append(decision_filter)

    if sort_by == "screen_match_score":
        query += ' ORDER BY screen_match_score DESC'
    elif sort_by == "company_name":
        query += ' ORDER BY company_name ASC'
    else:
        query += ' ORDER BY id ASC'

    query += ' LIMIT ?'
    params.append(limit)

    return db.execute(query, params).fetchall()


def update_batch_job(job_id, **kwargs):
    """Update a single batch job record."""
    db = get_db()
    sets = []
    params = []
    for key, value in kwargs.items():
        sets.append(f"{key} = ?")
        params.append(value)
    sets.append("updated_at = CURRENT_TIMESTAMP")
    params.append(job_id)
    db.execute(f"UPDATE batch_jobs SET {', '.join(sets)} WHERE id = ?", params)
    db.commit()


def override_batch_screen(job_id, new_decision):
    """Manually override screening decision for a batch job."""
    db = get_db()
    db.execute(
        '''UPDATE batch_jobs SET screen_decision = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?''',
        (new_decision, job_id)
    )
    db.commit()
