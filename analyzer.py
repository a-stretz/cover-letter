"""
Combined Job Analyzer and Cover Letter Generator
Single API call for analysis + cover letter generation (if APPLY)
"""

import os
import json
from anthropic import Anthropic

from profile import (
    get_profile_summary,
    REJECT_CRITERIA,
    RESUME_ROUTING,
    PRIORITY_TRIGGERS,
    SAMPLE_COVER_LETTERS
)


def get_client():
    """Get Anthropic API client"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return Anthropic(api_key=api_key)


COMBINED_PROMPT = """You are analyzing a job description for Austin Stretz and, if he should apply, generating a cover letter.

AUSTIN'S PROFESSIONAL PROFILE:
{profile}

AUTO-REJECT CRITERIA:
{reject_criteria}

RESUME ROUTING LOGIC:
{resume_routing}

PRIORITY TRIGGERS:
{priority_triggers}

---

JOB DESCRIPTION:
{job_description}

ADDITIONAL CONTEXT PROVIDED BY USER:
{additional_context}

---

ANALYSIS INSTRUCTIONS:

1. DECISION: Determine if Austin should APPLY or REJECT based on criteria above.

2. DECISION SUMMARY: Write 2-3 sentences explaining the decision. Quick at-a-glance: Should he apply? Why/why not?

3. EXPERIENCE MATCH SCORING (use these 4 criteria):
   - Responsibility Alignment: How Austin's past responsibilities match their needs
   - Domain Experience: Relevant domain/industry expertise
   - Technical Skills: Which of Austin's technical skills match
   - Requirements Fit: How well Austin meets their listed requirements

   Score 1-10:
   - 9-10: Exceptional fit - Austin's experience directly maps to their needs
   - 7-8: Strong fit - Majority of experience aligns, minor gaps
   - 5-6: Moderate fit - Some relevant experience, some gaps
   - 3-4: Weak fit - Limited overlap, significant gaps
   - 1-2: Poor fit - Minimal relevant experience

   Write a single cohesive paragraph (4-6 sentences) incorporating all 4 criteria naturally.
   Be specific about which of Austin's projects/skills match. Mention gaps briefly but honestly.

4. LOCATION: Classify as Remote/Hybrid/Onsite/KC Metro. Note if it fits Austin's preferences.

5. COMPENSATION: Detect salary range if mentioned. Classify as Below Range/In Range/Above Range/Unknown.

6. COMPANY DOMAIN: One sentence describing the company's industry/space.

7. KEYWORDS: List 5-8 key technical/domain keywords from the job posting.

8. RESUME SELECTION: Choose Edge AI, AI PM, or Traditional PM based on keyword analysis.

9. IF DECISION IS APPLY: Generate a cover letter following rules below.
   IF DECISION IS REJECT: Set cover_letter to null.

---

COVER LETTER GENERATION RULES (only if APPLY):

You are writing an authentic, professional cover letter that sounds human, grounded, and specific.
Write in Austin Stretz's natural voice, based strictly on his real experience and the job description.
Your goal is clarity, credibility, and fit. Not polish for its own sake.

ACCEPTABLE LANGUAGE:
Use language that is:
- Plainspoken and professional
- Specific and concrete
- Calm, confident, and factual
- Grounded in real work Austin has done
- Written the way a strong product manager would speak in a hiring conversation

Preferred phrasing patterns:
- "I have worked on..."
- "My role involved..."
- "I led / owned / supported..."
- "This role aligns well with my experience in..."
- "The work you are doing around X matches the type of problems I have been solving..."
- "I am interested in applying my experience with..."

Use short to medium-length sentences. Vary sentence structure naturally.

BANNED LANGUAGE (DO NOT USE):

Emotional or performative language:
- "resonated with me"
- "I was drawn to"
- "excited by"
- "passionate about"
- "thrilled"
- "energized"
- "inspired"

Generic enthusiasm or filler:
- "This opportunity feels like a perfect fit"
- "I would love the chance"
- "I am eager to contribute"
- "cutting-edge"
- "fast-paced environment"
- "innovative solutions"
- "next-generation"

LLM-style patterns:
- Abstract mission statements
- Vague impact claims
- Rephrasing the job description
- Over-explaining obvious concepts

Defensive or compensating language:
- Mentioning skills Austin does not have
- Justifying gaps or missing requirements
- Hedging phrases such as "while I may not have..."
- Highlighting learning curves or weaknesses

Punctuation violations:
- No em dashes (— or --)
- No exclamation points
- No semicolons
- No emojis
- Only periods and commas are allowed

CONTENT RULES:
- Every skill or experience mentioned must be real and defensible
- Only reference qualifications that clearly match the job description
- Do not invent tools, industries, or scope
- Do not oversell or exaggerate impact
- If a requirement does not match Austin's experience, ignore it entirely

