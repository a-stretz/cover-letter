"""
Austin Stretz's Professional Profile
Comprehensive data for job analysis and cover letter generation
"""

PROFILE = {
    "contact": {
        "name": "Austin Stretz",
        "email": "a.stretz@outlook.com",
        "personal_email": "austin@neosavant.ai",
        "phone": "913-515-8304",
        "location": "Kansas City, MO"
    },

    "identity": {
        "title": "Technical Product Architect",
        "specialization": "AI-driven biomechanics and computer vision systems",
        "one_liner": "Technical Product Architect who specializes in building AI-driven biomechanics systems, translating complex CV/ML outputs into reliable metrics, heuristics, real-time feedback, and scalable product workflows.",
        "hybrid_skills": [
            "product management",
            "computer vision geometry",
            "biomechanical reasoning",
            "forensic QA",
            "real-time system design",
            "AI interpretability frameworks"
        ]
    },

    "experience": {
        "current": {
            "title": "AI Product Manager",
            "company": "NeoSavant.ai",
            "dates": "Nov 2023 – Present",
            "description": "Edge-AI Computer Vision platform for real-time sports performance analysis",
            "products": {
                "SmartPlayer": {
                    "description": "2D/3D Performance Review System",
                    "details": [
                        "Core video playback and analysis interface for mobile users",
                        "Converts high-volume computer vision outputs into interpretable, actionable insights",
                        "Architected information hierarchy: Shot → Frame → Metric → Heuristic → Semantic Summary → Cue",
                        "Defined UX for 2D/3D toggle, skeleton overlays, phase navigation, metric displays",
                        "Built frame-to-metric synchronization logic, error-state UX, projection-plane interpretation"
                    ],
                    "impact": "Transformed research prototype into usable product, enabled coaches/athletes to understand AI"
                },
                "VoiceAssist": {
                    "description": "Real-Time AI Coaching Feedback Engine",
                    "details": [
                        "Invented RVSE system (Result, Verbosity, Specificity, Encouragement) - configurable AI coaching personality",
                        "Designed linguistic constraints (6-14 words, commander-style tone, action-first verbs)",
                        "Built cue architecture with 6,000+ possible permutations",
                        "Created timing/cadence logic, phase-based cue mapping, multi-shot adaptation"
                    ],
                    "impact": "Top platform differentiator, bridges biomechanics → athlete understanding"
                },
                "HeuristicSystemV4": {
                    "description": "Biomechanical Intelligence Engine",
                    "details": [
                        "Rebuilt entire measurement system from scratch after discovering fundamental geometry errors",
                        "Corrected projection planes, vector directionality, kinematic chain alignment",
                        "Reconstructed metrics from raw 3D coordinates by decoding protobuf files",
                        "Built multi-source validation framework comparing CV95, CB95, Kinovea, manual annotations",
                        "Achieved >90% accuracy for upper body metrics (validated against 1,164 frames)"
                    ],
                    "impact": "Created semantic architecture powering SmartPlayer and Voice Assist"
                },
                "OnsiteCapture": {
                    "description": "Operations Platform",
                    "details": [
                        "Defined system requirements for flagship multi-camera capture platform",
                        "Designed operator workflows, UX wireframes, calibration flows",
                        "Built configuration logic for high-volume environments (camps, tryouts, leagues)",
                        "Created SOPs for multi-Jetson rig setup, camera alignment, network bridging"
                    ],
                    "impact": "Made hardware/software pipeline operationally viable for events"
                }
            },
            "technical_contributions": [
                "Protocol Buffer decoding and coordinate extraction (390K frames, 38.6M data points processed)",
                "3D geometry analysis: projection planes, vector math, angle reconstruction",
                "Jitter & stability analysis: quantified measurement precision (±4-6° typical)",
                "Keypoint occlusion handling, reference frame transformations (AttemptFrame, SkeletalFrame)",
                "Batch processing workflows, forensic QA pipelines",
                "Built 1.4M+ image annotation pipeline aligned with ML team priorities"
            ],
            "data_analysis": [
                "Multi-source metric validation: manual clinical annotations (Kinovea), automated CV detection, protobuf outputs",
                "Root cause investigations identifying projection drift, coordinate system bugs",
                "Created comprehensive QA methodology: 20-shot test sessions, cue quality frameworks, system behavior diagnosis"
            ],
            "product_leadership": [
                "Authored PRDs, user stories, product vision documents, market/competitive analyses",
                "Led Alpha Program: structured SME interviews converting coaching knowledge → measurable metrics",
                "Built Beta Testing Program: segment-based cohorts, perception-based accuracy evaluation",
                "Conducted field research, on-site operations, user interviews",
                "Managed external vendors (data science, ML, 3D, dev, annotation, UX)"
            ]
        },
        "previous": {
            "title": "Product Lead / Sales Operations / Co-Founder",
            "company": "1872 Consulting, LLC",
            "dates": "Jun 2015 – Dec 2024",
            "highlights": [
                "Led modernization of enterprise HRIS platform (B2B SaaS): legacy AS400 → API-driven system",
                "Designed multi-tenant compliance systems for Fortune 100 clients",
                "Built API-driven integrations and automation workflows across enterprise platforms",
                "Drove 126% revenue growth, closed $1.1M Fortune 100 contract",
                "Product strategy for scalable SaaS platform serving recruitment industry",
                "Defined product vision, user flows, MVP strategy for HRIS compliance platforms",
                "Built Account Manager training program, KPIs, HubSpot dashboards"
            ]
        }
    },

    "skills": {
        "ai_ml_cv": [
            "Computer vision pipelines (MediaPipe BlazePose, OpenCV)",
            "3D pose estimation, keypoint detection",
            "Model output interpretation, metric validation",
            "Protocol Buffer parsing and data extraction",
            "Jitter analysis, stability quantification",
            "Projection-plane geometry, coordinate transformations"
        ],
        "programming_data": [
            "Python (primary language)",
            "Data analysis: CSV processing, batch workflows",
            "Video processing, frame extraction",
            "Multi-source data validation",
            "Forensic debugging methodologies"
        ],
        "product_ux": [
            "Product strategy, roadmapping, backlog management",
            "PRD authoring, user story creation",
            "UX flows, journey mapping, experience design",
            "Information architecture for complex systems",
            "Real-time interaction design",
            "Operator/field workflow design"
        ],
        "biomechanics": [
            "Joint angle measurement, kinematic analysis",
            "Movement phase segmentation (Prep, Load, Drive, Release, Follow-through)",
            "Stability requirements, directional correctness",
            "Cross-sport movement generalization",
            "Heuristic architecture for performance interpretation"
        ]
    },

    "domains": [
        "Sports Technology: Basketball shooting analysis, motion capture, performance analytics",
        "AI Product Development: 0→1 product creation, AI interpretability, prompt engineering",
        "Biomechanics: Movement semantics, coaching feedback systems, metric design",
        "Edge AI: Real-time processing, on-device inference, multi-camera systems",
        "Computer Vision: 3D reconstruction, pose estimation, video analytics",
        "B2B SaaS: Enterprise product management, platform development, scalable systems",
        "Product Platforms: Multi-tenant architecture, API-driven products, integration workflows"
    ],

    "certifications": [
        {"name": "Advanced Certified Scrum Product Owner (A-CSPO)", "org": "Scrum Alliance", "date": "Jun 2025"},
        {"name": "AI Product Manager Certification", "org": "IBM", "date": "Mar 2025"},
        {"name": "Certified Scrum Product Owner (CSPO)", "org": "Scrum Alliance", "date": "Dec 2024"}
    ],

    "achievements": [
        "Processed 300+ video sessions (390,000 frames, 38.6M data points)",
        "Built system achieving >90% correlation with manual clinical measurements",
        "Created 1.4M+ image annotation pipeline",
        "Designed Voice Assist with 6,000+ cue permutations",
        "Led Beta program with structured testing cohorts across coach/trainer segments",
        "Documented comprehensive heuristic system (v4) used across entire platform"
    ],

    "compensation": {
        "min": 100000,
        "max": 160000,
        "target": 130000,
        "contract_min_hourly": 40
    },

    "location_preferences": {
        "preferred": "Remote",
        "acceptable": [
            "Kansas City, MO",
            "Kansas City, KS",
            "Overland Park",
            "Shawnee",
            "Lenexa",
            "Olathe",
            "Independence",
            "Blue Springs",
            "Belton",
            "Liberty",
            "De Soto"
        ],
        "max_distance_miles": 30,
        "reject_onsite_outside_kc": True
    },

    "target_roles": [
        "AI/ML Product Manager",
        "Technical Product Manager",
        "Product Owner (AI/ML focus)",
        "Senior Product Manager (growth-stage startups preferred)",
        "Platform Product Manager",
        "B2B SaaS Product Manager",
        "Enterprise Product Manager",
        "Integration/API Product Manager"
    ]
}


