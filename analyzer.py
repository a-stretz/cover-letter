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

2. DECISION SUMMARY: Provide 2-3 bullet points (not a paragraph):
   - First bullet: Clear apply/reject rationale in one strong, direct sentence
   - Second bullet: Primary alignment or misalignment factor
   - Third bullet (if APPLY): What makes this a particularly good or just adequate fit

3. ROLE SUMMARY: Synthesize what this role actually IS in 2-4 bullet points:
   - What is the core function of this role?
   - What team/department does it sit in? Who does it report to?
   - What are they actually building or managing?
   - What's the day-to-day focus?
   This helps quickly understand the role without re-reading the full JD.

4. EXPERIENCE MATCH SCORING (use these 4 criteria):
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

   Provide as bullet points, not a paragraph. Be specific about which projects/skills match.

5. LOCATION: Classify as Remote/Hybrid/Onsite/KC Metro. One bullet point on location fit.

6. COMPENSATION: Detect salary range if mentioned.
   IMPORTANT LOGIC: Austin's minimum is $100,000. A salary range is "In Range" if the MAXIMUM value >= $100,000.
   Examples:
   - $90k-$120k → IN RANGE (max $120k >= $100k)
   - $80k-$100k → IN RANGE (max $100k >= $100k)
   - $70k-$90k → BELOW RANGE (max $90k < $100k)
   - $120k-$160k → IN RANGE
   - $150k+ → IN RANGE
   - Not mentioned → UNKNOWN
   Output format: "[detected range] ([fit classification])" e.g., "$90k-$120k (In Range)"

7. COMPANY DOMAIN: One bullet point describing the company's industry/space.

8. KEYWORDS: List 5-8 key technical/domain keywords from the job posting.

9. RESUME SELECTION: Choose Edge AI, AI PM, or Traditional PM based on keyword analysis.

10. REJECT REASONS: If REJECT, provide as bullet points.

11. IF DECISION IS APPLY: Generate a cover letter following rules below.
    IF DECISION IS REJECT: Set cover_letter to null.

---

COVER LETTER GENERATION RULES (only if APPLY):

# CRITICAL: DO NOT HALLUCINATE DETAILS NOT IN AUSTIN'S PROFILE
# Every fact you mention MUST come from the profile above. Do not invent experience.

ANTI-HALLUCINATION RULES (ABSOLUTE - NEVER VIOLATE):

EDUCATION:
- Austin has NO college degree listed in his profile
- DO NOT mention any university, degree, or education
- DO NOT reference "Kansas University", "Kansas State", or any other school
- If you don't see education in the profile, DO NOT invent it

ACTUAL JOB HISTORY (ONLY USE THESE):
1. AI Product Manager at NeoSavant.ai (Nov 2023 – Present)
   - Edge-AI Computer Vision platform for sports performance analysis
   - Products: SmartPlayer, Voice Assist, Heuristic v4, Onsite Capture
2. Product Lead / Sales Operations / Co-Founder at 1872 Consulting, LLC (Jun 2015 – Dec 2024)
   - HR Tech consulting, HRIS platform modernization, Fortune 100 clients

DO NOT invent job titles like:
- "Senior Technical Product Manager" (not his title)
- "VP of Product" (never held)
- "Director of..." (never held)
- Any title not explicitly listed above

ACTUAL CERTIFICATIONS (ONLY THESE):
- Advanced Certified Scrum Product Owner (A-CSPO) - Scrum Alliance
- AI Product Manager Certification - IBM
- Certified Scrum Product Owner (CSPO) - Scrum Alliance

ACTUAL PROJECTS (ONLY REFERENCE THESE):
- SmartPlayer (2D/3D Performance Review System)
- Voice Assist (Real-Time AI Coaching Feedback Engine)
- Heuristic System v4 (Biomechanical Intelligence Engine)
- Onsite Capture (Operations Platform)
- Claude Hoops Metrics (optional - personal project)

IF UNSURE: Be more general rather than making up specifics.

---

