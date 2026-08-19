import asyncio
import feedparser
import html
import logging
import re
import urllib.request

from typing import List
from datetime import datetime

from app.ingestion.base import JobSource, RawJob

logger = logging.getLogger(__name__)


class RSSAdapter(JobSource):
    """Adapter for consuming RSS/Atom job feeds."""

    def __init__(
        self,
        source_id: int,
        source_name: str,
        rss_url: str,
    ):
        super().__init__(source_id, source_name)
        self.rss_url = rss_url

    async def fetch(self) -> List[RawJob]:
        """Download, parse and normalize an RSS/Atom feed."""

        logger.info(
            f"[{self.source_name}] Fetching RSS from {self.rss_url}"
        )

        try:
            feed_data = await asyncio.to_thread(
                self._download_feed
            )

        except Exception as e:
            logger.error(
                f"[{self.source_name}] RSS download failed: {e}"
            )
            raise RuntimeError(
                f"RSS feed could not be downloaded: {e}"
            ) from e

        try:
            feed = feedparser.parse(feed_data)

        except Exception as e:
            logger.error(
                f"[{self.source_name}] RSS parsing failed: {e}"
            )
            raise RuntimeError(
                f"RSS feed could not be parsed: {e}"
            ) from e

        if getattr(feed, "bozo", False):
            error = getattr(
                feed,
                "bozo_exception",
                "Unknown RSS parsing error",
            )

            logger.warning(
                f"[{self.source_name}] RSS parsing warning: {error}"
            )

            if not feed.entries:
                raise RuntimeError(
                    f"RSS feed could not be parsed: {error}"
                )

        entries = getattr(feed, "entries", [])

        if not entries:
            logger.warning(
                f"[{self.source_name}] RSS returned 0 entries"
            )
            return []

        logger.info(
            f"[{self.source_name}] RSS returned "
            f"{len(entries)} entries"
        )

        jobs: List[RawJob] = []

        for index, entry in enumerate(entries, 1):
            try:
                # --------------------------------------------------
                # TITLE
                # --------------------------------------------------

                title = self._clean_text(
                    entry.get("title", "")
                )

                if not title:
                    logger.warning(
                        f"[{self.source_name}] "
                        f"Entry {index} has no title"
                    )
                    continue

                # --------------------------------------------------
                # DESCRIPTION
                # --------------------------------------------------

                description = self._get_description(entry)

                # --------------------------------------------------
                # URL
                # --------------------------------------------------

                url = entry.get("link", "")

                if url:
                    url = str(url).strip()

                # --------------------------------------------------
                # COMPANY
                # --------------------------------------------------

                company = self._clean_text(
                    entry.get(
                        "himalayasjobs_companyname",
                        "",
                    )
                )

                # Himalayas is currently returning the literal
                # placeholder "name" instead of the actual company.
                #
                # Do NOT accept that as a real company name.
                if self._is_invalid_company(company):
                    company = ""

                # Generic RSS author fallback.
                if not company:
                    company = self._clean_text(
                        entry.get("author", "")
                    )

                if self._is_invalid_company(company):
                    company = ""

                # Last fallback:
                # Extract company slug from Himalayas URL.
                if not company and url:
                    company = self._company_from_url(url)

                if not company:
                    company = "Unknown"

                # --------------------------------------------------
                # LOCATION
                # --------------------------------------------------

                location = self._clean_text(
                    entry.get(
                        "himalayasjobs_locationrestriction",
                        "",
                    )
                )

                # --------------------------------------------------
                # JOB TYPE
                # --------------------------------------------------

                job_type = self._extract_job_type(
                    description
                )

                # --------------------------------------------------
                # EXTERNAL ID
                # --------------------------------------------------

                external_id = entry.get("id")

                if external_id:
                    external_id = str(
                        external_id
                    ).strip()

                # --------------------------------------------------
                # RAW JOB
                # --------------------------------------------------

                job = RawJob(
                    title=self._limit(
                        title,
                        255,
                    ),
                    company=self._limit(
                        company,
                        255,
                    ),
                    location=self._limit(
                        location,
                        255,
                    ) or None,
                    description=description or None,
                    url=url or None,
                    job_type=self._limit(
                        job_type,
                        100,
                    ) or None,
                    published_at=(
                        self._parse_published_date(
                            entry
                        )
                    ),
                    external_id=external_id,
                )

                jobs.append(job)

            except Exception as e:
                logger.error(
                    f"[{self.source_name}] "
                    f"Error parsing entry {index}: {e}"
                )
                continue

        logger.info(
            f"[{self.source_name}] "
            f"Successfully parsed {len(jobs)} jobs"
        )

        # Debug first 10 jobs.
        for index, job in enumerate(
            jobs[:10],
            1,
        ):
            logger.info(
                f"[{self.source_name}] "
                f"JOB {index}: "
                f"title={job.title!r} | "
                f"company={job.company!r} | "
                f"location={job.location!r} | "
                f"job_type={job.job_type!r}"
            )

        return jobs

    # ==============================================================
    # DOWNLOAD
    # ==============================================================

    def _download_feed(self) -> bytes:
        """Download RSS feed with browser-like headers."""

        request = urllib.request.Request(
            self.rss_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/150.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "application/rss+xml, "
                    "application/atom+xml, "
                    "application/xml, "
                    "text/xml, */*"
                ),
                "Accept-Language": (
                    "en-US,en;q=0.9"
                ),
                "Connection": "close",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:

            data = response.read()

            if not data:
                raise RuntimeError(
                    "RSS server returned an empty response"
                )

            logger.info(
                f"[{self.source_name}] "
                f"Downloaded {len(data)} bytes"
            )

            return data

    # ==============================================================
    # COMPANY
    # ==============================================================

    @staticmethod
    def _is_invalid_company(company: str) -> bool:
        """Return True when RSS company value is unusable."""

        if not company:
            return True

        normalized = company.strip().lower()

        invalid_values = {
            "name",
            "unknown",
            "null",
            "none",
            "n/a",
            "na",
            "-",
        }

        return normalized in invalid_values

    @staticmethod
    def _company_from_url(url: str) -> str:
        """
        Extract a company name from a Himalayas job URL.

        Example:

        https://himalayas.app/companies/twilio/jobs/abc

        becomes:

        Twilio
        """

        if not url:
            return ""

        match = re.search(
            r"/companies/([^/]+)/jobs/",
            url,
            flags=re.IGNORECASE,
        )

        if not match:
            return ""

        slug = match.group(1)

        if not slug:
            return ""

        # Convert URL slug to readable company name.
        company = slug.replace("-", " ")

        company = re.sub(
            r"\s+",
            " ",
            company,
        ).strip()

        # Preserve common acronyms where possible.
        words = []

        for word in company.split():
            if word.isupper():
                words.append(word)
            else:
                words.append(
                    word[:1].upper() + word[1:]
                )

        return " ".join(words)

    # ==============================================================
    # DESCRIPTION
    # ==============================================================
    @staticmethod
    def _get_description(entry) -> str:
        """Get and clean the best available job description."""

        raw_description = ""

        content = entry.get("content")

        if content and isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue

                value = item.get("value")

                if value:
                    raw_description = str(value)
                    break

        if not raw_description:
            summary = entry.get("summary", "")

            if summary:
                raw_description = str(summary)

        if not raw_description:
            return ""

        return RSSAdapter._clean_description(
            raw_description
        )
    @staticmethod
    def _clean_description(value: str) -> str:
        """Clean malformed HTML/CSS from an RSS description."""

        if not value:
            return ""

        text = html.unescape(str(value))

        # ---------------------------------------------------------
        # Remove complete style/script/noscript blocks
        # ---------------------------------------------------------

        text = re.sub(
            r"<(script|style|noscript)\b[^>]*>.*?</\1>",
            " ",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # ---------------------------------------------------------
        # Remove CSS blocks INCLUDING their selector
        #
        # Example:
        # div.content {background: #fff}
        # ---------------------------------------------------------

        text = re.sub(
            r"(?:[#.][\w-]+|[a-zA-Z][\w-]*(?:\.[\w-]+)*)"
            r"\s*\{[^{}]*\}",
            " ",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # ---------------------------------------------------------
        # Remove HTML tags
        # ---------------------------------------------------------

        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        # ---------------------------------------------------------
        # Remove CSS declarations that survived
        # ---------------------------------------------------------

        text = re.sub(
            r"[a-zA-Z_-]+\s*:\s*[^;{}]+;?",
            " ",
            text,
        )

        # ---------------------------------------------------------
        # Remove common CSS selector leftovers
        # ---------------------------------------------------------

        text = re.sub(
            r"\b(?:div|span|body|html|p|section|article)"
            r"(?:\.[a-zA-Z_-][\w-]*)?",
            " ",
            text,
            flags=re.IGNORECASE,
        )

        # ---------------------------------------------------------
        # Normalize whitespace
        # ---------------------------------------------------------

        text = text.replace("\xa0", " ")

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()
    @staticmethod
    def _extract_job_type(
        description: str,
    ) -> str:
        """Extract job type from description."""

        if not description:
            return ""

        text = html.unescape(
            str(description)
        )

        text = re.sub(
            r"<br\s*/?>",
            "\n",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"</(?:p|div|h[1-6]|li)>",
            "\n",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        text = text.replace(
            "\xa0",
            " ",
        )

        patterns = [
            r"\bJob\s+Type\s*:\s*([^\n]+)",
            r"\bRole\s+Type\s*:\s*([^\n]+)",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if match:
                return " ".join(
                    match.group(1).split()
                ).strip()

        return ""
    # ==============================================================
    # TEXT CLEANING
    # ==============================================================

    @staticmethod
    def _clean_text(value) -> str:
        """Clean HTML and entities from text."""

        if value is None:
            return ""

        value = html.unescape(
            str(value)
        )

        value = re.sub(
            r"<[^>]+>",
            " ",
            value,
        )

        return " ".join(
            value.split()
        ).strip()

    # ==============================================================
    # LENGTH LIMIT
    # ==============================================================

    @staticmethod
    def _limit(
        value: str,
        max_length: int,
    ) -> str:
        """Prevent database string overflow."""

        if not value:
            return ""

        return str(value).strip()[:max_length]

    # ==============================================================
    # DATE
    # ==============================================================

    @staticmethod
    def _parse_published_date(entry) -> datetime:
        """Extract published/updated date."""

        try:
            published = getattr(
                entry,
                "published_parsed",
                None,
            )

            if published:
                return datetime(
                    *published[:6]
                )

            updated = getattr(
                entry,
                "updated_parsed",
                None,
            )

            if updated:
                return datetime(
                    *updated[:6]
                )

        except Exception as e:
            logger.debug(
                f"Could not parse date: {e}"
            )

        return datetime.utcnow()
