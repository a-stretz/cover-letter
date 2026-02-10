"""
Follow-Up Message Generator
Generates LinkedIn messages, follow-up emails, and general fit messages
"""

import os
import json
from anthropic import Anthropic

from profile import get_profile_summary


def get_client():
    """Get Anthropic API client"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return Anthropic(api_key=api_key)


MESSAGE_SPECS = {
    "linkedin_connection": {
        "name": "LinkedIn Connection Request",
        "max_chars": 250,
        "description": "Brief professional intro, mention role or mutual interest, no fluff",
        "format": "Plain text",
        "filename_suffix": "LinkedIn Connection"
    },
    "linkedin_inmail": {
        "name": "LinkedIn InMail",
        "word_range": "150-300 words",
        "description": "Subject line + body. Hook → Value prop → Interest → CTA",
        "format": "Plain text with subject line",
        "filename_suffix": "LinkedIn InMail"
    },
    "follow_up_email": {
        "name": "Follow-up Email",
        "word_range": "200-350 words",
        "description": "Post-application check-in (3-5 days after applying). Brief value reminder + optional artifact mention",
        "format": "Email with subject line",
        "filename_suffix": "Follow-up Email"
    },
    "general_fit": {
        "name": "General Fit Message",
        "word_range": "flexible",
        "description": "Explains how Austin's experience fits the role. Can be used for various purposes. Conversational tone",
        "format": "Plain text",
        "filename_suffix": "General Message"
    }
}

AUDIENCE_CONTEXT = {
    "recruiter": "Focus on qualifications, experience match, and availability. Recruiters care about whether you meet the requirements and are a viable candidate.",
    "hiring_manager": "Focus on specific value you'd bring to the team, understanding of their challenges, and how your experience solves their problems.",
    "technical_lead": "Focus on technical depth, specific projects, tools/technologies used, and technical problem-solving approach."
}

TONE_CONTEXT = {
    "professional": "Maintain formal but warm tone. Clear, direct language. No excessive enthusiasm.",
    "enthusiastic": "Show genuine excitement about the role/company. More energy in word choice. Still professional but warmer.",
    "technical": "Lead with technical credibility. Reference specific technologies, methodologies, metrics. More detailed on technical aspects."
}


MESSAGE_PROMPT = """Generate a {message_type} for Austin Stretz.

AUSTIN'S PROFILE:
{profile}

JOB CONTEXT:
Company: {company_name}
Job Title: {job_title}
Job Description Summary: {job_summary}

NOTE: If company name or job title is blank/empty, do not reference them directly. Write the message without specific company name mentions if unavailable.

MESSAGE SPECIFICATIONS:
Type: {message_type_name}
{specs}

TARGET AUDIENCE: {audience}
{audience_context}

TONE: {tone}
{tone_context}

ADDITIONAL CONTEXT FROM USER:
{additional_context}

---

CONTENT RULES (CRITICAL):
- NO em-dashes (— or --)
- NO "resonated with me"
- NO "I was drawn to"
- Speak naturally, not like an LLM
- Reference Austin's ACTUAL experience
- Be specific about fit
- Use simple punctuation (periods, commas only)

{char_limit_instruction}

---

OUTPUT FORMAT - Respond with valid JSON only:
{{
  "message": "The full message text",
  "subject": "Subject line if applicable, otherwise null",
  "character_count": number,
  "word_count": number
}}"""


def generate_follow_up_message(
    message_type: str,
    company_name: str,
    job_title: str,
    job_description: str,
    audience: str = "recruiter",
    tone: str = "professional",
    additional_context: str = ""
) -> dict:
    """
    Generate a follow-up message based on type, audience, and tone.

    Args:
        message_type: One of 'linkedin_connection', 'linkedin_inmail', 'follow_up_email', 'general_fit'
        company_name: Company name
        job_title: Job title
        job_description: Full or summarized job description
        audience: One of 'recruiter', 'hiring_manager', 'technical_lead'
        tone: One of 'professional', 'enthusiastic', 'technical'
        additional_context: Optional additional notes from user

    Returns:
        Dictionary with message, subject (if applicable), character_count, word_count
    """
    if message_type not in MESSAGE_SPECS:
        raise ValueError(f"Invalid message type: {message_type}")

    specs = MESSAGE_SPECS[message_type]
    client = get_client()

    # Build specs description
    specs_text = f"Max length: {specs.get('max_chars', specs.get('word_range', 'flexible'))}\n"
    specs_text += f"Description: {specs['description']}\n"
    specs_text += f"Format: {specs['format']}"

    # Character limit instruction for connection requests
    char_limit_instruction = ""
    if message_type == "linkedin_connection":
        char_limit_instruction = f"""
