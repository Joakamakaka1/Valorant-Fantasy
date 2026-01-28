import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, delete
from app.db.models.professional import Team, Player, Region, PlayerRole
from app.db.models.match import Match, PlayerMatchStats
from app.db.models.league import Roster, LeagueMember
from app.db.models.stats import UserPointsHistory
from app.service.professional import TeamService, PlayerService
from app.service.match import MatchService, PlayerMatchStatsService
from app.core.config import settings
from app.core.decorators import transactional
from app.core.exceptions import AlreadyExistsException
from datetime import datetime, timedelta
import re
import logging
import asyncio
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import selectinload
from app.core.redis import RedisCache

logger = logging.getLogger(__name__)

from app.service.vlr_scraper import VLRScraper

class SyncService:
    """
    Servicio encargado de la sincronización de datos con fuentes externas (VLR.gg).
    Maneja la actualización de partidos, estadísticas de jugadores, precios de mercado
    y puntuaciones de las ligas de fantasía.
    """
    def __init__(self, db: AsyncSession, redis: Optional[RedisCache] = None):
        self.db = db
        self.redis = redis
        self.team_service = TeamService(db)
        self.player_service = PlayerService(db, redis=redis)
        self.match_service = MatchService(db)
        self.stats_service = PlayerMatchStatsService(db, redis=redis)
        self.scraper = VLRScraper()

    async def get_matches_from_api(self, q="results"):
        """Obtiene partidos de la API de VLRGGAPI (Asíncrono)"""
        url = f"{settings.VLR_API_BASE_URL}/match?q={q}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json().get("data", {}).get("segments", [])
        except Exception as e:
            logger.error(f"Error fetching matches from API: {e}")
            return []

    async def sync_vct_kickoff_comprehensive(self):
        """
        Sincronización exhaustiva de eventos VCT Kickoff.
        
        Itera sobre los eventos de Kickoff definidos para 2026, obtiene las URLs de los partidos,
        y procesa cada partido individualmente. Incluye lógica de throttling para no saturar el scrapping.
        """
        events = [
            {"path": "/event/matches/2682/vct-2026-americas-kickoff", "name": "VCT 2026: Americas Kickoff", "region": "Americas"},
            {"path": "/event/matches/2684/vct-2026-emea-kickoff", "name": "VCT 2026: EMEA Kickoff", "region": "EMEA"},
            {"path": "/event/matches/2683/vct-2026-pacific-kickoff", "name": "VCT 2026: Pacific Kickoff", "region": "Pacific"},
            {"path": "/event/matches/2685/vct-2026-china-kickoff", "name": "VCT 2026: China Kickoff", "region": "CN"}
        ]
        
        total_synced = 0
        for event in events:
            logger.info(f"--- SYNCING EVENT: {event['name']} ---")
            match_urls = await self.scraper.get_match_urls_from_event(event["path"])
            
            for match_url in match_urls:
                # Respetar rate limits del servidor externo
                logger.info(f"Throttling: Waiting 1.5s...")
                await asyncio.sleep(1.5)

                parts = [p for p in match_url.split("/") if p]
                if not parts: continue
                vlr_id = parts[1] if parts[0] == "match" else parts[0]
                if not vlr_id.isdigit(): continue
                
                # Verificar si ya tenemos este partido procesado correctamente
                existing_match = await self.match_service.repo.get_by_vlr_match_id(vlr_id)
                if existing_match and existing_match.is_processed:
                    continue

                details = await self.scraper.scrape_match_details(match_url)
                if not details: continue

                # Procesar el partido en una transacción individual
                try:
                    # Guardar estado previo para saber si cambió a completed
                    old_status = existing_match.status if existing_match else None
                    
                    await self._sync_match_details(vlr_id, event, details, existing_match)
                    
                    # SI LLEGAMOS AQUÍ, EL COMMIT FUE EXITOSO (gracias a @transactional)
                    # Ahora invalidamos caché como se pidió: DESPUÉS del commit
                    total_synced += 1
                    
                    # 1. Si el partido pasó a ser 'completed', invalidamos su caché de estadísticas
                    has_stats = any(p["kills"] > 0 or p["rating"] > 0 for p in details["players"])
                    new_status = "completed" if has_stats else "upcoming"
                    
                    if old_status != "completed" and new_status == "completed":
                        if self.redis:
                            # Re-fetch match to get internal ID for cache key
                            m = await self.match_service.repo.get_by_vlr_match_id(vlr_id)
                            if m:
                                await self.redis.delete(f"stats:match:{m.id}")
                                logger.info(f"Caché de estadísticas invalidada para partido {m.id} (status: {old_status} -> {new_status})")

                except Exception as e:
                    logger.error(f"Error procesando partido {vlr_id}: {e}")
                    continue
                
        return total_synced

    @transactional
    async def _sync_match_details(self, vlr_id: str, event: Dict[str, Any], details: Dict[str, Any], existing_match: Optional[Match]):
        """Procesa los detalles de un partido dentro de una transacción garantizando consistencia."""
        has_stats = any(p["kills"] > 0 or p["rating"] > 0 for p in details["players"])
        status = "completed" if has_stats else "upcoming"

        # 2. Procesar Equipos: asegurar que existen en la DB
        team_models = []
        for t_info in details["teams"]:
            team = await self.team_service.repo.get_by_name(t_info["name"])
            if not team:
                team = await self.team_service.create(
                    name=t_info["name"], region=event["region"], logo_url=t_info["logo_url"]
                )
            elif t_info["logo_url"] and not team.logo_url:
                await self.team_service.update(team.id, {"logo_url": t_info["logo_url"]})
            team_models.append(team)

        if len(team_models) < 2: return

        # 3. Procesar Partido: Crear o Actualizar
        if not existing_match:
            existing_match = await self.match_service.create(
                vlr_match_id=vlr_id, status=status,
                tournament_name=event["name"],
                vlr_url=f"{self.scraper.vlr_base_url}{details.get('url', '')}",
                team_a_id=team_models[0].id, team_b_id=team_models[1].id,
                date=details.get("date"),
                score_team_a=details.get("scores", [0, 0])[0],
                score_team_b=details.get("scores", [0, 0])[1],
                format=self.deduce_format(details.get("scores", [0, 0])[0], details.get("scores", [0, 0])[1])
            )
        else:
            await self.match_service.update(existing_match.id, {
                "status": status,
                "date": details.get("date") or existing_match.date,
                "score_team_a": details.get("scores", [0, 0])[0],
                "score_team_b": details.get("scores", [0, 0])[1],
                "format": self.deduce_format(details.get("scores", [0, 0])[0], details.get("scores", [0, 0])[1])
            })

        # 4. Procesar Jugadores y Estadísticas
        stats_created = 0
        stats_skipped = 0
        
        for p_stats in details["players"]:
            try:
                current_team = team_models[0] if p_stats["team_index"] == 0 else team_models[1]
                
                # Buscar o crear jugador, asignando el equipo correcto
                player = await self.player_service.repo.get_by_name(p_stats["name"])
                if not player:
                    try:
                        player = await self.player_service.create(
                            name=p_stats["name"], role=self.infer_role(p_stats["agent"]),
                            region=event["region"], team_id=current_team.id,
                            base_price=10.0, current_price=10.0
                        )
                    except AlreadyExistsException:
                        player = await self.player_service.repo.get_by_name(p_stats["name"])
                        if not player: continue
                elif not player.team_id:
                    await self.player_service.update(player.id, {"team_id": current_team.id})

                # Crear estadísticas si el partido terminó
                if status == "completed":
                    try:
                        await self.stats_service.create(
                            match_id=existing_match.id, player_id=player.id,
                            agent=p_stats["agent"], kills=p_stats["kills"],
                            death=p_stats["deaths"], assists=p_stats["assists"],
                            acs=p_stats["acs"], adr=p_stats["adr"],
                            hs_percent=p_stats["hs_percent"], rating=p_stats["rating"],
                            first_kills=p_stats["first_kills"], first_deaths=p_stats["first_deaths"],
                            clutches_won=0 
                        )
                        stats_created += 1
                    except AlreadyExistsException:
                        stats_skipped += 1
                        continue
            except Exception as e:
                logger.error(f"Error procesando jugador {p_stats.get('name')}: {e}")
                continue

        if status == "completed":
            logger.info(f"Match {existing_match.vlr_match_id}: Stats creadas={stats_created}, Skipped={stats_skipped}")
            await self.match_service.mark_as_processed(existing_match.id)
            
            # Recargar con relaciones para actualización global de stats/puntos
            q = select(Match).where(Match.id == existing_match.id).options(
                selectinload(Match.player_stats).selectinload(PlayerMatchStats.player)
            )
            res = await self.db.execute(q)
            match_with_stats = res.scalar_one()
            
            # Actualizar puntos y precios de los jugadores involucrados
            await self.update_player_global_stats(match_with_stats)

    async def sync_kickoff_2026(self):
        return await self.sync_vct_kickoff_comprehensive()

    async def update_player_global_stats(self, match: Match):
        """Actualiza los puntos totales y precios (Asíncrono)"""
        # NO usamos @transactional aquí porque se asume que se llama desde _sync_match_details que YA es transaccional
        for stats in match.player_stats:
            player = stats.player
            new_points = player.points + stats.fantasy_points_earned
            
            q_all_stats = (
                select(PlayerMatchStats)
                .options(selectinload(PlayerMatchStats.match))
                .join(Match)
                .where(PlayerMatchStats.player_id == player.id, Match.status == "completed")
            )
            res_all_stats = await self.db.execute(q_all_stats)
            all_stats = res_all_stats.scalars().all()
            
            new_price = self.calculate_new_price(all_stats)
            
            await self.player_service.update(player.id, {
                "points": round(new_points, 2),
                "current_price": new_price,
                "matches_played": player.matches_played + 1
            })

        await self.recalculate_league_members_points_for_match(match)
        
        # Al final de actualizar todos los jugadores de un partido, invalidamos la caché global de jugadores
        if self.redis:
            await self.redis.delete("all_players_cache")
            logger.info("Caché 'all_players_cache' invalidada después de actualización global de precios")

    async def recalculate_league_members_points_for_match(self, match: Match):
        """Recalcula puntos de miembros de liga (Asíncrono)"""
        player_ids = [s.player_id for s in match.player_stats]
        q_affected = select(Roster).where(Roster.player_id.in_(player_ids))
        res_affected = await self.db.execute(q_affected)
        affected_rosters = res_affected.scalars().all()
        member_ids = list(set(r.league_member_id for r in affected_rosters))

        for member_id in member_ids:
            q_member = select(LeagueMember).where(LeagueMember.id == member_id)
            res_member = await self.db.execute(q_member)
            member = res_member.scalar_one_or_none()
            if not member: continue

            q_total = (
                select(func.sum(Player.points))
                .join(Roster, Roster.player_id == Player.id)
                .where(Roster.league_member_id == member_id)
            )
            res_total = await self.db.execute(q_total)
            total = res_total.scalar() or 0.0
            
            member.total_points = round(total, 2)
            await self.record_user_history(member.user_id)

    async def record_user_history(self, user_id: int):
        """Instantánea de historial de puntos del usuario (Asíncrono)"""
        q_total = select(func.sum(LeagueMember.total_points)).where(LeagueMember.user_id == user_id)
        res_total = await self.db.execute(q_total)
        total_points = res_total.scalar() or 0.0
        
        history = UserPointsHistory(
            user_id=user_id,
            total_points=round(total_points, 2),
            recorded_at=datetime.utcnow()
        )
        self.db.add(history)

    def calculate_new_price(self, player_stats_history: list) -> float:
        """Calcula el nuevo precio (Operación síncrona sobre datos ya cargados)"""
        if not player_stats_history:
            return 10.0
        
        # Necesitamos que el historial tenga las fechas cargadas o se asuma orden
        recent_stats = sorted(player_stats_history, key=lambda x: x.match.date if x.match and x.match.date else datetime.min, reverse=True)[:5]
        
        if not recent_stats:
            return 10.0
            
        points = [s.fantasy_points_earned for s in recent_stats]
        avg_points = sum(points) / len(points)
        match_count = len(player_stats_history)
        
        if len(points) > 1:
            variance = sum((x - avg_points) ** 2 for x in points) / (len(points) - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0.0
            
        safe_avg = max(1.0, avg_points)
        cv = std_dev / safe_avg
        consistency_factor = 1.0 / (1.0 + cv)
        
        performance_booster = 1.0
        if avg_points > 15.0:
            performance_booster = 1.1 + ((avg_points - 15.0) / 100.0)
            
        if match_count == 1: participation_factor = 0.5
        elif match_count == 2: participation_factor = 0.7
        elif match_count == 3: participation_factor = 0.85
        elif match_count == 4: participation_factor = 0.95
        else: participation_factor = 1.0
            
        raw_price = 5.0 + (avg_points * 2.2) * consistency_factor * participation_factor * performance_booster
        final_price = max(1.0, min(60.0, raw_price))
        return round(final_price, 2)

    @transactional
    async def recalibrate_all_prices(self):
        """Recalibra PUNTOS y PRECIOS para todos los jugadores basado en todo el historial"""
        q_all_stats = select(PlayerMatchStats)
        res_all_stats = await self.db.execute(q_all_stats)
        all_stats = res_all_stats.scalars().all()
        
        logger.info(f"Recalculating points for {len(all_stats)} match stats registries...")
        for stat in all_stats:
            stat.fantasy_points_earned = await self.stats_service.calculate_fantasy_points(stat, stat.match)

        players = await self.player_service.repo.get_all(limit=1000)
        logger.info(f"Starting Intensity-based recalibration for {len(players)} players...")
        
        for player in players:
            q_actual = (
                select(PlayerMatchStats)
                .options(selectinload(PlayerMatchStats.match))
                .join(Match)
                .where(PlayerMatchStats.player_id == player.id, Match.status == "completed")
            )
            res_actual = await self.db.execute(q_actual)
            actual_matches = res_actual.scalars().all()
            
            games_count = len(actual_matches)
            total_points = sum(ps.fantasy_points_earned for ps in actual_matches)
            new_price = self.calculate_new_price(actual_matches)
            
            await self.player_service.update(player.id, {
                "points": round(total_points, 2),
                "current_price": new_price,
                "matches_played": games_count
            })
        
        return len(players)

    def infer_region(self, tournament_name: str) -> str:
        if "Pacific" in tournament_name: return "Pacific"
        if "EMEA" in tournament_name: return "EMEA"
        if "Americas" in tournament_name: return "Americas"
        if "China" in tournament_name or "CN" in tournament_name: return "CN"
        return "EMEA"

    def infer_role(self, agent: str) -> str:
        if not agent: return "Flex"
        roles = {
            "Duelist": ["Jett", "Raze", "Phoenix", "Reyna", "Yoru", "Neon", "Iso", "Waylay"],
            "Initiator": ["Sova", "Breach", "Skye", "KAY/O", "Fade", "Gekko", "Tejo"],
            "Controller": ["Brimstone", "Omen", "Viper", "Astra", "Harbor", "Clove"],
            "Sentinel": ["Killjoy", "Cypher", "Sage", "Chamber", "Deadlock", "Vyse", "Veto"]
        }
        agent_clean = agent.strip()
        for role, agents in roles.items():
            if any(a.lower() == agent_clean.lower() for a in agents):
                return role
        return "Flex"

    @transactional
    async def update_all_player_roles(self):
        """Actualiza el rol de todos los jugadores (Asíncrono)"""
        from collections import Counter
        res_players = await self.db.execute(select(Player))
        players = res_players.scalars().all()
        updated_count = 0

        for player in players:
            res_stats = await self.db.execute(select(PlayerMatchStats).where(PlayerMatchStats.player_id == player.id))
            stats = res_stats.scalars().all()
            if not stats: continue
            
            role_counts = Counter()
            for s in stats:
                if s.agent:
                    role = self.infer_role(s.agent)
                    if role != "Flex": role_counts[role] += 1
            
            if not role_counts: continue

            unique_roles = list(role_counts.keys())
            if len(unique_roles) >= 3:
                new_role = "Flex"
            else:
                counts = role_counts.most_common()
                if len(counts) > 1 and counts[0][1] == counts[1][1]: new_role = "Flex"
                else: new_role = counts[0][0]
            
            if player.role != new_role:
                player.role = new_role
                updated_count += 1
        
        return updated_count

    def parse_relative_date(self, time_str: str) -> Optional[datetime]:
        if not time_str or "ago" not in time_str: return None
        now = datetime.utcnow()
        days = 0; hours = 0; minutes = 0
        match_days = re.search(r'(\d+)d', time_str)
        match_hours = re.search(r'(\d+)h', time_str)
        match_mins = re.search(r'(\d+)m', time_str)
        if match_days: days = int(match_days.group(1))
        if match_hours: hours = int(match_hours.group(1))
        if match_mins: minutes = int(match_mins.group(1))
        return now - timedelta(days=days, hours=hours, minutes=minutes)

    def deduce_format(self, score1: any, score2: any) -> str:
        try:
            s1 = int(score1) if score1 else 0
            s2 = int(score2) if score2 else 0
            total = s1 + s2
            if s1 == 3 or s2 == 3 or total >= 4: return "Bo5"
            return "Bo3"
        except: return "Bo3"
