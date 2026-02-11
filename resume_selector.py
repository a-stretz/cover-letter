"""
Resume Selector Module
Analyzes job descriptions and selects the most strategically aligned resume variant.
Does NOT generate or modify resumes - only selects from 3 pre-built variants.
"""

import os
import json
import re
from anthropic import Anthropic


def get_client():
    """Get Anthropic API client"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return Anthropic(api_key=api_key)


# Resume variants available for selection
RESUME_VARIANTS = [
    "AI Product Manager",
    "Platform Product Manager",
    "B2B SaaS Product Manager"
]

# Weighted keyword signals for each resume category
AI_SIGNALS = {
    "high_weight": [
        "AI Product Manager", "ML lifecycle", "model evaluation",
        "generative AI", "LLMs", "LLM", "AI copilots", "NLP",
        "model monitoring", "AI governance", "computer vision",
        "training data", "model interpretability", "ML platform",
        "AI-enabled products", "model behavior", "AI experimentation",
        "LLM orchestration", "prompt engineering", "AI feature development",
        "machine learning", "deep learning", "neural network",
        "AI strategy", "responsible AI", "AI ethics"
    ],
    "medium_weight": [
        "AI", "ML", "artificial intelligence", "machine learning product",
        "data science", "predictive", "inference", "embeddings",
        "vector", "RAG", "retrieval augmented", "fine-tuning",
        "model deployment", "AI ops", "MLOps"
    ]
}

PLATFORM_SIGNALS = {
    "high_weight": [
        "Platform Product Manager", "API integrations", "system integrations",
        "data pipelines", "cross-system workflows", "orchestration",
        "multi-product surfaces", "platform scalability",
        "infrastructure collaboration", "backend-heavy",
        "integration strategy", "enterprise system architecture",
        "SaaS platform ecosystem", "complex dependencies",
        "cross-team coordination", "systems thinking",
        "technical platform", "developer platform", "API strategy"
    ],
    "medium_weight": [
        "platform", "API", "integration", "microservices", "architecture",
        "scalability", "infrastructure", "backend", "distributed systems",
        "data pipeline", "ETL", "middleware", "service mesh",
        "technical coordination", "systems design"
    ]
}

SAAS_SIGNALS = {
    "high_weight": [
        "roadmap ownership", "feature delivery", "backlog management",
        "sprint execution", "customer discovery", "product requirements",
        "stakeholder management", "incremental releases", "SaaS metrics",
        "customer-facing PM", "shipping", "predictability",
        "delivery discipline", "business alignment", "mid-market SaaS",
        "B2B SaaS", "enterprise SaaS", "product-market fit"
    ],
    "medium_weight": [
        "roadmap", "backlog", "sprint", "agile", "scrum",
        "stakeholder", "feature", "release", "customer feedback",
        "user research", "product strategy", "go-to-market",
        "metrics", "KPIs", "OKRs", "prioritization"
    ]
}


def count_signal_score(text: str, signals: dict) -> int:
    """
    Count weighted signal score in text.
    High weight signals = 3 points each
    Medium weight signals = 1 point each
    """
    text_lower = text.lower()
    score = 0
    matched_signals = []

    for signal in signals.get("high_weight", []):
        if signal.lower() in text_lower:
            score += 3
            matched_signals.append(signal)

    for signal in signals.get("medium_weight", []):
        if signal.lower() in text_lower:
            score += 1
            matched_signals.append(signal)

    return score, matched_signals


def select_resume_local(job_description: str) -> dict:
    """
    Local/fast resume selection using keyword matching.
    Returns selection with confidence and reasoning.
    """
    # Calculate scores for each category
    ai_score, ai_matches = count_signal_score(job_description, AI_SIGNALS)
    platform_score, platform_matches = count_signal_score(job_description, PLATFORM_SIGNALS)
    saas_score, saas_matches = count_signal_score(job_description, SAAS_SIGNALS)

    scores = {
        "AI Product Manager": ai_score,
        "Platform Product Manager": platform_score,
        "B2B SaaS Product Manager": saas_score
    }

    matches = {
        "AI Product Manager": ai_matches,
        "Platform Product Manager": platform_matches,
        "B2B SaaS Product Manager": saas_matches
    }

    # Find the highest score
    max_score = max(scores.values())

    # Determine confidence based on score difference
    sorted_scores = sorted(scores.values(), reverse=True)
    score_gap = sorted_scores[0] - sorted_scores[1] if len(sorted_scores) > 1 else sorted_scores[0]

    if max_score < 5:
        confidence = "Low"
    elif score_gap < 5:
        confidence = "Medium"
    else:
        confidence = "High"

    # Select the resume with highest score
    # Apply priority rules for ties or close scores
    selected = None

    # Priority Rule 1: If AI is core (high score and significant gap)
    if ai_score >= 10 and ai_score > platform_score and ai_score > saas_score:
        selected = "AI Product Manager"
    # Priority Rule 2: If AI mentioned but platform has more signals
    elif platform_score > ai_score and platform_score >= saas_score:
        selected = "Platform Product Manager"
    # Priority Rule 3: If SaaS is clearly dominant
    elif saas_score > ai_score and saas_score > platform_score:
        selected = "B2B SaaS Product Manager"
    # Priority Rule 4: If AI is highest
    elif ai_score >= platform_score and ai_score >= saas_score:
        selected = "AI Product Manager"
    # Priority Rule 5: Default to Platform (most balanced)
    else:
        selected = "Platform Product Manager"

    # Get key signals (top 5 matches)
    key_signals = matches[selected][:5]

    # Generate reasoning
    reasoning = generate_reasoning(selected, scores, key_signals)

    return {
        "selected_resume": selected,
        "confidence": confidence,
        "reasoning": reasoning,
        "key_signals": key_signals,
        "suggested_emphasis": get_emphasis_suggestion(selected, key_signals),
        "scores": scores  # Include for debugging/transparency
    }


def generate_reasoning(selected: str, scores: dict, key_signals: list) -> str:
    """Generate human-readable reasoning for the selection."""

    if selected == "AI Product Manager":
        if scores["AI Product Manager"] > 15:
            return f"Strong AI/ML focus with emphasis on {', '.join(key_signals[:3]) if key_signals else 'AI product development'}. Core product value centers on AI capabilities."
        else:
            return f"AI signals present ({', '.join(key_signals[:2]) if key_signals else 'AI-related keywords'}). Role involves AI product work as primary focus."

    elif selected == "Platform Product Manager":
        if scores["Platform Product Manager"] > 15:
            return f"Heavy emphasis on system integration and technical coordination. Key signals: {', '.join(key_signals[:3]) if key_signals else 'platform development'}."
        else:
            return f"Platform and integration focus detected. Role emphasizes {', '.join(key_signals[:2]) if key_signals else 'cross-system coordination'}."

    else:  # B2B SaaS
        if scores["B2B SaaS Product Manager"] > 15:
            return f"Traditional PM responsibilities focused on {', '.join(key_signals[:3]) if key_signals else 'delivery and stakeholder management'}. Customer-facing product work."
        else:
            return f"Standard SaaS PM role with focus on {', '.join(key_signals[:2]) if key_signals else 'roadmap and feature delivery'}."


def get_emphasis_suggestion(selected: str, key_signals: list) -> str:
    """Provide micro-adjustment suggestion for interview prep."""

    suggestions = {
        "AI Product Manager": [
            "Emphasize AI interpretability and model evaluation experience from NeoSavant",
            "Highlight Heuristic v4 work showing ML output validation",
            "Discuss Voice Assist as example of AI-to-user translation"
        ],
        "Platform Product Manager": [
            "Emphasize systems integration experience from 1872 Consulting",
            "Highlight cross-team coordination and technical translation skills",
            "Discuss API-driven architecture work and platform scalability"
        ],
        "B2B SaaS Product Manager": [
            "Emphasize stakeholder management and delivery discipline",
            "Highlight Fortune 100 client experience from 1872 Consulting",
            "Discuss roadmap ownership and sprint execution track record"
        ]
    }

    return suggestions.get(selected, ["Tailor talking points to JD keywords"])[0]


# Claude-based selection for higher accuracy (optional, uses API)
SELECTION_PROMPT = """You are a resume strategy expert. Analyze this job description and select the most strategically aligned resume variant for Austin Stretz.

