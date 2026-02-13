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
    get_jobs_history, get_job_details, save_follow_up_message,
    create_batch_run, update_batch_run, save_batch_jobs,
    get_batch_runs, get_batch_run, get_batch_jobs,
    update_batch_job, override_batch_screen
)
from analyzer import analyze_and_generate
from cover_letter import save_cover_letter_docx, get_output_directory
from message_generator import generate_follow_up_message, save_message_to_file
from jd_saver import save_job_description_file
from resume_selector import select_resume
from batch_screener import parse_csv, screen_jobs, generate_batch_summary

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
        # Combined analysis + cover letter (single API call)
        result = analyze_and_generate(job_description, additional_context)

        cover_letter_filepath = None
        jd_filepath = None

        # Resume selection (separate call - selects from 3 pre-built variants)
        try:
            resume_selection = select_resume(job_description, use_api=True)
            result['resume_selection'] = resume_selection
        except Exception as e:
            print(f"Warning: Resume selection failed: {e}")
            # Fallback to local selection
            from resume_selector import select_resume_local
            result['resume_selection'] = select_resume_local(job_description)

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

        # If APPLY and cover letter was generated, auto-save cover letter
        if result['decision'] == 'APPLY' and result.get('cover_letter'):
            # Save cover letter
            cover_letter_filepath = save_cover_letter_docx(
                content=result['cover_letter'],
                company_name=result.get('company_name') or '',
                job_title=result.get('job_title') or ''
            )
            result['cover_letter_filepath'] = cover_letter_filepath

        # Save to database (with resume selection data)
        resume_selection = result.get('resume_selection', {})
        job_id = save_job_analysis(
            job_description=job_description,
            additional_context=additional_context,
            analysis_result=result,
            cover_letter_filepath=cover_letter_filepath,
            jd_filepath=jd_filepath,
            selected_resume=resume_selection.get('selected_resume'),
            resume_confidence=resume_selection.get('confidence'),
            resume_reasoning=resume_selection.get('reasoning')
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


# --- Batch Processing Endpoints ---

@app.route('/api/batch/import', methods=['POST'])
def batch_import():
    """
    Import jobs from CSV and run quick screening.
    Accepts: CSV text in body, screen_mode parameter, optional batch_name.
    Returns: batch_id, screening results, summary.
    """
    data = request.get_json()

    if not data or not data.get('csv_data'):
        return jsonify({'error': 'CSV data is required'}), 400

    csv_data = data['csv_data']
    screen_mode = data.get('screen_mode', 'balanced')
    batch_name = data.get('batch_name', '')

    try:
        # Parse CSV
        jobs = parse_csv(csv_data)
        if not jobs:
            return jsonify({'error': 'No valid jobs found in CSV'}), 400

        # Generate batch ID
        import uuid
        batch_id = str(uuid.uuid4())[:8]

        if not batch_name:
            batch_name = f"Batch {datetime.now().strftime('%m/%d %I:%M%p')} ({len(jobs)} jobs)"

        # Create batch run record
        create_batch_run(batch_id, batch_name, len(jobs), screen_mode)
        update_batch_run(batch_id, status='screening')

        # Screen jobs
        results = screen_jobs(jobs, mode=screen_mode)

        # Save to database
        save_batch_jobs(batch_id, results)

        # Generate summary
        summary = generate_batch_summary(results)

        # Update batch run with results
        update_batch_run(
            batch_id,
            status='screened',
            screen_in_count=summary['screen_in'],
            screen_out_count=summary['screen_out'],
            summary_json=json.dumps(summary)
        )

        return jsonify({
            'batch_id': batch_id,
            'batch_name': batch_name,
            'summary': summary,
            'results': [
                {
                    'job_title': r.get('job_title', ''),
                    'company_name': r.get('company_name', ''),
                    'location': r.get('location', ''),
                    'decision': r.get('decision', ''),
                    'match_score': r.get('match_score', 0),
                    'confidence': r.get('confidence', ''),
                    'primary_reject_reason': r.get('primary_reject_reason'),
                    'quick_notes': r.get('quick_notes', ''),
                } for r in results
            ]
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch/list')
def batch_list():
    """Get all batch runs."""
    try:
        runs = get_batch_runs()
        return jsonify([dict(r) for r in runs])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch/<batch_id>')
def batch_detail(batch_id):
    """Get batch run details with jobs."""
    try:
        run = get_batch_run(batch_id)
        if not run:
            return jsonify({'error': 'Batch not found'}), 404

        decision_filter = request.args.get('filter')
        sort_by = request.args.get('sort', 'screen_match_score')

        jobs = get_batch_jobs(batch_id, decision_filter=decision_filter, sort_by=sort_by)

        run_dict = dict(run)
        if run_dict.get('summary_json'):
            try:
                run_dict['summary'] = json.loads(run_dict['summary_json'])
            except json.JSONDecodeError:
                pass

        return jsonify({
            'batch': run_dict,
            'jobs': [dict(j) for j in jobs]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch/job/<int:job_id>/override', methods=['POST'])
def batch_override(job_id):
    """Override screening decision for a batch job."""
    data = request.get_json()
    new_decision = data.get('decision')

    if new_decision not in ('SCREEN_IN', 'SCREEN_OUT'):
        return jsonify({'error': 'Decision must be SCREEN_IN or SCREEN_OUT'}), 400

    try:
        override_batch_screen(job_id, new_decision)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch/job/<int:job_id>/analyze', methods=['POST'])
def batch_analyze_job(job_id):
    """Run full JADE analysis on a single batch job."""
    try:
        db = get_db()
        job = db.execute('SELECT * FROM batch_jobs WHERE id = ?', (job_id,)).fetchone()
        if not job:
            return jsonify({'error': 'Batch job not found'}), 404

        # Use full description if available, otherwise snippet
        job_description = job['job_description_full'] or job['job_snippet'] or ''
        if not job_description:
            return jsonify({'error': 'No job description available for analysis'}), 400

        # Build context
        context_parts = []
        if job['job_url']:
            context_parts.append(f"Job URL: {job['job_url']}")
        if job['salary_range']:
            context_parts.append(f"Salary: {job['salary_range']}")
        additional_context = '\n'.join(context_parts)

        # Run full analysis
        result = analyze_and_generate(job_description, additional_context)

        # Resume selection
        try:
            resume_selection = select_resume(job_description, use_api=True)
            result['resume_selection'] = resume_selection
        except Exception:
            from resume_selector import select_resume_local
            result['resume_selection'] = select_resume_local(job_description)

        cover_letter_filepath = None
        jd_filepath = None

        # Save JD file
        try:
            jd_filepath = save_job_description_file(
                job_description=job_description,
                company_name=result.get('company_name') or job['company_name'] or '',
                job_title=result.get('job_title') or job['job_title'] or ''
            )
            result['jd_filepath'] = jd_filepath
        except Exception:
            pass

        # Save cover letter if APPLY
        if result['decision'] == 'APPLY' and result.get('cover_letter'):
            cover_letter_filepath = save_cover_letter_docx(
                content=result['cover_letter'],
                company_name=result.get('company_name') or job['company_name'] or '',
                job_title=result.get('job_title') or job['job_title'] or ''
            )
            result['cover_letter_filepath'] = cover_letter_filepath

        # Save to jobs_analyzed
        resume_sel = result.get('resume_selection', {})
        analysis_id = save_job_analysis(
            job_description=job_description,
            additional_context=additional_context,
            analysis_result=result,
            cover_letter_filepath=cover_letter_filepath,
            jd_filepath=jd_filepath,
            selected_resume=resume_sel.get('selected_resume'),
            resume_confidence=resume_sel.get('confidence'),
            resume_reasoning=resume_sel.get('reasoning')
        )

        # Link batch job to analysis
        update_batch_job(job_id, analysis_id=analysis_id, analyzed_at=datetime.now().isoformat())

        result['job_id'] = analysis_id
        result['batch_job_id'] = job_id
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/batch/job/<int:job_id>/status', methods=['PUT'])
def batch_job_status(job_id):
    """Update application status for a batch job."""
    data = request.get_json()
    status = data.get('status')
    valid = ['NOT_APPLIED', 'APPLIED', 'INTERVIEW', 'REJECTED', 'OFFER']
    if status not in valid:
        return jsonify({'error': f'Status must be one of: {valid}'}), 400

    try:
        kwargs = {'application_status': status}
        if status == 'APPLIED':
            kwargs['applied_at'] = datetime.now().isoformat()
        update_batch_job(job_id, **kwargs)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
