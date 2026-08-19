"""Management commands for JobPulse."""
import asyncio
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Source, Job
from app.ingestion.manager import IngestionManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_sources(db: Session):
    """Seed database with default sources."""
    logger.info("Seeding sources...")
    
    default_sources = [
        Source(
            name="GitHub Jobs RSS",
            type="RSS",
            base_url="https://github.com/jobs.atom",
            status="UNKNOWN",
            health_score=0.0,
        ),
        Source(
            name="Dev.to API",
            type="API",
            base_url="https://dev.to/api/articles?tag=job",
            status="UNKNOWN",
            health_score=0.0,
        ),
        Source(
            name="Sandbox Jobs",
            type="SANDBOX",
            base_url="http://localhost:5000",
            status="UNKNOWN",
            health_score=0.0,
        ),
    ]
    
    for source in default_sources:
        existing = db.query(Source).filter_by(name=source.name).first()
        if not existing:
            db.add(source)
            logger.info(f"Added source: {source.name}")
        else:
            logger.info(f"Source already exists: {source.name}")
    
    db.commit()
    logger.info("Seeding complete!")


async def run_ingestion(db: Session, source_id: int = None):
    """Run ingestion for specific source or all sources."""
    manager = IngestionManager(db)
    
    if source_id:
        logger.info(f"Running ingestion for source {source_id}")
        await manager.ingest_source(source_id)
    else:
        logger.info("Running ingestion for all sources")
        await manager.ingest_all()


async def list_sources(db: Session):
    """List all sources and their status."""
    sources = db.query(Source).all()
    
    if not sources:
        logger.info("No sources found")
        return
    
    logger.info(f"\n{'ID':<3} {'Name':<25} {'Type':<10} {'Status':<10} {'Score':<6}")
    logger.info("-" * 60)
    
    for source in sources:
        logger.info(
            f"{source.id:<3} {source.name:<25} {source.type:<10} {source.status:<10} {source.health_score:.2f}"
        )


async def list_jobs(db: Session, limit: int = 10):
    """List recent jobs."""
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
    
    if not jobs:
        logger.info("No jobs found")
        return
    
    logger.info(f"\nLatest {limit} jobs:\n")
    
    for job in jobs:
        logger.info(f"[{job.id}] {job.title}")
        logger.info(f"    Company: {job.company}")
        logger.info(f"    Location: {job.location}")
        logger.info(f"    URL: {job.url}")
        logger.info(f"    Source: {job.source_name}")
        logger.info("")


if __name__ == "__main__":
    import sys
    
    db = SessionLocal()
    
    if len(sys.argv) < 2:
        logger.info("Usage: python -m app.management <command> [args]")
        logger.info("Commands:")
        logger.info("  seed_sources - Seed database with default sources")
        logger.info("  run_ingestion [source_id] - Run ingestion")
        logger.info("  list_sources - List all sources")
        logger.info("  list_jobs [limit] - List recent jobs")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "seed_sources":
        asyncio.run(seed_sources(db))
    elif command == "run_ingestion":
        source_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
        asyncio.run(run_ingestion(db, source_id))
    elif command == "list_sources":
        asyncio.run(list_sources(db))
    elif command == "list_jobs":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        asyncio.run(list_jobs(db, limit))
    else:
        logger.error(f"Unknown command: {command}")
        sys.exit(1)
    
    db.close()
