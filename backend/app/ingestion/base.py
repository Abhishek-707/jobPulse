from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class RawJob(BaseModel):
    """Raw job data before normalization."""
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    job_type: Optional[str] = None
    published_at: Optional[datetime] = None
    external_id: Optional[str] = None


class JobSource(ABC):
    """Base class for all job sources."""
    
    def __init__(self, source_id: int, source_name: str):
        self.source_id = source_id
        self.source_name = source_name
    
    @abstractmethod
    async def fetch(self) -> List[RawJob]:
        """Fetch raw jobs from source. Must be implemented by subclasses."""
        pass


class SourceAdapter:
    """Factory for creating source adapters."""
    
    @staticmethod
    def get_adapter(source_type: str, source_id: int, source_name: str, base_url: Optional[str] = None) -> JobSource:
        """Get appropriate adapter for source type."""
        if source_type == "RSS":
            from .rss_adapter import RSSAdapter
            return RSSAdapter(source_id, source_name, base_url)
        elif source_type == "API":
            from .api_adapter import APIAdapter
            return APIAdapter(source_id, source_name, base_url)
        elif source_type == "BROWSER":
            from .browser_adapter import BrowserAdapter
            return BrowserAdapter(source_id, source_name, base_url)
        elif source_type == "SANDBOX":
            from .sandbox_adapter import SandboxAdapter
            return SandboxAdapter(source_id, source_name, base_url)
        else:
            raise ValueError(f"Unknown source type: {source_type}")
