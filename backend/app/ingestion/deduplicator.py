from typing import List
from app.models import Job
from app.ingestion.normalizer import JobNormalizer
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class JobDeduplicator:
    """Detects and handles duplicate jobs across sources."""
    
    @staticmethod
    def is_duplicate(db: Session, content_hash: str) -> bool:
        """Check if job with this content hash already exists."""
        existing = db.query(Job).filter_by(content_hash=content_hash).first()
        return existing is not None
    
    @staticmethod
    def find_by_url(db: Session, url: str) -> bool:
        """Check if job with this URL already exists."""
        if not url:
            return False
        existing = db.query(Job).filter_by(url=url).first()
        return existing is not None
    
    @staticmethod
    def find_by_external_id(db: Session, source_id: int, external_id: str) -> bool:
        """Check if job with this external ID exists for this source."""
        if not external_id:
            return False
        existing = db.query(Job).filter_by(
            source_id=source_id,
            external_id=external_id
        ).first()
        return existing is not None
