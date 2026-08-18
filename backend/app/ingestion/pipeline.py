from datetime import datetime
from typing import List
from app.ingestion.base import RawJob
from app.schemas import JobCreate
import logging

logger = logging.getLogger(__name__)


class JobPipeline:
    """Main ingestion pipeline orchestrating fetch -> normalize -> validate -> store."""
    
    def __init__(self, db):
        self.db = db
    
    async def process_source(self, source, adapter):
        """Process a single source through the full pipeline."""
        from app.models import IngestionRun, Source, Job, IngestionError
        from app.ingestion.normalizer import JobNormalizer
        from app.ingestion.validator import JobValidator
        from app.ingestion.deduplicator import JobDeduplicator
        from datetime import datetime, timedelta
        import time
        
        start_time = datetime.utcnow()
        run = IngestionRun(
            source_id=source.id,
            started_at=start_time,
            status="SUCCESS",
        )
        self.db.add(run)
        self.db.flush()  # Get run ID
        
        try:
            # Step 1: FETCH
            logger.info(f"[{source.name}] Fetching jobs...")
            raw_jobs = await adapter.fetch()
            run.jobs_found = len(raw_jobs)
            logger.info(f"[{source.name}] Found {len(raw_jobs)} jobs")
            
            if len(raw_jobs) == 0 and source.last_run_at is not None:
                # Empty response - mark as DEGRADED
                source.status = "DEGRADED"
                error = IngestionError(
                    source_id=source.id,
                    run_id=run.id,
                    error_type="EMPTY_RESPONSE",
                    message=f"Source returned 0 jobs (expected ~{source.last_run_at})",
                )
                self.db.add(error)
                run.error_count += 1
                logger.warning(f"[{source.name}] Empty response detected")
            
            # Step 2-5: NORMALIZE, VALIDATE, DEDUPLICATE, STORE
            for raw_job in raw_jobs:
                try:
                    # Normalize
                    normalized = JobNormalizer.normalize(
                        raw_job,
                        source_id=source.id,
                        source_name=source.name,
                    )
                    
                    # Validate
                    is_valid, error_msg = JobValidator.validate(normalized.dict())
                    if not is_valid:
                        logger.warning(f"[{source.name}] Validation failed: {error_msg}")
                        run.jobs_failed += 1
                        error = IngestionError(
                            source_id=source.id,
                            run_id=run.id,
                            error_type="VALIDATION_ERROR",
                            message=error_msg,
                        )
                        self.db.add(error)
                        run.error_count += 1
                        continue
                    
                    # Deduplicate
                    if JobDeduplicator.is_duplicate(self.db, normalized.content_hash):
                        logger.debug(f"[{source.name}] Duplicate: {normalized.title}")
                        run.jobs_duplicate += 1
                        continue
                    
                    # Store
                    job = Job(**normalized.dict())
                    self.db.add(job)
                    run.jobs_added += 1
                    logger.debug(f"[{source.name}] Added: {normalized.title}")
                
                except Exception as e:
                    logger.error(f"[{source.name}] Error processing job: {e}")
                    run.jobs_failed += 1
                    run.error_count += 1
                    continue
            
            # Step 6: UPDATE SOURCE HEALTH
            source.last_run_at = datetime.utcnow()
            source.last_success_at = datetime.utcnow()
            source.status = "HEALTHY"
            
            # Calculate health score
            # (successful runs / total runs) * 0.6 + (1 - error_rate) * 0.4
            if run.jobs_found > 0:
                error_rate = run.error_count / run.jobs_found
                source.health_score = (
                    (run.jobs_added + run.jobs_updated) / run.jobs_found * 0.6 +
                    (1 - min(error_rate, 1.0)) * 0.4
                )
            else:
                source.health_score = 0.5
            
            run.status = "SUCCESS"
            logger.info(f"[{source.name}] Ingestion complete: {run.jobs_added} added, {run.jobs_duplicate} duplicates, {run.jobs_failed} failed")
        
        except Exception as e:
            logger.error(f"[{source.name}] Pipeline error: {e}")
            run.status = "FAILED"
            source.status = "FAILED"
            source.last_failure_at = datetime.utcnow()
            error = IngestionError(
                source_id=source.id,
                run_id=run.id,
                error_type="UNKNOWN",
                message=str(e),
            )
            self.db.add(error)
            run.error_count += 1
        
        finally:
            # Finalize run
            run.finished_at = datetime.utcnow()
            run.duration_ms = int((run.finished_at - start_time).total_seconds() * 1000)
            self.db.commit()
            logger.info(f"[{source.name}] Run {run.id} completed in {run.duration_ms}ms")
