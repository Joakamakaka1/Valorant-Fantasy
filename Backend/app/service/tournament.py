from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.repository.tournament import TournamentRepository, TournamentTeamRepository
from app.core.decorators import transactional
from app.db.models.tournament import Tournament, TournamentStatus
from app.service.vlr_scraper import VLRScraper
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class TournamentService:
    """
    Servicio para gestionar torneos.
    
    Responsabilidades:
    - Sincronizar torneos desde VLR.gg
    - Actualizar estado de torneos (upcoming/ongoing/completed)
    - Gestionar equipos participantes
    """
    
    def __init__(self, db: AsyncSession, scraper: Optional[VLRScraper] = None):
        self.db = db
        self.repo = TournamentRepository(db)
        self.team_repo = TournamentTeamRepository(db)
        self.scraper = scraper or VLRScraper()
    
    @transactional
    async def sync_tournaments_from_vlr(self):
        """
        Sincroniza torneos desde https://www.vlr.gg/events/?tier=60
        
        - Crea nuevos torneos si no existen
        - Actualiza status de torneos existentes
        - Scrapear equipos participantes para torneos "ongoing"
        
        Returns:
            int: Número de torneos procesados
        """
        logger.info("🔄 Syncing tournaments from VLR.gg events page...")
        
        events = await self.scraper.scrape_events_page()
        processed_count = 0
        
        for event_data in events:
            try:
                vlr_event_id = event_data["vlr_event_id"]
                tournament = await self.repo.get_by_vlr_event_id(vlr_event_id)
                
                if not tournament:
                    # Crear nuevo torneo
                    tournament = Tournament(
                        name=event_data["name"],
                        vlr_event_id=vlr_event_id,
                        vlr_event_path=event_data["vlr_event_path"],
                        status=TournamentStatus(event_data["status"]),
                        start_date=datetime.utcnow(),  # Placeholder, actualizar con parsing de dates
                        created_at=datetime.utcnow(),
                        last_scraped_at=datetime.utcnow()
                    )
                    tournament = await self.repo.create(tournament)
                    logger.info(f"  ✅ Created tournament: {tournament.name} ({tournament.status.value})")
                else:
                    # Actualizar status si cambió
                    new_status = TournamentStatus(event_data["status"])
                    if tournament.status != new_status:
                        old_status = tournament.status.value
                        tournament = await self.repo.update(tournament.id, {
                            "status": new_status,
                            "last_scraped_at": datetime.utcnow()
                        })
                        logger.info(f"  🔄 {tournament.name}: {old_status} → {new_status.value}")
                        
                        # Si cambió a "completed", se pueden otorgar recompensas
                        # (se manejará en el Worker)
                    else:
                        # Solo actualizar last_scraped_at
                        await self.repo.update(tournament.id, {
                            "last_scraped_at": datetime.utcnow()
                        })
                
                # Si está ongoing, scrapear equipos participantes
                if event_data["status"] == "ONGOING":  # Now uppercase after scraper fix
                    await self._update_tournament_teams(tournament)
                
                processed_count += 1
            
            except Exception as e:
                logger.error(f"Error processing tournament {event_data['name']}: {e}")
                continue
        
        logger.info(f"✅ Tournament sync complete: {processed_count} tournaments processed")
        return processed_count
    
    @transactional
    async def _update_tournament_teams(self, tournament: Tournament):
        """
        Actualiza los equipos participantes de un torneo ongoing.
        
        Args:
            tournament: Instancia de Tournament
        """
        logger.info(f"  📋 Updating teams for {tournament.name}...")
        
        # Scrapear equipos desde la página del torneo
        team_names = await self.scraper.scrape_tournament_teams(tournament.vlr_event_path)
        
        if not team_names:
            logger.warning(f"    ⚠️  No teams found for {tournament.name}")
            return
        
        # Obtener equipos desde la BD
        from app.service.professional import TeamService
        team_service = TeamService(self.db)
        
        teams_added = 0
        
        for team_name in team_names:
            try:
                # Buscar equipo por nombre
                team = await team_service.get_by_name(team_name)
                if not team:
                    logger.warning(f"    ⚠️  Team not found in DB: {team_name}")
                    continue
                
                # Verificar si ya existe la relación
                exists = await self.team_repo.exists(tournament.id, team.id)
                if exists:
                    continue
                
                # Crear relación
                await self.team_repo.create(tournament.id, team.id)
                teams_added += 1
            
            except Exception as e:
                logger.error(f"    ❌ Error adding team {team_name}: {e}")
                continue
        
        logger.info(f"    ✅ Added {teams_added} teams to {tournament.name}")
    
    async def get_ongoing_tournament(self) -> Optional[Tournament]:
        """Obtiene el torneo actualmente ongoing."""
        return await self.repo.get_ongoing_tournament()
    
    async def get_all_tournaments(self, skip: int = 0, limit: int = 100) -> List[Tournament]:
        """Lista todos los torneos."""
        return await self.repo.get_all(skip=skip, limit=limit)
