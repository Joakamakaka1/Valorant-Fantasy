from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.tournament import Tournament, TournamentTeam, TournamentStatus
from app.repository.base import BaseRepository
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class TournamentRepository(BaseRepository[Tournament]):
    """Repositorio para operaciones de base de datos con torneos."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Tournament, db)
    
    async def get_by_vlr_event_id(self, vlr_event_id: int) -> Optional[Tournament]:
        """Busca un torneo por su ID de VLR.gg."""
        query = select(Tournament).where(Tournament.vlr_event_id == vlr_event_id)
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_by_status(self, status: TournamentStatus) -> List[Tournament]:
        """Obtiene todos los torneos con un status específico."""
        query = select(Tournament).where(Tournament.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_ongoing_tournament(self) -> Optional[Tournament]:
        """Obtiene el torneo actualmente ongoing (solo debería haber 1)."""
        query = select(Tournament).where(Tournament.status == TournamentStatus.ONGOING)
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def update_status(self, tournament_id: int, new_status: TournamentStatus) -> Tournament:
        """Actualiza el status de un torneo."""
        return await self.update(tournament_id, {"status": new_status})


class TournamentTeamRepository:
    """Repositorio para la relación many-to-many entre torneos y equipos."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, tournament_id: int, team_id: int) -> TournamentTeam:
        """Crea una relación torneo-equipo."""
        tournament_team = TournamentTeam(
            tournament_id=tournament_id,
            team_id=team_id
        )
        self.db.add(tournament_team)
        await self.db.flush()
        return tournament_team
    
    async def get_teams_for_tournament(self, tournament_id: int) -> List[int]:
        """Obtiene IDs de equipos participantes en un torneo."""
        query = select(TournamentTeam.team_id).where(
            TournamentTeam.tournament_id == tournament_id
        )
        result = await self.db.execute(query)
        return [row[0] for row in result.all()]
    
    async def exists(self, tournament_id: int, team_id: int) -> bool:
        """Verifica si ya existe la relación torneo-equipo."""
        query = select(TournamentTeam).where(
            TournamentTeam.tournament_id == tournament_id,
            TournamentTeam.team_id == team_id
        )
        result = await self.db.execute(query)
        return result.scalars().first() is not None
    
    async def delete_all_for_tournament(self, tournament_id: int):
        """Elimina todas las relaciones de un torneo (para re-sync)."""
        query = delete(TournamentTeam).where(
            TournamentTeam.tournament_id == tournament_id
        )
        await self.db.execute(query)
