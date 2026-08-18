import httpx
from typing import List, Optional
from datetime import datetime
from app.ingestion.base import JobSource, RawJob
import logging

logger = logging.getLogger(__name__)


class APIAdapter(JobSource):
    """Adapter for consuming public job APIs."""
    
    def __init__(self, source_id: int, source_name: str, api_url: str, timeout: int = 30):
        super().__init__(source_id, source_name)
        self.api_url = api_url
        self.timeout = timeout
    
    async def fetch(self) -> List[RawJob]:
        """Fetch jobs from API."""
        try:
            logger.info(f"Fetching from API {self.api_url}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.api_url)
                response.raise_for_status()
                
                data = response.json()
                jobs = self._parse_api_response(data)
                logger.info(f"Fetched {len(jobs)} jobs from API")
                return jobs
        
        except httpx.TimeoutException:
            logger.error(f"API request timed out after {self.timeout}s")
            raise
        except httpx.HTTPError as e:
            logger.error(f"API HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching from API: {e}")
            raise
    
    def _parse_api_response(self, data: dict) -> List[RawJob]:
        """Parse API response into RawJob objects.
        
        This is a generic implementation that assumes data['jobs'] exists.
        Override in subclasses for specific API formats.
        """
        jobs = []
        
        # Generic handling: look for 'jobs' or 'results' key
        job_list = data.get('jobs', data.get('results', data.get('data', [])))
        
        if not isinstance(job_list, list):
            job_list = []
        
        for item in job_list:
            try:
                job = RawJob(
                    title=item.get('title', item.get('job_title', '')),
                    company=item.get('company', item.get('company_name', '')),
                    location=item.get('location', item.get('location_name', None)),
                    description=item.get('description', item.get('summary', '')),
                    url=item.get('url', item.get('link', '')),
                    job_type=item.get('job_type', item.get('employment_type', None)),
                    published_at=self._parse_date(item.get('published_at', item.get('date_posted'))),
                    external_id=item.get('id', item.get('external_id')),
                )
                jobs.append(job)
            except Exception as e:
                logger.error(f"Error parsing API job: {e}")
                continue
        
        return jobs
    
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse date from various formats."""
        if not date_str:
            return None
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            pass
        
        try:
            # Try common format
            return datetime.strptime(date_str, '%Y-%m-%d')
        except Exception:
            logger.debug(f"Could not parse date: {date_str}")
            return None
