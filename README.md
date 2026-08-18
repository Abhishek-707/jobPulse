# JobPulse — Resilient Job Intelligence Engine

A production-grade job ingestion and intelligence platform demonstrating multi-source data aggregation, resilience patterns, and professional engineering practices.

## Project Overview

JobPulse is a comprehensive job intelligence system that:

- **Aggregates** job listings from multiple sources (RSS feeds, public APIs, controlled browser extraction)
- **Normalizes** diverse data formats into a unified Job model
- **Deduplicates** jobs across sources using deterministic matching
- **Persists** structured data in PostgreSQL with proper indexing
- **Tracks** ingestion health and detects anomalies
- **Handles** failures gracefully with retry logic and exponential backoff
- **Enriches** jobs with optional AI analysis (skills, categories, summaries)
- **Exposes** a clean REST API for consumption
- **Displays** jobs in a professional Next.js dashboard

## Why This Project Matters

This project demonstrates:

✅ **Systems Architecture** — Source adapters, normalized data models, resilient pipelines  
✅ **Resilience Engineering** — Retries, timeouts, graceful degradation, health monitoring  
✅ **Data Engineering** — Parsing, validation, deduplication, persistence  
✅ **Backend Development** — FastAPI, Pydantic, SQLAlchemy, PostgreSQL  
✅ **Frontend Development** — Next.js dashboard with search and filtering  
✅ **Testing** — Unit, integration, and failure scenario tests  
✅ **DevOps** — Docker, containerization, environment management  
✅ **AI Integration** — Optional LLM-based enrichment (doesn't break system if unavailable)  
✅ **Ethical Engineering** — Clear boundaries on scraping, documented limitations  

## Architecture

```
┌─────────────┬──────────────┬──────────────┐
│   RSS       │  Public API  │   Browser    │
│ Feed        │  (e.g., Jobs)│  (Sandbox)   │
└──────┬──────┴──────┬───────┴──────┬───────┘
       │             │              │
       └─────────────┼──────────────┘
                     ↓
          Source Adapters Layer
          (Abstract fetching)
                     ↓
    ┌────────────────┼────────────────┐
    ↓                ↓                ↓
  Parser         Validator      Normalizer
                     ↓
              Deduplicator
              (content_hash)
                     ↓
            PostgreSQL Database
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
    FastAPI      Health Engine  AI Enrichment
    (REST API)   (Monitoring)   (Optional)
        ↓            ↓            ↓
        └────────────┼────────────┘
                     ↓
              Next.js Dashboard
```

## Technology Stack

### Backend
- **Python 3.12+** — Async-capable language
- **FastAPI** — Modern, fast web framework with automatic OpenAPI docs
- **Pydantic** — Data validation and serialization
- **SQLAlchemy 2.0** — ORM with async support
- **PostgreSQL** — Reliable relational database
- **Psycopg 3** — PostgreSQL driver with async support
- **HTTPX** — Async HTTP client

### Ingestion
- **Playwright** — Browser automation for controlled extraction
- **feedparser** — RSS/Atom feed parsing
- **BeautifulSoup 4** — HTML parsing and extraction

### Frontend
- **Next.js 14** — React meta-framework with SSR
- **TypeScript** — Type-safe JavaScript
- **Tailwind CSS** — Utility-first CSS framework
- **React Query** — Data fetching and caching

### Infrastructure
- **Docker** — Containerization
- **Docker Compose** — Local orchestration
- **Git** — Version control

### Testing
- **Pytest** — Python testing framework
- **FastAPI TestClient** — API testing
- **Playwright Test** — End-to-end testing (future)

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Node.js 18 or higher
- PostgreSQL 14 or higher
- Git
- Docker & Docker Compose (optional, for containerized setup)

### Step 1: Clone Repository

```bash
git clone https://github.com/Abhishek-707/jobPulse.git
cd jobPulse
```

### Step 2: Backend Setup

#### 2a. Create Virtual Environment

```bash
cd backend
python -m venv venv

# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### 2b. Install Dependencies

```bash
pip install -r requirements.txt
playwright install  # Install browser binaries
```

#### 2c. Configure Environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials:
# DATABASE_URL=postgresql://postgres:your_password@localhost:5432/jobpulse
```

#### 2d. Create Database

```bash
# Using psql:
psql -U postgres -c "CREATE DATABASE jobpulse;"

# Or using createdb:
createdb -U postgres jobpulse
```

#### 2e. Run Backend

```bash
python -m uvicorn app.main:app --reload
```

✅ Backend running at: http://localhost:8000  
✅ API docs at: http://localhost:8000/docs  
✅ ReDoc at: http://localhost:8000/redoc  

### Step 3: Frontend Setup (Optional, for Phase 14+)

```bash
cd ../frontend
npm install
npm run dev
```

✅ Frontend running at: http://localhost:3000

### Docker Setup (Alternative)

```bash
docker-compose up
```

This starts:
- PostgreSQL on port 5432
- FastAPI on port 8000

## Database Schema

### Tables

#### `sources`
Represents job sources (RSS, API, browser, sandbox).

```sql
id              SERIAL PRIMARY KEY
name            VARCHAR(255) UNIQUE
type            VARCHAR(50)  -- RSS, API, BROWSER, SANDBOX
base_url        VARCHAR(500)
status          VARCHAR(50)  -- HEALTHY, DEGRADED, FAILED, UNKNOWN
health_score    FLOAT        -- 0.0 to 1.0
last_success_at TIMESTAMP
last_failure_at TIMESTAMP
last_run_at     TIMESTAMP
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
```

#### `jobs`
Normalized job listings.

```sql
id              SERIAL PRIMARY KEY
source_id       INTEGER REFERENCES sources(id)
external_id     VARCHAR(500)  -- Source's unique ID
title           VARCHAR(255)
company         VARCHAR(255)
location        VARCHAR(255)
description     TEXT
url             VARCHAR(1000)
source_name     VARCHAR(100)
job_type        VARCHAR(100)  -- Full-time, Part-time, etc.
published_at    TIMESTAMP
collected_at    TIMESTAMP
content_hash    VARCHAR(64) UNIQUE  -- SHA256 for deduplication
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
```

#### `ingestion_runs`
Tracks each ingestion execution.

```sql
id              SERIAL PRIMARY KEY
source_id       INTEGER REFERENCES sources(id)
started_at      TIMESTAMP
finished_at     TIMESTAMP
status          VARCHAR(50)  -- SUCCESS, PARTIAL, FAILED
jobs_found      INTEGER DEFAULT 0
jobs_added      INTEGER DEFAULT 0
jobs_updated    INTEGER DEFAULT 0
jobs_duplicate  INTEGER DEFAULT 0
jobs_failed     INTEGER DEFAULT 0
error_count     INTEGER DEFAULT 0
duration_ms     INTEGER
created_at      TIMESTAMP DEFAULT NOW()
```

#### `ingestion_errors`
Stores ingestion failures.

```sql
id              SERIAL PRIMARY KEY
source_id       INTEGER REFERENCES sources(id)
run_id          INTEGER REFERENCES ingestion_runs(id)
error_type      VARCHAR(50)  -- TIMEOUT, HTTP_ERROR, PARSER_ERROR, etc.
message         VARCHAR(1000)
created_at      TIMESTAMP DEFAULT NOW()
```

#### `ai_enrichments`
AI-generated enrichments (optional).

```sql
id              SERIAL PRIMARY KEY
job_id          INTEGER UNIQUE REFERENCES jobs(id)
status          VARCHAR(50)  -- PENDING, COMPLETED, FAILED
category        VARCHAR(255)
skills          TEXT
experience_level VARCHAR(100)
summary         TEXT
seniority       VARCHAR(100)
technology_stack TEXT
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
```

## API Endpoints

### Health

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development"
}
```

### Jobs

```bash
# List all jobs (paginated)
GET /api/jobs?page=1&limit=20

