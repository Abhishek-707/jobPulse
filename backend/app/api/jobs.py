from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Job
from app.schemas import JobResponse
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=List[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List all jobs with pagination."""
    skip = (page - 1) * limit
    jobs = db.query(Job).offset(skip).limit(limit).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a single job by ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"error": "Job not found"}
    return job


@router.get("/search", response_model=List[JobResponse])
def search_jobs(
    q: str = Query(..., min_length=1),
    location: str = Query(None),
    db: Session = Depends(get_db),
):
    """Search jobs by query and optional location."""
    query = db.query(Job)
    
    # Search in title, company, description
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (Job.title.ilike(search_term)) |
            (Job.company.ilike(search_term)) |
            (Job.description.ilike(search_term))
        )
    
    # Filter by location
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    
    return query.limit(100).all()
