import feedparser
from typing import List
from datetime import datetime
from app.ingestion.base import JobSource, RawJob
import logging

logger = logging.getLogger(__name__)


class RSSAdapter(JobSource):
    """Adapter for consuming RSS/Atom feeds."""
    
    def __init__(self, source_id: int, source_name: str, rss_url: str):
        super().__init__(source_id, source_name)
        self.rss_url = rss_url
    
    async def fetch(self) -> List[RawJob]:
        """Fetch jobs from RSS feed."""
        try:
            logger.info(f"Fetching RSS from {self.rss_url}")
            feed = feedparser.parse(self.rss_url)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS parsing warning: {feed.bozo_exception}")
            
            jobs = []
            for entry in feed.entries:
                try:
                    job = RawJob(
                        title=entry.get('title', ''),
                        company=entry.get('author', ''),
                        location=entry.get('location', None),
                        description=entry.get('summary', ''),
                        url=entry.get('link', ''),
                        published_at=self._parse_published_date(entry),
                        external_id=entry.get('id', None),
                    )
                    jobs.append(job)
                except Exception as e:
                    logger.error(f"Error parsing RSS entry: {e}")
                    continue
            
            logger.info(f"Fetched {len(jobs)} jobs from RSS")
            return jobs
        
        except Exception as e:
            logger.error(f"Error fetching RSS: {e}")
            raise
    
    @staticmethod
    def _parse_published_date(entry) -> datetime:
        """Extract and parse published date from RSS entry."""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
        except Exception as e:
            logger.debug(f"Could not parse date: {e}")
        return datetime.now()