# Decision logic constants
REJECT_CRITERIA = """
Auto-Reject if ANY of these are true:
1. Location: Onsite required AND not in KC metro area (>30 miles from Kansas City)
   KC Metro includes: Kansas City MO/KS, Overland Park, Shawnee, Lenexa, Olathe, Independence, Blue Springs, Belton, Liberty, De Soto
2. Compensation: ONLY reject if the MAXIMUM of the stated salary range < $100k
   CRITICAL: If a range like "$85k-$120k" is posted, this is IN RANGE because max ($120k) >= $100k
   Examples:
   - $85k-$120k → IN RANGE (max is $120k) - DO NOT REJECT
   - $90k-$95k → BELOW RANGE (max is $95k) - REJECT
   - $100k-$130k → IN RANGE - DO NOT REJECT
   - Salary not listed → DO NOT REJECT (Unknown)
   Contract: $40+/hr is acceptable
3. Experience: Explicitly requires "10+ years" experience
4. Technical Requirements: Requires specific technical skills Austin doesn't have
   Examples: Hardware engineering, deep ML research, specific unfamiliar frameworks
   NOT a rejection: Python (has it), ML concepts (knows them), CV (expert)
5. Role Mismatch: Not a PM/Product Owner/TPM role (e.g., pure marketing, sales, engineering IC roles)
"""

