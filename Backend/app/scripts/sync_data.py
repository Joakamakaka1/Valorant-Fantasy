from app.db.session import SessionLocal
from app.service.sync import SyncService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_sync():
    db = SessionLocal()
    try:
        sync_service = SyncService(db)
        logger.info("Starting VLR.gg Kickoff 2026 synchronization...")
        
        synced_count = sync_service.sync_kickoff_2026()
        
        logger.info(f"Synchronization finished. {synced_count} matches processed/synced.")
    except Exception as e:
        logger.error(f"Critical error during synchronization: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_sync()
