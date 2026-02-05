from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.service.sync import SyncService
from app.auth.deps import get_async_db, allow_admin
import logging

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger("admin_sync")

@router.post("/sync-vlr", dependencies=[Depends(allow_admin)])
async def trigger_vlr_sync(background_tasks: BackgroundTasks):
    """
    Manually triggers a full VLR.gg synchronization in the background (Async).
    """
    async def run_sync():
        async with AsyncSessionLocal() as new_db:
            try:
                srv = SyncService(new_db)
                logger.info("Manual admin sync started via background task.")
                count = await srv.sync_kickoff_2026()
                # @transactional handles commits
                logger.info(f"Manual admin sync completed. Matches: {count}")
            except Exception as e:
                logger.error(f"Error during manual admin sync: {e}")

    background_tasks.add_task(run_sync)
    return {"message": "VCT 2026 synchronization started in the background."}

@router.post("/recalibrate-prices", dependencies=[Depends(allow_admin)])
async def recalibrate_prices(db: AsyncSession = Depends(get_async_db)):
    """
    Recalcula los precios de todos los jugadores según el nuevo algoritmo (Async).
    """
    sync_service = SyncService(db)
    count = await sync_service.recalibrate_all_prices()
    return {"message": f"Recalibration completed for {count} players."}
