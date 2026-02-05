"""
Job Description Analyzer
Uses Claude API to analyze job descriptions and make application decisions
"""

import os
import json
from anthropic import Anthropic

from profile import (
    get_profile_summary,
    REJECT_CRITERIA,
    RESUME_ROUTING,
    PRIORITY_TRIGGERS
)


def get_client():
    """Get Anthropic API client"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return Anthropic(api_key=api_key)


ANALYSIS_PROMPT = """You are analyzing a job description to help Austin Stretz decide:
1. Should he apply? (APPLY or REJECT)
2. Which resume variant to use? (Edge AI, AI PM, or Traditional PM)
3. Is this a priority application requiring extra effort?

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

IMPORTANT INSTRUCTIONS:
1. Carefully read the job description and identify company name, job title, location, compensation, and required experience.
2. Apply the auto-reject criteria first. If ANY reject criteria are met, decision MUST be REJECT.
3. Count keyword occurrences to determine the best resume variant.
4. Check if any priority triggers apply.
5. Be specific in your analysis - cite actual text from the job description.

Respond ONLY with valid JSON in this exact format (no markdown, no explanation):
{{
  "decision": "APPLY" or "REJECT",
  "recommended_resume": "Edge AI" or "AI PM" or "Traditional PM",
  "priority_level": "PRIORITY" or "STANDARD" or "REJECT",
  "company_name": "detected company name or null if not found",
  "job_title": "detected job title or null if not found",
  "analysis": {{
    "experience_match": "Strong/Moderate/Weak - explain why with specific examples from job posting",
    "compensation": "Detected salary range and assessment. Say 'Not specified' if not found",
    "location": "Remote/Hybrid/Onsite - and whether it fits KC metro requirement",
    "reject_reasons": ["specific reason 1 with evidence", "reason 2"] or [] if none,
    "priority_reasons": ["specific reason 1", "reason 2"] or [] if none,
    "key_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "resume_rationale": "Explain why this resume variant was chosen based on keyword analysis",
    "extra_touches": ["LinkedIn outreach to hiring manager", "Portfolio artifact: Hoops Metrics case study"] or [] if not priority,
    "talking_points": ["Specific point for interviews based on job requirements", "Another talking point"] or []
  }}
}}"""


def analyze_job_description(job_description: str, additional_context: str = "") -> dict:
    """
    Analyze a job description and return application decision + recommendations.

    Args:
        job_description: The full text of the job description
        additional_context: Optional additional context from the user

    Returns:
        Dictionary containing decision, resume type, priority level, and analysis details
    """
    client = get_client()

    prompt = ANALYSIS_PROMPT.format(
        profile=get_profile_summary(),
        reject_criteria=REJECT_CRITERIA,
        resume_routing=RESUME_ROUTING,
        priority_triggers=PRIORITY_TRIGGERS,
        job_description=job_description,
        additional_context=additional_context or "None provided"
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
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
            # Remove markdown code block markers
            lines = response_text.split('\n')
            # Remove first and last line if they're code markers
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines[-1].strip() == '```':
                lines = lines[:-1]
            response_text = '\n'.join(lines)

        result = json.loads(response_text)

        # Validate required fields
        required_fields = ['decision', 'recommended_resume', 'priority_level', 'analysis']
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field: {field}")

        # Validate decision value
        if result['decision'] not in ['APPLY', 'REJECT']:
            raise ValueError(f"Invalid decision value: {result['decision']}")

        # Validate resume type
        valid_resumes = ['Edge AI', 'AI PM', 'Traditional PM']
        if result['recommended_resume'] not in valid_resumes:
            raise ValueError(f"Invalid resume type: {result['recommended_resume']}")

        # Validate priority level
        valid_priorities = ['PRIORITY', 'STANDARD', 'REJECT']
        if result['priority_level'] not in valid_priorities:
            raise ValueError(f"Invalid priority level: {result['priority_level']}")

        return result

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Claude response as JSON: {e}\nResponse: {response_text[:500]}")
