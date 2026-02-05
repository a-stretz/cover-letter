"""
Database module for SQLite operations
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

    db.executescript('''
        -- Professional profile storage
        CREATE TABLE IF NOT EXISTS professional_profile (
            id INTEGER PRIMARY KEY,
            name TEXT DEFAULT 'Austin Stretz',
            email TEXT DEFAULT 'a.stretz@outlook.com',
            phone TEXT DEFAULT '913-515-8304',
            location TEXT DEFAULT 'Kansas City, MO',
            summary TEXT,
            experience_json TEXT,
            skills_json TEXT,
            certifications_json TEXT,
            target_roles TEXT,
            compensation_min INTEGER DEFAULT 100000,
            compensation_max INTEGER DEFAULT 160000,
            compensation_target INTEGER DEFAULT 130000,
            location_preferences TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Jobs analyzed
        CREATE TABLE IF NOT EXISTS jobs_analyzed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_description TEXT NOT NULL,
            company_name TEXT,
            job_title TEXT,
            additional_context TEXT,

            -- Decision outputs
            decision TEXT NOT NULL CHECK(decision IN ('APPLY', 'REJECT')),
            recommended_resume TEXT CHECK(recommended_resume IN ('Edge AI', 'AI PM', 'Traditional PM')),
            priority_level TEXT CHECK(priority_level IN ('PRIORITY', 'STANDARD', 'REJECT')),

            -- Analysis details
            experience_match TEXT,
            compensation_detected TEXT,
            location_fit TEXT,
            reject_reasons_json TEXT,
            priority_reasons_json TEXT,
            keywords_found_json TEXT,
            resume_rationale TEXT,
            extra_touches_json TEXT,
            talking_points_json TEXT,

            -- Generated content
            cover_letter_body TEXT,
            cover_letter_filepath TEXT,
            customization_inputs_json TEXT,

            -- Tracking
            status TEXT DEFAULT 'analyzed' CHECK(status IN ('analyzed', 'applied', 'interview_scheduled', 'interview_completed', 'rejected', 'offer')),
            status_updated_at TIMESTAMP,
            notes TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Portfolio artifacts (future)
        CREATE TABLE IF NOT EXISTS portfolio_artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            artifact_type TEXT,
            keywords_json TEXT,
            filepath TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes if not exist
        CREATE INDEX IF NOT EXISTS idx_jobs_decision ON jobs_analyzed(decision);
        CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs_analyzed(priority_level);
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs_analyzed(status);
        CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs_analyzed(company_name);
        CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs_analyzed(created_at DESC);
    ''')

    db.commit()
    current_app.teardown_appcontext(close_db)


def save_job_analysis(job_description, additional_context, analysis_result):
    """Save job analysis to database and return the job ID"""
    db = get_db()

    cursor = db.execute(
        '''INSERT INTO jobs_analyzed (
            job_description,
            additional_context,
            company_name,
            job_title,
            decision,
            recommended_resume,
            priority_level,
            experience_match,
            compensation_detected,
            location_fit,
            reject_reasons_json,
            priority_reasons_json,
            keywords_found_json,
            resume_rationale,
            extra_touches_json,
            talking_points_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            job_description,
            additional_context,
            analysis_result.get('company_name'),
            analysis_result.get('job_title'),
            analysis_result.get('decision'),
            analysis_result.get('recommended_resume'),
            analysis_result.get('priority_level'),
            analysis_result.get('analysis', {}).get('experience_match'),
            analysis_result.get('analysis', {}).get('compensation'),
            analysis_result.get('analysis', {}).get('location'),
            json.dumps(analysis_result.get('analysis', {}).get('reject_reasons', [])),
            json.dumps(analysis_result.get('analysis', {}).get('priority_reasons', [])),
            json.dumps(analysis_result.get('analysis', {}).get('key_keywords', [])),
            analysis_result.get('analysis', {}).get('resume_rationale'),
            json.dumps(analysis_result.get('analysis', {}).get('extra_touches', [])),
            json.dumps(analysis_result.get('analysis', {}).get('talking_points', []))
        )
    )

    db.commit()
    return cursor.lastrowid
