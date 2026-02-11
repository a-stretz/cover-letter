"""
Job Application Decision & Cover Letter Generator
Main Flask Application - Streamlined one-button workflow
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from database import (
    init_db, get_db, save_job_analysis, update_job_cover_letter,
    get_jobs_history, get_job_details, save_follow_up_message
)
from analyzer import analyze_and_generate
from cover_letter import save_cover_letter_docx, get_output_directory
from message_generator import generate_follow_up_message, save_message_to_file
from jd_saver import save_job_description_file
from resume_generator import generate_resume

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
    """
    One-button analyze: Analyzes job, generates cover letter if APPLY, auto-saves file.
    Returns complete analysis with cover letter and file path.
    """
    data = request.get_json()

    if not data or not data.get('job_description'):
        return jsonify({'error': 'Job description is required'}), 400

    job_description = data['job_description']
    additional_context = data.get('additional_context', '')

    try:
        # Combined analysis + cover letter + resume customization (single API call)
        result = analyze_and_generate(job_description, additional_context)

        cover_letter_filepath = None
        jd_filepath = None
        resume_filepath = None
        resume_title = None
        resume_summary = None

        # Always save the JD file (regardless of apply/reject)
        try:
            jd_filepath = save_job_description_file(
                job_description=job_description,
                company_name=result.get('company_name') or '',
                job_title=result.get('job_title') or ''
            )
            result['jd_filepath'] = jd_filepath
        except Exception as e:
            print(f"Warning: Failed to save JD file: {e}")

        # If APPLY and cover letter was generated, auto-save cover letter and resume
        if result['decision'] == 'APPLY' and result.get('cover_letter'):
            # Save cover letter
            cover_letter_filepath = save_cover_letter_docx(
                content=result['cover_letter'],
                company_name=result.get('company_name') or '',
                job_title=result.get('job_title') or ''
            )
            result['cover_letter_filepath'] = cover_letter_filepath

            # Generate and save tailored resume
            resume_customization = result.get('resume_customization')
            if resume_customization:
                try:
                    resume_filepath = generate_resume(
                        customization=resume_customization,
                        company_name=result.get('company_name') or '',
                        job_title=result.get('job_title') or ''
                    )
                    result['resume_filepath'] = resume_filepath
                    resume_title = resume_customization.get('recommended_title')
                    resume_summary = resume_customization.get('summary')
                except Exception as e:
                    print(f"Warning: Failed to generate resume: {e}")
                    import traceback
                    traceback.print_exc()

        # Save to database
        job_id = save_job_analysis(
            job_description=job_description,
            additional_context=additional_context,
            analysis_result=result,
            cover_letter_filepath=cover_letter_filepath,
            jd_filepath=jd_filepath,
            resume_filepath=resume_filepath,
            resume_title=resume_title,
            resume_summary=resume_summary
        )

        result['job_id'] = job_id
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/override-reject', methods=['POST'])
def override_reject():
    """
    Override a REJECT decision: generates cover letter anyway and saves to file.
    Used when user wants to apply despite the automated rejection.
    """
    data = request.get_json()

    if not data or not data.get('job_id'):
        return jsonify({'error': 'Job ID is required'}), 400

    job_id = data['job_id']

    # Get job details from database
    job = get_job_details(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        from analyzer import generate_cover_letter_only

        # Generate cover letter for this job
        cover_letter = generate_cover_letter_only(
            job_description=job['job_description'],
            company_name=job['company_name'] or '',
            job_title=job['job_title'] or '',
            resume_type=job['recommended_resume'] or 'Traditional PM',
            priority_level='STANDARD'
        )

        # Save to file
        cover_letter_filepath = save_cover_letter_docx(
            content=cover_letter,
            company_name=job['company_name'] or '',
            job_title=job['job_title'] or ''
        )

        # Update database to mark as overridden
        db = get_db()
        db.execute(
            '''UPDATE jobs_analyzed
               SET decision = 'APPLY',
                   decision_summary = decision_summary || ' [OVERRIDE: User chose to apply anyway]',
                   cover_letter_filepath = ?,
                   cover_letter_generated = 1,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?''',
            (cover_letter_filepath, job_id)
        )
        db.commit()

        return jsonify({
            'success': True,
            'cover_letter': cover_letter,
            'cover_letter_filepath': cover_letter_filepath
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-message', methods=['POST'])
def generate_message():
    """Generate a follow-up message for a job"""
    data = request.get_json()

    required = ['job_id', 'message_type']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    job_id = data['job_id']
    message_type = data['message_type']
    audience = data.get('audience', 'recruiter')
    tone = data.get('tone', 'professional')
    additional_context = data.get('additional_context', '')

    # Get job details from database
    job = get_job_details(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        # Generate the message
        result = generate_follow_up_message(
            message_type=message_type,
            company_name=job['company_name'],
            job_title=job['job_title'],
            job_description=job['job_description'],
            audience=audience,
            tone=tone,
            additional_context=additional_context
        )

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/save-message', methods=['POST'])
def save_message():
    """Save a generated message to file"""
    data = request.get_json()

    required = ['job_id', 'message_type', 'message']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    job_id = data['job_id']
    message_type = data['message_type']
    message_text = data['message']
    subject = data.get('subject')

    # Get job details
    job = get_job_details(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    try:
        output_dir = get_output_directory()
        filepath = save_message_to_file(
            message_text=message_text,
            subject=subject,
            company_name=job['company_name'],
            message_type=message_type,
            output_dir=output_dir
        )

        # Save to database
        save_follow_up_message(job_id, message_type, message_text, filepath)

        return jsonify({
            'success': True,
            'filepath': filepath
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/history')
def history():
    """Get job analysis history with optional filters"""
    filters = {}
    if request.args.get('decision'):
        filters['decision'] = request.args.get('decision')
    if request.args.get('resume'):
        filters['resume'] = request.args.get('resume')
    if request.args.get('priority'):
        filters['priority'] = request.args.get('priority')
    if request.args.get('location'):
        filters['location'] = request.args.get('location')
    if request.args.get('compensation'):
        filters['compensation'] = request.args.get('compensation')

    search = request.args.get('search')

    jobs = get_jobs_history(filters=filters if filters else None, search=search)
    return jsonify([dict(job) for job in jobs])


@app.route('/api/job/<int:job_id>')
def get_job(job_id):
    """Get full details for a specific job"""
    job = get_job_details(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Convert to dict and parse JSON fields
    job_dict = dict(job)

    # Parse JSON fields
    json_fields = ['reject_reasons_json', 'priority_reasons_json', 'messages_json']
    for field in json_fields:
        if job_dict.get(field):
            try:
                job_dict[field] = json.loads(job_dict[field])
            except json.JSONDecodeError:
                pass

    return jsonify(job_dict)


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
