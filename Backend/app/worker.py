import asyncio
import logging
import sys
import signal
import traceback
from datetime import datetime
from app.db.session import AsyncSessionLocal
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
    """
    Execution of the sync task (Async).
    
    Ciclo completo:
    1. Sincronizar torneos desde VLR.gg
    2. Detectar torneo ongoing y activar jugadores participantes
    3. Sincronizar partidos del torneo activo (o Kickoff si no hay torneo)
    4. Detectar torneos completados y otorgar recompensas
    """
    from app.core.redis import RedisCache
    from app.core.config import settings
    from app.service.tournament import TournamentService
    from app.service.player_activation import PlayerActivationService
    from app.service.rewards import RewardService
    from app.db.models.tournament import TournamentStatus
    
    redis = RedisCache(settings.redis_url)
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"--- STARTING WORKER SYNC AT {datetime.utcnow()} ---")
            
            # ==== FASE 1: SINCRONIZAR TORNEOS DESDE VLR.gg ====
            logger.info("\n📅 PHASE 1: Syncing tournaments from VLR.gg...")
            tournament_service = TournamentService(db)
            await tournament_service.sync_tournaments_from_vlr()
            await db.commit()
            
            # ==== FASE 2: ACTIVAR JUGADORES PARA TORNEOS ONGOING ====
            logger.info("\n👥 PHASE 2: Managing player activation...")
            player_activation_service = PlayerActivationService(db)
            
            # Obtener TODOS los torneos ongoing (puede haber varios: 4 Kickoffs + Masters si coinciden)
            ongoing_tournaments = await tournament_service.repo.get_by_status(TournamentStatus.ONGOING)
            
            if ongoing_tournaments:
                logger.info(f"  🎮 {len(ongoing_tournaments)} ongoing tournament(s) detected:")
                for t in ongoing_tournaments:
                    logger.info(f"     - {t.name} (ID: {t.id})")
                
                # Activar jugadores de TODOS los torneos ongoing
                # Necesitamos combinar equipos de todos los torneos
                all_participating_team_ids = set()
                for tournament in ongoing_tournaments:
                    team_ids = await tournament_service.team_repo.get_teams_for_tournament(tournament.id)
                    all_participating_team_ids.update(team_ids)
                
                logger.info(f"  📋 Total teams participating across all ongoing tournaments: {len(all_participating_team_ids)}")
                
                # Activar jugadores de equipos participantes
                # Usamos el primer torneo ongoing para marcar, pero el punto es que están activos
                primary_tournament = ongoing_tournaments[0]
                activation_result = await player_activation_service.activate_players_for_tournament(
                    primary_tournament.id
                )
                await db.commit()
                logger.info(
                    f"  ✅ Activated {activation_result['activated']} players, "
                    f"deactivated {activation_result['deactivated']}"
                )
                
                # ==== FASE 3: SINCRONIZAR PARTIDOS DE TODOS LOS TORNEOS ONGOING ====
                logger.info(f"\n⚽ PHASE 3: Syncing matches for ongoing tournaments...")
                sync_service = SyncService(db, redis=redis)
                total_matches = 0
                
                for tournament in ongoing_tournaments:
                    logger.info(f"  📍 Syncing {tournament.name}...")
                    event_path = tournament.vlr_event_path
                    count = await sync_service.sync_from_event(event_path, tournament_id=tournament.id)
                    total_matches += count
                    await db.commit()
                
                logger.info(f"  ✅ Total matches processed: {total_matches}")
            else:
                logger.info("  ℹ️  No ongoing tournament. Deactivating all players...")
                await player_activation_service.deactivate_all_players()
                await db.commit()
                
                # Fallback: Sincronizar Kickoff 2026 si no hay torneo ongoing
                logger.info("\n⚽ PHASE 3: Syncing Kickoff 2026 (fallback)...")
                sync_service = SyncService(db, redis=redis)
                count = await sync_service.sync_kickoff_2026()
                await db.commit()
                logger.info(f"  ✅ Matches processed/updated: {count}")
            
            # ==== FASE 4: OTORGAR RECOMPENSAS SI TORNEO COMPLETADO ====
            logger.info("\n🎁 PHASE 4: Checking for completed tournaments...")
            completed_tournaments = await tournament_service.repo.get_by_status(TournamentStatus.COMPLETED)
            
            # Buscar torneos que recién pasaron a "completed" (sin recompensas otorgadas)
            # Para simplificar, otorgamos recompensas si hay algún torneo completed
            # En producción, podrías añadir un flag `rewards_granted` al Tournament
            if completed_tournaments:
                reward_service = RewardService(db)
                for tournament in completed_tournaments:
                    logger.info(f"  🏆 Tournament completed: {tournament.name}")
                    
                    # Aquí podrías verificar si ya se otorgaron recompensas
                    # Por ahora, lo hacemos una vez cuando detectamos el torneo completed
                    # En la próxima iteración, puedes añadir un campo `rewards_granted`
                    
                # Otorgar recompensas (asumiendo que es la primera vez)
                # Para evitar duplicados, esto debería ejecutarse solo una vez
                # Puedes añadir lógica adicional o un flag en el modelo Tournament
                logger.info("  💰 Granting tournament rewards...")
                # reward_result = await reward_service.grant_tournament_rewards(tournament.id)
                # await db.commit()
                # logger.info(f"  ✅ Rewards granted: {reward_result['members_rewarded']} members")
                
                logger.info("  ⚠️  Reward granting disabled (requires rewards_granted flag in Tournament)")
            else:
                logger.info("  ℹ️  No completed tournaments")
            
            logger.info(f"\n--- WORKER SYNC COMPLETE AT {datetime.utcnow()} ---")
            
        except Exception as e:
            logger.error(f"Error during worker sync: {e}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            await db.rollback()
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