RESUME_ROUTING = """
EDGE AI RESUME if (5+ keyword matches):
- Keywords: "edge AI", "edge computing", "computer vision", "machine vision", "IoT", "embedded ML", "TensorFlow Lite", "on-device", "real-time processing", "video analytics", "motion analysis", "pose estimation"
- Domain: Manufacturing, robotics, automotive, sports tech with CV focus

AI PM RESUME if (5+ keyword matches):
- Keywords: "AI product", "ML", "machine learning", "LLM", "generative AI", "agentic", "NLP", "model", "prompt engineering", "AI strategy", "responsible AI"
- Domain: AI platforms, LLM applications, AI tooling
- NOT edge-focused

TRADITIONAL PM RESUME if:
- Keywords: "roadmap", "backlog", "PRD", "user stories", "sprint", "stakeholder", "KPI", "product strategy", "agile", "scrum"
- Lacks significant AI/edge keywords (< 5 mentions)
- Traditional SaaS, B2B, enterprise software
- Also good for: Platform PM, API products, integration-heavy products, workflow automation

DEFAULT: Traditional PM if unclear
"""

PRIORITY_TRIGGERS = """
Mark as PRIORITY (recommend extra touches) if ANY of these apply:
1. Location: Kansas City metro (local advantage)
2. Industry: Sports tech, biomechanics, athletics, performance analysis, motion capture
3. Company: Growth-stage startup, Series A-C
4. Strong Experience Alignment:
   - Matches Austin's specific expertise (computer vision, biomechanics, sports)
   - Tech stack overlap (Python, OpenCV, video analytics, ML)
   - Product type match (AI coaching, analysis platforms, real-time systems)
5. Compensation: Sweet spot $120k-$140k
6. Keywords: "basketball", "sports", "biomechanics", "motion", "coaching", "performance"
7. Remote with reasonable requirements
8. B2B SaaS / Enterprise Products:
   - Enterprise SaaS platforms
   - API-driven products
   - Multi-tenant systems
   - Integration-heavy products
   - Workflow automation platforms
   - Platform PM roles

Extra Touches to Recommend for Priority:
- Craft detailed, highly personalized cover letter
- LinkedIn outreach to hiring manager
- Portfolio artifact suggestion: Claude Hoops Metrics case study
- Talking points for interview prep
- Personal passion angle (if sports-related)
"""


