from app.db.session import AsyncSessionLocal
from app.service.sync import SyncService
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_sync():
    async with AsyncSessionLocal() as db:
        try:
            sync_service = SyncService(db)
            logger.info("Starting VLR.gg Kickoff 2026 synchronization (Async)...")
            
            synced_count = await sync_service.sync_kickoff_2026()
            
            logger.info(f"Synchronization finished. {synced_count} matches processed/synced.")
        except Exception as e:
            logger.error(f"Critical error during synchronization: {e}")

if __name__ == "__main__":
    asyncio.run(run_sync())
