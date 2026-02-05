"""
Cover Letter Generation Module
Uses Claude API to generate tailored cover letters and saves them as .docx files
"""

import os
import re
from datetime import datetime
from anthropic import Anthropic
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from profile import get_profile_summary, SAMPLE_COVER_LETTERS


def get_client():
    """Get Anthropic API client"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return Anthropic(api_key=api_key)


# Output directory for cover letters
# Default to current directory if Windows path doesn't exist (for development/testing)
DEFAULT_OUTPUT_DIR = r"C:\Users\astre\Desktop\Persy\The Hunt\Hunt Covers"
FALLBACK_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def get_output_directory():
    """Get the output directory, creating fallback if needed"""
    if os.path.exists(DEFAULT_OUTPUT_DIR):
        return DEFAULT_OUTPUT_DIR

    # Create fallback directory
    if not os.path.exists(FALLBACK_OUTPUT_DIR):
        os.makedirs(FALLBACK_OUTPUT_DIR)
    return FALLBACK_OUTPUT_DIR


COVER_LETTER_PROMPT = """Generate a professional cover letter for Austin Stretz applying to this role.

AUSTIN'S PROFESSIONAL PROFILE:
{profile}

JOB DESCRIPTION:
{job_description}

COMPANY: {company_name}
JOB TITLE: {job_title}
RESUME VARIANT BEING USED: {resume_type}
PRIORITY LEVEL: {priority_level}

OPTIONAL CUSTOMIZATION (weave naturally into content if provided):
Company News/Context: {company_news}
Personal Connection: {personal_connection}
Specific Notes: {specific_notes}

---

STYLE REQUIREMENTS - THIS IS CRITICAL:

Voice & Tone:
- Professional but conversational, NOT overly formal
- Confident without arrogance
- Specific and concrete (avoid generic buzzwords)
- Shows deep understanding of the role's challenges
- Emphasizes outcomes and impact
- Authentic and genuine

Austin's Natural Phrases (use these patterns):
- "This role resonates because..."
- "I'm comfortable operating in..."
- "I care deeply about..."
- "My experience has focused on..."
- "In my recent product roles..."
- "A core part of my experience..."
- "I'm particularly drawn to..."
- "I would welcome the opportunity..."

Structure Requirements:
- 3-4 paragraphs total, flowing prose
- 300-400 words (NO MORE)
- NO bullet points
- Each paragraph has a clear purpose
- Specific examples woven naturally into narrative

Paragraph Structure:
1. OPENING HOOK (1-2 sentences): Lead with understanding of role's unique value. Show you grasp what makes THIS role/company different.
   For sports tech, can open with "This is a dream role."
   Otherwise: "This role resonates because..." or "This role caught my attention because..."

2. CORE RELEVANT EXPERIENCE: Pull from these products based on job focus:
   - SmartPlayer: UX, analysis, visualization, user-facing AI
   - Voice Assist: Real-time feedback, AI coaching, NLP/language
   - Heuristic v4: ML metrics, measurement, technical validation, accuracy
   - Data QA: Quality, testing, validation, debugging
   - Onsite platform: Operations, hardware, deployment, field work
   Include specific achievements with metrics.

3. TECHNICAL CREDIBILITY: Show depth without jargon overload. Demonstrate domain mastery.

4. VALUES/CULTURE FIT OR PERSONAL PASSION:
   - How Austin works: collaborative, customer-focused, iterative
   - What he cares about: user trust, measurement rigor, operational excellence
   - Personal passion if highly relevant (especially for sports tech)

CLOSING: "I would welcome the opportunity to..." (brief, confident)

---

EXAMPLE COVER LETTERS - LEARN AUSTIN'S VOICE FROM THESE:

BOLD Cover Letter (AI platform, measurement focus):
{sample_bold}

Conviva Cover Letter (0→1 product, agent analytics):
{sample_conviva}

Hudl Cover Letter (Sports tech, personal passion):
{sample_hudl}

---

