# Development Guide

## Running Tests

```bash
cd backend
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_*.py    # Run specific tests
pytest --cov=app          # With coverage
```

## Running Management Commands

```bash
cd backend

# Seed database with sources
python -m app.management seed_sources

# List all sources
python -m app.management list_sources

# Run ingestion for all sources
python -m app.management run_ingestion

# Run ingestion for specific source
python -m app.management run_ingestion 1

# List recent jobs
python -m app.management list_jobs 20
```

## Running the Sandbox

```bash
cd sandbox
pip install -r requirements.txt
python app.py
```

Then open: http://localhost:5000

## Full Local Setup

### Terminal 1: PostgreSQL
```bash
brew services start postgresql
```

### Terminal 2: Sandbox
```bash
cd sandbox
pip install -r requirements.txt
python app.py
```

### Terminal 3: Backend
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

### Terminal 4: Run Ingestion
```bash
cd backend
source venv/bin/activate
python -m app.management seed_sources
python -m app.management run_ingestion
```

## API Documentation

Once backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Debugging

### Check database
```bash
psql -U abhishekgiri -d jobpulse
\dt  # List tables
SELECT * FROM sources;
SELECT * FROM jobs LIMIT 5;
```

### View logs

Backend logs appear in the terminal where uvicorn is running.

### Test specific adapter

```python
# In Python shell
from app.ingestion.rss_adapter import RSSAdapter
import asyncio

adapter = RSSAdapter(1, "Test", "https://github.com/jobs.atom")
jobs = asyncio.run(adapter.fetch())
print(f"Fetched {len(jobs)} jobs")
```

## Common Issues

### "connection to server failed"
- Ensure PostgreSQL is running: `brew services start postgresql`

### "psycopg.OperationalError"
- Check DATABASE_URL in .env file
- Verify database exists: `psql -U abhishekgiri -l | grep jobpulse`

### "ModuleNotFoundError"
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

### Sandbox not accessible
- Ensure sandbox is running on port 5000
- Check: `curl http://localhost:5000/health`

## Next Steps

1. Run `python -m app.management seed_sources`
2. Start sandbox: `cd sandbox && python app.py`
3. Run ingestion: `python -m app.management run_ingestion 3`
4. Check jobs: `python -m app.management list_jobs 10`
5. View API: http://localhost:8000/docs