# Get single job
GET /api/jobs/{id}

# Search jobs
GET /api/jobs/search?q=python&location=remote
```

### Sources

```bash
# List all sources
GET /api/sources

# Get source details
GET /api/sources/{id}

# Get source health
GET /api/sources/{id}/health
```

### Ingestion

```bash
# List ingestion runs
GET /api/ingestion/runs?source_id=1

# Trigger ingestion for a source
POST /api/ingestion/run
{"source_id": 1}
```

## Ingestion Pipeline

The standard ingestion flow for any source:

```
1. FETCH
   └─ Source adapter retrieves raw data
   └─ Handles timeouts and HTTP errors

2. PARSE
   └─ Convert to structured format
   └─ RSS → dict, API JSON → dict, HTML → dict

3. VALIDATE
   └─ Pydantic validates against schema
   └─ Rejects invalid records
   └─ Logs validation errors

4. NORMALIZE
   └─ Map source fields to canonical Job model
   └─ Example: job_title → title, employer → company

5. DEDUPLICATE
   └─ Generate content_hash (SHA256 of title + company + location)
   └─ Check against existing jobs
   └─ Skip duplicates, mark metrics

6. STORE
   └─ Insert or update in PostgreSQL
   └─ Record metrics: added, updated, duplicate

7. HEALTH UPDATE
   └─ Update source.health_score
   └─ Update source.last_run_at
   └─ Update source.status (HEALTHY, DEGRADED, FAILED)

