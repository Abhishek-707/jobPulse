from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Source, Job
from app.schemas import SourceResponse


router = APIRouter(
    prefix="/api/sources",
    tags=["sources"],
)


@router.get("", response_model=List[SourceResponse])
def list_sources(
    db: Session = Depends(get_db),
):
    """List all job sources."""

    return (
        db.query(Source)
        .order_by(Source.name.asc())
        .all()
    )


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: int,
    db: Session = Depends(get_db),
):
    """Get a single source."""

    source = (
        db.query(Source)
        .filter(Source.id == source_id)
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Source not found",
        )

    return source


@router.get("/{source_id}/health")
def get_source_health(
    source_id: int,
    db: Session = Depends(get_db),
):
    """Get health information for a source."""

    source = (
        db.query(Source)
        .filter(Source.id == source_id)
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Source not found",
        )

    return {
        "id": source.id,
        "name": source.name,
        "status": source.status,
        "health_score": source.health_score,
        "last_success_at": source.last_success_at,
        "last_failure_at": source.last_failure_at,
        "last_run_at": source.last_run_at,
    }

@router.delete("/cleanup-devto")
def cleanup_devto_jobs(
    db: Session = Depends(get_db),
):
    """Remove legacy Dev.to article records."""

    deleted = (
        db.query(Job)
        .filter(Job.source_name == "Dev.to API")
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "message": "Legacy Dev.to jobs removed",
        "deleted": deleted,
    }
@router.post("/seed")
def seed_sources(
    db: Session = Depends(get_db),
):
    """
    Initialize the three JobPulse sources.

    Existing sources are updated instead of duplicated.
    Old Dev.to API configuration is replaced by Remote Jobs API.
    """

    sources = [
        {
            "name": "Himalayas Jobs RSS",
            "type": "RSS",
            "base_url": "https://himalayas.app/jobs/rss",
        },
        {
            "name": "Remote Jobs API",
            "type": "API",
            "base_url": "https://remoteok.com/api",
        },
        {
            "name": "Sandbox Jobs",
            "type": "SANDBOX",
            "base_url": "http://localhost:5000",
        },
    ]

    results = []

    # ---------------------------------------------------------
    # FIND EXISTING SOURCES
    # ---------------------------------------------------------

    rss = (
        db.query(Source)
        .filter(Source.name == "Himalayas Jobs RSS")
        .first()
    )

    api = (
        db.query(Source)
        .filter(Source.id == 2)
        .first()
    )

    sandbox = (
        db.query(Source)
        .filter(Source.name == "Sandbox Jobs")
        .first()
    )

    # ---------------------------------------------------------
    # RSS
    # ---------------------------------------------------------

    if rss is None:
        rss = Source(
            name="Himalayas Jobs RSS",
            type="RSS",
            base_url="https://himalayas.app/jobs/rss",
            status="HEALTHY",
            health_score=0.0,
        )
        db.add(rss)
        results.append("Created Himalayas Jobs RSS")
    else:
        rss.type = "RSS"
        rss.base_url = "https://himalayas.app/jobs/rss"
        results.append("Updated Himalayas Jobs RSS")

    # ---------------------------------------------------------
    # API
    # ---------------------------------------------------------

    if api is None:
        api = Source(
            name="Remote Jobs API",
            type="API",
            base_url="https://remoteok.com/api",
            status="HEALTHY",
            health_score=0.0,
        )
        db.add(api)
        results.append("Created Remote Jobs API")
    else:
        api.name = "Remote Jobs API"
        api.type = "API"
        api.base_url = "https://remoteok.com/api"
        api.status = "HEALTHY"
        results.append("Updated source 2 to Remote Jobs API")

    # ---------------------------------------------------------
    # SANDBOX
    # ---------------------------------------------------------

    if sandbox is None:
        sandbox = Source(
            name="Sandbox Jobs",
            type="SANDBOX",
            base_url="http://localhost:5000",
            status="HEALTHY",
            health_score=0.0,
        )
        db.add(sandbox)
        results.append("Created Sandbox Jobs")
    else:
        sandbox.type = "SANDBOX"
        sandbox.base_url = "http://localhost:5000"
        results.append("Updated Sandbox Jobs")

    db.commit()

    # ---------------------------------------------------------
    # REMOVE OLD DEV.TO JOBS
    # ---------------------------------------------------------

    old_devto_source = (
        db.query(Source)
        .filter(Source.name == "Dev.to API")
        .first()
    )

    deleted_jobs = 0

    if old_devto_source is not None:

        old_jobs = (
            db.query(Job)
            .filter(
                Job.source_id == old_devto_source.id
            )
            .all()
        )

        for job in old_jobs:
            db.delete(job)
            deleted_jobs += 1

        db.delete(old_devto_source)

        db.commit()

        results.append(
            f"Removed old Dev.to source and {deleted_jobs} jobs"
        )

    return {
        "message": "JobPulse sources initialized successfully",
        "changes": results,
        "old_devto_jobs_deleted": deleted_jobs,
    }