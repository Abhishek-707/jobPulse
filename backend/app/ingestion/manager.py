import logging

from sqlalchemy.orm import Session

from app.ingestion.base import SourceAdapter
from app.ingestion.pipeline import JobPipeline
from app.models import Source


logger = logging.getLogger(__name__)


class IngestionManager:
    """Coordinates ingestion across configured job sources."""

    def __init__(self, db: Session):
        self.db = db
        self.pipeline = JobPipeline(db)

    async def ingest_all(self):
        """Run ingestion for every configured source."""

        sources = (
            self.db
            .query(Source)
            .order_by(Source.id.asc())
            .all()
        )

        logger.info(
            "Starting ingestion for %d sources",
            len(sources),
        )

        results = []

        for source in sources:
            try:
                result = await self.ingest_source(
                    source.id
                )

                results.append(result)

            except Exception as exc:
                logger.exception(
                    "Error ingesting source '%s': %s",
                    source.name,
                    exc,
                )

                try:
                    source.status = "FAILED"
                    self.db.commit()
                except Exception:
                    self.db.rollback()

                results.append(
                    {
                        "source_id": source.id,
                        "source_name": source.name,
                        "status": "FAILED",
                        "error": str(exc),
                    }
                )

        logger.info(
            "Finished ingestion for %d sources",
            len(sources),
        )

        return results

    async def ingest_source(
        self,
        source_id: int,
    ):
        """Run ingestion for one source."""

        source = (
            self.db
            .query(Source)
            .filter(Source.id == source_id)
            .first()
        )

        if source is None:
            raise ValueError(
                f"Source {source_id} not found"
            )

        # ---------------------------------------------------------
        # Validate source configuration
        # ---------------------------------------------------------

        if not source.base_url:
            source.status = "FAILED"

            try:
                self.db.commit()
            except Exception:
                self.db.rollback()

            raise ValueError(
                f"Source '{source.name}' "
                f"does not have a configured URL"
            )

        # ---------------------------------------------------------
        # Build adapter
        # ---------------------------------------------------------

        logger.info(
            "Ingesting source '%s' "
            "(type=%s, url=%s)",
            source.name,
            source.type,
            source.base_url,
        )

        adapter = SourceAdapter.get_adapter(
            source_type=source.type,
            source_id=source.id,
            source_name=source.name,
            base_url=source.base_url,
        )

        # ---------------------------------------------------------
        # Run pipeline
        # ---------------------------------------------------------

        await self.pipeline.process_source(
            source,
            adapter,
        )

        return {
            "source_id": source.id,
            "source_name": source.name,
            "status": source.status,
        }