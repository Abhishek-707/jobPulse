from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job
from app.schemas import JobResponse


router = APIRouter(
    prefix="/api/jobs",
    tags=["jobs"],
)


@router.get(
    "",
    response_model=List[JobResponse],
)
def list_jobs(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None),
    source_id: Optional[int] = Query(None),
    limit: int = Query(500, ge=1, le=1000),
):
    """
    Return collected jobs.

    Default limit is 500 so the dashboard can display
    the complete collected dataset for the assignment.
    """

    query = db.query(Job)

    # Search
    if search:
        search_value = f"%{search}%"

        query = query.filter(
            (Job.title.ilike(search_value))
            | (Job.company.ilike(search_value))
            | (Job.location.ilike(search_value))
        )

    # Filter by source
    if source_id is not None:
        query = query.filter(
            Job.source_id == source_id
        )

    return (
        query
        .order_by(Job.id.desc())
        .limit(limit)
        .all()
    )