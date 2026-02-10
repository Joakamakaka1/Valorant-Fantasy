from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from app.core.decorators import transactional
from app.db.models.professional import Player
from app.db.models.tournament import Tournament
from app.repository.tournament import TournamentTeamRepository
from typing import List
import logging

logger = logging.getLogger(__name__)


class PlayerActivationService:
    """
    Servicio para gestionar activación/desactivación de jugadores según torneos.
    
    Lógica:
    - Jugadores de equipos participantes en torneo ongoing → current_tournament_id = tournament.id (ACTIVOS)
    - Resto de jugadores → current_tournament_id = NULL (INACTIVOS)
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.team_repo = TournamentTeamRepository(db)
    
    @transactional
    async def activate_players_for_tournament(self, tournament_id: int) -> dict:
        """
        Activa jugadores que participan en el torneo, desactiva el resto.
        
        Args:
            tournament_id: ID del torneo ongoing
        
        Returns:
            dict: {"activated": int, "deactivated": int}
        """
        logger.info(f"🔄 Activating players for tournament {tournament_id}...")
        
        # 1. Obtener IDs de equipos participantes
        participating_team_ids = await self.team_repo.get_teams_for_tournament(tournament_id)
        
        if not participating_team_ids:
            logger.warning(f"  ⚠️  No participating teams found for tournament {tournament_id}")
            return {"activated": 0, "deactivated": 0}
        
        logger.info(f"  📋 {len(participating_team_ids)} teams participating")
        
        # 2. Activar jugadores de equipos participantes
        query_activate = (
            update(Player)
            .where(Player.team_id.in_(participating_team_ids))
            .values(current_tournament_id=tournament_id)
        )
        result_activate = await self.db.execute(query_activate)
        activated_count = result_activate.rowcount
        
        # 3. Desactivar jugadores de equipos NO participantes
        query_deactivate = (
            update(Player)
            .where(~Player.team_id.in_(participating_team_ids))
            .values(current_tournament_id=None)
        )
        result_deactivate = await self.db.execute(query_deactivate)
        deactivated_count = result_deactivate.rowcount
        
        await self.db.flush()
        
        logger.info(f"  ✅ Players activated: {activated_count}, deactivated: {deactivated_count}")
        
        return {
            "activated": activated_count,
            "deactivated": deactivated_count
        }
    
    @transactional
    async def deactivate_all_players(self) -> int:
        """
        Desactiva TODOS los jugadores (cuando no hay torneo ongoing).
        
        Returns:
            int: Número de jugadores desactivados
        """
        logger.info("🔄 Deactivating all players (no ongoing tournament)...")
        
        query = update(Player).values(current_tournament_id=None)
        result = await self.db.execute(query)
        
        await self.db.flush()
        
        logger.info(f"  ✅ Deactivated {result.rowcount} players")
        return result.rowcount
    
    async def get_active_players_count(self, tournament_id: int) -> int:
        """Obtiene el número de jugadores activos en un torneo."""
        query = select(Player).where(Player.current_tournament_id == tournament_id)
        result = await self.db.execute(query)
        players = result.scalars().all()
        return len(players)