STRUCTURE (EXACTLY 3 PARAGRAPHS):

Paragraph 1:
- State interest in the role and company
- Reference the company's product, platform, or problem space
- The opening should sound intentional and role-specific

Paragraph 2:
- Connect Austin's real experience directly to the role
- Reference concrete work: systems owned, products shipped, workflows defined, teams partnered with
- Pull from: SmartPlayer, Voice Assist, Heuristic v4, Data QA, Onsite platform
- Focus on fit, not aspiration

Paragraph 3:
- Close professionally and calmly
- Reinforce alignment and interest
- No dramatic or emotional language

SAMPLE COVER LETTERS FOR VOICE REFERENCE:
{sample_bold}

{sample_conviva}

{sample_hudl}

---

OUTPUT FORMAT - Respond with valid JSON only (no markdown):
{{
  "decision": "APPLY" or "REJECT",
  "decision_summary": "2-3 sentence summary of why apply/reject",
  "company_name": "detected company name or null",
  "job_title": "detected job title or null",
  "recommended_resume": "Edge AI" or "AI PM" or "Traditional PM",
  "priority_level": "PRIORITY" or "STANDARD" or "REJECT",
  "analysis": {{
    "location_type": "Remote" or "Hybrid" or "Onsite" or "KC Metro",
    "location_details": "brief note on location fit",
    "compensation_range": "detected range or 'Not specified'",
    "compensation_fit": "Below Range" or "In Range" or "Above Range" or "Unknown",
    "company_domain": "One sentence about company's industry/space",
    "experience_match": {{
      "score": 1-10,
      "label": "Exceptional Fit" or "Strong Fit" or "Moderate Fit" or "Weak Fit" or "Poor Fit",
      "summary": "4-6 sentence paragraph incorporating all criteria",
      "responsibility_alignment": "brief note",
      "domain_experience": "brief note",
      "technical_skills": "brief note on matching skills",
      "requirements_fit": "brief note"
    }},
    "keywords_detected": "comma-separated list of 5-8 keywords",
    "reject_reasons": ["reason1", "reason2"] or [],
    "priority_reasons": ["reason1", "reason2"] or [],
    "resume_rationale": "Why this resume variant was chosen"
  }},
  "cover_letter": "Full cover letter body text (exactly 3 paragraphs) or null if REJECT"
}}"""


COVER_LETTER_ONLY_PROMPT = """You are writing an authentic, professional cover letter for Austin Stretz.
Write in his natural voice, based strictly on his real experience and the job description.
Your goal is clarity, credibility, and fit. Not polish for its own sake.

AUSTIN'S PROFESSIONAL PROFILE:
{profile}

JOB DESCRIPTION:
{job_description}

COMPANY: {company_name}
JOB TITLE: {job_title}
RESUME VARIANT: {resume_type}

---

ACCEPTABLE LANGUAGE:
Use language that is:
- Plainspoken and professional
- Specific and concrete
- Calm, confident, and factual
- Grounded in real work Austin has done
- Written the way a strong product manager would speak in a hiring conversation

Preferred phrasing patterns:
- "I have worked on..."
- "My role involved..."
- "I led / owned / supported..."
- "This role aligns well with my experience in..."
- "The work you are doing around X matches the type of problems I have been solving..."
- "I am interested in applying my experience with..."

Use short to medium-length sentences. Vary sentence structure naturally.

BANNED LANGUAGE (DO NOT USE):

Emotional or performative language:
- "resonated with me"
- "I was drawn to"
- "excited by"
- "passionate about"
- "thrilled"
- "energized"
- "inspired"

Generic enthusiasm or filler:
- "This opportunity feels like a perfect fit"
- "I would love the chance"
- "I am eager to contribute"
- "cutting-edge"
- "fast-paced environment"
- "innovative solutions"
- "next-generation"

LLM-style patterns:
- Abstract mission statements
- Vague impact claims
- Rephrasing the job description
- Over-explaining obvious concepts

Defensive or compensating language:
- Mentioning skills Austin does not have
- Justifying gaps or missing requirements
- Hedging phrases such as "while I may not have..."
- Highlighting learning curves or weaknesses

Punctuation violations:
- No em dashes (— or --)
- No exclamation points
- No semicolons
- No emojis
- Only periods and commas are allowed

CONTENT RULES:
- Every skill or experience mentioned must be real and defensible
- Only reference qualifications that clearly match the job description
- Do not invent tools, industries, or scope
- Do not oversell or exaggerate impact
- If a requirement does not match Austin's experience, ignore it entirely

STRUCTURE (EXACTLY 3 PARAGRAPHS):

Paragraph 1:
- State interest in the role and company
- Reference the company's product, platform, or problem space
- The opening should sound intentional and role-specific

