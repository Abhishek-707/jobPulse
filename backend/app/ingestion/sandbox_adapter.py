from typing import List
from datetime import datetime
import logging

import httpx

from app.ingestion.base import JobSource, RawJob

logger = logging.getLogger(__name__)


class SandboxAdapter(JobSource):
    """Adapter for the controlled JobPulse sandbox."""

    def __init__(self, source_id: int, source_name: str, sandbox_url: str):
        super().__init__(source_id, source_name)
        self.sandbox_url = sandbox_url.rstrip("/")

    async def fetch(self) -> List[RawJob]:
        """Fetch jobs from the sandbox JSON API."""
        try:
            url = f"{self.sandbox_url}/api/jobs"

            logger.info(f"Fetching from sandbox {url}")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()

            jobs = []

            for job in data.get("jobs", []):
                published_at = job.get("published_at")

                if published_at:
                    published_at = datetime.fromisoformat(
                        published_at.replace("Z", "+00:00")
                    )

                raw_job = RawJob(
                    title=job["title"],
                    company=job["company"],
                    location=job.get("location"),
                    description=job.get("description"),
                    url=job.get("url"),
                    job_type=job.get("job_type"),
                    published_at=published_at,
                    external_id=job.get("id"),
                )

                jobs.append(raw_job)

            logger.info(f"Fetched {len(jobs)} jobs from sandbox")

            return jobs

        except Exception as e:
            logger.error(f"Error fetching from sandbox: {e}")
            raise