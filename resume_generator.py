"""
Resume Customization Engine
Generates tailored .docx resumes based on JD analysis
"""

import os
import re
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# Output directory for resumes
DEFAULT_RESUME_DIR = r"C:\Users\astre\Desktop\Persy\The Hunt\Hunt Resumes"
FALLBACK_RESUME_DIR = os.path.join(os.path.dirname(__file__), "output", "resumes")

# Font configuration
FONT_NAME = "Aptos Narrow"
FALLBACK_FONT = "Calibri"  # Fallback if Aptos Narrow not available


def get_resume_directory():
    """Get the resume output directory, creating fallback if needed"""
    if os.path.exists(DEFAULT_RESUME_DIR):
        return DEFAULT_RESUME_DIR
    if not os.path.exists(FALLBACK_RESUME_DIR):
        os.makedirs(FALLBACK_RESUME_DIR)
    return FALLBACK_RESUME_DIR


def clean_filename_part(text: str) -> str:
    """Clean a string for use in filename"""
    if not text:
        return ""
    cleaned = re.sub(r'[<>:"/\\|?*]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def set_font(run, size_pt, bold=False, italic=False, font_name=FONT_NAME):
    """Apply font settings to a run"""
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    # Set font for East Asian text as well
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)


def add_horizontal_rule(paragraph):
    """Add a horizontal rule below a paragraph"""
    p = paragraph._p
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '000000')
    pBdr.append(bottom)
    pPr.append(pBdr)


def add_section_header(doc, title):
    """Add a section header with horizontal rule"""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(10)
    para.paragraph_format.space_after = Pt(4)
    run = para.add_run(title.upper())
    set_font(run, 11, bold=True)
    add_horizontal_rule(para)
    return para


def add_role_header(doc, role_title, company, date_range):
    """Add a role header with date right-aligned"""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(8)
    para.paragraph_format.space_after = Pt(2)

    # Role and company
    run = para.add_run(f"{role_title} — {company}")
    set_font(run, 11, bold=True)

    # Add tab stop for right alignment
    tab_stops = para.paragraph_format.tab_stops
    tab_stops.add_tab_stop(Inches(7.0), WD_ALIGN_PARAGRAPH.RIGHT)

    # Date
    para.add_run("\t")
    date_run = para.add_run(date_range)
    set_font(date_run, 11, bold=False)

    return para


def add_company_description(doc, description):
    """Add italicized company description"""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(4)
    run = para.add_run(description)
    set_font(run, 10, italic=True)
    return para


def add_sub_header(doc, title):
    """Add a bold sub-section header"""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(6)
    para.paragraph_format.space_after = Pt(2)
    run = para.add_run(title)
    set_font(run, 10, bold=True)
    return para


def add_bullet_point(doc, text, indent=0.25):
    """Add a bullet point"""
    para = doc.add_paragraph(style='List Bullet')
    para.paragraph_format.left_indent = Inches(indent)
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(2)

    # Handle bold prefix (e.g., "System Name: description")
    if ": " in text and text.index(": ") < 60:
        prefix, rest = text.split(": ", 1)
        bold_run = para.add_run(prefix + ": ")
        set_font(bold_run, 10, bold=True)
        text_run = para.add_run(rest)
        set_font(text_run, 10)
    else:
        run = para.add_run(text)
        set_font(run, 10)

    return para


def add_simple_bullet(doc, text, indent=0.25):
    """Add a simple bullet point without bold prefix handling"""
    para = doc.add_paragraph(style='List Bullet')
    para.paragraph_format.left_indent = Inches(indent)
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(2)
    run = para.add_run(text)
    set_font(run, 10)
    return para


def create_two_column_competencies(doc, competencies):
    """Create a two-column layout for competencies"""
    table = doc.add_table(rows=4, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Remove table borders
    for row in table.rows:
        for cell in row.cells:
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for border_name in ['top', 'left', 'bottom', 'right']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'nil')
                tcBorders.append(border)
            tcPr.append(tcBorders)

    # Fill in competencies (4 per column)
    for i, comp in enumerate(competencies[:8]):
        row_idx = i % 4
        col_idx = i // 4
        cell = table.cell(row_idx, col_idx)
        cell.text = ""
        para = cell.paragraphs[0]
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(2)
        run = para.add_run(f"• {comp}")
        set_font(run, 10)

    return table


