from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Any
from sqlalchemy.orm import joinedload
import logging
from app.db.models.match import Match, PlayerMatchStats
from app.core.exceptions import AppError
from app.core.constants import ErrorCode
from app.core.decorators import transactional
from app.repository.match import MatchRepository, PlayerMatchStatsRepository
from app.core.redis import RedisCache
from app.schemas.match import PlayerMatchStatsOut, MatchOut

logger = logging.getLogger(__name__)

class MatchService:
    '''
    Servicio que maneja la lógica de negocio de partidos (Asíncrono).
    Se encarga de crear, actualizar, obtener y borrar partidos, además de gestionar las consultas con filtros.
    
    Implementa caché selectiva para partidos completados (datos inmutables).
    '''
    CACHE_KEY_PREFIX = "match_detail:"
    
    def __init__(self, db: AsyncSession, redis: Optional[RedisCache] = None):
        self.db = db
        self.repo = MatchRepository(db)
        self.redis = redis

    def _get_match_options(self):
        # Opciones de carga ansiosa (Eager Loading) para optimizar consultas de partidos
        return [
            joinedload(Match.team_a),
            joinedload(Match.team_b),
            joinedload(Match.player_stats).joinedload(PlayerMatchStats.player)
        ]

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Match]:
        return await self.repo.get_all(skip=skip, limit=limit, options=self._get_match_options())

    async def get_by_id(self, match_id: int) -> Optional[Any]:
        """
        Obtiene un partido por ID con caché condicional.
        
        REGLA: Solo cachea partidos completados (status == "completed") sin TTL,
        ya que los datos históricos son inmutables. Los partidos "upcoming" o "live"
        no se cachean para garantizar datos en tiempo real.
        """
        cache_key = f"{self.CACHE_KEY_PREFIX}{match_id}"
        
        # Intentar obtener de caché
        if self.redis:
            cached_response = await self.redis.get(cache_key)
            if cached_response and "success" in cached_response:
                match_data = cached_response.get("data")
                logger.info(f"CACHE_HIT: Match {match_id} found in Redis")
                return match_data
        
        # Caché miss o Redis no disponible: consultar DB
        logger.info(f"CACHE_MISS: Fetching match {match_id} from database")
        match = await self.repo.get_by_id(match_id, options=self._get_match_options())
        if not match:
            raise AppError(404, ErrorCode.NOT_FOUND, "El partido no existe")
        
        # REGLA: Solo cachear partidos completados (inmutables)
        if self.redis and match.status == "completed":
            # Usar schema para serialización correcta (maneja relaciones y datetime)
            match_dict = MatchOut.model_validate(match).model_dump(mode='json')
            await self.redis.set(
                cache_key,
                {"success": True, "data": match_dict}
                # Sin TTL - datos inmutables una vez completados
            )
            logger.info(f"Match {match_id} cached (status: completed)")
        elif match.status != "completed":
            logger.info(f"Match {match_id} NOT cached (status: {match.status} - datos cambiantes)")
        
        return match

    async def get_by_status(self, status: str) -> List[Match]:
        return await self.repo.get_by_status(status, options=self._get_match_options())

    async def get_unprocessed(self) -> List[Match]:
        # Obtiene partidos completados que aún no se han procesado (cálculo de puntos)
        return await self.repo.get_unprocessed()

    async def get_by_team(self, team_id: int) -> List[Match]:
        return await self.repo.get_by_team(team_id, options=self._get_match_options())

    async def get_recent(self, days: int = 7) -> List[Match]:
        # Obtiene partidos de los últimos N días
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
        
        # Validación de duplicados por ID de VLR
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
        
        updated_match = await self.repo.update(match_id, match_data, options=self._get_match_options())
        
        # Invalidar caché si existe (el match puede haber cambiado de estado o datos)
        if self.redis:
            cache_key = f"{self.CACHE_KEY_PREFIX}{match_id}"
            await self.redis.delete(cache_key)
            logger.info(f"Cache invalidated for match {match_id} after update")
        
        return updated_match

    @transactional
    async def mark_as_processed(self, match_id: int) -> Match:
        # Marca un partido como procesado para evitar recálculos innecesarios
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
    
    Implementa caché con TTL para estadísticas de partidos (datos inmutables una vez procesados).
    '''
    CACHE_KEY_PREFIX = "stats:match:"
    CACHE_TTL_SECONDS = 86400  # 24 horas
    
    def __init__(self, db: AsyncSession, redis: Optional[RedisCache] = None):
        self.db = db
        self.repo = PlayerMatchStatsRepository(db)
        self.redis = redis

    async def get_by_match(self, match_id: int) -> List[Any]:
        """
        Obtiene estadísticas de un partido con caché (TTL 24h).
        
        Partidos completados son inmutables, por lo que la caché es efectiva y reduce carga en la DB.
        """
        cache_key = f"{self.CACHE_KEY_PREFIX}{match_id}"
        
        # Intentar obtener de caché
        if self.redis:
            cached_response = await self.redis.get(cache_key)
            if cached_response and "success" in cached_response:
                stats_data = cached_response.get("data", [])
                logger.info(f"CACHE_HIT: Stats for match {match_id} found in Redis ({len(stats_data)} players)")
                return stats_data
        
        # Caché miss o Redis no disponible: consultar DB
        logger.info(f"CACHE_MISS: Fetching stats for match {match_id} from database")
        stats = await self.repo.get_by_match(match_id, options=[joinedload(PlayerMatchStats.player)])
        
        # Guardar en caché con TTL de 24 horas
        if self.redis and stats:
            # Usar schema para serialización correcta (maneja relaciones como player)
            stats_dict = [PlayerMatchStatsOut.model_validate(stat).model_dump() for stat in stats]
            await self.redis.set(
                cache_key,
                {"success": True, "data": stats_dict},
                ttl=self.CACHE_TTL_SECONDS
            )
        
        return stats

    async def get_by_player(self, player_id: int) -> List[PlayerMatchStats]:
        return await self.repo.get_by_player(player_id, options=[joinedload(PlayerMatchStats.player)])

    async def get_recent_by_player(self, player_id: int, limit: int = 5) -> List[PlayerMatchStats]:
        return await self.repo.get_by_player_recent(player_id, limit, options=[joinedload(PlayerMatchStats.player)])

    async def calculate_fantasy_points(self, stats: PlayerMatchStats, match: Match = None) -> float:
        """
        Calcula los puntos de fantasía para un jugador en un partido específico.
        
        NUEVA FÓRMULA V2 (0-20 puntos máx):
        - Estadísticas base (K/D/A): hasta 8 puntos
        - Performance (ACS, ADR, Rating): hasta 7 puntos
        - Clutch & Impact (FK, FD, Clutches): hasta 3 puntos
        - Resultado del partido (Victoria/Sweep): hasta 2 puntos
        """
        points = 0.0
        
        # =================================================================
        # 1. ESTADÍSTICAS BASE (hasta 8 puntos)
        # =================================================================
        # K/D Ratio ponderado - enfoque en impacto neto
        kd_ratio = stats.kills / max(stats.death, 1)
        
        # Kills base: 0.3 por kill (aprox 20 kills = 6 pts)
        points += stats.kills * 0.30
        
        # Penalidad por muertes: -0.25 por death
        points += stats.death * -0.25
        
        # Assists: 0.2 por asistencia (aprox 5 assists = 1 pt)
        points += stats.assists * 0.20
        
        # Bonus si K/D > 2.0 (jugador dominante)
        if kd_ratio >= 2.0:
            points += (kd_ratio - 2.0) * 1.5  # Aprox +1-2 pts para K/D muy alto
        
        # =================================================================
        # 2. PERFORMANCE METRICS (hasta 7 puntos)
        # =================================================================
        # ACS (Average Combat Score): Indicador clave de impacto
        if stats.acs >= 300:
            points += 3.0  # ACS excepcional
        elif stats.acs >= 250:
            points += 2.0  # ACS alto
        elif stats.acs >= 200:
            points += 1.0  # ACS sólido
        elif stats.acs >= 150:
            points += 0.5  # ACS promedio
        
        # ADR (Average Damage per Round): Consistencia de daño
        if stats.adr >= 120:
            points += 2.0  # ADR elite
        elif stats.adr >= 100:
            points += 1.5  # ADR alto
        elif stats.adr >= 80:
            points += 1.0  # ADR bueno
        elif stats.adr >= 60:
            points += 0.5  # ADR promedio
        
        # VLR Rating: Métrica compuesta de VLR
        if stats.rating >= 1.30:
            points += 2.5  # Rating excepcional (MVP candidate)
        elif stats.rating >= 1.15:
            points += 1.5  # Rating muy bueno
        elif stats.rating >= 1.00:
            points += 0.75  # Rating positivo
        elif stats.rating >= 0.85:
            points += 0.25  # Rating aceptable
        # No penalidad por rating bajo (ya se refleja en K/D)
        
        # =================================================================
        # 3. CLUTCH & IMPACT PLAYS (hasta 3 puntos)
        # =================================================================
        # First Kills: Iniciar rondas con ventaja es clave
        points += stats.first_kills * 0.8  # 2-3 FK = 1.6-2.4 pts
        
        # First Deaths: Penaliza morir primero (pone en desventaja al equipo)
        points += stats.first_deaths * -0.6
        
        # Clutches Won: Jugadas de altísimo valor
        points += stats.clutches_won * 1.5  # 1-2 clutches = 1.5-3 pts
        
        # =================================================================
        # 4. BONUS POR RESULTADO (hasta 2 puntos)
        # =================================================================
        if match and match.status == "completed":
            from app.db.models.professional import Player
            query = select(Player).where(Player.id == stats.player_id)
            result = await self.db.execute(query)
            player = result.scalars().first()
            
            if player and player.team_id:
                won = False
                is_sweep = False
                
                s_a = match.score_team_a or 0
                s_b = match.score_team_b or 0
                
                if player.team_id == match.team_a_id:
                    if s_a > s_b:
                        won = True
                        if s_b == 0: is_sweep = True
                elif player.team_id == match.team_b_id:
                    if s_b > s_a:
                        won = True
                        if s_a == 0: is_sweep = True
                
                if won:
                    points += 1.5  # Bonus por victoria
                    if is_sweep:
                        points += 0.5  # Bonus adicional por sweep (2-0 o 3-0)
        
        # =================================================================
        # LIMITACIÓN FINAL: Cap a 20 puntos
        # =================================================================
        points = min(points, 20.0)
        points = max(points, 0.0)  # No permitir puntos negativos
        
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
        
        # Calcula puntos al crear la estadística
        stats.fantasy_points_earned = await self.calculate_fantasy_points(stats, match)
        
        # Use options to ensure player is loaded if we return it in response (typically stats out includes player)
        created_stats = await self.repo.create(stats, options=[joinedload(PlayerMatchStats.player)])
        
        # Invalidar caché de este partido si existe (datos cambiaron)
        if self.redis:
            cache_key = f"{self.CACHE_KEY_PREFIX}{match_id}"
            await self.redis.delete(cache_key)
            logger.info(f"Cache invalidated for match {match_id} after stats creation")
        
        return created_stats

    @transactional
    async def update(self, stats_id: int, stats_data: dict) -> PlayerMatchStats:
        stats = await self.repo.get(stats_id)
        if not stats:
            raise AppError(404, ErrorCode.NOT_FOUND, "Estadísticas no encontradas")
        
        updated_stats = await self.repo.update(stats_id, stats_data, options=[joinedload(PlayerMatchStats.player)])
        
        match_repo = MatchRepository(self.db)
        match = await match_repo.get_by_id(updated_stats.match_id)
        
        # Recalcular puntos al actualizar
        new_points = await self.calculate_fantasy_points(updated_stats, match)
        if new_points != updated_stats.fantasy_points_earned:
             updated_stats = await self.repo.update(stats_id, {"fantasy_points_earned": new_points}, options=[joinedload(PlayerMatchStats.player)])
             
        return updated_stats

    @transactional
    async def delete(self, stats_id: int) -> None:
        if not await self.repo.delete(stats_id):
             raise AppError(404, ErrorCode.NOT_FOUND, "Estadísticas no encontradas")