8. OPTIONAL: AI ENRICHMENT
   └─ Send job description to LLM
   └─ Extract skills, category, summary
   └─ Store in ai_enrichments table
   └─ If AI fails, job remains fully functional
```

## Resilience Features

### Retry Logic

Transient failures automatically retry:

```
Attempt 1 → wait 1s → Attempt 2 → wait 2s → Attempt 3 → Fail
```

**Retryable errors:**
- HTTP 5xx (server error)
- Timeout
- Connection refused

**Non-retryable:**
- HTTP 4xx (client error)
- Empty response (flagged as DEGRADED instead)

### Timeout Handling

All requests have configurable timeouts (default 30s):

```python
httpx.get(url, timeout=30.0)
playwright.goto(url, timeout=30000)
```

Hanging requests won't block the entire pipeline.

### Empty Response Detection

If a source normally returns ~100 jobs but suddenly returns 0:

```python
if jobs_found == 0 and source.last_run_at is not None:
    # Mark source as DEGRADED, not SUCCESS
    source.status = SourceStatus.DEGRADED
    log error: "EMPTY_RESPONSE"
```

### Health Scoring

Each source gets a score (0.0–1.0) based on:

```python
health_score = (
    (successful_runs / total_runs) * 0.6 +      # 60% success rate
    (1 - error_rate) * 0.4                      # 40% low error rate
)
```

### Graceful Degradation

One failed source doesn't break the whole system:

```python
for source in sources:
    try:
        ingest(source)
    except Exception as e:
        log.error(f"Source {source.name} failed: {e}")
        update_source_status(source, FAILED)
        continue  # Try next source
```

### Error Logging

All failures are stored:

```sql
INSERT INTO ingestion_errors (source_id, run_id, error_type, message)
VALUES (1, 42, 'TIMEOUT', 'Request exceeded 30s limit')
```

## Deduplication Strategy

Jobs are deduplicated using a multi-level approach:

### Level 1: Exact Match (Fastest)

```python
# Check if external_id already exists
Job.query.filter_by(source_id=source_id, external_id=external_id).first()
```

### Level 2: Content Hash (Most Common)

```python
import hashlib

content = f"{job.title}|{job.company}|{job.location}"
content_hash = hashlib.sha256(content.encode()).hexdigest()

# Check if hash exists
Job.query.filter_by(content_hash=content_hash).first()
```

### Level 3: URL Match

```python
# If job has URL, check for duplicates by URL
Job.query.filter_by(url=job.url).first()
```

### Future: Semantic Matching

With more time, implement LLM-based similarity:

```python
# "Python Developer" vs "Python Dev" would match
# Uses sentence transformers or LLM embeddings
```

## AI Enrichment (Optional)

When enabled, the system enriches jobs with:

### Extracted Fields

- **Category**: Backend, Frontend, AI/ML, DevOps, etc.
- **Skills**: Python, FastAPI, PostgreSQL, Docker, etc.
- **Experience Level**: Junior (0-2y), Mid (2-5y), Senior (5+y)
- **Summary**: 2-3 sentence description of the role
- **Seniority**: Entry-level, Mid-level, Senior, Lead
- **Tech Stack**: Specific technologies mentioned

### Example

```json
{
  "job_id": 42,
  "status": "COMPLETED",
  "category": "Backend Development",
  "skills": "Python, FastAPI, PostgreSQL, Docker",
  "experience_level": "Mid",
  "summary": "Senior backend engineer to lead API development for...",
  "seniority": "Senior",
  "technology_stack": "Python, FastAPI, PostgreSQL, Redis"
}
```

### Failure Handling

If AI enrichment fails, the job remains fully functional:

```python
try:
    enrichment = ai_service.enrich(job)
    save_enrichment(enrichment)
except AIServiceError:
    log.warning(f"AI enrichment failed for job {job.id}")
    # Job is still available in search/display
```

## Testing

### Run All Tests

```bash
cd backend
pytest
```

### Run Specific Test Category

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Failure scenario tests
pytest tests/failure/
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html
```

### Test Categories

#### Unit Tests

- Normalization logic
- Validation rules
- Deduplication algorithm
- Health score calculation

#### Integration Tests

- Source adapter → Database
- Full ingestion pipeline
- Error handling
- Retry logic

#### Failure Tests

- Timeout handling
- HTTP 500 handling
- Empty response detection
- Malformed data handling
- HTML structure changes

#### API Tests

- GET /api/jobs
- GET /api/jobs/{id}
- GET /api/sources
- POST /api/ingestion/run

## Deployment

### Frontend Deployment