def add_skills_section(doc, skills_tools):
    """Add the skills/tools section at the bottom"""
    for section in skills_tools:
        label = section.get('label', '')
        items = section.get('items', '')
        if label and items:
            para = doc.add_paragraph()
            para.paragraph_format.space_before = Pt(2)
            para.paragraph_format.space_after = Pt(2)
            label_run = para.add_run(f"{label}: ")
            set_font(label_run, 10, bold=True)
            items_run = para.add_run(items)
            set_font(items_run, 10)


# Locked content - never changes
LOCKED_CERTIFICATIONS = [
    "Advanced Certified Scrum Product Owner (A-CSPO) — Scrum Alliance (Jun 2025)",
    "AI Product Manager — IBM (Mar 2025)",
    "Certified Scrum Product Owner (CSPO) — Scrum Alliance (Dec 2024)"
]

LOCKED_ADDITIONAL_EXPERIENCE = [
    {
        "title": "Technical Inside Sales Rep",
        "company": "Nidec Motor Corporation",
        "dates": "May 2014 – Jun 2015",
        "bullets": [
            "Managed technical sales pipeline for electric motor and control systems across industrial manufacturing sectors",
            "Developed CRM workflows, tracking close rates, quote turnaround, and territory performance"
        ]
    },
    {
        "title": "Parts Sales Representative",
        "company": "Burt Automotive Network",
        "dates": "May 2013 – May 2014",
        "bullets": [
            "Led B2B and B2C automotive parts sales, coordinating with service departments and dealers",
            "Maintained inventory systems and managed customer escalations"
        ]
    },
    {
        "title": "Marketing Coordinator",
        "company": "ASW Fuel Oils",
        "dates": "May 2011 – Aug 2012",
        "bullets": [
            "Built customer database and referral tracking system",
            "Planned and executed marketing events and promotional campaigns"
        ]
    },
    {
        "title": "Student Fundraising Associate",
        "company": "Student Fundraising Association",
        "dates": "Sep 2008 – May 2010",
        "bullets": [
            "Top-tier performer in university alumni fundraising campaigns",
            "Developed donor cultivation and retention strategies"
        ]
    }
]

LOCKED_EDUCATION = "B.S. Business Administration, University of Kansas — Lawrence, KS"

LOCKED_CONTACT = {
    "name": "Austin Stretz",
    "location": "Kansas City, MO",
    "email": "a.stretz@outlook.com",
    "phone": "913-515-8304"
}

NEOSAVANT_COMPANY_DESCRIPTION = "Edge-AI Computer Vision platform for real-time sports performance analysis. Developing AI-powered coaching systems that deliver biomechanical feedback using computer vision, 3D pose estimation, and proprietary heuristics."


