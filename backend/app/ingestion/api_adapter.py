import httpx
from typing import List, Optional, Any
from datetime import datetime
from app.ingestion.base import JobSource, RawJob
import logging


logger = logging.getLogger(__name__)


class APIAdapter(JobSource):
    """Adapter for consuming public job APIs."""

    def __init__(
        self,
        source_id: int,
        source_name: str,
        api_url: str,
        timeout: int = 30,
    ):
        super().__init__(source_id, source_name)
        self.api_url = api_url
        self.timeout = timeout

    async def fetch(self) -> List[RawJob]:
        """Fetch jobs from a public API."""

        try:
            logger.info(
                f"[{self.source_name}] Fetching from API {self.api_url}"
            )

            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "JobPulse/1.0",
                    "Accept": "application/json",
                },
            ) as client:

                response = await client.get(self.api_url)

                logger.info(
                    f"[{self.source_name}] API response: "
                    f"{response.status_code}"
                )

                response.raise_for_status()

                data = response.json()

                jobs = self._parse_api_response(data)

                logger.info(
                    f"[{self.source_name}] "
                    f"Fetched {len(jobs)} valid jobs"
                )

                return jobs

        except httpx.TimeoutException as e:
            logger.error(
                f"[{self.source_name}] "
                f"API request timed out after {self.timeout}s: {e}"
            )
            raise

        except httpx.HTTPStatusError as e:
            logger.error(
                f"[{self.source_name}] "
                f"API HTTP status error: {e.response.status_code}"
            )
            raise

        except httpx.HTTPError as e:
            logger.error(
                f"[{self.source_name}] API HTTP error: {e}"
            )
            raise

        except Exception as e:
            logger.error(
                f"[{self.source_name}] Error fetching from API: {e}"
            )
            raise

    def _parse_api_response(
        self,
        data: Any,
    ) -> List[RawJob]:
        """Parse common public job API responses."""

        if isinstance(data, list):
            job_list = data

        elif isinstance(data, dict):
            job_list = (
                data.get("jobs")
                or data.get("results")
                or data.get("data")
                or []
            )

        else:
            logger.warning(
                f"[{self.source_name}] "
                f"Unsupported response type: {type(data).__name__}"
            )
            return []

        if not isinstance(job_list, list):
            return []

        jobs: List[RawJob] = []

        for index, item in enumerate(job_list, start=1):

            if not isinstance(item, dict):
                continue

            try:
                # -------------------------------------------------
                # TITLE
                # -------------------------------------------------

                title = self._first_value(
                    item,
                    [
                        "position",
                        "title",
                        "job_title",
                        "name",
                    ],
                )

                # -------------------------------------------------
                # COMPANY
                # -------------------------------------------------

                company = self._first_value(
                    item,
                    [
                        "company",
                        "company_name",
                        "organization",
                        "employer",
                    ],
                )

                # -------------------------------------------------
                # LOCATION
                # -------------------------------------------------

                location = self._first_value(
                    item,
                    [
                        "location",
                        "location_name",
                        "city",
                        "region",
                    ],
                )

                # -------------------------------------------------
                # DESCRIPTION
                # -------------------------------------------------

                description = self._first_value(
                    item,
                    [
                        "description",
                        "summary",
                        "body",
                    ],
                )

                # -------------------------------------------------
                # URL
                # -------------------------------------------------

                url = self._first_value(
                    item,
                    [
                        "url",
                        "apply_url",
                        "job_url",
                        "link",
                    ],
                )

                # Remote OK sometimes provides an apply URL
                if not url:
                    url = self._first_value(
                        item,
                        [
                            "apply_url",
                        ],
                    )

                # -------------------------------------------------
                # JOB TYPE
                # -------------------------------------------------

                job_type = self._first_value(
                    item,
                    [
                        "job_type",
                        "employment_type",
                        "employment",
                        "type",
                    ],
                )

                # -------------------------------------------------
                # DATE
                # -------------------------------------------------

                published_at = self._parse_date(
                    self._first_value(
                        item,
                        [
                            "date",
                            "published_at",
                            "date_posted",
                            "published",
                            "created_at",
                        ],
                    )
                )

                # -------------------------------------------------
                # EXTERNAL ID
                # -------------------------------------------------

                external_id = self._first_value(
                    item,
                    [
                        "id",
                        "slug",
                        "external_id",
                    ],
                )

                # -------------------------------------------------
                # IMPORTANT VALIDATION
                # -------------------------------------------------

                # A real job listing should have at least:
                #
                # 1. A title
                # 2. A company
                #
                # This prevents generic articles from becoming jobs.

                if not title:
                    logger.debug(
                        f"[{self.source_name}] "
                        f"Skipping item {index}: missing job title"
                    )
                    continue

                if not company:
                    logger.debug(
                        f"[{self.source_name}] "
                        f"Skipping item {index}: missing company"
                    )
                    continue

                # -------------------------------------------------
                # CREATE JOB
                # -------------------------------------------------

                job = RawJob(
                    title=self._limit(
                        str(title).strip(),
                        255,
                    ),

                    company=self._limit(
                        str(company).strip(),
                        255,
                    ),

                    location=(
                        self._limit(
                            str(location).strip(),
                            255,
                        )
                        if location
                        else None
                    ),

                    description=(
                        str(description).strip()
                        if description
                        else None
                    ),

                    url=(
                        str(url).strip()
                        if url
                        else None
                    ),

                    job_type=(
                        self._limit(
                            str(job_type).strip(),
                            100,
                        )
                        if job_type
                        else None
                    ),

                    published_at=published_at,

                    external_id=(
                        str(external_id).strip()
                        if external_id is not None
                        else None
                    ),
                )

                jobs.append(job)

            except Exception as e:
                logger.error(
                    f"[{self.source_name}] "
                    f"Error parsing API item {index}: {e}"
                )
                continue

        logger.info(
            f"[{self.source_name}] "
            f"Successfully parsed {len(jobs)} real job listings"
        )

        return jobs

    @staticmethod
    def _first_value(
        item: dict,
        keys: List[str],
    ) -> Optional[Any]:
        """Return the first non-empty value."""

        for key in keys:
            value = item.get(key)

            if value is not None and value != "":
                return value

        return None

    @staticmethod
    def _limit(
        value: str,
        max_length: int,
    ) -> str:
        """Prevent database string overflow."""

        if not value:
            return ""

        return str(value).strip()[:max_length]

    @staticmethod
    def _parse_date(
        date_value: Optional[Any],
    ) -> Optional[datetime]:
        """Parse common API date formats."""

        if not date_value:
            return None

        if isinstance(date_value, datetime):
            return date_value

        date_str = str(date_value).strip()

        if not date_str:
            return None

        try:
            return datetime.fromisoformat(
                date_str.replace("Z", "+00:00")
            )
        except Exception:
            pass

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%a, %d %b %Y %H:%M:%S %z",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(
                    date_str,
                    fmt,
                )
            except Exception:
                continue

        return None