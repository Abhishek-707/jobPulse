from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Source
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


@router.post("/seed")
def seed_sources(
    db: Session = Depends(get_db),
):
    """
    Create the default JobPulse sources.

    This is useful for initializing a fresh production database.
    Existing sources are not duplicated.
    """

    default_sources = [
        {
            "name": "Himalayas Jobs RSS",
            "type": "RSS",
            "base_url": "https://himalayas.app/jobs/rss",
            "status": "HEALTHY",
            "health_score": 0.0,
        },
        {
            "name": "Dev.to API",
            "type": "API",
            "base_url": "https://dev.to/api/articles?tag=job",
            "status": "HEALTHY",
            "health_score": 0.0,
        },
        {
            "name": "Sandbox Jobs",
            "type": "SANDBOX",
            "base_url": "http://localhost:5000",
            "status": "HEALTHY",
            "health_score": 0.0,
        },
    ]

    created = []
    existing = []

    for data in default_sources:
        source = (
            db.query(Source)
            .filter(Source.name == data["name"])
            .first()
        )

        if source:
            existing.append(source.name)
            continue

        source = Source(**data)
        db.add(source)
        created.append(source.name)

    db.commit()

    return {
        "message": "Source initialization completed",
        "created": created,
        "already_existing": existing,
    }