def generate_resume(customization: dict, company_name: str = "", job_title: str = "") -> str:
    """
    Generate a tailored resume .docx file.

    Args:
        customization: Dict with resume customization instructions from Claude
        company_name: Company name for filename
        job_title: Job title for filename

    Returns:
        Filepath where the resume was saved
    """
    doc = Document()

    # Set page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)

    # === HEADER ===
    # Name
    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_para.paragraph_format.space_after = Pt(2)
    name_run = name_para.add_run(LOCKED_CONTACT["name"])
    set_font(name_run, 18, bold=True)

    # Title
    title = customization.get('recommended_title', 'AI Product Manager')
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_para.paragraph_format.space_before = Pt(0)
    title_para.paragraph_format.space_after = Pt(2)
    title_run = title_para.add_run(title)
    set_font(title_run, 12)

    # Contact line
    contact_para = doc.add_paragraph()
    contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_para.paragraph_format.space_before = Pt(0)
    contact_para.paragraph_format.space_after = Pt(4)
    contact_text = f"{LOCKED_CONTACT['location']} | {LOCKED_CONTACT['email']} | {LOCKED_CONTACT['phone']}"
    contact_run = contact_para.add_run(contact_text)
    set_font(contact_run, 10)

    # Horizontal rule after header
    rule_para = doc.add_paragraph()
    rule_para.paragraph_format.space_before = Pt(0)
    rule_para.paragraph_format.space_after = Pt(4)
    add_horizontal_rule(rule_para)

    # === SUMMARY ===
    add_section_header(doc, "Summary")
    summary_text = customization.get('summary', '')
    if summary_text:
        summary_para = doc.add_paragraph()
        summary_para.paragraph_format.space_before = Pt(2)
        summary_para.paragraph_format.space_after = Pt(6)
        summary_run = summary_para.add_run(summary_text)
        set_font(summary_run, 10, italic=True)

    # === CORE COMPETENCIES ===
    add_section_header(doc, "Core Competencies")
    competencies = customization.get('competencies', [])
    if competencies:
        create_two_column_competencies(doc, competencies)

    # === CERTIFICATIONS ===
    add_section_header(doc, "Certifications")
    for cert in LOCKED_CERTIFICATIONS:
        add_simple_bullet(doc, cert)

    # === PROFESSIONAL EXPERIENCE ===
    add_section_header(doc, "Professional Experience")

    # NeoSavant role
    add_role_header(doc, "AI Product Manager", "NeoSavant.ai", "Nov 2023 – Present")
    add_company_description(doc, NEOSAVANT_COMPANY_DESCRIPTION)

    # NeoSavant sub-sections
    neosavant = customization.get('neosavant', {})
    subheaders = neosavant.get('subheaders', [
        "Product Management & Execution",
        "Product Research, Validation & Domain Translation",
        "Key Product Systems & Platform Capabilities",
        "Quality, Data & Operations"
    ])

    # Sub-section 1: Product Management & Execution
    add_sub_header(doc, subheaders[0] if len(subheaders) > 0 else "Product Management & Execution")
    for bullet in neosavant.get('pm_execution_bullets', []):
        add_simple_bullet(doc, bullet)

    # Sub-section 2: Product Research, Validation & Domain Translation
    add_sub_header(doc, subheaders[1] if len(subheaders) > 1 else "Product Research, Validation & Domain Translation")
    for bullet in neosavant.get('research_validation_bullets', []):
        add_simple_bullet(doc, bullet)

    # Sub-section 3: Key Product Systems & Platform Capabilities
    add_sub_header(doc, subheaders[2] if len(subheaders) > 2 else "Key Product Systems & Platform Capabilities")
    for bullet in neosavant.get('key_systems_bullets', []):
        add_bullet_point(doc, bullet)  # Uses bold prefix handling

    # Sub-section 4: Quality, Data & Operations
    add_sub_header(doc, subheaders[3] if len(subheaders) > 3 else "Quality, Data & Operations")
    for bullet in neosavant.get('quality_data_bullets', []):
        add_simple_bullet(doc, bullet)

    # 1872 Consulting role
    add_role_header(doc, "Product Lead / Sales Operations / Co-Founder", "1872 Consulting, LLC", "Jun 2015 – Dec 2024")
    for bullet in customization.get('consulting_1872_bullets', []):
        add_simple_bullet(doc, bullet)

    # === ADDITIONAL PROFESSIONAL EXPERIENCE ===
    add_section_header(doc, "Additional Professional Experience")
    for exp in LOCKED_ADDITIONAL_EXPERIENCE:
        add_role_header(doc, exp['title'], exp['company'], exp['dates'])
        for bullet in exp['bullets']:
            add_simple_bullet(doc, bullet)

    # === EDUCATION ===
    add_section_header(doc, "Education")
    edu_para = doc.add_paragraph()
    edu_para.paragraph_format.space_before = Pt(2)
    edu_para.paragraph_format.space_after = Pt(6)
    edu_run = edu_para.add_run(LOCKED_EDUCATION)
    set_font(edu_run, 10)

    # === SKILLS/TOOLS ===
    skills_tools = customization.get('skills_tools', {})
    skills_sections = []

    for i in range(1, 4):
        label = skills_tools.get(f'section_{i}_label', '')
        items = skills_tools.get(f'section_{i}_items', '')
        if label and items:
            skills_sections.append({'label': label, 'items': items})

    if skills_sections:
        add_skills_section(doc, skills_sections)

    # === SAVE FILE ===
    output_dir = get_resume_directory()

    # Build filename
    company_part = clean_filename_part(company_name) if company_name else ""
    title_part = clean_filename_part(job_title) if job_title else ""

    filename_parts = ["Claude"]
    if company_part:
        filename_parts.append(company_part)
    if title_part:
        filename_parts.append(title_part)
    filename_parts.append("Resume.docx")

    filename = " ".join(filename_parts)
    filepath = os.path.join(output_dir, filename)

    # Handle duplicates
    counter = 1
    base_filepath = filepath
    while os.path.exists(filepath):
        name, ext = os.path.splitext(base_filepath)
        filepath = f"{name} ({counter}){ext}"
        counter += 1

    doc.save(filepath)
    return filepath