IMPORTANT:
- Generate ONLY the body paragraphs
- Do NOT include the header (name, contact, date) - the system adds this
- Do NOT include the greeting (Dear X) - the system adds this
- Do NOT include the closing (Sincerely, Austin Stretz) - the system adds this
- Output clean text that will be inserted between greeting and closing
- Must feel authentically like Austin wrote it, not generic AI output
- Be SPECIFIC to this job - reference actual requirements from the posting"""


def generate_cover_letter(
    job_description: str,
    company_name: str,
    job_title: str,
    resume_type: str,
    priority_level: str,
    company_news: str = "",
    personal_connection: str = "",
    specific_notes: str = ""
) -> str:
    """
    Generate a cover letter using Claude API.

    Returns:
        The body text of the cover letter (without header, greeting, closing)
    """
    client = get_client()

    prompt = COVER_LETTER_PROMPT.format(
        profile=get_profile_summary(),
        job_description=job_description,
        company_name=company_name or "Unknown Company",
        job_title=job_title or "Product Management Role",
        resume_type=resume_type,
        priority_level=priority_level,
        company_news=company_news or "None provided",
        personal_connection=personal_connection or "None provided",
        specific_notes=specific_notes or "None provided",
        sample_bold=SAMPLE_COVER_LETTERS["BOLD"],
        sample_conviva=SAMPLE_COVER_LETTERS["Conviva"],
        sample_hudl=SAMPLE_COVER_LETTERS["Hudl"]
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Extract the response text
    cover_letter_body = message.content[0].text.strip()

    # Clean up any stray formatting
    # Remove any accidental greetings that might have been included
    lines = cover_letter_body.split('\n')
    cleaned_lines = []
    for line in lines:
        lower_line = line.lower().strip()
        # Skip greeting lines
        if lower_line.startswith('dear '):
            continue
        # Skip closing lines
        if lower_line.startswith('sincerely') or lower_line.startswith('best regards'):
            continue
        if lower_line == 'austin stretz':
            continue
        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines).strip()


def generate_filename(company_name: str, job_title: str) -> str:
    """Generate a clean filename for the cover letter"""
    # Clean up company name
    if company_name:
        # Remove special characters
        clean_company = re.sub(r'[^\w\s-]', '', company_name)
        clean_company = clean_company.strip()
        return f"Austin Stretz - {clean_company} Cover Letter.docx"

    # Use job title if no company
    if job_title:
        clean_title = re.sub(r'[^\w\s-]', '', job_title)
        clean_title = clean_title.strip()
        return f"Austin Stretz - {clean_title} Cover Letter.docx"

    # Default
    return "Austin Stretz - Product Management Cover Letter.docx"


def save_cover_letter_docx(content: str, company_name: str, job_title: str) -> str:
    """
    Save the cover letter to a .docx file.

    Args:
        content: The body text of the cover letter
        company_name: Company name for greeting and filename
        job_title: Job title for filename fallback

    Returns:
        The full file path where the document was saved
    """
    doc = Document()

    # Set margins (1 inch all sides)
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Header - Name
    header_para = doc.add_paragraph()
    header_run = header_para.add_run("Austin Stretz")
    header_run.bold = True
    header_run.font.name = 'Calibri'
    header_run.font.size = Pt(11)

    # Contact info line
    contact_para = doc.add_paragraph()
    contact_run = contact_para.add_run("Kansas City, MO | a.stretz@outlook.com | 913-515-8304")
    contact_run.font.name = 'Calibri'
    contact_run.font.size = Pt(11)

    # Date
    date_para = doc.add_paragraph()
    date_run = date_para.add_run(datetime.now().strftime("%m/%d/%Y"))
    date_run.font.name = 'Calibri'
    date_run.font.size = Pt(11)

    # Blank line
    doc.add_paragraph()

    # Greeting
    greeting_para = doc.add_paragraph()
    if company_name:
        greeting_text = f"Dear {company_name} Hiring Team,"
    else:
        greeting_text = "Dear Hiring Team,"
    greeting_run = greeting_para.add_run(greeting_text)
    greeting_run.font.name = 'Calibri'
    greeting_run.font.size = Pt(11)

    # Blank line after greeting
    doc.add_paragraph()

    # Body paragraphs
    paragraphs = content.split('\n\n')
    for para_text in paragraphs:
        if para_text.strip():
            para = doc.add_paragraph()
            run = para.add_run(para_text.strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(11)

    # Blank line before closing
    doc.add_paragraph()

    # Closing
    closing_para = doc.add_paragraph()
    closing_run = closing_para.add_run("Sincerely,")
    closing_run.font.name = 'Calibri'
    closing_run.font.size = Pt(11)

    # Signature
    sig_para = doc.add_paragraph()
    sig_run = sig_para.add_run("Austin Stretz")
    sig_run.font.name = 'Calibri'
    sig_run.font.size = Pt(11)

    # Generate filename and save
    output_dir = get_output_directory()
    filename = generate_filename(company_name, job_title)
    filepath = os.path.join(output_dir, filename)

    # Handle duplicate filenames
    counter = 1
    base_filepath = filepath
    while os.path.exists(filepath):
        name, ext = os.path.splitext(base_filepath)
        filepath = f"{name} ({counter}){ext}"
        counter += 1

    doc.save(filepath)
    return filepath
