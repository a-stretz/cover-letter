"""
Job Description File Saver
Saves formatted job descriptions as text files
"""

import os
import re


# Output directory for JD files
DEFAULT_JD_DIR = r"C:\Users\astre\Desktop\Persy\The Hunt\JD"
FALLBACK_JD_DIR = os.path.join(os.path.dirname(__file__), "output", "jd")


def get_jd_directory():
    """Get the JD output directory, creating fallback if needed"""
    if os.path.exists(DEFAULT_JD_DIR):
        return DEFAULT_JD_DIR

    # Create fallback directory
    if not os.path.exists(FALLBACK_JD_DIR):
        os.makedirs(FALLBACK_JD_DIR)
    return FALLBACK_JD_DIR


def clean_filename_part(text: str) -> str:
    """Clean a string for use in filename"""
    if not text:
        return ""
    # Remove characters not allowed in filenames
    cleaned = re.sub(r'[<>:"/\\|?*]', '', text)
    # Replace multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def format_job_description(job_description: str, company_name: str, job_title: str) -> str:
    """
    Format the job description for saving.
    Cleans up the text and adds a header.
    """
    lines = []

    # Header with company and title
    if company_name or job_title:
        header_parts = []
        if company_name:
            header_parts.append(company_name)
        if job_title:
            header_parts.append(job_title)
        lines.append(" - ".join(header_parts))
        lines.append("=" * len(lines[0]))
        lines.append("")

    # Clean up the job description text
    jd_text = job_description.strip()

    # Remove common HTML artifacts
    jd_text = re.sub(r'<[^>]+>', '', jd_text)  # Remove HTML tags
    jd_text = re.sub(r'&nbsp;', ' ', jd_text)
    jd_text = re.sub(r'&amp;', '&', jd_text)
    jd_text = re.sub(r'&lt;', '<', jd_text)
    jd_text = re.sub(r'&gt;', '>', jd_text)
    jd_text = re.sub(r'&#\d+;', '', jd_text)

    # Normalize whitespace while preserving paragraph breaks
    jd_text = re.sub(r'\r\n', '\n', jd_text)
    jd_text = re.sub(r'\r', '\n', jd_text)

    # Clean up multiple blank lines
    jd_text = re.sub(r'\n{3,}', '\n\n', jd_text)

    # Clean up leading/trailing whitespace on each line
    jd_lines = []
    for line in jd_text.split('\n'):
        jd_lines.append(line.strip())

    lines.extend(jd_lines)

    return '\n'.join(lines)


def save_job_description_file(job_description: str, company_name: str, job_title: str) -> str:
    """
    Save the job description to a text file.

    Args:
        job_description: The raw job description text
        company_name: Company name (can be empty)
        job_title: Job title (can be empty)

    Returns:
        The full file path where the document was saved
    """
    output_dir = get_jd_directory()

    # Build filename: Claude {Company Name} {Job Title} JD.txt
    company_part = clean_filename_part(company_name) if company_name else ""
    title_part = clean_filename_part(job_title) if job_title else ""

    filename_parts = ["Claude"]
    if company_part:
        filename_parts.append(company_part)
    if title_part:
        filename_parts.append(title_part)
    filename_parts.append("JD.txt")

    filename = " ".join(filename_parts)

    filepath = os.path.join(output_dir, filename)

    # Handle duplicate filenames
    counter = 1
    base_filepath = filepath
    while os.path.exists(filepath):
        name, ext = os.path.splitext(base_filepath)
        filepath = f"{name} ({counter}){ext}"
        counter += 1

    # Format and save
    formatted_jd = format_job_description(job_description, company_name, job_title)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(formatted_jd)

    return filepath
