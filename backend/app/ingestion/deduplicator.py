from typing import Iterable, Set

from sqlalchemy.orm import Session

from app.models import Job


class JobDeduplicator:
    """Efficient job duplicate detection."""

    @staticmethod
    def get_existing_hashes(
        db: Session,
        content_hashes: Iterable[str],
    ) -> Set[str]:
        """Return content hashes already in the database."""

        hashes = {
            value.strip()
            for value in content_hashes
            if value and value.strip()
        }

        if not hashes:
            return set()

        rows = (
            db.query(Job.content_hash)
            .filter(
                Job.content_hash.in_(hashes)
            )
            .all()
        )

        return {
            row[0]
            for row in rows
            if row[0]
        }

    @staticmethod
    def get_existing_external_ids(
        db: Session,
        source_id: int,
        external_ids: Iterable[str],
    ) -> Set[str]:
        """Return external IDs already stored for a source."""

        ids = {
            value.strip()
            for value in external_ids
            if value and value.strip()
        }

        if not ids:
            return set()

        rows = (
            db.query(Job.external_id)
            .filter(
                Job.source_id == source_id,
                Job.external_id.in_(ids),
            )
            .all()
        )

        return {
            row[0]
            for row in rows
            if row[0]
        }

    @staticmethod
    def get_existing_urls(
        db: Session,
        urls: Iterable[str],
    ) -> Set[str]:
        """Return URLs already stored."""

        values = {
            value.strip()
            for value in urls
            if value and value.strip()
        }

        if not values:
            return set()

        rows = (
            db.query(Job.url)
            .filter(
                Job.url.in_(values)
            )
            .all()
        )

        return {
            row[0]
            for row in rows
            if row[0]
        }

    @staticmethod
    def is_duplicate(
        db: Session,
        content_hash: str,
    ) -> bool:
        """Check whether a content hash already exists."""

        if not content_hash:
            return False

        return (
            db.query(Job.id)
            .filter(
                Job.content_hash == content_hash
            )
            .first()
            is not None
        )