# Sample cover letters for voice learning
SAMPLE_COVER_LETTERS = {
    "BOLD": """This role reflects a mature view of what AI product leadership requires right now — not just building features, but building trust. In a space crowded by noise and overselling, BOLD's commitment to measurement-first evaluation and transparent performance standards is exactly the kind of platform I want to help shape.

My experience has focused on building AI-driven systems that don't just produce outputs — they produce trustworthy, interpretable, and actionable outputs. At NeoSavant, I've led product development for an edge-AI platform that delivers real-time biomechanical feedback using computer vision. That's required me to define the metrics themselves, build multi-source validation frameworks, and architect user-facing systems that surface AI-generated feedback at the right moment, in the right form.

Core to that work has been ensuring that the outputs we surface actually mean something — both technically and perceptually. I've designed QA pipelines to diagnose measurement drift and built prompt-driven coaching cue systems that translate raw pose estimation into language athletes and coaches can use. I'm comfortable operating at the intersection of ML capabilities, UX constraints, and the messy realities of production systems.

I'm drawn to BOLD because the work here matters — helping organizations move past hype cycles and toward responsible, evidence-backed AI adoption. That mirrors how I've built products: start with what's true, surface what's useful, and earn trust through iteration. I would welcome the opportunity to bring that approach to your team.""",

    "Conviva": """This role resonates with me because it's tackling one of the messiest parts of agentic AI — not just what the agent can do, but how we understand and improve what it actually did. Observability for autonomous systems isn't solved; it requires someone comfortable operating in ambiguity, learning from real usage, and building toward clarity.

My recent work has been building AI products that operate in messy, real-world conditions — edge-AI systems for real-time sports performance analysis. That's meant designing metrics and heuristics that extract meaning from high-volume CV outputs, creating QA pipelines that catch drift before users see it, and architecting how raw model outputs translate into feedback a user can act on. I've led 0→1 product work that's required tight iteration loops with athletes, coaches, and ML engineers to figure out what signals actually matter.

I'm drawn to Conviva because agent analytics represents a category-shaping opportunity — the kind of problem where the product needs to define what "good" even looks like. I care about the craft of building interpretable, trustworthy AI systems, and this role sits at the center of how that gets done at scale. I would welcome the opportunity to help shape that product direction.""",

    "Hudl": """This is a dream role. I've spent the last two years building AI-driven performance analysis tools for basketball shooting — designing systems that translate computer vision outputs into real-time feedback coaches and athletes actually use. This role would let me bring that same approach to football, a sport I've followed closely since I was a kid and still watch obsessively every Sunday.

My current work at NeoSavant has focused on turning raw pose estimation data into trustworthy, interpretable insights. That's meant architecting the metric and heuristic layer that powers our product, building multi-source validation workflows to ensure measurement accuracy, and designing real-time feedback systems that deliver the right cue at the right moment. I've led Alpha and Beta testing programs with coaches and trainers, learning how to translate technical outputs into user trust.

I care deeply about sports technology — not just as a product category, but as a way to help athletes improve. I love talking to coaches, sitting in on film sessions, and figuring out what feedback actually changes behavior on the field. This role combines my technical background in AI-driven performance analysis with a sport and user base I genuinely care about. I would welcome the opportunity to bring that passion — and that product skillset — to Hudl."""
}


