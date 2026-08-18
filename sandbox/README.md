# JobPulse Sandbox

A controlled job listing website for testing JobPulse ingestion.

## Quick Start

```bash
cd sandbox
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open: http://localhost:5000

## API Endpoints

- `GET /` - HTML job listings page
- `GET /api/jobs` - JSON API with all jobs
- `GET /api/jobs/<job_id>` - Single job
- `GET /health` - Health check

## Purpose

This sandbox provides:
- ✅ Predictable test data
- ✅ Controlled environment (no external dependencies)
- ✅ Easy to modify job data
- ✅ Failure simulation capability (future)
- ✅ No ethical concerns (owns its own data)

## Mock Data

Five sample jobs with:
- Title, Company, Location
- Description, URL, Job Type
- Published date

Easy to extend with more jobs in `app.py`.
