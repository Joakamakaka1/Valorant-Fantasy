import asyncio
import logging
from datetime import datetime
from app.db.session import SessionLocal
from app.service.sync import SyncService

logger = logging.getLogger("background_sync")

async def sync_vlr_task():  
    """Periodic task to sync VCT data from VLR.gg every 6 hours"""
    logger.info("Background sync worker started.")
    while True:
        try:
            logger.info(f"--- STARTING PERIODIC SYNC AT {datetime.utcnow()} ---")
            db = SessionLocal()
            try:
                sync_service = SyncService(db)
                count = sync_service.sync_kickoff_2026()
                db.commit()
                logger.info(f"--- PERIODIC SYNC COMPLETE. Matches processed/updated: {count} ---")
            except Exception as e:
                logger.error(f"Error during periodic sync: {e}")
                db.rollback()
            finally:
                db.close()
            
            # Wait for 12 hours
            await asyncio.sleep(60 * 60 * 12)
            
        except asyncio.CancelledError:
            logger.info("Background sync task cancelled.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in background sync loop: {e}")
            await asyncio.sleep(60) # Wait a bit before retrying if there's a fatal error
