import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, delete
from app.db.models.professional import Player
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
        self._tbd_team_cache = None  # Cache para el equipo TBD

    async def _get_or_create_tbd_team(self):
        """
        Obtiene o crea el equipo placeholder TBD.
        Este equipo se usa para matches upcoming donde aún no se conocen los equipos.
        """
        if self._tbd_team_cache:
            return self._tbd_team_cache
            
        tbd_team = await self.team_service.repo.get_by_name("TBD")
        if not tbd_team:
            tbd_team = await self.team_service.create(
                name="TBD",
                region="GLOBAL",
                logo_url=None
            )
            logger.info(f"Created TBD placeholder team (ID: {tbd_team.id})")
        else:
            logger.debug(f"Using existing TBD team (ID: {tbd_team.id})")
        
        self._tbd_team_cache = tbd_team
        return tbd_team


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
            
            for match_info in match_urls:
                # match_info es ahora un dict: {"url": "/123/...", "status": "live|upcoming|completed"}
                match_url = match_info["url"] if isinstance(match_info, dict) else match_info
                detected_status = match_info.get("status", "unknown") if isinstance(match_info, dict) else "unknown"
                
                # Respetar rate limits del servidor externo
                logger.info(f"Throttling: Waiting {settings.SCRAPER_THROTTLE_SECONDS}s...")
                await asyncio.sleep(settings.SCRAPER_THROTTLE_SECONDS)

                parts = [p for p in match_url.split("/") if p]
                if not parts: continue
                vlr_id = parts[1] if parts[0] == "match" else parts[0]
                if not vlr_id.isdigit(): continue
                
                # Verificar si ya tenemos este partido procesado correctamente
                existing_match = await self.match_service.repo.get_by_vlr_match_id(vlr_id)
                
                # CAMBIO IMPORTANTE: Solo saltar si está completed Y processed
                # Permitir actualización de partidos live o upcoming
                if existing_match and existing_match.is_processed and existing_match.status == "completed":
                    logger.debug(f"Match {vlr_id} already processed and completed, skipping")
                    continue
                
                # Si es live, siempre actualizar (puede que haya terminado)
                if existing_match and existing_match.status == "live":
                    logger.info(f"Updating LIVE match {vlr_id} (detected: {detected_status}) to check if completed")
                elif existing_match and detected_status == "live":
                    logger.info(f"Match {vlr_id} is now LIVE (was {existing_match.status})")

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
        
        # USAR STATUS DEL SCRAPER (confiar en la detección del scraper)
        status = details.get("status", "upcoming")
        
        # Verificar si hay stats reales (para logging y validaciones)
        has_real_stats = any(p["kills"] > 0 or p["rating"] > 0 for p in details["players"])
        
        # Scores: Si es upcoming, forzar 0-0
        if status == "upcoming":
            final_score_a = 0
            final_score_b = 0
        else:
            final_score_a = details.get("scores", [0, 0])[0]
            final_score_b = details.get("scores", [0, 0])[1]
            
            # Validación: scores deben ser razonables (0-3 típicamente en BO3/BO5)
            if final_score_a > 3 or final_score_b > 3:
                logger.error(f"Match {vlr_id}: Invalid scores {final_score_a}-{final_score_b} (BO3 max is 2-1), resetting to 0-0")
                final_score_a = 0
                final_score_b = 0
                # Si los scores son inválidos, probablemente el scraper falló
                if status == "completed":
                    status = "upcoming"  # Resetear a upcoming si los datos son inconsistentes

        # 2. Procesar Equipos: asegurar que existen en la DB
        team_models = []
        
        # VALIDACIÓN CRÍTICA: Verificar que tenemos exactamente 2 equipos con nombres válidos
        if len(details["teams"]) < 2:
            logger.error(f"Match {vlr_id}: Scraper returned less than 2 teams ({len(details['teams'])}). Teams data: {details['teams']}")
            return
        
        for t_info in details["teams"]:
            team_name = t_info.get("name", "").strip()
            
            # Si el equipo es TBD, usar el team TBD persistente
            if not team_name or team_name.upper() == "TBD":
                team = await self._get_or_create_tbd_team()
                logger.debug(f"Match {vlr_id}: Using TBD placeholder team (ID: {team.id})")
                team_models.append(team)
                continue
            
            # Validar que el nombre del equipo no esté vacío (ya sabemos que no es TBD)
            if len(team_name) < 2:
                logger.error(f"Match {vlr_id}: Team name too short: '{team_name}'. Full team data: {t_info}")
                return
            
            # Procesar equipo real
            team = await self.team_service.repo.get_by_name(team_name)
            if not team:
                team = await self.team_service.create(
                    name=team_name, region=event["region"], logo_url=t_info["logo_url"]
                )
                logger.info(f"Created new team: {team_name} (ID: {team.id})")
            elif t_info["logo_url"] and not team.logo_url:
                await self.team_service.update(team.id, {"logo_url": t_info["logo_url"]})
            team_models.append(team)

        # Doble verificación de seguridad
        if len(team_models) < 2: 
            logger.error(f"Match {vlr_id}: Failed to create/find 2 teams. Only got {len(team_models)} teams.")
            return

        # 3. Procesar Partido: Crear o Actualizar
        match_data = {
            "status": status,
            "date": details.get("date"),
            "score_team_a": final_score_a,
            "score_team_b": final_score_b,
            "format": self.deduce_format(final_score_a, final_score_b),
            # CRÍTICO: Siempre actualizar team_a_id y team_b_id para reemplazar TBD teams
            "team_a_id": team_models[0].id,
            "team_b_id": team_models[1].id
        }

        if not existing_match:
            # Crear nuevo
            match_params = {
                "vlr_match_id": vlr_id,
                "tournament_name": event["name"],
                "vlr_url": f"{self.scraper.vlr_base_url}{details.get('url', '')}",
                **match_data
            }
            # Usamos date del existing o del details si es nuevo
            if not match_params["date"]: 
                match_params["date"] = datetime.utcnow() # Fallback por seguridad
            
            existing_match = await self.match_service.create(**match_params)
        else:
            # Actualizar existente
            # Mantenemos la fecha antigua si la nueva viene vacía
            if not match_data["date"]:
                match_data.pop("date")
            
            # Log status changes
            old_status = existing_match.status
            if old_status != status:
                logger.info(f"Match {vlr_id} status changed: {old_status} -> {status}")
            
            # Log team updates para debugging
            if existing_match.team_a_id != team_models[0].id or existing_match.team_b_id != team_models[1].id:
                logger.info(f"Match {vlr_id} teams updated: ({existing_match.team_a_id}, {existing_match.team_b_id}) -> ({team_models[0].id}, {team_models[1].id})")
            
            await self.match_service.update(existing_match.id, match_data)

        # 4. Procesar Jugadores y Estadísticas
        # Solo procesamos stats si el partido está completado
        if status != "completed":
            logger.debug(f"Match {vlr_id} status={status}, skipping player stats processing")
        else:
            stats_created = 0
            stats_updated = 0
            
            # VALIDACIÓN: Verificar que tenemos stats de jugadores
            if not details["players"]:
                logger.error(f"Match {vlr_id}: No player stats found despite status=completed")
            else:
                # Validar conteo de jugadores por equipo
                team_0_count = sum(1 for p in details["players"] if p["team_index"] == 0)
                team_1_count = sum(1 for p in details["players"] if p["team_index"] == 1)
                logger.info(f"Match {vlr_id}: Player count - Team A: {team_0_count}, Team B: {team_1_count}")
                
                if team_0_count < 5 or team_1_count < 5:
                    logger.warning(f"Match {vlr_id}: Incomplete player roster (expected 5 per team)")
            
            for p_stats in details["players"]:
                try:
                    current_team = team_models[0] if p_stats["team_index"] == 0 else team_models[1]
                    
                    # Buscar o crear jugador
                    player = await self.player_service.repo.get_by_name(p_stats["name"])
                    if not player:
                        try:
                            player = await self.player_service.create(
                                name=p_stats["name"], role=self.infer_role(p_stats["agent"]),
                                region=event["region"], team_id=current_team.id,
                                base_price=10.0, current_price=10.0
                            )
                        except AlreadyExistsException:
                            # Concurrencia: si se creó justo en otro hilo
                            player = await self.player_service.repo.get_by_name(p_stats["name"])
                    
                    if not player: 
                        logger.error(f"Match {vlr_id}: Failed to create/find player {p_stats['name']}")
                        continue

                    # Actualizar equipo del jugador si ha cambiado (importante para TBD -> Equipo Real)
                    if player.team_id != current_team.id:
                        await self.player_service.update(player.id, {"team_id": current_team.id})

                    # Datos limpios de la estadística
                    stat_data = {
                        "agent": p_stats["agent"],
                        "kills": p_stats["kills"],
                        "death": p_stats["deaths"],
                        "assists": p_stats["assists"],
                        "acs": p_stats["acs"],
                        "adr": p_stats["adr"],
                        "hs_percent": p_stats["hs_percent"],
                        "rating": p_stats["rating"],
                        "first_kills": p_stats["first_kills"],
                        "first_deaths": p_stats["first_deaths"],
                        "clutches_won": 0
                    }

                    # Buscamos manualmente si ya existe la stat
                    q_exist = select(PlayerMatchStats).where(
                        PlayerMatchStats.match_id == existing_match.id,
                        PlayerMatchStats.player_id == player.id
                    )
                    res_exist = await self.db.execute(q_exist)
                    existing_stat = res_exist.scalar_one_or_none()

                    if existing_stat:
                        # UPDATE: Actualizamos los valores existentes
                        for k, v in stat_data.items():
                            setattr(existing_stat, k, v)
                        
                        # CRÍTICO: Recalcular fantasy points después de actualizar stats
                        existing_stat.fantasy_points_earned = await self.stats_service.calculate_fantasy_points(existing_stat, existing_match)
                        stats_updated += 1
                    else:
                        # INSERT: Creamos nueva stat
                        new_stat = PlayerMatchStats(
                            match_id=existing_match.id,
                            player_id=player.id,
                            **stat_data
                        )
                        
                        # CRÍTICO: Calcular fantasy points ANTES de añadir a la DB
                        new_stat.fantasy_points_earned = await self.stats_service.calculate_fantasy_points(new_stat, existing_match)
                        self.db.add(new_stat)
                        stats_created += 1
                        
                        logger.debug(f"Player {p_stats['name']}: {new_stat.fantasy_points_earned:.2f} fantasy points")

                except Exception as e:
                    logger.error(f"Error procesando jugador {p_stats.get('name')} en match {vlr_id}: {e}", exc_info=True)
                    continue
            
            # Log stats processing results
            logger.info(f"Match {existing_match.vlr_match_id}: Stats Created={stats_created}, Updated={stats_updated}")

        # Marcar como procesado y actualizar precios solo si está completed
        if status == "completed":
            await self.match_service.mark_as_processed(existing_match.id)
            logger.info(f"Match {existing_match.vlr_match_id} marked as processed (completed)")
        elif status == "live":
            # Asegurar que live matches NO estén marcados como processed
            if existing_match.is_processed:
                await self.match_service.update(existing_match.id, {"is_processed": False})
                logger.info(f"Match {existing_match.vlr_match_id} set to is_processed=False (LIVE)")
            logger.info(f"Match {existing_match.vlr_match_id} is LIVE, will check again later")
        
        # Solo actualizar precios si el partido está realmente completado
        if status == "completed":
            # Recargar con relaciones para actualización global
            q = select(Match).where(Match.id == existing_match.id).options(
                selectinload(Match.player_stats).selectinload(PlayerMatchStats.player)
            )
            res = await self.db.execute(q)
            match_with_stats = res.scalar_one()
            
            # Actualizar puntos y precios
            await self.update_player_global_stats(match_with_stats)
        else:
            logger.debug(f"Match {existing_match.vlr_match_id} status={status}, skipping price/points update")

    async def sync_kickoff_2026(self):
        return await self.sync_vct_kickoff_comprehensive()
    
    async def sync_from_event(self, event_path: str, tournament_id: Optional[int] = None):
        """
        Sincronización de partidos desde un evento específico.
        
        Args:
            event_path: Path del evento en VLR.gg (e.g., "/event/2760/valorant-masters-santiago-2026")
                       El scraper manejará automáticamente si tiene /matches o no.
            tournament_id: ID del torneo para asociar partidos (opcional)
        
        Returns:
            int: Número de partidos sincronizados
        """
        logger.info(f"--- SYNCING EVENT: {event_path} ---")
        if tournament_id:
            logger.info(f"  Tournament ID: {tournament_id}")
        
        # Obtener URLs de partidos del evento
        match_urls = await self.scraper.get_match_urls_from_event(event_path)
        
        total_synced = 0
        for match_info in match_urls:
            match_url = match_info["url"] if isinstance(match_info, dict) else match_info
            detected_status = match_info.get("status", "unknown") if isinstance(match_info, dict) else "unknown"
            
            # Throttling
            logger.info(f"Throttling: Waiting {settings.SCRAPER_THROTTLE_SECONDS}s...")
            await asyncio.sleep(settings.SCRAPER_THROTTLE_SECONDS)
            
            parts = [p for p in match_url.split("/") if p]
            if not parts: continue
            vlr_id = parts[1] if parts[0] == "match" else parts[0]
            if not vlr_id.isdigit(): continue
            
            # Verificar si ya tenemos este partido procesado
            existing_match = await self.match_service.repo.get_by_vlr_match_id(vlr_id)
            
            # Solo saltar si está completed Y processed
            if existing_match and existing_match.is_processed and existing_match.status == "completed":
                logger.debug(f"Match {vlr_id} already processed and completed, skipping")
                continue
            
            # Si es live, siempre actualizar
            if existing_match and existing_match.status == "live":
                logger.info(f"Updating LIVE match {vlr_id} (detected: {detected_status})")
            elif existing_match and detected_status == "live":
                logger.info(f"Match {vlr_id} is now LIVE (was {existing_match.status})")
            
            details = await self.scraper.scrape_match_details(match_url)
            if not details: continue
            
            # Procesar el partido
            try:
                old_status = existing_match.status if existing_match else None
                
                # Inyectar tournament_id en details si está presente
                if tournament_id:
                    details["tournament_id"] = tournament_id
                
                # Crear event dict para mantener compatibilidad con _sync_match_details
                event = {"name": "Tournament Match", "path": event_path}
                
                await self._sync_match_details(vlr_id, event, details, existing_match)
                total_synced += 1
                
                # Invalidar caché si necesario
                has_stats = any(p["kills"] > 0 or p["rating"] > 0 for p in details["players"])
                new_status = "completed" if has_stats else "upcoming"
                
                if old_status != "completed" and new_status == "completed":
                    if self.redis:
                        m = await self.match_service.repo.get_by_vlr_match_id(vlr_id)
                        if m:
                            await self.redis.delete(f"stats:match:{m.id}")
                            logger.info(f"Cache invalidated for match {m.id}")
            
            except Exception as e:
                logger.error(f"Error syncing match {vlr_id}: {e}")
                continue
        
        logger.info(f"--- EVENT SYNC COMPLETE. Matches processed: {total_synced} ---")
        return total_synced

    async def update_player_global_stats(self, match: Match):
        """Actualiza los puntos totales y precios (Asíncrono) recalculando desde la base de datos."""
        for stats in match.player_stats:
            player = stats.player
            
            # Recalcular TODOS los puntos y partidos desde la base de datos para evitar duplicaciones
            q_all_stats = (
                select(PlayerMatchStats)
                .options(selectinload(PlayerMatchStats.match))
                .join(Match)
                .where(PlayerMatchStats.player_id == player.id, Match.status == "completed")
            )
            res_all_stats = await self.db.execute(q_all_stats)
            all_stats = res_all_stats.scalars().all()
            
            # Cálculo exacto basado en el historial real
            total_points = sum(s.fantasy_points_earned for s in all_stats)
            total_matches = len(all_stats)
            new_price = self.calculate_new_price(all_stats)
            
            await self.player_service.update(player.id, {
                "points": round(total_points, 2),
                "current_price": new_price,
                "matches_played": total_matches
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
        """
        Calcula el nuevo precio de un jugador (0-85M máx).
        
        NUEVA FÓRMULA V2:
        - Performance reciente (últimos 5 partidos): 60% peso
        - Consistencia (desviación estándar): 20% peso
        - Tendencia/Momentum (últimos 2 vs 3-5): 10% peso
        - Participación (penaliza jugadores con pocos partidos): 10% peso
        """
        if not player_stats_history:
            return 10.0  # Precio inicial para jugadores nuevos
        
        # Ordenar por fecha (más recientes primero)
        recent_stats = sorted(
            player_stats_history,
            key=lambda x: x.match.date if x.match and x.match.date else datetime.min,
            reverse=True
        )[:5]  # Últimos 5 partidos
        
        if not recent_stats:
            return 10.0
        
        # =================================================================
        # 1. PERFORMANCE RECIENTE (60% del peso)
        # =================================================================
        points = [s.fantasy_points_earned for s in recent_stats]
        avg_points = sum(points) / len(points)
        
        # Base de precio: 5M + (avg_points * 2.5)
        # Ejemplo: 10 pts promedio = 5 + 25 = 30M
        # Ejemplo: 15 pts promedio = 5 + 37.5 = 42.5M
        base_price = 5.0 + (avg_points * 2.5)
        
        # =================================================================
        # 2. CONSISTENCIA (20% del peso)
        # =================================================================
        if len(points) > 1:
            variance = sum((x - avg_points) ** 2 for x in points) / (len(points) - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0.0
        
        # Coefficient of Variation: menor CV = más consistente
        safe_avg = max(1.0, avg_points)
        cv = std_dev / safe_avg
        
        # Factor de consistencia: 0.85 a 1.20
        if cv < 0.15:
            consistency_multiplier = 1.20  # Muy consistente
        elif cv < 0.25:
            consistency_multiplier = 1.10
        elif cv < 0.40:
            consistency_multiplier = 1.00
        elif cv < 0.55:
            consistency_multiplier = 0.95
        else:
            consistency_multiplier = 0.85  # Muy inconsistente
        
        # =================================================================
        # 3. TENDENCIA / MOMENTUM (10% del peso)
        # =================================================================
        trend_multiplier = 1.0
        if len(points) >= 3:
            # Comparar promedio de últimos 2 partidos vs promedio de partidos 3-5
            recent_avg = sum(points[:2]) / 2
            older_avg = sum(points[2:]) / len(points[2:])
            
            if recent_avg > older_avg * 1.3:
                trend_multiplier = 1.12  # +12% jugador en racha ascendente
            elif recent_avg > older_avg * 1.1:
                trend_multiplier = 1.05  # +5% mejorando
            elif recent_avg < older_avg * 0.7:
                trend_multiplier = 0.90  # -10% jugador en declive
            elif recent_avg < older_avg * 0.9:
                trend_multiplier = 0.97  # -3% empeorando
        
        # =================================================================
        # 4. FACTOR DE PARTICIPACIÓN (10% peso)
        # =================================================================
        total_matches = len(player_stats_history)
        if total_matches == 1:
            participation_factor = 0.50  # -50% para 1 solo partido (muy volátil)
        elif total_matches == 2:
            participation_factor = 0.70  # -30% para 2 partidos
        elif total_matches == 3:
            participation_factor = 0.85  # -15% para 3 partidos
        elif total_matches == 4:
            participation_factor = 0.95  # -5% para 4 partidos
        else:
            participation_factor = 1.00  # Sin penalización
        
        # =================================================================
        # 5. CÁLCULO FINAL CON CAPS
        # =================================================================
        final_price = (
            base_price
            * consistency_multiplier
            * trend_multiplier
            * participation_factor
        )
        
        # Límites: Mínimo 2M, Máximo 85M
        final_price = max(2.0, min(85.0, final_price))
        
        return round(final_price, 2)

    @transactional
    async def recalibrate_all_prices(self):
        """Recalibra PUNTOS y PRECIOS para todos los jugadores basado en todo el historial"""
        q_all_stats = select(PlayerMatchStats).options(selectinload(PlayerMatchStats.match))
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
