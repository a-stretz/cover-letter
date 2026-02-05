# Job Application Decision & Cover Letter Generator

A web application that analyzes job descriptions against Austin Stretz's professional profile, makes strategic application decisions, recommends the appropriate resume variant, and generates authentic, tailored cover letters.

## Features

- **Job Analysis**: Analyzes job descriptions using Claude AI to determine if Austin should apply
- **Decision Logic**: Auto-reject criteria, resume routing, and priority detection
- **Resume Recommendations**: Suggests Edge AI, AI PM, or Traditional PM resume variant
- **Cover Letter Generation**: Generates authentic, tailored cover letters in Austin's voice
- **File Export**: Saves cover letters as .docx files with proper formatting
- **Application Tracking**: SQLite database tracks all analyzed jobs

## Tech Stack

- **Backend**: Python with Flask
- **Database**: SQLite
- **Frontend**: HTML/CSS/JavaScript (single page app)
- **AI**: Anthropic Claude API (Sonnet 4.5)
- **File Generation**: python-docx

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

Copy `.env.example` to `.env` and add your Anthropic API key:

```bash
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=your-api-key-here
```

### 3. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Analyzing a Job

1. Paste the full job description into the text area
2. Optionally add context (company name, notes, personal connections)
3. Click "ANALYZE JOB"
4. Review the decision, resume recommendation, and analysis details

### Generating a Cover Letter

If the decision is "APPLY":

1. Optionally fill in customization fields:
   - Company News/Context (recent funding, product launches)
   - Personal Connection (referrals, mutual connections)
   - Specific Excitement (why you're drawn to this role)
2. Click "GENERATE COVER LETTER"
3. Review the preview
4. Click "SAVE TO FILE" to export as .docx

### Viewing History

Click the "History" tab to see all analyzed jobs with their decisions and statuses.

## Decision Logic

### Auto-Reject Criteria

- Onsite required outside KC metro area (>30 miles)
- Salary < $100k for FTE roles (Contract $40+/hr acceptable)
- Requires 10+ years experience explicitly
- Requires specific technical skills Austin doesn't have
- Not a PM/Product Owner/TPM role

### Resume Routing

- **Edge AI Resume**: 5+ keywords related to edge computing, computer vision, IoT, motion analysis
- **AI PM Resume**: 5+ keywords related to AI/ML products, LLMs, generative AI
- **Traditional PM Resume**: Standard PM keywords, lacks AI/edge focus

### Priority Triggers

- Kansas City metro location
- Sports tech, biomechanics, athletics industry
- Growth-stage startup (Series A-C)
- Strong experience alignment
- Compensation sweet spot ($120k-$140k)

## File Output

Cover letters are saved to:
- Windows: `C:\Users\astre\Desktop\Persy\The Hunt\Hunt Covers\`
- Other: `./output/` directory

Naming convention: `Austin Stretz - [Company Name] Cover Letter.docx`

## Project Structure

```
cover-letter/
├── app.py              # Flask application
├── database.py         # SQLite database operations
├── profile.py          # Austin's professional profile
├── analyzer.py         # Job description analyzer
├── cover_letter.py     # Cover letter generator
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Frontend UI
├── output/             # Fallback cover letter output
└── job_applications.db # SQLite database (auto-created)
```

## API Endpoints

- `POST /api/analyze` - Analyze a job description
- `POST /api/generate-cover-letter` - Generate cover letter for analyzed job
- `POST /api/save-cover-letter` - Save cover letter to .docx file
- `GET /api/history` - Get job analysis history
- `GET /api/job/<id>` - Get specific job details
- `PUT /api/job/<id>/status` - Update job application status
