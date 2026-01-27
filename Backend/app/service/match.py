from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models.match import Match, PlayerMatchStats
from app.core.exceptions import AppError
from app.core.constants import ErrorCode
from app.core.decorators import transactional
from app.repository.match import MatchRepository, PlayerMatchStatsRepository

class MatchService:
    '''
    Servicio que maneja la lógica de negocio de partidos.
    
    Responsabilidades:
    - Validación de duplicados (vlr_match_id)
    - Gestión de partidos no procesados
    - CRUD con validaciones de negocio
    '''
    def __init__(self, db: Session):
        self.db = db
        self.repo = MatchRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Match]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_id(self, match_id: int) -> Optional[Match]:
        match = self.repo.get_by_id(match_id)
        if not match:
            raise AppError(404, ErrorCode.NOT_FOUND, "El partido no existe")
        return match

    def get_by_status(self, status: str) -> List[Match]:
        return self.repo.get_by_status(status)

    def get_unprocessed(self) -> List[Match]:
        '''Obtiene partidos completados pero no procesados (para calcular puntos)'''
        return self.repo.get_unprocessed()

    def get_by_team(self, team_id: int) -> List[Match]:
        return self.repo.get_by_team(team_id)

    def get_recent(self, days: int = 7) -> List[Match]:
        return self.repo.get_recent(days)

    @transactional
    def create(self, *, vlr_match_id: str, date=None, status: str = "upcoming",
               tournament_name: Optional[str] = None, stage: Optional[str] = None,
               vlr_url: Optional[str] = None, format: Optional[str] = None,
               team_a_id: Optional[int] = None, team_b_id: Optional[int] = None,
               score_team_a: int = 0, score_team_b: int = 0) -> Match:
        '''
        Crea un nuevo partido validando que el vlr_match_id no esté duplicado.
        '''
        # Validar duplicados
        if self.repo.get_by_vlr_match_id(vlr_match_id):
            raise AppError(409, ErrorCode.DUPLICATED, f"El partido con ID {vlr_match_id} ya existe")
        
        # Crear partido
        match = Match(
            vlr_match_id=vlr_match_id,
            date=date,
            status=status,
            tournament_name=tournament_name,
            stage=stage,
            vlr_url=vlr_url,
            format=format,
            team_a_id=team_a_id,
            team_b_id=team_b_id,
            score_team_a=score_team_a,
            score_team_b=score_team_b
        )
        return self.repo.create(match)

    @transactional
    def update(self, match_id: int, match_data: dict) -> Match:
        '''
        Actualiza un partido.
        '''
        match = self.repo.get_by_id(match_id)
        if not match:
            raise AppError(404, ErrorCode.NOT_FOUND, "El partido no existe")
        
        return self.repo.update(match_id, match_data)

    @transactional
    def mark_as_processed(self, match_id: int) -> Match:
        '''Marca un partido como procesado (después de calcular puntos)'''
        match = self.repo.get_by_id(match_id)
        if not match:
            raise AppError(404, ErrorCode.NOT_FOUND, "El partido no existe")
        
        return self.repo.update(match_id, {"is_processed": True})

    @transactional
    def delete(self, match_id: int) -> None:
        match = self.repo.get_by_id(match_id)
        if not match:
            raise AppError(404, ErrorCode.NOT_FOUND, "El partido no existe")
        
        self.repo.delete(match)


