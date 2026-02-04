"""
Force Re-Scrape Specific Matches

This script manually forces re-scraping of specific matches that have TBD teams.
It bypasses the event API and directly scrapes the match detail pages.

Usage:
    python -m app.scripts.force_rescrape_matches
"""

import asyncio
import logging
import sys
from app.db.session import AsyncSessionLocal
from app.service.sync import SyncService
from app.core.redis import RedisCache
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("force_rescrape")

async def force_rescrape_matches():
    """
    Force re-scrape matches with TBD teams.
    """
    # Matches from SQL query - All TBD matches that need fixing
    vlr_match_ids_to_fix = [
        # First batch (already fixed, keeping for reference)
        "594758",  # Team Vitality vs GIANTX
        "594757",  # Natus Vincere vs FNATIC
        "598939",
        "598945",
        "594762",
        "594761",
        "598938",
        "598944",
        # Second batch (new from user screenshot)
        "596416",  # TBD vs Cloud9
        "596415",  # TBD vs 100 Thieves
        "595646",  # TBD vs TBD
        "598943",  # TBD vs TBD
        "595645",  # TBD vs TBD
        "598942",  # TBD vs TBD
        "594756",  # TBD vs TBD
        "594755",  # TBD vs TBD
        "598937",  # TBD vs TBD
        "598936",  # TBD vs TBD
    ]
    
    redis = RedisCache(settings.redis_url)
    
    async with AsyncSessionLocal() as db:
        try:
            sync_service = SyncService(db, redis=redis)
            
            for vlr_id in vlr_match_ids_to_fix:
                logger.info(f"Force scraping match {vlr_id}...")
                
                # Construct match URL
                match_url = f"/{vlr_id}"
                
                # Scrape details directly
                details = await sync_service.scraper.scrape_match_details(match_url)
                
                if not details:
                    logger.error(f"Failed to scrape match {vlr_id}")
                    continue
                
                logger.info(f"Match {vlr_id} - Teams: {[t['name'] for t in details['teams']]}")
                logger.info(f"Match {vlr_id} - Players found: {len(details['players'])}")
                
                # Get existing match
                existing_match = await sync_service.match_service.repo.get_by_vlr_match_id(vlr_id)
                
                if existing_match:
                    logger.info(f"Match {vlr_id} exists in DB, updating...")
                    # Determine event/region from existing data
                    event = {
                        "name": existing_match.tournament_name or "Unknown",
                        "region": "EMEA"  # Assume EMEA for now, can be improved
                    }
                else:
                    logger.info(f"Match {vlr_id} NOT in DB, will create new")
                    event = {
                        "name": "VCT 2026: EMEA Kickoff",
                        "region": "EMEA"
                    }
                
                # Process the match
                await sync_service._sync_match_details(vlr_id, event, details, existing_match)
                
                logger.info(f"✅ Match {vlr_id} processed successfully")
                
                # Wait between requests
                await asyncio.sleep(2)
                
            logger.info("All matches processed!")
            
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
        finally:
            await redis.close()

if __name__ == "__main__":
    asyncio.run(force_rescrape_matches())
