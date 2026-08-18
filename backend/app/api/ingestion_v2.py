from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import IngestionRun, Source
from app.schemas import IngestionRunResponse
from app.ingestion.manager import IngestionManager
from typing import List
import logging
import asyncio

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
def trigger_ingestion(source_id: int, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Trigger ingestion for a source.
    
    Runs ingestion in background and returns immediately.
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    # Queue background task
    async def run_ingestion():
        manager = IngestionManager(db)
        await manager.ingest_source(source_id)
    
    if background_tasks:
        background_tasks.add_task(lambda: asyncio.run(run_ingestion()))
    
    return {
        "message": f"Ingestion for source '{source.name}' has been queued",
        "source_id": source_id,
        "status": "queued",
    }


@router.post("/run-all")
def trigger_ingestion_all(db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """Trigger ingestion for all sources."""
    
    async def run_all():
        manager = IngestionManager(db)
        await manager.ingest_all()
    
    if background_tasks:
        background_tasks.add_task(lambda: asyncio.run(run_all()))
    
    return {
        "message": "Ingestion for all sources has been queued",
        "status": "queued",
    }