Paragraph 2:
- Connect Austin's real experience directly to the role
- Reference concrete work: systems owned, products shipped, workflows defined, teams partnered with
- Pull from: SmartPlayer, Voice Assist, Heuristic v4, Data QA, Onsite platform at NeoSavant
- Focus on fit, not aspiration

Paragraph 3:
- Close professionally and calmly
- Reinforce alignment and interest
- No dramatic or emotional language

SAMPLE COVER LETTERS FOR VOICE REFERENCE:
{sample_bold}

{sample_conviva}

{sample_hudl}

---

Generate ONLY the cover letter body (exactly 3 paragraphs).
No header, greeting, or closing signature. The system adds those.
Output plain text ready to insert into a document."""


# Extended list of banned phrases for post-processing
BANNED_PHRASES = [
    "resonated with me",
    "I was drawn to",
    "I'm particularly drawn to",
    "excited by",
    "passionate about",
    "thrilled",
    "energized",
    "inspired by",
    "This opportunity feels like a perfect fit",
    "I would love the chance",
    "I am eager to contribute",
    "cutting-edge",
    "fast-paced environment",
    "innovative solutions",
    "next-generation",
    "while I may not have",
    "although I lack",
    "I'm excited to",
    "I'm thrilled to",
]


def clean_cover_letter(cover_letter: str) -> str:
    """Clean cover letter of banned phrases and punctuation"""
    if not cover_letter:
        return cover_letter

    # Remove em-dashes
    cover_letter = cover_letter.replace('—', ',').replace('--', ',')

    # Remove exclamation points
    cover_letter = cover_letter.replace('!', '.')

    # Remove semicolons
    cover_letter = cover_letter.replace(';', ',')

    # Remove banned phrases (case-insensitive replacement)
    for phrase in BANNED_PHRASES:
        # Check for the phrase in various cases
        if phrase.lower() in cover_letter.lower():
            # Find and replace (preserving surrounding text)
            import re
            pattern = re.compile(re.escape(phrase), re.IGNORECASE)
            # Replace with empty string or neutral alternative
            cover_letter = pattern.sub('', cover_letter)

    # Clean up any double spaces or awkward punctuation left behind
    cover_letter = cover_letter.replace('  ', ' ')
    cover_letter = cover_letter.replace(' ,', ',')
    cover_letter = cover_letter.replace(',,', ',')
    cover_letter = cover_letter.replace('..', '.')

    return cover_letter.strip()


def analyze_and_generate(job_description: str, additional_context: str = "") -> dict:
    """
    Analyze job description and generate cover letter in one API call.
    Returns analysis result with cover letter if decision is APPLY.
    """
    client = get_client()

    prompt = COMBINED_PROMPT.format(
        profile=get_profile_summary(),
        reject_criteria=REJECT_CRITERIA,
        resume_routing=RESUME_ROUTING,
        priority_triggers=PRIORITY_TRIGGERS,
        job_description=job_description,
        additional_context=additional_context or "None provided",
        sample_bold=SAMPLE_COVER_LETTERS["BOLD"],
        sample_conviva=SAMPLE_COVER_LETTERS["Conviva"],
        sample_hudl=SAMPLE_COVER_LETTERS["Hudl"]
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Extract the response text
    response_text = message.content[0].text.strip()

    # Parse JSON response
    try:
        # Handle potential markdown code blocks
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines[-1].strip() == '```':
                lines = lines[:-1]
            response_text = '\n'.join(lines)

        result = json.loads(response_text)

        # Validate required fields
        required_fields = ['decision', 'decision_summary', 'recommended_resume', 'priority_level', 'analysis']
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")

        # Validate decision value
        if result['decision'] not in ['APPLY', 'REJECT']:
            raise ValueError(f"Invalid decision value: {result['decision']}")

        # Clean cover letter if present
        if result.get('cover_letter'):
            result['cover_letter'] = clean_cover_letter(result['cover_letter'])

        return result

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Claude response as JSON: {e}\nResponse: {response_text[:500]}")


# Keep the old function for backwards compatibility
def analyze_job_description(job_description: str, additional_context: str = "") -> dict:
    """Legacy function - now calls analyze_and_generate"""
    return analyze_and_generate(job_description, additional_context)


def generate_cover_letter_only(
    job_description: str,
    company_name: str,
    job_title: str,
    resume_type: str,
    priority_level: str
) -> str:
    """
    Generate just a cover letter without full analysis.
    Used for override scenarios where user wants to apply despite rejection.
    """
    client = get_client()

    prompt = COVER_LETTER_ONLY_PROMPT.format(
        profile=get_profile_summary(),
        job_description=job_description,
        company_name=company_name or "Unknown Company",
        job_title=job_title or "Product Role",
        resume_type=resume_type,
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

    cover_letter = message.content[0].text.strip()

    # Clean the cover letter
    return clean_cover_letter(cover_letter)
