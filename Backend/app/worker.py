import asyncio
import logging
import sys
from datetime import datetime
from app.db.session import SessionLocal, AsyncSessionLocal
from app.service.sync import SyncService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("vlr_worker")

async def run_sync():
    """Execution of the sync task (Async)"""
    from app.core.redis import RedisCache
    from app.core.config import settings
    
    redis = RedisCache(settings.redis_url)
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"--- STARTING WORKER SYNC AT {datetime.utcnow()} ---")
            sync_service = SyncService(db, redis=redis)
            count = await sync_service.sync_kickoff_2026()
            logger.info(f"--- WORKER SYNC COMPLETE. Matches processed/updated: {count} ---")
        except Exception as e:
            logger.error(f"Error during worker sync: {e}")
        finally:
            await redis.close()

async def main_loop(interval_hours: int = 12):
    """Main loop for the worker"""
    logger.info(f"Worker started. Sync interval: {interval_hours} hours.")
    
    # Run once at startup
    await run_sync()
    
    while True:
        logger.info(f"Worker sleeping for {interval_hours} hours...")
        await asyncio.sleep(interval_hours * 3600)
        await run_sync()

if __name__ == "__main__":
    # You can pass --once to run it only once
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        asyncio.run(run_sync())
    else:
        try:
            asyncio.run(main_loop())
        except KeyboardInterrupt:
            logger.info("Worker stopped by user.")