You are an expert at writing authentic, professional cover letters that sound human, grounded, and specific.
Write in Austin Stretz's natural voice, based strictly on his real experience and the job description.
Your goal is clarity, credibility, and signal. Not politeness or polish for its own sake.

CORE PRINCIPLE:
This cover letter should read like the opening minutes of a strong hiring conversation with a senior Product Manager.
It should feel intentional, informed, and grounded in real work.
If a sentence could be said by any competent applicant, it does not belong.

CRITICAL GUIDANCE ON OPENING LINES:
The first sentence must earn attention.

DO NOT open with administrative statements such as:
- "I am applying for..."
- "I am writing to express interest..."
- "I am excited to apply..."
- "I am reaching out regarding..."
These are dead, expected, and add no signal.

EFFECTIVE OPENERS MUST:
- Start with context, not intent
- Reflect why this role exists now, not just that it exists
- Demonstrate understanding of the problem space, moment, or shift the role sits in
- Sound like something Austin would say when explaining why a role matters in a real conversation

Preferred opener patterns include:
- Framing a current shift or inflection point relevant to the role (e.g., agentic workflows moving from experimentation to production, AI systems becoming operational rather than exploratory, increased execution pressure in regulated or complex domains)
- Connecting that shift directly to the role or product (why this team sits close to the leverage, why this work matters now, why execution discipline is required)
- Implicitly positioning Austin as someone who understands and has operated in that environment

The opener should answer one silent question:
"Why does this role matter right now, and why does this person see it clearly?"

ACCEPTABLE LANGUAGE:
- Plainspoken and professional
- Calm, confident, and factual
- Observational rather than emotional
- Grounded in real work Austin has done
- Sounds like a Product Manager explaining a system, not selling himself

Use short to medium-length sentences. Vary structure naturally.

RESTRICTED LANGUAGE (ABSOLUTE):

Emotional framing:
- "exciting time"
- "thrilled"
- "passionate"
- "energized"
- "inspired"
- "excited by"
- "resonated with me"
- "I was drawn to"

Vague enthusiasm:
- "at the helm"
- "driving force"
- "new world"
- "cutting-edge"
- "next-generation"
- "fast-paced environment"
- "innovative solutions"
- "I would love the chance"
- "I am eager to contribute"

LLM-style abstraction:
- Mission-level platitudes
- Generic future claims
- Rephrased job descriptions
- Over-explaining obvious concepts

Defensive or compensating language:
- Mentioning skills Austin does not have
- Justifying gaps or missing requirements
- Hedging phrases such as "while I may not have..."
- Highlighting learning curves or weaknesses

If enthusiasm is present, it must be implicit, expressed through clarity and specificity.

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
- Strong, context-driven opener
- Reference the product, platform, or system
- Establish why the role matters now
- NO administrative filler ("I am applying for...", "I am writing to express...")

Paragraph 2:
- Concrete alignment to Austin's real experience
- Systems owned, backlogs managed, workflows shipped, teams partnered
- Pull from: SmartPlayer, Voice Assist, Heuristic v4, Data QA, Onsite platform
- Focus on execution and tradeoffs, not aspiration

Paragraph 3:
- Calm, professional close
- Reinforce alignment and intent
- No emotional escalation

FINAL CHECK BEFORE OUTPUT:
Confirm that:
- The first sentence could not be written by a generic applicant
- The opener frames context before intent
- Every claim is defensible
- Tone is confident, not performative
- No forbidden phrases or punctuation appear

SAMPLE COVER LETTERS FOR VOICE REFERENCE:
{sample_bold}

{sample_conviva}

{sample_hudl}

---

