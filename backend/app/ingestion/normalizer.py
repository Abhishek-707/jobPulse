import hashlib
import re
from datetime import datetime
from html import unescape

from app.schemas import JobCreate


class JobNormalizer:
    """Converts raw job data into a normalized JobCreate object."""
    @staticmethod
    def clean_text(value: str | None) -> str | None:
        """Clean malformed HTML/CSS and normalize text."""

        if not value:
            return None

        text = unescape(str(value))

        # Remove style/script/noscript blocks.
        text = re.sub(
            r"<(script|style|noscript)\b[^>]*>.*?</\1>",
            " ",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # Remove CSS blocks including selectors.
        text = re.sub(
            r"(?:[#.][\w-]+|[a-zA-Z][\w-]*(?:\.[\w-]+)*)"
            r"\s*\{[^{}]*\}",
            " ",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # Remove HTML tags.
        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        # Remove CSS declarations.
        text = re.sub(
            r"[a-zA-Z_-]+\s*:\s*[^;{}]+;?",
            " ",
            text,
        )

        # Remove common CSS selector leftovers.
        text = re.sub(
            r"\b(?:div|span|body|html|p|section|article)"
            r"(?:\.[a-zA-Z_-][\w-]*)?",
            " ",
            text,
            flags=re.IGNORECASE,
        )

        text = text.replace(
            "\xa0",
            " ",
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        text = text.strip()

        return text or None

    @staticmethod
    def normalize(
        raw_job,
        source_id: int,
        source_name: str,
    ) -> JobCreate:
        """Convert RawJob into the canonical JobCreate schema."""

        title = JobNormalizer.clean_text(
            raw_job.title
        ) or ""

        company = JobNormalizer.clean_text(
            raw_job.company
        ) or ""

        location = JobNormalizer.clean_text(
            raw_job.location
        )

        description = JobNormalizer.clean_text(
            raw_job.description
        )

        content_hash = JobNormalizer.generate_hash(
            title=title,
            company=company,
            location=location or "",
        )

        return JobCreate(
            title=title,
            company=company,
            location=location,
            description=description,
            url=raw_job.url,
            source_id=source_id,
            source_name=source_name,
            external_id=raw_job.external_id,
            job_type=raw_job.job_type,
            published_at=(
                raw_job.published_at
                or datetime.utcnow()
            ),
            content_hash=content_hash,
        )

    @staticmethod
    def generate_hash(
        title: str,
        company: str,
        location: str = "",
    ) -> str:
        """
        Generate a deterministic SHA256 fingerprint.

        Used as a fallback duplicate-detection mechanism.
        """

        content = (
            f"{title.lower().strip()}|"
            f"{company.lower().strip()}|"
            f"{location.lower().strip()}"
        )

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()