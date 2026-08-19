from datetime import datetime
import logging

from app.ingestion.deduplicator import JobDeduplicator
from app.ingestion.normalizer import JobNormalizer
from app.ingestion.validator import JobValidator


logger = logging.getLogger(__name__)


class JobPipeline:
    """
    Main job ingestion pipeline.

    FETCH
      ↓
    NORMALIZE
      ↓
    VALIDATE
      ↓
    DEDUPLICATE
      ↓
    STORE
      ↓
    UPDATE RUN + SOURCE HEALTH
    """

    def __init__(self, db):
        self.db = db

    async def process_source(self, source, adapter):
        """Process one configured source."""

        from app.models import (
            IngestionError,
            IngestionRun,
            IngestionRunStatus,
            Job,
        )

        start_time = datetime.utcnow()

        run = IngestionRun(
            source_id=source.id,
            started_at=start_time,
            status=IngestionRunStatus.RUNNING,
        )

        self.db.add(run)
        self.db.flush()

        try:
            # =========================================================
            # FETCH
            # =========================================================

            logger.info(
                "[%s] Fetching jobs...",
                source.name,
            )

            raw_jobs = await adapter.fetch()

            run.jobs_found = len(raw_jobs)

            logger.info(
                "[%s] Found %s jobs",
                source.name,
                len(raw_jobs),
            )

            if not raw_jobs:
                source.status = "DEGRADED"

                self.db.add(
                    IngestionError(
                        source_id=source.id,
                        run_id=run.id,
                        error_type="EMPTY_RESPONSE",
                        message="Source returned 0 jobs",
                    )
                )

                run.error_count += 1

            # =========================================================
            # NORMALIZE + VALIDATE
            # =========================================================

            valid_jobs = []

            for raw_job in raw_jobs:
                try:
                    normalized = JobNormalizer.normalize(
                        raw_job,
                        source_id=source.id,
                        source_name=source.name,
                    )

                    is_valid, error_msg = (
                        JobValidator.validate(
                            normalized.model_dump()
                        )
                    )

                    if not is_valid:
                        run.jobs_failed += 1
                        run.error_count += 1

                        self.db.add(
                            IngestionError(
                                source_id=source.id,
                                run_id=run.id,
                                error_type="VALIDATION_ERROR",
                                message=error_msg
                                or "Validation failed",
                            )
                        )

                        continue

                    valid_jobs.append(normalized)

                except Exception as exc:
                    run.jobs_failed += 1
                    run.error_count += 1

                    logger.exception(
                        "[%s] Job normalization failed",
                        source.name,
                    )

                    self.db.add(
                        IngestionError(
                            source_id=source.id,
                            run_id=run.id,
                            error_type="PARSER_ERROR",
                            message=str(exc)[:1000],
                        )
                    )

            # =========================================================
            # DEDUPLICATION
            # =========================================================

            hashes = [
                job.content_hash
                for job in valid_jobs
                if job.content_hash
            ]

            external_ids = [
                job.external_id
                for job in valid_jobs
                if job.external_id
            ]

            urls = [
                job.url
                for job in valid_jobs
                if job.url
            ]

            existing_hashes = (
                JobDeduplicator.get_existing_hashes(
                    self.db,
                    hashes,
                )
            )

            existing_external_ids = (
                JobDeduplicator.get_existing_external_ids(
                    self.db,
                    source.id,
                    external_ids,
                )
            )

            existing_urls = (
                JobDeduplicator.get_existing_urls(
                    self.db,
                    urls,
                )
            )

            seen_hashes = set(existing_hashes)
            seen_external_ids = set(
                existing_external_ids
            )
            seen_urls = set(existing_urls)

            jobs_to_store = []

            for job in valid_jobs:
                duplicate = False

                if (
                    job.external_id
                    and job.external_id
                    in seen_external_ids
                ):
                    duplicate = True

                elif (
                    job.url
                    and job.url in seen_urls
                ):
                    duplicate = True

                elif (
                    job.content_hash
                    and job.content_hash in seen_hashes
                ):
                    duplicate = True

                if duplicate:
                    run.jobs_duplicate += 1
                    continue

                if job.external_id:
                    seen_external_ids.add(
                        job.external_id
                    )

                if job.url:
                    seen_urls.add(job.url)

                if job.content_hash:
                    seen_hashes.add(
                        job.content_hash
                    )

                jobs_to_store.append(job)

            # =========================================================
            # STORE
            # =========================================================

            for normalized in jobs_to_store:
                try:
                    # SAVEPOINT:
                    # A failure here rolls back only this job,
                    # not the entire ingestion run.
                    with self.db.begin_nested():
                        job = Job(
                            **normalized.model_dump()
                        )

                        self.db.add(job)
                        self.db.flush()

                    run.jobs_added += 1

                except Exception as exc:
                    run.jobs_failed += 1
                    run.error_count += 1

                    logger.exception(
                        "[%s] Failed to store job",
                        source.name,
                    )

                    self.db.add(
                        IngestionError(
                            source_id=source.id,
                            run_id=run.id,
                            error_type="DATABASE_ERROR",
                            message=str(exc)[:1000],
                        )
                    )

            # =========================================================
            # FINAL STATUS
            # =========================================================

            if run.jobs_failed == 0:
                run.status = IngestionRunStatus.SUCCESS

            elif (
                run.jobs_added > 0
                or run.jobs_duplicate > 0
            ):
                run.status = IngestionRunStatus.PARTIAL

            else:
                run.status = IngestionRunStatus.FAILED

            # =========================================================
            # SOURCE HEALTH
            # =========================================================

            finished_at = datetime.utcnow()

            source.last_run_at = finished_at

            if run.status == IngestionRunStatus.SUCCESS:
                source.status = "HEALTHY"
                source.last_success_at = finished_at

            elif run.status == IngestionRunStatus.PARTIAL:
                source.status = "DEGRADED"
                source.last_success_at = finished_at

            else:
                source.status = "FAILED"
                source.last_failure_at = finished_at

            # =========================================================
            # HEALTH SCORE
            # =========================================================

            if run.jobs_found > 0:
                failure_rate = (
                    run.jobs_failed
                    / run.jobs_found
                )

                source.health_score = max(
                    0.0,
                    min(
                        1.0,
                        1.0 - failure_rate,
                    ),
                )
            else:
                source.health_score = 0.5

            # =========================================================
            # RUN METADATA
            # =========================================================

            run.finished_at = finished_at

            run.duration_ms = int(
                (
                    finished_at - start_time
                ).total_seconds()
                * 1000
            )

            logger.info(
                "[%s] Ingestion complete: "
                "%s added, "
                "%s duplicates, "
                "%s failed",
                source.name,
                run.jobs_added,
                run.jobs_duplicate,
                run.jobs_failed,
            )

        except Exception as exc:
            # =========================================================
            # PIPELINE FAILURE
            # =========================================================

            logger.exception(
                "[%s] Pipeline failed",
                source.name,
            )

            # Roll back the current transaction.
            self.db.rollback()

            finished_at = datetime.utcnow()

            # Re-load source after rollback.
            source = (
                self.db.query(type(source))
                .filter(
                    type(source).id == source.id
                )
                .one()
            )

            failed_run = IngestionRun(
                source_id=source.id,
                started_at=start_time,
                finished_at=finished_at,
                status=IngestionRunStatus.FAILED,
                error_count=1,
                duration_ms=int(
                    (
                        finished_at - start_time
                    ).total_seconds()
                    * 1000
                ),
            )

            self.db.add(failed_run)
            self.db.flush()

            source.status = "FAILED"
            source.last_failure_at = finished_at
            source.last_run_at = finished_at

            self.db.add(
                IngestionError(
                    source_id=source.id,
                    run_id=failed_run.id,
                    error_type="UNKNOWN",
                    message=str(exc)[:1000],
                )
            )

        finally:
            try:
                self.db.commit()

            except Exception:
                self.db.rollback()

                logger.exception(
                    "[%s] Failed to commit "
                    "pipeline result",
                    source.name,
                )