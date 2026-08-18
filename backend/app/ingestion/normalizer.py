from typing import List
from datetime import datetime
import hashlib
from app.models import Job
from app.schemas import JobCreate
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class JobNormalizer:
    """Converts raw job data to normalized Job model."""
    
    @staticmethod
    def normalize(raw_job, source_id: int, source_name: str) -> JobCreate:
        """Normalize raw job to canonical Job schema."""
        
        # Generate content hash for deduplication
        content_hash = JobNormalizer.generate_hash(
            title=raw_job.title,
            company=raw_job.company,
            location=raw_job.location or "",
        )
        
        normalized = JobCreate(
            title=raw_job.title.strip(),
            company=raw_job.company.strip(),
            location=raw_job.location.strip() if raw_job.location else None,
            description=raw_job.description.strip() if raw_job.description else None,
            url=raw_job.url,
            source_id=source_id,
            source_name=source_name,
            external_id=raw_job.external_id,
            job_type=raw_job.job_type,
            published_at=raw_job.published_at or datetime.utcnow(),
            content_hash=content_hash,
        )
        
        return normalized
    
    @staticmethod
    def generate_hash(title: str, company: str, location: str = "") -> str:
        """Generate SHA256 hash for deduplication."""
        content = f"{title.lower().strip()}|{company.lower().strip()}|{location.lower().strip()}"
        return hashlib.sha256(content.encode()).hexdigest()