OUTPUT FORMAT - Respond with valid JSON only (no markdown):
{{
  "decision": "APPLY" or "REJECT",
  "decision_summary": "2-3 bullet points as a single string with bullet markers (• First point\\n• Second point\\n• Third point)",
  "company_name": "detected company name or null if not found",
  "job_title": "detected job title or null if not found",
  "priority_level": "PRIORITY" or "STANDARD" or "REJECT",
  "analysis": {{
    "role_summary": "2-4 bullet points as a single string (• Core function\\n• Team/reporting\\n• What they build\\n• Day-to-day focus)",
    "location_type": "Remote" or "Hybrid" or "Onsite" or "KC Metro",
    "location_details": "brief bullet on location fit",
    "compensation_range": "detected range or 'Not specified'",
    "compensation_fit": "Below Range" or "In Range" or "Above Range" or "Unknown",
    "company_domain": "One bullet point about company's industry/space",
    "experience_match": {{
      "score": 1-10,
      "label": "Exceptional Fit" or "Strong Fit" or "Moderate Fit" or "Weak Fit" or "Poor Fit",
      "summary": "3-5 bullet points as a single string covering all 4 criteria",
      "responsibility_alignment": "brief bullet",
      "domain_experience": "brief bullet",
      "technical_skills": "brief bullet on matching skills",
      "requirements_fit": "brief bullet"
    }},
    "keywords_detected": "comma-separated list of 5-8 keywords",
    "reject_reasons": ["reason1", "reason2"] or [],
    "priority_reasons": ["reason1", "reason2"] or []
  }},
  "cover_letter": "Full cover letter body text (exactly 3 paragraphs) or null if REJECT"
}}"""


COVER_LETTER_ONLY_PROMPT = """You are an expert at writing authentic, professional cover letters that sound human, grounded, and specific.
Write in Austin Stretz's natural voice, based strictly on his real experience and the job description.
Your goal is clarity, credibility, and signal. Not politeness or polish for its own sake.

# CRITICAL: DO NOT HALLUCINATE DETAILS NOT IN AUSTIN'S PROFILE
# Every fact you mention MUST come from the profile above. Do not invent experience.

ANTI-HALLUCINATION RULES (ABSOLUTE - NEVER VIOLATE):

EDUCATION:
- Austin has NO college degree listed in his profile
- DO NOT mention any university, degree, or education
- DO NOT reference "Kansas University", "Kansas State", or any other school
- If you don't see education in the profile, DO NOT invent it

ACTUAL JOB HISTORY (ONLY USE THESE):
1. AI Product Manager at NeoSavant.ai (Nov 2023 – Present)
   - Edge-AI Computer Vision platform for sports performance analysis
   - Products: SmartPlayer, Voice Assist, Heuristic v4, Onsite Capture
2. Product Lead / Sales Operations / Co-Founder at 1872 Consulting, LLC (Jun 2015 – Dec 2024)
   - HR Tech consulting, HRIS platform modernization, Fortune 100 clients

DO NOT invent job titles like:
- "Senior Technical Product Manager" (not his title)
- "VP of Product" (never held)
- "Director of..." (never held)
- Any title not explicitly listed above

ACTUAL CERTIFICATIONS (ONLY THESE):
- Advanced Certified Scrum Product Owner (A-CSPO) - Scrum Alliance
- AI Product Manager Certification - IBM
- Certified Scrum Product Owner (CSPO) - Scrum Alliance

ACTUAL PROJECTS (ONLY REFERENCE THESE):
- SmartPlayer (2D/3D Performance Review System)
- Voice Assist (Real-Time AI Coaching Feedback Engine)
- Heuristic System v4 (Biomechanical Intelligence Engine)
- Onsite Capture (Operations Platform)
- Claude Hoops Metrics (optional - personal project)

IF UNSURE: Be more general rather than making up specifics.

---

AUSTIN'S PROFESSIONAL PROFILE:
{profile}

JOB DESCRIPTION:
{job_description}

COMPANY: {company_name}
JOB TITLE: {job_title}
RESUME VARIANT: {resume_type}

---

CORE PRINCIPLE:
This cover letter should read like the opening minutes of a strong hiring conversation with a senior Product Manager.
It should feel intentional, informed, and grounded in real work.
If a sentence could be said by any competent applicant, it does not belong.

CRITICAL GUIDANCE ON OPENING LINES:
The first sentence must earn attention.

DO NOT open with administrative statements such as:
- "I am applying for..."
- "I am writing to express interest..."
- "I am excited to apply..."
- "I am reaching out regarding..."
These are dead, expected, and add no signal.

