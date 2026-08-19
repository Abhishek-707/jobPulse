from typing import List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
)

from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.ingestion.manager import IngestionManager

from app.models import (
    IngestionRun,
    IngestionError,
    Source,
    Job,
)

from app.schemas import IngestionRunResponse


router = APIRouter(
    prefix="/api/ingestion",
    tags=["ingestion"],
)


@router.get(
    "/runs",
    response_model=List[IngestionRunResponse],
)
def list_ingestion_runs(
    db: Session = Depends(get_db),
    source_id: int | None = Query(None),
):
    """List recent ingestion runs."""

    query = db.query(IngestionRun)

    if source_id is not None:
        query = query.filter(
            IngestionRun.source_id == source_id
        )

    return (
        query
        .order_by(
            IngestionRun.created_at.desc()
        )
        .limit(100)
        .all()
    )


async def _run_source_ingestion(
    source_id: int,
):
    """Run ingestion using a fresh database session."""

    db = SessionLocal()

    try:
        manager = IngestionManager(db)

        await manager.ingest_source(
            source_id
        )

    except Exception as e:
        db.rollback()

        # IMPORTANT:
        # Don't hide ingestion errors while debugging.
        print(
            f"INGESTION ERROR for source {source_id}: "
            f"{type(e).__name__}: {e}"
        )

        import traceback

        traceback.print_exc()

    finally:
        db.close()


@router.post("/run")
async def trigger_ingestion(
    source_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Queue ingestion for one source."""

    source = (
        db.query(Source)
        .filter(
            Source.id == source_id
        )
        .first()
    )

    if source is None:
        raise HTTPException(
            status_code=404,
            detail="Source not found",
        )

    background_tasks.add_task(
        _run_source_ingestion,
        source_id,
    )

    return {
        "message": (
            f"Ingestion for source "
            f"'{source.name}' has been queued"
        ),
        "source_id": source_id,
        "status": "queued",
    }


@router.delete("/reset")
def reset_data(
    db: Session = Depends(get_db),
):
    """
    Delete all collected jobs and ingestion history.

    Sources are preserved.
    """

    try:

        # Delete jobs first
        jobs_deleted = (
            db.query(Job)
            .delete(
                synchronize_session=False
            )
        )

        # ingestion_errors references ingestion_runs,
        # so errors MUST be deleted first.
        errors_deleted = (
            db.query(IngestionError)
            .delete(
                synchronize_session=False
            )
        )

        # Now ingestion runs can be deleted.
        runs_deleted = (
            db.query(IngestionRun)
            .delete(
                synchronize_session=False
            )
        )

        db.commit()

        return {
            "status": "success",
            "message": (
                "JobPulse data reset successfully."
            ),
            "jobs_deleted": jobs_deleted,
            "errors_deleted": errors_deleted,
            "runs_deleted": runs_deleted,
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Reset failed: {str(e)}",
        )