CRITICAL: LinkedIn connection requests have a STRICT 250 character limit.
Your message MUST be under 250 characters including spaces.
Count carefully. Be concise. Every word must earn its place.
"""

    # Truncate job description for context (keep it manageable)
    job_summary = job_description[:1500] + "..." if len(job_description) > 1500 else job_description

    prompt = MESSAGE_PROMPT.format(
        message_type=message_type,
        profile=get_profile_summary(),
        company_name=company_name or "",
        job_title=job_title or "",
        job_summary=job_summary,
        message_type_name=specs['name'],
        specs=specs_text,
        audience=audience,
        audience_context=AUDIENCE_CONTEXT.get(audience, ""),
        tone=tone,
        tone_context=TONE_CONTEXT.get(tone, ""),
        additional_context=additional_context or "None provided",
        char_limit_instruction=char_limit_instruction
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    response_text = message.content[0].text.strip()

    # Parse JSON response
    try:
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines[-1].strip() == '```':
                lines = lines[:-1]
            response_text = '\n'.join(lines)

        result = json.loads(response_text)

        # Clean the message
        msg = result.get('message', '')
        msg = msg.replace('—', ',').replace('--', ',')
        banned = ['resonated with me', 'I was drawn to', "I'm particularly drawn to"]
        for phrase in banned:
            msg = msg.replace(phrase, 'caught my attention')
            msg = msg.replace(phrase.capitalize(), 'This caught my attention')
        result['message'] = msg

        # Recalculate counts after cleaning
        result['character_count'] = len(msg)
        result['word_count'] = len(msg.split())

        # For connection requests, enforce the limit
        if message_type == "linkedin_connection" and result['character_count'] > 250:
            # Try to trim
            msg = msg[:247] + "..."
            result['message'] = msg
            result['character_count'] = len(msg)
            result['word_count'] = len(msg.split())
            result['trimmed'] = True

        # Add metadata
        result['message_type'] = message_type
        result['filename_suffix'] = specs['filename_suffix']

        return result

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse response: {e}\nResponse: {response_text[:500]}")


def save_message_to_file(message_text: str, subject: str, company_name: str, message_type: str, output_dir: str) -> str:
    """
    Save a message to a text file.

    Args:
        message_text: The message content
        subject: Subject line (if applicable)
        company_name: Company name for filename
        message_type: Type of message for filename suffix
        output_dir: Directory to save to

    Returns:
        Full filepath where the message was saved
    """
    import re
    from datetime import datetime

    specs = MESSAGE_SPECS.get(message_type, {})
    suffix = specs.get('filename_suffix', 'Message')

    # Clean company name for filename
    if company_name:
        clean_company = re.sub(r'[^\w\s-]', '', company_name).strip()
    else:
        clean_company = ""

    # Build filename - handle empty company name gracefully
    if clean_company:
        filename = f"Austin Stretz - {clean_company} {suffix}.txt"
    else:
        filename = f"Austin Stretz - {suffix}.txt"
    filepath = os.path.join(output_dir, filename)

    # Handle duplicates
    counter = 1
    base_filepath = filepath
    while os.path.exists(filepath):
        name, ext = os.path.splitext(base_filepath)
        filepath = f"{name} ({counter}){ext}"
        counter += 1

    # Build file content
    content = ""
    if subject:
        content += f"Subject: {subject}\n\n"
    content += message_text

    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath
