"""
Cover Letter File Generation Module
Handles saving cover letters as .docx files
"""

import os
import re
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches


# Output directory for cover letters
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


def generate_filename(company_name: str, job_title: str, suffix: str = "Cover Letter") -> str:
    """Generate a clean filename for the document"""
    # Clean up company name
    if company_name:
        clean_name = re.sub(r'[^\w\s-]', '', company_name).strip()
        return f"Austin Stretz - {clean_name} {suffix}.docx"

    # Use job title if no company
    if job_title:
        clean_title = re.sub(r'[^\w\s-]', '', job_title).strip()
        return f"Austin Stretz - {clean_title} {suffix}.docx"

    # Default
    return f"Austin Stretz - Product Management {suffix}.docx"


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
