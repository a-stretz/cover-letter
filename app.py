"""
Job Application Decision & Cover Letter Generator
Main Flask Application
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from database import init_db, get_db, save_job_analysis
from analyzer import analyze_job_description
from cover_letter import generate_cover_letter, save_cover_letter_docx

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Initialize database on startup
with app.app_context():
    init_db()


@app.route('/')
def index():
    """Main page - job analysis form"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze a job description and return decision + recommendations"""
    data = request.get_json()

    if not data or not data.get('job_description'):
        return jsonify({'error': 'Job description is required'}), 400

    job_description = data['job_description']
    additional_context = data.get('additional_context', '')

    try:
        # Analyze the job description using Claude API
        analysis_result = analyze_job_description(job_description, additional_context)

        # Save to database
        job_id = save_job_analysis(
            job_description=job_description,
            additional_context=additional_context,
            analysis_result=analysis_result
        )

        analysis_result['job_id'] = job_id
        return jsonify(analysis_result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-cover-letter', methods=['POST'])
def generate_cover():
    """Generate a cover letter for a job"""
    data = request.get_json()

    if not data or not data.get('job_id'):
        return jsonify({'error': 'Job ID is required'}), 400

    job_id = data['job_id']
    company_news = data.get('company_news', '')
    personal_connection = data.get('personal_connection', '')
    specific_notes = data.get('specific_notes', '')

    # Get job details from database
    db = get_db()
    job = db.execute(
        'SELECT * FROM jobs_analyzed WHERE id = ?', (job_id,)
    ).fetchone()

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        # Generate cover letter using Claude API
        cover_letter_body = generate_cover_letter(
            job_description=job['job_description'],
            company_name=job['company_name'],
            job_title=job['job_title'],
            resume_type=job['recommended_resume'],
            priority_level=job['priority_level'],
            company_news=company_news,
            personal_connection=personal_connection,
            specific_notes=specific_notes
        )

        # Update database with cover letter
        db.execute(
            '''UPDATE jobs_analyzed
               SET cover_letter_body = ?,
                   customization_inputs_json = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?''',
            (
                cover_letter_body,
                json.dumps({
                    'company_news': company_news,
                    'personal_connection': personal_connection,
                    'specific_notes': specific_notes
                }),
                job_id
            )
        )
        db.commit()

        return jsonify({
            'success': True,
            'cover_letter_body': cover_letter_body,
            'company_name': job['company_name'],
            'job_title': job['job_title']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/save-cover-letter', methods=['POST'])
def save_cover():
    """Save the cover letter to a .docx file"""
    data = request.get_json()

    if not data or not data.get('job_id'):
        return jsonify({'error': 'Job ID is required'}), 400

    job_id = data['job_id']

    # Get job details from database
    db = get_db()
    job = db.execute(
        'SELECT * FROM jobs_analyzed WHERE id = ?', (job_id,)
    ).fetchone()

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    if not job['cover_letter_body']:
        return jsonify({'error': 'No cover letter generated yet'}), 400

    try:
        # Save to .docx file
        filepath = save_cover_letter_docx(
            content=job['cover_letter_body'],
            company_name=job['company_name'],
            job_title=job['job_title']
        )

        # Update database with filepath
        db.execute(
            '''UPDATE jobs_analyzed
               SET cover_letter_filepath = ?,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?''',
            (filepath, job_id)
        )
        db.commit()

        return jsonify({
            'success': True,
            'filepath': filepath
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history')
def history():
    """Get job analysis history"""
    db = get_db()
    jobs = db.execute(
        '''SELECT id, company_name, job_title, decision, recommended_resume,
                  priority_level, status, created_at
           FROM jobs_analyzed
           ORDER BY created_at DESC
           LIMIT 100'''
    ).fetchall()

    return jsonify([dict(job) for job in jobs])


@app.route('/api/job/<int:job_id>')
def get_job(job_id):
    """Get details for a specific job"""
    db = get_db()
    job = db.execute(
        'SELECT * FROM jobs_analyzed WHERE id = ?', (job_id,)
    ).fetchone()

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(dict(job))


@app.route('/api/job/<int:job_id>/status', methods=['PUT'])
def update_status(job_id):
    """Update the status of a job application"""
    data = request.get_json()

    if not data or not data.get('status'):
        return jsonify({'error': 'Status is required'}), 400

    valid_statuses = ['analyzed', 'applied', 'interview_scheduled',
                      'interview_completed', 'rejected', 'offer']

    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    db = get_db()
    db.execute(
        '''UPDATE jobs_analyzed
           SET status = ?, status_updated_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?''',
        (data['status'], job_id)
    )
    db.commit()

    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
