from app.db.session import SessionLocal
from app.db.models.professional import Team, Player, PriceHistoryPlayer
from app.db.models.match import Match, PlayerMatchStats
from app.db.models.league import Roster, LeagueMember
from app.service.sync import SyncService
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("deep_sync_v2")

def reset_and_deep_sync():
    db = SessionLocal()
    try:
        logger.info("--- STARTING REFINED DEEP RESET ---")
        db.query(Roster).delete(synchronize_session=False)
        db.query(PriceHistoryPlayer).delete(synchronize_session=False)
        db.query(PlayerMatchStats).delete(synchronize_session=False)
        db.query(Match).delete(synchronize_session=False)
        db.query(Player).delete(synchronize_session=False)
        db.query(LeagueMember).update({LeagueMember.selected_team_id: None})
        db.query(Team).delete(synchronize_session=False)
        db.commit()
        
        sync = SyncService(db)
        logger.info("Starting refined VCT 2026 Kickoff sync...")
        count = sync.sync_kickoff_2026()
        db.commit()
        
        logger.info(f"--- SYNC COMPLETE ---")
        logger.info(f"Matches: {db.query(Match).count()}")
        logger.info(f"Players: {db.query(Player).count()}")
        logger.info(f"Teams: {db.query(Team).count()}")
        
        # Spot check a completed match
        m = db.query(Match).filter(Match.status == 'completed').first()
        if m:
            print(f"Sample Match: {m.team_a.name} {m.score_team_a}:{m.score_team_b} {m.team_b.name} on {m.date}")
            p_stat = db.query(PlayerMatchStats).filter(PlayerMatchStats.match_id == m.id).first()
            if p_stat:
                print(f"Sample Stat: {p_stat.player.name} | Deaths: {p_stat.death} | Rating: {p_stat.rating}")

    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_and_deep_sync()
