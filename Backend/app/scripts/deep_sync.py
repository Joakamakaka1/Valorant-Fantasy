from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, update, select, func
from app.db.session import AsyncSessionLocal
from app.db.models.professional import Team, Player, PriceHistoryPlayer
from app.db.models.match import Match, PlayerMatchStats
from app.db.models.league import Roster, LeagueMember
from app.service.sync import SyncService
import logging
import sys
import asyncio

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("deep_sync_v2")

async def reset_and_deep_sync():
    async with AsyncSessionLocal() as db:
        try:
            logger.info("--- STARTING REFINED DEEP RESET (Async) ---")
            await db.execute(delete(Roster))
            await db.execute(delete(PriceHistoryPlayer))
            await db.execute(delete(PlayerMatchStats))
            await db.execute(delete(Match))
            await db.execute(delete(Player))
            await db.execute(update(LeagueMember).values(selected_team_id=None))
            await db.execute(delete(Team))
            await db.commit()
            
            sync = SyncService(db)
            logger.info("Starting refined VCT 2026 Kickoff sync...")
            count = await sync.sync_kickoff_2026()
            await db.commit()
            
            logger.info(f"--- SYNC COMPLETE ---")
            
            # Counts
            res_m = await db.execute(select(func.count(Match.id)))
            res_p = await db.execute(select(func.count(Player.id)))
            res_t = await db.execute(select(func.count(Team.id)))
            
            logger.info(f"Matches count: {res_m.scalar()}")
            logger.info(f"Players count: {res_p.scalar()}")
            logger.info(f"Teams count: {res_t.scalar()}")
            
            # Spot check
            q_sample = select(Match).where(Match.status == 'completed').limit(1)
            res_sample = await db.execute(q_sample)
            m = res_sample.scalar_one_or_none()
            if m:
                # Need to load relationships if needed, but selectinload etc. would be better
                # For a script, we can just fetch specifically if needed
                pass

        except Exception as e:
            logger.error(f"Error: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(reset_and_deep_sync())