AVAILABLE RESUME VARIANTS:
1. AI Product Manager - Emphasizes AI/ML product experience, computer vision, model evaluation, AI interpretability
2. Platform Product Manager - Emphasizes system integration, API strategy, cross-team coordination, technical platforms
3. B2B SaaS Product Manager - Emphasizes roadmap ownership, stakeholder management, delivery discipline, customer-facing PM work

JOB DESCRIPTION:
{job_description}

SELECTION ALGORITHM:

STEP 1: Identify Dominant Category Signals

A. AI/ML Dominant Signals (select AI Resume if these dominate):
- AI Product Manager, ML lifecycle, model evaluation
- Generative AI, LLMs, AI copilots, NLP
- Model monitoring, AI governance, computer vision
- Training data, model interpretability, ML platform
- AI-enabled products, model behavior, AI experimentation
- LLM orchestration, prompt engineering, AI feature development

B. Platform/Integration Dominant Signals (select Platform Resume if these dominate):
- Platform Product Manager, API integrations
- System integrations, data pipelines, cross-system workflows
- Orchestration, multi-product surfaces, platform scalability
- Infrastructure collaboration, backend-heavy
- Integration strategy, enterprise system architecture
- Cross-team coordination, systems thinking

C. Traditional B2B SaaS Dominant Signals (select SaaS Resume if these dominate):
- Roadmap ownership, feature delivery, backlog management
- Sprint execution, customer discovery, product requirements
- Stakeholder management, incremental releases, SaaS metrics
- Customer-facing PM, shipping, predictability, delivery discipline

