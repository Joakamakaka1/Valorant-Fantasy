import asyncio
import logging
import sys
import signal
import traceback
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

# Event para shutdown limpio
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """
    Maneja señales SIGTERM/SIGINT para graceful shutdown.
    Permite que Docker y Ctrl+C detengan el worker limpiamente.
    """
    signal_name = signal.Signals(signum).name
    logger.warning(f"Received signal {signal_name}. Initiating graceful shutdown...")
    shutdown_event.set()

# Registrar handlers de señales
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

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
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
        finally:
            await redis.close()

async def main_loop(interval_hours: int = 4):
    """
    Main loop for the worker with graceful shutdown support.
    
    Args:
        interval_hours: Hours to wait between sync cycles (default: 4)
    """
    logger.info(f"Worker started. Sync interval: {interval_hours} hours.")
    logger.info("Worker will respond to SIGTERM/SIGINT for graceful shutdown.")
    
    # Run once at startup (si no se ha recibido señal de shutdown)
    if not shutdown_event.is_set():
        await run_sync()
    
    while not shutdown_event.is_set():
        try:
            # Esperar shutdown_event O timeout (lo que ocurra primero)
            logger.info(f"Worker sleeping for {interval_hours} hours... (Press Ctrl+C to stop)")
            await asyncio.wait_for(
                shutdown_event.wait(), 
                timeout=interval_hours * 3600
            )
            # Si llegamos aquí, es porque shutdown_event fue seteado
            break
        except asyncio.TimeoutError:
            # Timeout normal después de interval_hours
            if not shutdown_event.is_set():
                await run_sync()
    
    logger.info("Worker shut down gracefully. All tasks completed.")

if __name__ == "__main__":
    # You can pass --once to run it only once
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        asyncio.run(run_sync())
    else:
        try:
            asyncio.run(main_loop())
        except KeyboardInterrupt:
            # Esto no debería alcanzarse ya que SIGINT está manejado
            logger.info("Worker stopped by user (KeyboardInterrupt).")
        except Exception as e:
            logger.error(f"Worker crashed: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            sys.exit(1)

