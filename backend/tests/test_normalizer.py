import pytest
from app.ingestion.normalizer import JobNormalizer
from app.ingestion.base import RawJob
from datetime import datetime


def test_normalize_basic_job():
    """Test basic job normalization."""
    raw_job = RawJob(
        title="Python Developer",
        company="Acme Corp",
        location="New York",
        description="Build APIs",
        url="https://example.com/jobs/1",
    )
    
    normalized = JobNormalizer.normalize(raw_job, source_id=1, source_name="TestSource")
    
    assert normalized.title == "Python Developer"
    assert normalized.company == "Acme Corp"
    assert normalized.location == "New York"
    assert normalized.source_id == 1
    assert normalized.source_name == "TestSource"


def test_generate_hash():
    """Test content hash generation."""
    hash1 = JobNormalizer.generate_hash("Python Dev", "Acme", "NYC")
    hash2 = JobNormalizer.generate_hash("python dev", "acme", "nyc")  # Different case
    
    # Should be the same (case-insensitive)
    assert hash1 == hash2
    
    # Different content should produce different hash
    hash3 = JobNormalizer.generate_hash("Java Dev", "Acme", "NYC")
    assert hash1 != hash3