class PlayerMatchStatsService:
    '''
    Servicio que maneja la lógica de negocio de estadísticas de jugadores.
    
    Responsabilidades:
    - Validación de stats (no negativas)
    - Cálculo de fantasy points (implementar fórmula)
    - CRUD con validaciones de negocio
    '''
    def __init__(self, db: Session):
        self.db = db
        self.repo = PlayerMatchStatsRepository(db)

    def get_by_match(self, match_id: int) -> List[PlayerMatchStats]:
        return self.repo.get_by_match(match_id)

    def get_by_player(self, player_id: int) -> List[PlayerMatchStats]:
        return self.repo.get_by_player(player_id)

    def get_recent_by_player(self, player_id: int, limit: int = 5) -> List[PlayerMatchStats]:
        return self.repo.get_by_player_recent(player_id, limit)

    def calculate_fantasy_points(self, stats: PlayerMatchStats, match: Match = None) -> float:
        '''
        Calcula los puntos de fantasy equilibrados (Fórmula v3).
        Reduce carga de stats individuales y añade bonus por victoria/dominio.
        '''
        points = 0.0
        
        # 1. ESTADÍSTICAS INDIVIDUALES (Pesos equilibrados)
        points += stats.kills * 0.75
        points -= stats.death * 0.5
        points += stats.assists * 0.3
        
        # Impacto (Entry frags / Clutches)
        points += stats.first_kills * 1.5
        points -= stats.first_deaths * 1.2
        points += stats.clutches_won * 3.0
        
        # Impacto en Daño (ADR / 10 = 1 punto)
        if stats.adr:
            points += (stats.adr / 10.0)
            
        # Bonus por Rating (Eficiencia)
        if stats.rating > 1.10:
            points += (stats.rating - 1.10) * 10
        
        # 2. BONUS POR RESULTADO (Si tenemos el contexto del partido)
        if match and match.status == "completed":
            from app.db.models.professional import Player
            player = self.db.query(Player).filter(Player.id == stats.player_id).first()
            if player and player.team_id:
                # Determinar si el jugador ganó
                won = False
                is_sweep = False
                is_close = False
                
                # Obtener scores
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
                
                # Aplicar Bonus de Victoria
                if won:
                    points += 7.0 # Base victoria
                    if is_sweep: points += 5.0 # Extra por 2-0 / 3-0
                    if is_close: points += 2.0 # Extra por sufrimiento
        
        # Reducción global del 65% (factor 0.35)
        points = points * 0.35
        
        return round(points, 2)

    @transactional
    def create(self, *, match_id: int, player_id: int, agent: Optional[str] = None,
               kills: int = 0, death: int = 0, assists: int = 0,
               acs: float = 0.0, adr: float = 0.0, kast: float = 0.0,
               hs_percent: float = 0.0, rating: float = 0.0,
               first_kills: int = 0, first_deaths: int = 0, clutches_won: int = 0) -> PlayerMatchStats:
        '''
        Crea estadísticas de un jugador en un partido y calcula puntos de fantasy.
        '''
        # Crear stats
        stats = PlayerMatchStats(
            match_id=match_id,
            player_id=player_id,
            agent=agent,
            kills=kills,
            death=death,
            assists=assists,
            acs=acs,
            adr=adr,
            kast=kast,
            hs_percent=hs_percent,
            rating=rating,
            first_kills=first_kills,
            first_deaths=first_deaths,
            clutches_won=clutches_won
        )
        
        # Calcular fantasy points equilibrados
        from app.repository.match import MatchRepository
        match_repo = MatchRepository(self.db)
        match = match_repo.get_by_id(match_id)
        
        stats.fantasy_points_earned = self.calculate_fantasy_points(stats, match)
        
        return self.repo.create(stats)

    @transactional
    def update(self, stats_id: int, stats_data: dict) -> PlayerMatchStats:
        '''
        Actualiza estadísticas y recalcula puntos de fantasy.
        '''
        stats = self.repo.get_by_id(stats_id)
        if not stats:
            raise AppError(404, ErrorCode.NOT_FOUND, "Estadísticas no encontradas")
        
        # Actualizar
        updated_stats = self.repo.update(stats_id, stats_data)
        
        # Recalcular fantasy points equilibrados
        from app.repository.match import MatchRepository
        match_repo = MatchRepository(self.db)
        match = match_repo.get_by_id(updated_stats.match_id)
        
        updated_stats.fantasy_points_earned = self.calculate_fantasy_points(updated_stats, match)
        self.db.commit()
        
        return updated_stats

    @transactional
    def delete(self, stats_id: int) -> None:
        stats = self.repo.get_by_id(stats_id)
        if not stats:
            raise AppError(404, ErrorCode.NOT_FOUND, "Estadísticas no encontradas")
        
        self.repo.delete(stats)
