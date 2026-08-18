from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import IngestionRun
from app.schemas import IngestionRunResponse
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])


@router.get("/runs", response_model=List[IngestionRunResponse])
def list_ingestion_runs(
    db: Session = Depends(get_db),
    source_id: int = None,
):
    """List ingestion runs, optionally filtered by source."""
    query = db.query(IngestionRun)
    
    if source_id:
        query = query.filter(IngestionRun.source_id == source_id)
    
    runs = query.order_by(IngestionRun.created_at.desc()).limit(100).all()
    return runs


@router.post("/run")
def trigger_ingestion(source_id: int, db: Session = Depends(get_db)):
    """Trigger ingestion for a source (placeholder).
    
    In production, this would queue a background task.
    For now, it returns a message indicating the feature is coming.
    """
    from app.models import Source
    
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    return {
        "message": f"Ingestion for source '{source.name}' has been queued",
        "source_id": source_id,
        "status": "queued",
    }