def get_profile_summary():
    """Return a formatted summary of the profile for prompts"""
    return f"""
Name: {PROFILE['contact']['name']}
Location: {PROFILE['contact']['location']}
Email: {PROFILE['contact']['email']}
Phone: {PROFILE['contact']['phone']}

PROFESSIONAL IDENTITY:
{PROFILE['identity']['one_liner']}

CURRENT ROLE:
{PROFILE['experience']['current']['title']} at {PROFILE['experience']['current']['company']} ({PROFILE['experience']['current']['dates']})
{PROFILE['experience']['current']['description']}

KEY PRODUCTS BUILT:
1. SmartPlayer - 2D/3D Performance Review System
   - Transformed research prototype into usable product for coaches/athletes
   - Architected information hierarchy: Shot → Frame → Metric → Heuristic → Semantic Summary → Cue

2. Voice Assist - Real-Time AI Coaching Feedback Engine
   - Invented RVSE system for configurable AI coaching personality
   - Built cue architecture with 6,000+ possible permutations
   - Top platform differentiator

3. Heuristic System v4 - Biomechanical Intelligence Engine
   - Rebuilt measurement system, achieved >90% accuracy vs manual clinical measurements
   - Multi-source validation: CV95, CB95, Kinovea, manual annotations

4. Onsite Capture - Operations Platform
   - Multi-camera capture platform for high-volume environments

PREVIOUS ROLE:
Product Lead / Co-Founder at 1872 Consulting, LLC (Jun 2015 – Dec 2024)
- Led modernization of enterprise HRIS platform (B2B SaaS): legacy AS400 → API-driven system
- Designed multi-tenant compliance systems for Fortune 100 clients
- Built API-driven integrations and automation workflows across enterprise platforms
- Product strategy for scalable SaaS platform serving recruitment industry
- Drove 126% revenue growth, closed $1.1M Fortune 100 contract

DOMAIN EXPERTISE:
- Sports Technology: Basketball shooting analysis, motion capture, performance analytics
- AI Product Development: 0→1 product creation, AI interpretability, prompt engineering
- B2B SaaS: Enterprise product management, platform development, scalable systems
- Product Platforms: Multi-tenant architecture, API-driven products, integration workflows
- Edge AI: Real-time processing, on-device inference, multi-camera systems
- Computer Vision: 3D reconstruction, pose estimation, video analytics

TECHNICAL EXPERTISE:
- Computer vision: MediaPipe BlazePose, OpenCV, pose estimation
- 3D geometry: projection planes, vector math, coordinate transformations
- Protocol Buffer parsing, data extraction (390K frames, 38.6M data points)
- Python, batch processing, forensic QA pipelines

CERTIFICATIONS:
- Advanced Certified Scrum Product Owner (A-CSPO) - Scrum Alliance
- AI Product Manager Certification - IBM
- Certified Scrum Product Owner (CSPO) - Scrum Alliance

KEY ACHIEVEMENTS:
- Processed 300+ video sessions (390,000 frames, 38.6M data points)
- Built system achieving >90% correlation with manual clinical measurements
- Created 1.4M+ image annotation pipeline
- Designed Voice Assist with 6,000+ cue permutations

COMPENSATION EXPECTATIONS:
- W2 Full-Time: $100,000 - $160,000 (target: $130,000)
- Contract: Minimum $40/hr

LOCATION PREFERENCES:
- Remote (preferred)
- Kansas City Metro Area acceptable for hybrid/onsite
- Reject: Onsite required outside KC metro area
"""
