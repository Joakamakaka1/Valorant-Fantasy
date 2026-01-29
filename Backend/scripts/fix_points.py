import asyncio
import logging
from app.db.session import AsyncSessionLocal
from app.service.sync import SyncService
from app.db.models.match import Match
from app.db.models.professional import Player
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix-points")

async def fix_player_points():
    async with AsyncSessionLocal() as db:
        sync_service = SyncService(db)
        
        # 1. Obtener todos los jugadores
        q_players = select(Player)
        res_players = await db.execute(q_players)
        players = res_players.scalars().all()
        
        logger.info(f"Recalculating points for {len(players)} players...")
        
        for player in players:
            from app.db.models.match import PlayerMatchStats
            
            # Recalcular desde estadísticas completadas
            q_stats = (
                select(PlayerMatchStats)
                .options(selectinload(PlayerMatchStats.match))
                .join(Match)
                .where(PlayerMatchStats.player_id == player.id, Match.status == "completed")
            )
            res_stats = await db.execute(q_stats)
            all_stats = res_stats.scalars().all()
            
            total_points = sum(s.fantasy_points_earned for s in all_stats)
            total_matches = len(all_stats)
            new_price = sync_service.calculate_new_price(all_stats)
            
            # Actualizar
            player.points = round(total_points, 2)
            player.matches_played = total_matches
            player.current_price = new_price
            
            if total_points > 0:
                logger.info(f"Fixed {player.name}: {total_points} pts, {total_matches} matches")
        
        await db.commit()
        logger.info("Recalculation complete. Database is now consistent.")

if __name__ == "__main__":
    asyncio.run(fix_player_points())