# Master competency pool for reference
MASTER_COMPETENCY_POOL = [
    "Product Strategy, Roadmapping & Ownership",
    "User Research, Practitioner Interviews & Discovery",
    "Cross-Functional & Stakeholder Alignment",
    "Requirements Definition & Acceptance Criteria",
    "Applied AI, Computer Vision & ML Products",
    "UX Flows, Journey Mapping & Experience Design",
    "Product Quality, Validation & Model Evaluation",
    "Multi-Domain Product Delivery (B2B, B2C, Field)",
    "Technical Requirements & Systems Architecture",
    "Data Pipeline & ML Workflow Management",
    "Vendor Management & External Partner Coordination",
    "Sprint Planning, Backlog Ownership & Agile Delivery",
    "GTM Strategy & Revenue Operations",
    "Regulatory, Compliance & Enterprise Systems",
    "Real-Time Systems & Edge Computing",
    "Documentation, Knowledge Management & Enablement"
]

# Master technology library
MASTER_TECHNOLOGY_LIBRARY = {
    "product_delivery": [
        "Jira", "Monday.com", "Trello", "Figma", "Lucidchart", "Miro",
        "GitHub", "GitLab", "Google Sheets", "Google Docs", "Excel",
        "PowerPoint", "HubSpot", "Clay", "ChatGPT", "Claude", "Gemini"
    ],
    "ai_edge_cv": [
        "NVIDIA Jetson (edge inference)", "NVIDIA DeepStream (video inference pipelines)",
        "Google BlazePose (33-landmark 3D pose)", "YOLO-based detection models",
        "LSTM temporal models", "VST multi-camera capture systems",
        "AIDA capture systems", "WebRTC (real-time streaming)",
        "Ant Media Server", "AWS S3 (object storage)", "MinIO (object storage)"
    ],
    "data_infrastructure": [
        "Protocol Buffers (.pb)", "JSON configuration schemas",
        "YAML configuration files", "Python (NumPy, Pandas)",
        "CLI tooling", "Kinovea (manual annotation)", "OBS Studio (capture validation)"
    ]
}

# Default NeoSavant bullets for reference
DEFAULT_NEOSAVANT_BULLETS = {
    "pm_execution_bullets": [
        "Own end-to-end product lifecycle for AI-powered performance analysis platform, from discovery through delivery",
        "Lead cross-functional collaboration with ML engineers, 3D developers, UX designers, and field operations teams",
        "Define product requirements, acceptance criteria, and success metrics for complex computer vision features"
    ],
    "research_validation_bullets": [
        "Conduct practitioner interviews with coaches, trainers, and athletes to translate domain expertise into product requirements",
        "Design and execute Alpha and Beta testing programs with structured cohorts and perception-based accuracy evaluation",
        "Build validation frameworks comparing AI outputs against manual clinical measurements (>90% accuracy achieved)"
    ],
    "key_systems_bullets": [
        "Video-Based Performance Review System (2D/3D/XR): Architected information hierarchy from raw CV outputs to actionable insights, enabling coaches to interpret AI-generated biomechanical analysis",
        "Real-Time Feedback & Coaching System: Designed configurable AI coaching personality system (RVSE) with 6,000+ cue permutations, delivering context-aware feedback during live sessions",
        "Model Behavior & Interpretation Framework: Rebuilt metric validation system from 3D coordinates, correcting projection planes and achieving >90% correlation with clinical measurements",
        "Onsite Capture & Operations Platform: Defined system requirements for multi-camera capture rigs, operator workflows, and high-volume event configurations"
    ],
    "quality_data_bullets": [
        "Built forensic QA pipelines to diagnose measurement drift, coordinate system bugs, and model behavior issues",
        "Processed 390,000+ frames (38.6M data points) for metric validation and system debugging",
        "Created 1.4M+ image annotation pipeline aligned with ML team training priorities",
        "Designed comprehensive testing methodology: 20-shot sessions, cue quality frameworks, systematic behavior diagnosis"
    ]
}

# Default 1872 bullets for reference
DEFAULT_1872_BULLETS = [
    "Led modernization of enterprise HRIS platform (B2B SaaS): legacy AS400 → API-driven system serving Fortune 100 clients",
    "Designed multi-tenant compliance systems for regulated industries including transportation, energy, and construction",
    "Built API-driven integrations and automation workflows across CRM, HRIS, and custom enterprise platforms",
    "Drove 126% revenue growth through product strategy, market positioning, and sales operations optimization",
    "Defined product vision, user flows, and MVP strategy for compliance verification and workforce management tools",
    "Managed vendor relationships, external development partners, and cross-functional delivery teams"
]
