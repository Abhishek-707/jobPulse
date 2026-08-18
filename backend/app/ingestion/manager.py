from sqlalchemy.orm import Session
from app.models import Source
from app.ingestion.base import SourceAdapter
from app.ingestion.pipeline import JobPipeline
import logging

logger = logging.getLogger(__name__)


class IngestionManager:
    """Manages ingestion for all sources."""
    
    def __init__(self, db: Session):
        self.db = db
        self.pipeline = JobPipeline(db)
    
    async def ingest_all(self):
        """Ingest all active sources."""
        sources = self.db.query(Source).all()
        
        logger.info(f"Starting ingestion for {len(sources)} sources")
        
        for source in sources:
            try:
                adapter = SourceAdapter.get_adapter(
                    source_type=source.type,
                    source_id=source.id,
                    source_name=source.name,
                    base_url=source.base_url,
                )
                
                await self.pipeline.process_source(source, adapter)
            
            except Exception as e:
                logger.error(f"Error ingesting source {source.name}: {e}")
                source.status = "FAILED"
                self.db.commit()
    
    async def ingest_source(self, source_id: int):
        """Ingest a single source by ID."""
        source = self.db.query(Source).filter_by(id=source_id).first()
        if not source:
            raise ValueError(f"Source {source_id} not found")
        
        logger.info(f"Ingesting source: {source.name}")
        
        adapter = SourceAdapter.get_adapter(
            source_type=source.type,
            source_id=source.id,
            source_name=source.name,
            base_url=source.base_url,
        )
        
        await self.pipeline.process_source(source, adapter)
