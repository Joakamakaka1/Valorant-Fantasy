"""
Script para recalibrar TODOS los precios de jugadores con el nuevo cap de 85M.

IMPORTANTE: Ejecutar DESPUÉS de actualizar la fórmula en sync.py.

Este script:
1. Recalcula fantasy_points_earned para todos los PlayerMatchStats con la fórmula de 20pts
2. Recalcula current_price para todos los jugadores con el nuevo cap de 85M
3. Actualiza matches_played y points globales

Uso:
    python -m app.scripts.recalibrate_prices_85m
    
    O desde la raíz del backend:
    python app/scripts/recalibrate_prices_85m.py
"""
import asyncio
import sys
import logging
from pathlib import Path

# Añadir el directorio raíz al PYTHONPATH para imports
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from app.db.session import AsyncSessionLocal
from app.service.sync import SyncService
from app.core.redis import RedisCache
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Ejecuta la recalibración completa de precios y puntos."""
    
    logger.info("=" * 70)
    logger.info("INICIANDO RECALIBRACIÓN DE PRECIOS CON CAP DE 85M")
    logger.info("=" * 70)
    
    redis = RedisCache(settings.redis_url)
    
    async with AsyncSessionLocal() as db:
        try:
            sync_service = SyncService(db, redis=redis)
            
            logger.info("\n🔄 PASO 1/2: Recalculando puntos con fórmula de 20pts máx...")
            logger.info("           (y actualizando precios con cap de 85M)")
            
            num_players = await sync_service.recalibrate_all_prices()
            
            logger.info(f"\n✅ RECALIBRACIÓN COMPLETA")
            logger.info(f"   - Jugadores procesados: {num_players}")
            logger.info(f"   - Todos los PlayerMatchStats recalculados con fórmula 20pts")
            logger.info(f"   - Todos los precios recalculados con cap de 85M")
            
            logger.info("\n📊 Verificando jugadores más caros...")
            # Obtener top 5 jugadores más caros para verificar
            from app.service.professional import PlayerService
            player_service = PlayerService(db, redis=redis)
            
            from sqlalchemy import select, desc
            from app.db.models.professional import Player
            
            query = select(Player).order_by(desc(Player.current_price)).limit(5)
            result = await db.execute(query)
            top_players = result.scalars().all()
            
            logger.info("\n   TOP 5 JUGADORES MÁS CAROS:")
            for i, player in enumerate(top_players, 1):
                logger.info(f"   {i}. {player.name}: {player.current_price:.2f}M (Puntos: {player.points:.2f})")
            
            # Verificar que ninguno supera 85M
            max_price_found = max(p.current_price for p in top_players) if top_players else 0
            if max_price_found > 85.0:
                logger.error(f"\n❌ ERROR: Se encontró un jugador con precio > 85M: {max_price_found:.2f}M")
                logger.error("   Revisar la fórmula de cálculo en sync.py")
            else:
                logger.info(f"\n✅ Validación OK: Precio máximo encontrado: {max_price_found:.2f}M (< 85M)")
            
            logger.info("\n" + "=" * 70)
            logger.info("RECALIBRACIÓN FINALIZADA EXITOSAMENTE")
            logger.info("=" * 70)
            
            # Invalidar caché de jugadores
            if redis:
                await redis.delete("all_players_cache")
                logger.info("\n🗑️  Caché de jugadores invalidada")
            
        except Exception as e:
            logger.error(f"\n❌ ERROR DURANTE RECALIBRACIÓN: {e}")
            logger.error(f"   Tipo: {type(e).__name__}")
            import traceback
            logger.error(f"\n{traceback.format_exc()}")
            sys.exit(1)
        finally:
            await redis.close()
    
    logger.info("\n✨ Script completado. Revisa los logs anteriores para verificar.")


if __name__ == "__main__":
    asyncio.run(main())
