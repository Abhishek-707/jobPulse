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