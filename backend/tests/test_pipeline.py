import pytest
from app.ingestion.normalizer import JobNormalizer
from app.ingestion.base import RawJob
from app.ingestion.validator import JobValidator
from datetime import datetime


def test_pipeline_normalize_then_validate():
    """Test normalizer output passes validator."""
    raw_job = RawJob(
        title="Python Developer",
        company="Acme Corp",
        location="NYC",
        description="Build APIs",
        url="https://example.com/1",
    )
    
    # Normalize
    normalized = JobNormalizer.normalize(raw_job, source_id=1, source_name="Test")
    
    # Validate
    is_valid, error = JobValidator.validate(normalized.dict())
    assert is_valid, f"Validation failed: {error}"


def test_pipeline_validates_missing_title():
    """Test pipeline rejects jobs with missing title."""
    raw_job = RawJob(
        title="",  # Empty title
        company="Acme Corp",
        location="NYC",
    )
    
    normalized = JobNormalizer.normalize(raw_job, source_id=1, source_name="Test")
    is_valid, error = JobValidator.validate(normalized.dict())
    
    assert not is_valid
    assert "title" in error.lower()


def test_pipeline_validates_missing_company():
    """Test pipeline rejects jobs with missing company."""
    raw_job = RawJob(
        title="Python Developer",
        company="",  # Empty company
        location="NYC",
    )
    
    normalized = JobNormalizer.normalize(raw_job, source_id=1, source_name="Test")
    is_valid, error = JobValidator.validate(normalized.dict())
    
    assert not is_valid
    assert "company" in error.lower()