EFFECTIVE OPENERS MUST:
- Start with context, not intent
- Reflect why this role exists now, not just that it exists
- Demonstrate understanding of the problem space, moment, or shift the role sits in
- Sound like something Austin would say when explaining why a role matters in a real conversation

Preferred opener patterns include:
- Framing a current shift or inflection point relevant to the role (e.g., agentic workflows moving from experimentation to production, AI systems becoming operational rather than exploratory, increased execution pressure in regulated or complex domains)
- Connecting that shift directly to the role or product (why this team sits close to the leverage, why this work matters now, why execution discipline is required)
- Implicitly positioning Austin as someone who understands and has operated in that environment

The opener should answer one silent question:
"Why does this role matter right now, and why does this person see it clearly?"

ACCEPTABLE LANGUAGE:
- Plainspoken and professional
- Calm, confident, and factual
- Observational rather than emotional
- Grounded in real work Austin has done
- Sounds like a Product Manager explaining a system, not selling himself

Use short to medium-length sentences. Vary structure naturally.

RESTRICTED LANGUAGE (ABSOLUTE):

Emotional framing:
- "exciting time"
- "thrilled"
- "passionate"
- "energized"
- "inspired"
- "excited by"
- "resonated with me"
- "I was drawn to"

Vague enthusiasm:
- "at the helm"
- "driving force"
- "new world"
- "cutting-edge"
- "next-generation"
- "fast-paced environment"
- "innovative solutions"
- "I would love the chance"
- "I am eager to contribute"

LLM-style abstraction:
- Mission-level platitudes
- Generic future claims
- Rephrased job descriptions
- Over-explaining obvious concepts

Defensive or compensating language:
- Mentioning skills Austin does not have
- Justifying gaps or missing requirements
- Hedging phrases such as "while I may not have..."
- Highlighting learning curves or weaknesses

If enthusiasm is present, it must be implicit, expressed through clarity and specificity.

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
- Strong, context-driven opener
- Reference the product, platform, or system
- Establish why the role matters now
- NO administrative filler ("I am applying for...", "I am writing to express...")

Paragraph 2:
- Concrete alignment to Austin's real experience
- Systems owned, backlogs managed, workflows shipped, teams partnered
- Pull from: SmartPlayer, Voice Assist, Heuristic v4, Data QA, Onsite platform at NeoSavant
- Focus on execution and tradeoffs, not aspiration

Paragraph 3:
- Calm, professional close
- Reinforce alignment and intent
- No emotional escalation

FINAL CHECK BEFORE OUTPUT:
Confirm that:
- The first sentence could not be written by a generic applicant
- The opener frames context before intent
- Every claim is defensible
- Tone is confident, not performative
- No forbidden phrases or punctuation appear

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
    # Administrative openers (dead, expected, no signal)
    "I am applying for",
    "I am writing to express interest",
    "I am writing to express my interest",
    "I am excited to apply",
    "I am reaching out regarding",
    "I'm applying for",
    "I'm writing to express",
    "I'm excited to apply",
    # Emotional framing
    "resonated with me",
    "I was drawn to",
    "I'm particularly drawn to",
    "excited by",
    "passionate about",
    "thrilled",
    "energized",
    "inspired by",
    "exciting time",
    "I'm excited to",
    "I'm thrilled to",
    "I am excited to",
    "I am thrilled to",
    # Vague enthusiasm
    "at the helm",
    "driving force",
    "new world",
    "cutting-edge",
    "next-generation",
    "fast-paced environment",
    "innovative solutions",
    "This opportunity feels like a perfect fit",
    "I would love the chance",
    "I am eager to contribute",
    "I'm eager to",
    # Defensive/compensating language
    "while I may not have",
    "although I lack",
    "while I don't have",
    "although I don't have",
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

        # Validate required fields (resume selection is now handled separately by resume_selector.py)
        required_fields = ['decision', 'decision_summary', 'priority_level', 'analysis']
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
        company_name=company_name or "",
        job_title=job_title or "",
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
