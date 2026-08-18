import pytest
from app.ingestion.validator import JobValidator


def test_valid_job():
    """Test validation of a valid job."""
    job_data = {
        "title": "Python Developer",
        "company": "Acme Corp",
        "location": "New York",
        "url": "https://example.com/jobs/1",
    }
    
    is_valid, error = JobValidator.validate(job_data)
    assert is_valid is True
    assert error is None


def test_missing_title():
    """Test validation fails for missing title."""
    job_data = {
        "company": "Acme Corp",
        "location": "New York",
    }
    
    is_valid, error = JobValidator.validate(job_data)
    assert is_valid is False
    assert "title" in error.lower()


def test_missing_company():
    """Test validation fails for missing company."""
    job_data = {
        "title": "Python Developer",
        "location": "New York",
    }
    
    is_valid, error = JobValidator.validate(job_data)
    assert is_valid is False
    assert "company" in error.lower()


def test_invalid_url():
    """Test validation fails for invalid URL."""
    job_data = {
        "title": "Python Developer",
        "company": "Acme Corp",
        "url": "not-a-valid-url",
    }
    
    is_valid, error = JobValidator.validate(job_data)
    assert is_valid is False
    assert "url" in error.lower()
