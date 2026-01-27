from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.service.sync import SyncService
from app.auth.deps import allow_admin
import logging

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("admin_sync")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/sync-vlr", dependencies=[Depends(allow_admin)])
async def trigger_vlr_sync(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Manually triggers a full VLR.gg synchronization in the background.
    """
    # We use a wrapper to handle the session independently if it's in a background task
    def run_sync():
        new_db = SessionLocal()
        try:
            srv = SyncService(new_db)
            logger.info("Manual admin sync started via background task.")
            count = srv.sync_kickoff_2026()
            new_db.commit()
            logger.info(f"Manual admin sync completed. Matches: {count}")
        except Exception as e:
            logger.error(f"Error during manual admin sync: {e}")
            new_db.rollback()
        finally:
            new_db.close()

    background_tasks.add_task(run_sync)
    
    return {"message": "VCT 2026 synchronization started in the background."}

@router.post("/recalibrate-prices", dependencies=[Depends(allow_admin)])
def recalibrate_prices(db: Session = Depends(get_db)):
    """
    Recalcula los precios de todos los jugadores según el nuevo algoritmo.
    """
    sync_service = SyncService(db)
    count = sync_service.recalibrate_all_prices()
    db.commit()
    return {"message": f"Recalibration completed for {count} players."}