STEP 2: Resolve Overlaps (Priority Rules)
1. If AI is core to product value → AI resume
2. If AI mentioned but not central → Platform or SaaS based on system complexity
3. If integrations are central but AI is peripheral → Platform
4. If JD is vague/general SaaS → B2B SaaS
5. If still unclear → Default to Platform (most balanced)

GUARDRAILS:
- Do NOT choose AI just because "AI" appears once
- Do NOT choose Platform just because "API" appears once
- Evaluate signal DENSITY, not just presence
- Prioritize responsibilities over tech stack mentions

OUTPUT FORMAT - Respond with valid JSON only:
{{
    "selected_resume": "AI Product Manager" | "Platform Product Manager" | "B2B SaaS Product Manager",
    "confidence": "Low" | "Medium" | "High",
    "reasoning": "2-3 sentence explanation of why this resume variant is the best strategic fit",
    "key_signals": ["signal1", "signal2", "signal3", "signal4", "signal5"],
    "suggested_emphasis": "One sentence suggesting what to emphasize in interview prep"
}}"""


def select_resume(job_description: str, use_api: bool = True) -> dict:
    """
    Select the best resume variant for the job description.

    Args:
        job_description: The full job description text
        use_api: If True, use Claude API for more accurate selection.
                 If False, use local keyword matching (faster, no API cost).

    Returns:
        Dictionary with selected_resume, confidence, reasoning, key_signals, suggested_emphasis
    """
    if not use_api:
        return select_resume_local(job_description)

    try:
        client = get_client()

        prompt = SELECTION_PROMPT.format(job_description=job_description)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response_text = message.content[0].text.strip()

        # Parse JSON response
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines[-1].strip() == '```':
                lines = lines[:-1]
            response_text = '\n'.join(lines)

        result = json.loads(response_text)

        # Validate the response
        if result.get("selected_resume") not in RESUME_VARIANTS:
            raise ValueError(f"Invalid resume selection: {result.get('selected_resume')}")

        return result

    except Exception as e:
        # Fallback to local selection if API fails
        print(f"API selection failed, using local: {e}")
        return select_resume_local(job_description)
