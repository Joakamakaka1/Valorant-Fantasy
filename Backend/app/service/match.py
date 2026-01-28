from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from sqlalchemy.orm import joinedload
from app.db.models.match import Match, PlayerMatchStats
from app.core.exceptions import AppError
from app.core.constants import ErrorCode
from app.core.decorators import transactional
from app.repository.match import MatchRepository, PlayerMatchStatsRepository

class MatchService:
    '''
    Servicio que maneja la lógica de negocio de partidos (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MatchRepository(db)

    def _get_match_options(self):
        return [
            joinedload(Match.team_a),
            joinedload(Match.team_b),
            joinedload(Match.player_stats).joinedload(PlayerMatchStats.player)
        ]

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Match]:
        return await self.repo.get_all(skip=skip, limit=limit, options=self._get_match_options())

    async def get_by_id(self, match_id: int) -> Optional[Match]:
        match = await self.repo.get_by_id(match_id, options=self._get_match_options())
        if not match:
            raise AppError(404, ErrorCode.NOT_FOUND, "El partido no existe")
        return match

    async def get_by_status(self, status: str) -> List[Match]:
        return await self.repo.get_by_status(status, options=self._get_match_options())

    async def get_unprocessed(self) -> List[Match]:
        return await self.repo.get_unprocessed()

    async def get_by_team(self, team_id: int) -> List[Match]:
        return await self.repo.get_by_team(team_id, options=self._get_match_options())

    async def get_recent(self, days: int = 7) -> List[Match]:
        return await self.repo.get_recent(days, options=self._get_match_options())
    
    async def get_matches_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        team_id: Optional[int] = None,
        unprocessed: bool = False,
        recent_days: Optional[int] = None
    ) -> List[Match]:
        """
        Método helper para obtener partidos con filtros múltiples.
        
        Centraliza la lógica de filtrado que antes estaba en el endpoint.
        Prioridad: unprocessed > status_filter > team_id > recent_days > paginación
        """
        if unprocessed:
            return await self.get_unprocessed()
        if status_filter:
            return await self.get_by_status(status_filter)
        if team_id:
            return await self.get_by_team(team_id)
        if recent_days:
            return await self.get_recent(days=recent_days)
        
        return await self.get_all(skip=skip, limit=limit)

    @transactional
    async def create(self, *, vlr_match_id: str, date=None, status: str = "upcoming",
               tournament_name: Optional[str] = None, stage: Optional[str] = None,
               vlr_url: Optional[str] = None, format: Optional[str] = None,
               team_a_id: Optional[int] = None, team_b_id: Optional[int] = None,
               score_team_a: int = 0, score_team_b: int = 0) -> Match:
        if await self.repo.get_by_vlr_match_id(vlr_match_id):
            raise AppError(409, ErrorCode.DUPLICATED, f"El partido con ID {vlr_match_id} ya existe")
        
        match = Match(
            vlr_match_id=vlr_match_id, date=date, status=status,
            tournament_name=tournament_name, stage=stage, vlr_url=vlr_url,
            format=format, team_a_id=team_a_id, team_b_id=team_b_id,
            score_team_a=score_team_a, score_team_b=score_team_b
        )
        return await self.repo.create(match)

    @transactional
    async def update(self, match_id: int, match_data: dict) -> Match:
        match = await self.repo.get(match_id)
        if not match:
            raise AppError(404, ErrorCode.NOT_FOUND, "El partido no existe")
        return await self.repo.update(match_id, match_data, options=self._get_match_options())

    @transactional
    async def mark_as_processed(self, match_id: int) -> Match:
        match = await self.repo.get(match_id)
        if not match:
            raise AppError(404, ErrorCode.NOT_FOUND, "El partido no existe")
        return await self.repo.update(match_id, {"is_processed": True}, options=self._get_match_options())

    @transactional
    async def delete(self, match_id: int) -> None:
        if not await self.repo.delete(match_id):
             raise AppError(404, ErrorCode.NOT_FOUND, "El partido no existe")


class PlayerMatchStatsService:
    '''
    Servicio que maneja la lógica de negocio de estadísticas de jugadores (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PlayerMatchStatsRepository(db)

    async def get_by_match(self, match_id: int) -> List[PlayerMatchStats]:
        return await self.repo.get_by_match(match_id, options=[joinedload(PlayerMatchStats.player)])

    async def get_by_player(self, player_id: int) -> List[PlayerMatchStats]:
        return await self.repo.get_by_player(player_id, options=[joinedload(PlayerMatchStats.player)])

    async def get_recent_by_player(self, player_id: int, limit: int = 5) -> List[PlayerMatchStats]:
        return await self.repo.get_by_player_recent(player_id, limit, options=[joinedload(PlayerMatchStats.player)])

    async def calculate_fantasy_points(self, stats: PlayerMatchStats, match: Match = None) -> float:
        points = 0.0
        
        # 1. ESTADÍSTICAS INDIVIDUALES
        points += stats.kills * 0.75
        points -= stats.death * 0.5
        points += stats.assists * 0.3
        points += stats.first_kills * 1.5
        points -= stats.first_deaths * 1.2
        points += stats.clutches_won * 3.0
        
        if stats.adr:
            points += (stats.adr / 10.0)
            
        if stats.rating > 1.10:
            points += (stats.rating - 1.10) * 10
        
        # 2. BONUS POR RESULTADO
        if match and match.status == "completed":
            from app.db.models.professional import Player
            query = select(Player).where(Player.id == stats.player_id)
            result = await self.db.execute(query)
            player = result.scalars().first()
            
            if player and player.team_id:
                won = False
                is_sweep = False
                is_close = False
                
                s_a = match.score_team_a or 0
                s_b = match.score_team_b or 0
                
                if player.team_id == match.team_a_id:
                    if s_a > s_b: 
                        won = True
                        if s_b == 0: is_sweep = True
                        elif s_a - s_b == 1: is_close = True
                elif player.team_id == match.team_b_id:
                    if s_b > s_a: 
                        won = True
                        if s_a == 0: is_sweep = True
                        elif s_b - s_a == 1: is_close = True
                
                if won:
                    points += 7.0
                    if is_sweep: points += 5.0
                    if is_close: points += 2.0
        
        points = points * 0.35
        return round(points, 2)

    @transactional
    async def create(self, *, match_id: int, player_id: int, agent: Optional[str] = None,
               kills: int = 0, death: int = 0, assists: int = 0,
               acs: float = 0.0, adr: float = 0.0, kast: float = 0.0,
               hs_percent: float = 0.0, rating: float = 0.0,
               first_kills: int = 0, first_deaths: int = 0, clutches_won: int = 0) -> PlayerMatchStats:
        stats = PlayerMatchStats(
            match_id=match_id, player_id=player_id, agent=agent,
            kills=kills, death=death, assists=assists,
            acs=acs, adr=adr, kast=kast,
            hs_percent=hs_percent, rating=rating,
            first_kills=first_kills, first_deaths=first_deaths, clutches_won=clutches_won
        )
        
        match_repo = MatchRepository(self.db)
        match = await match_repo.get_by_id(match_id)
        
        stats.fantasy_points_earned = await self.calculate_fantasy_points(stats, match)
        
        # Use options to ensure player is loaded if we return it in response (typically stats out includes player)
        return await self.repo.create(stats, options=[joinedload(PlayerMatchStats.player)])

    @transactional
    async def update(self, stats_id: int, stats_data: dict) -> PlayerMatchStats:
        stats = await self.repo.get(stats_id)
        if not stats:
            raise AppError(404, ErrorCode.NOT_FOUND, "Estadísticas no encontradas")
        
        updated_stats = await self.repo.update(stats_id, stats_data, options=[joinedload(PlayerMatchStats.player)])
        
        match_repo = MatchRepository(self.db)
        match = await match_repo.get_by_id(updated_stats.match_id)
        
        # Recalculate points
        new_points = await self.calculate_fantasy_points(updated_stats, match)
        if new_points != updated_stats.fantasy_points_earned:
             updated_stats = await self.repo.update(stats_id, {"fantasy_points_earned": new_points}, options=[joinedload(PlayerMatchStats.player)])
             
        return updated_stats

    @transactional
    async def delete(self, stats_id: int) -> None:
        if not await self.repo.delete(stats_id):
             raise AppError(404, ErrorCode.NOT_FOUND, "Estadísticas no encontradas")
