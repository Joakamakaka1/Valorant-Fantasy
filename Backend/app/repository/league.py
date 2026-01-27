from sqlalchemy.orm import Session, joinedload
from app.db.models.league import League, LeagueMember, Roster
from typing import List, Optional

class LeagueRepository:
    '''
    Repositorio de ligas - Capa de acceso a datos.
    '''
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[League]:
        return (
            self.db.query(League)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, league_id: int) -> Optional[League]:
        return (
            self.db.query(League)
            .filter(League.id == league_id)
            .first()
        )

    def get_by_invite_code(self, invite_code: str) -> Optional[League]:
        """Obtener liga por código de invitación"""
        return (
            self.db.query(League)
            .filter(League.invite_code == invite_code)
            .first()
        )

    def get_by_admin(self, admin_user_id: int) -> List[League]:
        """Obtener todas las ligas creadas por un usuario"""
        return (
            self.db.query(League)
            .filter(League.admin_user_id == admin_user_id)
            .all()
        )

    def get_by_status(self, status: str) -> List[League]:
        """Obtener ligas por estado (drafting, active, finished)"""
        return (
            self.db.query(League)
            .filter(League.status == status)
            .all()
        )

    def create(self, league: League) -> League:
        self.db.add(league)
        self.db.flush()
        return league

    def update(self, league_id: int, league_data: dict) -> League:
        league = self.get_by_id(league_id)
        
        for key, value in league_data.items():
            if value is not None:
                setattr(league, key, value)
        
        return league

    def delete(self, league: League) -> None:
        self.db.delete(league)


class LeagueMemberRepository:
    '''
    Repositorio de miembros de liga - Capa de acceso a datos.
    '''
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[LeagueMember]:
        return (
            self.db.query(LeagueMember)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, member_id: int) -> Optional[LeagueMember]:
        return (
            self.db.query(LeagueMember)
            .filter(LeagueMember.id == member_id)
            .first()
        )

    def get_by_league(self, league_id: int) -> List[LeagueMember]:
        """Obtener todos los miembros de una liga"""
        return (
            self.db.query(LeagueMember)
            .filter(LeagueMember.league_id == league_id)
            .all()
        )

    def get_by_user(self, user_id: int) -> List[LeagueMember]:
        """Obtener todas las ligas en las que participa un usuario"""
        return (
            self.db.query(LeagueMember)
            .filter(LeagueMember.user_id == user_id)
            .all()
        )

    def get_by_user_with_league(self, user_id: int) -> List[LeagueMember]:
        """Obtener todas las ligas en las que participa un usuario e incluyendo el nombre de la liga"""
        return (
            self.db.query(LeagueMember)
            .options(joinedload(LeagueMember.members_league))
            .filter(LeagueMember.user_id == user_id)
            .all()
        )

    def get_by_league_and_user(self, league_id: int, user_id: int) -> Optional[LeagueMember]:
        """Verificar si un usuario ya está en una liga"""
        return (
            self.db.query(LeagueMember)
            .filter(LeagueMember.league_id == league_id)
            .filter(LeagueMember.user_id == user_id)
            .first()
        )

    def get_league_rankings(self, league_id: int) -> List[LeagueMember]:
        """Obtener rankings de una liga (por implementar lógica de puntos totales)"""
        # Aquí eventualmente ordenaremos por puntos totales del roster
        return (
            self.db.query(LeagueMember)
            .filter(LeagueMember.league_id == league_id)
            .all()
        )
    
    def get_league_rankings_with_user(self, league_id: int) -> List[LeagueMember]:
        """Obtener miembros de una liga incluyendo info del usuario, roster y jugadores"""
        return (
            self.db.query(LeagueMember)
            .options(
                joinedload(LeagueMember.user),
                joinedload(LeagueMember.roster).joinedload(Roster.player)
            )
            .filter(LeagueMember.league_id == league_id)
            .order_by(LeagueMember.total_points.desc())
            .all()
        )

    def create(self, member: LeagueMember) -> LeagueMember:
        self.db.add(member)
        self.db.flush()
        return member

    def update(self, member_id: int, member_data: dict) -> LeagueMember:
        member = self.get_by_id(member_id)
        
        for key, value in member_data.items():
            if value is not None:
                setattr(member, key, value)
        
        return member

    def delete(self, member: LeagueMember) -> None:
        self.db.delete(member)


class RosterRepository:
    '''
    Repositorio de rosters - Capa de acceso a datos.
    '''
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Roster]:
        return (
            self.db.query(Roster)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, roster_id: int) -> Optional[Roster]:
        return (
            self.db.query(Roster)
            .filter(Roster.id == roster_id)
            .first()
        )

    def get_by_league_member(self, league_member_id: int) -> List[Roster]:
        """Obtener todos los jugadores del roster de un miembro"""
        return (
            self.db.query(Roster)
            .filter(Roster.league_member_id == league_member_id)
            .all()
        )

    def get_starters_by_league_member(self, league_member_id: int) -> List[Roster]:
        """Obtener jugadores titulares del roster"""
        return (
            self.db.query(Roster)
            .filter(Roster.league_member_id == league_member_id)
            .filter(Roster.is_starter == True)
            .all()
        )

    def get_bench_by_league_member(self, league_member_id: int) -> List[Roster]:
        """Obtener suplentes del roster"""
        return (
            self.db.query(Roster)
            .filter(Roster.league_member_id == league_member_id)
            .filter(Roster.is_bench == True)
            .all()
        )

    def get_by_player_and_member(self, league_member_id: int, player_id: int) -> Optional[Roster]:
        """Verificar si un jugador ya está en el roster"""
        return (
            self.db.query(Roster)
            .filter(Roster.league_member_id == league_member_id)
            .filter(Roster.player_id == player_id)
            .first()
        )

    def create(self, roster: Roster) -> Roster:
        self.db.add(roster)
        self.db.flush()
        return roster

    def update(self, roster_id: int, roster_data: dict) -> Roster:
        roster = self.get_by_id(roster_id)
        
        for key, value in roster_data.items():
            if value is not None:
                setattr(roster, key, value)
        
        return roster

    def delete(self, roster: Roster) -> None:
        self.db.delete(roster)

    def delete_all_by_league_member(self, league_member_id: int) -> None:
        """Eliminar todo el roster de un miembro (útil para reset)"""
        self.db.query(Roster).filter(Roster.league_member_id == league_member_id).delete()
