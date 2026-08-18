from typing import List, Optional
from app.models import Job
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class JobValidator:
    """Validates job data before storage."""
    
    REQUIRED_FIELDS = ['title', 'company']
    
    @staticmethod
    def validate(job_data: dict) -> tuple[bool, Optional[str]]:
        """Validate job data. Returns (is_valid, error_message)."""
        
        # Check required fields
        for field in JobValidator.REQUIRED_FIELDS:
            if not job_data.get(field) or not str(job_data.get(field)).strip():
                return False, f"Missing required field: {field}"
        
        # Check title length
        if len(job_data.get('title', '')) > 255:
            return False, "Title too long (max 255 characters)"
        
        # Check company length
        if len(job_data.get('company', '')) > 255:
            return False, "Company name too long (max 255 characters)"
        
        # Check URL format if present
        url = job_data.get('url')
        if url and not (url.startswith('http://') or url.startswith('https://')):
            return False, "Invalid URL format"
        
        return True, None
