"""
Scout Company Registry — target companies for automated job discovery.

Tiers:
  1 — Dream targets (sports tech / AI / CV product)
  2 — Strong fits  (AI product / ML infra / video AI)
  3 — Opportunistic (large tech with relevant PM surface)

Each entry:
  name                  display name
  tier                  1 | 2 | 3
  greenhouse_board_token  slug for Greenhouse boards API (or None)
  lever_company           slug for Lever postings API (or None)
  exa_query               fallback Exa web search query
  notes                   brief fit rationale
"""

COMPANIES: list[dict] = [
    # ── Tier 1: Dream targets ──────────────────────────────────────────────
    {
        "name": "Catapult Sports",
        "tier": 1,
        "greenhouse_board_token": "catapultsports",
        "lever_company": None,
        "exa_query": "Catapult Sports product manager jobs site:catapult.com OR site:greenhouse.io",
        "notes": "Elite sports performance analytics; CV + wearables + AI coaching pipeline",
    },
    {
        "name": "Hudl",
        "tier": 1,
        "greenhouse_board_token": "hudl",
        "lever_company": None,
        "exa_query": "Hudl product manager AI video jobs site:hudl.com OR site:greenhouse.io",
        "notes": "Video analytics for sports teams; massive PM + AI video surface",
    },
    {
        "name": "Stats Perform",
        "tier": 1,
        "greenhouse_board_token": None,
        "lever_company": "statsperform",
        "exa_query": "Stats Perform product manager AI ML jobs site:statsperform.com OR site:lever.co",
        "notes": "Sports AI/ML data + predictive analytics; strong CV/AI PM alignment",
    },
    {
        "name": "Tempus AI",
        "tier": 1,
        "greenhouse_board_token": "tempus",
        "lever_company": None,
        "exa_query": "Tempus AI product manager jobs site:tempus.com OR site:greenhouse.io",
        "notes": "AI-driven clinical intelligence; translating complex ML output into product — mirrors NeoSavant work",
    },
    # ── Tier 2: Strong fits ────────────────────────────────────────────────
    {
        "name": "Twelve Labs",
        "tier": 2,
        "greenhouse_board_token": "twelvelabs",
        "lever_company": None,
        "exa_query": "Twelve Labs product manager jobs site:twelvelabs.io OR site:greenhouse.io",
        "notes": "Video understanding AI; PM for video search/retrieval product closely mirrors CV pipeline work",
    },
    {
        "name": "Runway",
        "tier": 2,
        "greenhouse_board_token": None,
        "lever_company": "runway",
        "exa_query": "Runway ML product manager jobs site:runwayml.com OR site:lever.co",
        "notes": "Generative AI video; AI PM with media/video domain knowledge",
    },
    {
        "name": "Scale AI",
        "tier": 2,
        "greenhouse_board_token": "scaleai",
        "lever_company": None,
        "exa_query": "Scale AI product manager annotation ML jobs site:scale.com OR site:greenhouse.io",
        "notes": "AI data platform; annotation pipeline + ML validation expertise is a direct match",
    },
    {
        "name": "Sievert Larsen & Associates",
        "tier": 2,
        "greenhouse_board_token": None,
        "lever_company": None,
        "exa_query": "technical product manager AI Kansas City remote jobs site:linkedin.com OR site:indeed.com",
        "notes": "Placeholder — replace with local KC AI company target",
    },
    # ── Tier 3: Opportunistic ──────────────────────────────────────────────
    {
        "name": "Google DeepMind",
        "tier": 3,
        "greenhouse_board_token": None,
        "lever_company": None,
        "exa_query": "Google DeepMind technical product manager computer vision remote jobs",
        "notes": "Large surface; targeting CV/AI PM roles specifically — low conversion but high value if landed",
    },
    {
        "name": "Meta Reality Labs",
        "tier": 3,
        "greenhouse_board_token": None,
        "lever_company": None,
        "exa_query": "Meta Reality Labs product manager computer vision pose estimation jobs",
        "notes": "Pose estimation + CV alignment with wearable/AR hardware surface",
    },
]


def get_companies(tier: int | None = None) -> list[dict]:
    """Return companies, optionally filtered by tier."""
    if tier is None:
        return COMPANIES
    return [c for c in COMPANIES if c["tier"] == tier]


def get_company(name: str) -> dict | None:
    """Return a company by exact name, or None."""
    for c in COMPANIES:
        if c["name"].lower() == name.lower():
            return c
    return None