**Vercel** (recommended for Next.js):

1. Push to GitHub
2. Connect to Vercel at https://vercel.com
3. Automatic deployment on push to main

### Backend Deployment

**Options:**

- **Railway** — Easiest, good free tier
- **Render** — Similar to Railway
- **AWS** (Elastic Beanstalk, ECS, Lambda)
- **Google Cloud** (Cloud Run, App Engine)
- **DigitalOcean** (App Platform)

**Environment Variables:**

```bash
DATABASE_URL=postgresql://user:pass@host/dbname
AI_ENABLED=true
AI_API_KEY=sk-...
ENVIRONMENT=production
CORS_ORIGINS=["https://yourdomain.com"]
```

### Database Deployment

**Managed PostgreSQL:**

- **Railway PostgreSQL** — $5/month
- **Supabase** — 500MB free tier
- **AWS RDS** — $10-50/month
- **Railway** — $5/month
- **Render** — Free tier available

## Limitations & Future Improvements

### Current Limitations

1. **Sequential Ingestion** — Sources run one at a time, not in parallel
2. **In-Memory Deduplication Cache** — Could improve with Redis
3. **Basic AI** — No confidence scoring or validation
4. **Simple Search** — Keyword only, no full-text search
5. **No Notifications** — Users can't get alerts for new jobs
6. **No User Accounts** — Public read-only API

### Future Improvements

1. **Parallel Workers** — Process multiple sources concurrently
2. **Redis Caching** — Speed up duplicate detection
3. **Semantic Search** — LLM-based job similarity
4. **Full-Text Search** — PostgreSQL FTS or Elasticsearch
5. **User Accounts** — Save searches, bookmarks, preferences
6. **Job Alerts** — Email/webhook notifications
7. **Analytics** — Track hiring trends, salary ranges
8. **Advanced Filtering** — Salary, company size, tech stack
9. **Data Exports** — CSV, JSON downloads
10. **Microservices** — Separate ingestion, API, and AI services

## Ethical Scraping Boundary

### ✅ What We Do

- Consume public RSS feeds
- Use public APIs with proper authentication
- Extract from controlled sandboxes
- Respect rate limits and timeouts
- Use appropriate User-Agent headers
- Cache results to minimize requests
- Honor `robots.txt` and `sitemap.xml`
- Gracefully handle `429 Too Many Requests`

### ❌ What We Don't Do

- Bypass CAPTCHA
- Bypass authentication or access controls
- Defeat security protections
- Scrape private user information
- Cause excessive traffic (DDoS-like behavior)
- Ignore explicit access restrictions
- Misrepresent the scraper's identity
- Resell or redistribute restricted data

### Philosophy

If a source blocks automated access, the system gracefully handles the failure rather than attempting to defeat the protection.

## Environment Variables

See `.env.example` for template. Key variables:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/jobpulse

# Environment
ENVIRONMENT=development  # or production

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# API
API_TITLE=JobPulse API
API_VERSION=0.1.0

# Ingestion
INGESTION_TIMEOUT=30
INGESTION_MAX_RETRIES=3

# AI (optional)
AI_ENABLED=false
AI_API_KEY=
```

## Security Considerations

### Never Commit

- `.env` files with real credentials
- API keys
- Database passwords
- Private tokens

### Always Use

- Environment variables for secrets
- `.env.example` with placeholders
- HTTPS in production
- Database user with limited permissions
- Firewall rules (only allow necessary ports)
- Secret rotation (API keys, passwords)

### API Security

- CORS properly configured
- Input validation on all endpoints
- Rate limiting (future)
- API key authentication (future)
- Request signing (future)

## Development Workflow

### Creating a Feature

1. Create feature branch
   ```bash
   git checkout -b feat/my-feature
   ```

2. Make changes and test
   ```bash
   pytest tests/
   ```

3. Commit with clear message
   ```bash
   git commit -m "feat: add feature X"
   ```

4. Push and create pull request
   ```bash
   git push origin feat/my-feature
   ```

### Commit Message Format

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
refactor: refactor code
chore: dependency updates
```

## Documentation

- **README.md** — This file
- **DECISIONS.md** — Architecture decisions and trade-offs
- **API Docs** — http://localhost:8000/docs (Swagger UI)
- **ReDoc** — http://localhost:8000/redoc
- **Source Code** — Well-commented for clarity

## Contact & Support

Built as part of **AcdyOn Technologies** hiring assessment.

For questions or issues:

1. Check the documentation
2. Review similar issues on GitHub
3. Open a new GitHub issue with details
4. Include error logs and reproduction steps

## License

MIT License — See LICENSE file (if present)

---

**Made with ❤️ for AcdyOn Technologies**
