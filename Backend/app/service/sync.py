import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.db.models.professional import Team, Player, Region, PlayerRole
from app.db.models.match import Match, PlayerMatchStats
from app.service.professional import TeamService, PlayerService
from app.service.match import MatchService, PlayerMatchStatsService
from app.core.config import settings
from datetime import datetime, timedelta
import re
import logging
import time

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, db: Session):
        self.db = db
        self.team_service = TeamService(db)
        self.player_service = PlayerService(db)
        self.match_service = MatchService(db)
        self.stats_service = PlayerMatchStatsService(db)
        self.vlr_base_url = "https://www.vlr.gg"

    def get_matches_from_api(self, q="results"):
        """Obtiene partidos de la API de VLRGGAPI"""
        url = f"{settings.VLR_API_BASE_URL}/match?q={q}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json().get("data", {}).get("segments", [])
        except Exception as e:
            logger.error(f"Error fetching matches from API: {e}")
            return []

    def scrape_match_details(self, match_page_url: str):
        """Scrappea los detalles de un partido desde VLR.gg"""
        full_url = f"{self.vlr_base_url}{match_page_url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(full_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 1. Obtener equipos
            headers = soup.select(".match-header-link")
            teams = []
            for h in headers:
                name = h.select_one(".match-header-link-name").text.strip()
                logo = h.select_one("img")["src"] if h.select_one("img") else None
                url = h.get("href")
                if logo and logo.startswith("//"):
                    logo = "https:" + logo
                teams.append({"name": name, "logo_url": logo, "url": url})

            # 2. Obtener estadísticas de jugadores (VLR structure)
            all_maps_container = soup.select_one(".vm-stats-game[data-game-id='all']")
            if not all_maps_container:
                logger.info(f"No All Maps container found for {match_page_url}, searching everywhere")
                all_maps_container = soup
            
            # VLR usa .wf-table-inset para las tablas de "All Maps"
            # Intentar encontrar las tablas de estadísticas agregadas
            stats_tables = all_maps_container.select("table.wf-table-inset")
            
            if not stats_tables:
                # Fallback: buscar .wf-table-stats (formato antiguo o mapas individuales)
                logger.warning(f"No .wf-table-inset found, trying .wf-table-stats fallback")
                stats_tables = all_maps_container.select(".wf-table-stats")
            
            if not stats_tables:
                # Fallback final: buscar cualquier tabla grande
                logger.warning(f"No standard tables found, searching all tables")
                all_tables = soup.find_all("table")
                stats_tables = []
                for t in all_tables:
                    if len(t.select("tr:first-child th")) > 5:
                        stats_tables.append(t)
            
            logger.info(f"Finally using {len(stats_tables)} stat tables for {match_page_url}")
            
            if len(stats_tables) == 0:
                logger.warning(f"RAW HTML SNIPPET: {response.text[:500]}")
            
            players_stats = []

            for team_idx, table in enumerate(stats_tables):
                if team_idx > 1: break # Only first 2 tables
                
                # 1. Mapear columnas dinámicamente por encabezados
                headers_cells = table.select("thead th")
                col_map = {}
                for i, th in enumerate(headers_cells):
                    txt = th.text.strip().upper()
                    if txt == "K": col_map["kills"] = i
                    elif txt == "D": col_map["deaths"] = i
                    elif txt == "A": col_map["assists"] = i
                    elif txt == "RATING": col_map["rating"] = i
                    elif txt == "ACS": col_map["acs"] = i
                    elif txt == "ADR": col_map["adr"] = i
                    elif txt == "KAST": col_map["kast"] = i
                    elif txt == "HS%": col_map["hs_percent"] = i
                    elif txt == "FK": col_map["first_kills"] = i
                    elif txt == "FD": col_map["first_deaths"] = i

                rows = table.select("tbody tr")
                logger.info(f"Table {team_idx} has {len(rows)} rows. Col map: {col_map}")
                
                for row in rows:
                    name_elem = row.select_one(".mod-player") or row.select_one(".text-of")
                    if not name_elem: continue
                    
                    player_name = name_elem.text.strip().split("\n")[0].strip()
                    if not player_name or len(player_name) < 2: continue
                    
                    # Agent
                    agent_img = row.select_one(".mod-agents img")
                    agent = "Unknown"
                    if agent_img:
                        agent = agent_img.get("title") or agent_img.get("alt") or "Unknown"
                    
                    cols = row.select("td")
                    
                    def get_val(key, is_int=False):
                        idx = col_map.get(key)
                        if idx is None or idx >= len(cols): return 0 if is_int else 0.0
                        
                        # VLR stats cells often have multiple lines: Total\nMap1\nMap2
                        # and sometimes start with '/' characters.
                        # We want the FIRST actual value (the total).
                        raw_text = cols[idx].text.strip()
                        # Limpiar ruido: '/' y espacios extra
                        clean_text = raw_text.replace("/", "").strip()
                        lines = [l.strip() for l in clean_text.split("\n") if l.strip()]
                        
                        if not lines: return 0 if is_int else 0.0
                        
                        val_str = lines[0].replace("%", "").strip()
                        try:
                            # Handling cases like '24/10' (if any left)
                            if "/" in val_str and is_int: val_str = val_str.split("/")[0]
                            return int(val_str) if is_int else float(val_str)
                        except: return 0 if is_int else 0.0

                    # Extract Rating or fallback to KAST
                    rating = get_val("rating")
                    if rating == 0.0:
                        # Fallback: simple formula or KAST if user suggested
                        kast = get_val("kast")
                        rating = kast / 100.0 if kast > 0 else 0.0

                    players_stats.append({
                        "name": player_name,
                        "agent": agent,
                        "team_index": team_idx,
                        "rating": rating,
                        "acs": get_val("acs"),
                        "kills": get_val("kills", True),
                        "deaths": get_val("deaths", True),
                        "assists": get_val("assists", True),
                        "adr": get_val("adr"),
                        "hs_percent": get_val("hs_percent"),
                        "first_kills": get_val("first_kills", True),
                        "first_deaths": get_val("first_deaths", True)
                    })

            # Fallback for upcoming matches: If no players found in stats tables, search for them in the match header
            if not players_stats:
                logger.info(f"No stats tables found for {match_page_url}, searching for rosters in headers...")
                # Search for player links in the match page
                # VLR often has player names in columns for upcoming matches
                match_players = soup.select(".match-header-vs .match-header-vs-players")
                for i, container in enumerate(match_players):
                    if i > 1: break # Team A and Team B
                    player_links = container.select("a")
                    for p_link in player_links:
                        p_name = p_link.text.strip().split("\n")[0].strip()
                        if p_name:
                            players_stats.append({
                                "name": p_name,
                                "agent": "Unknown",
                                "team_index": i,
                                "rating": 0.0, "acs": 0.0, "kills": 0, "deaths": 0, "assists": 0,
                                "adr": 0.0, "hs_percent": 0.0, "first_kills": 0, "first_deaths": 0
                            })

            # 3. Obtener Fecha y Scores
            date_info = soup.select_one(".moment-tz-convert")
            match_date = None
            if date_info and date_info.get("data-utc-ts"):
                try:
                    match_date = datetime.strptime(date_info.get("data-utc-ts"), "%Y-%m-%d %H:%M:%S")
                except: pass

            score_elems = soup.select(".match-header-vs-score span")
            scores = [0, 0]
            if len(score_elems) >= 3:
                try:
                    scores[0] = int(score_elems[0].text.strip())
                    scores[1] = int(score_elems[2].text.strip())
                except: pass

            return {
                "teams": teams,
                "players": players_stats,
                "date": match_date,
                "scores": scores
            }

        except Exception as e:
            logger.error(f"Error scraping match {match_page_url}: {e}")
            return None

    def scrape_team_roster(self, team_page_url: str):
        """Scrappe el roster completo de un equipo desde su página de VLR.gg"""
        full_url = f"{self.vlr_base_url}{team_page_url}"
        headers = { "User-Agent": "Mozilla/5.0" }
        try:
            response = requests.get(full_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            roster = []
            # VLR Team page has players in .team-roster-item or similar
            player_elems = soup.select(".team-roster-item")
            for p_elem in player_elems:
                name_elem = p_elem.select_one(".team-roster-item-name-alias")
                if name_elem:
                    roster.append(name_elem.text.strip())
            
            # Additional fallback for different layouts
            if not roster:
                # Look for links in the roster section
                for p_link in soup.select("a[href^='/player/']"):
                    # Only aliases, usually in a div with specific class
                    p_name = p_link.text.strip()
                    if p_name and not any(x in p_name.lower() for x in ["staff", "coach", "manager"]):
                        if len(p_name) > 1 and p_name not in roster:
                            roster.append(p_name)
            
            return roster
        except Exception as e:
            logger.error(f"Error scraping team roster {team_page_url}: {e}")
            return []

    def get_match_urls_from_event(self, event_path: str):
        """Scrappe todas las URLs de partidos de una página de evento de VLR.gg"""
        url = f"{self.vlr_base_url}{event_path}"
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        try:
            logger.info(f"Fetching event matches from: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            
            match_links = []
            # Scrapear ABSOLUTAMENTE TODOS los links y filtrar por patrones de partido
            all_links = soup.find_all("a")
            for a in all_links:
                href = a.get("href", "")
                
                # Un partido de VLR puede ser /12345/team-vs-team o /match/12345/team...
                # El patrón más seguro es un slash seguido de 5 o más dígitos
                match_pattern = re.search(r'^/(\d{5,})/', href)
                if not match_pattern:
                    match_pattern = re.search(r'/match/(\d{5,})/', href)
                
                if match_pattern and not any(x in href for x in ["/news/", "/event/", "/rankings/", "/forum/", "/player/", "/team/"]):
                    clean_href = href.split("?")[0].split("#")[0]
                    if clean_href not in match_links:
                        match_links.append(clean_href)
            
            logger.info(f"Found {len(match_links)} potential match links for: {event_path}")
            return match_links
        except Exception as e:
            logger.error(f"Error fetching match URLs from {event_path}: {e}")
            return []

    def sync_vct_kickoff_comprehensive(self):
        """Sincronización exhaustiva raspando directamente los eventos de VLR.gg"""
        # Usar rutas base sin series_id para maximizar compatibilidad si es posible
        events = [
            {"path": "/event/matches/2682/vct-2026-americas-kickoff", "name": "VCT 2026: Americas Kickoff", "region": "Americas"},
            {"path": "/event/matches/2684/vct-2026-emea-kickoff", "name": "VCT 2026: EMEA Kickoff", "region": "EMEA"},
            {"path": "/event/matches/2683/vct-2026-pacific-kickoff", "name": "VCT 2026: Pacific Kickoff", "region": "Pacific"},
            {"path": "/event/matches/2685/vct-2026-china-kickoff", "name": "VCT 2026: China Kickoff", "region": "CN"}
        ]
        
        total_synced = 0
        for event in events:
            logger.info(f"--- SYNCING EVENT: {event['name']} ---")
            match_urls = self.get_match_urls_from_event(event["path"])
            
            # Procesar cada URL de partido
            for match_url in match_urls:
                # 1.5s Throttling to prevent IP bans
                logger.info(f"Throttling: Waiting 1.5s before next match...")
                time.sleep(1.5)

                # El ID de VLR está en la URL: /12345/team-a-vs-team-b o /match/12345/slug
                parts = [p for p in match_url.split("/") if p]
                if not parts: continue
                
                # Si empieza por 'match', el ID es parts[1]. Si no, es parts[0]
                vlr_id = parts[1] if parts[0] == "match" else parts[0]
                
                # Verificar que el ID sea numérico
                if not vlr_id.isdigit(): continue
                existing_match = self.match_service.repo.get_by_vlr_match_id(vlr_id)
                if existing_match and existing_match.is_processed:
                    continue

                # 1.5s Throttling to prevent IP bans
                logger.info(f"Throttling: Waiting 1.5s before next match...")
                time.sleep(1.5)

                # Scrapear detalles completos del partido
                details = self.scrape_match_details(match_url)
                if not details: continue

                # 1. Determinar estado
                # Si hay jugadores con estadísticas, está completado. Si no, upcoming.
                has_stats = any(p["kills"] > 0 or p["rating"] > 0 for p in details["players"])
                status = "completed" if has_stats else "upcoming"

                # 2. Procesar/Crear Equipos
                team_models = []
                for t_info in details["teams"]:
                    team = self.team_service.repo.get_by_name(t_info["name"])
                    if not team:
                        team = self.team_service.create(
                            name=t_info["name"],
                            region=event["region"],
                            logo_url=t_info["logo_url"]
                        )
                    elif t_info["logo_url"] and not team.logo_url:
                        self.team_service.update(team.id, {"logo_url": t_info["logo_url"]})
                    team_models.append(team)

                if len(team_models) < 2: continue

                # 3. Procesar/Crear Partido
                if not existing_match:
                    existing_match = self.match_service.create(
                        vlr_match_id=vlr_id,
                        status=status,
                        tournament_name=event["name"],
                        vlr_url=f"{self.vlr_base_url}{match_url}",
                        team_a_id=team_models[0].id,
                        team_b_id=team_models[1].id,
                        date=details.get("date"),
                        score_team_a=details.get("scores", [0, 0])[0],
                        score_team_b=details.get("scores", [0, 0])[1],
                        format=self.deduce_format(details.get("scores", [0, 0])[0], details.get("scores", [0, 0])[1])
                    )
                else:
                    self.match_service.update(existing_match.id, {
                        "status": status,
                        "date": details.get("date") or existing_match.date,
                        "score_team_a": details.get("scores", [0, 0])[0],
                        "score_team_b": details.get("scores", [0, 0])[1],
                        "format": self.deduce_format(details.get("scores", [0, 0])[0], details.get("scores", [0, 0])[1])
                    })

                # 4. Procesar Jugadores y Estadísticas
                for p_stats in details["players"]:
                    current_team = team_models[0] if p_stats["team_index"] == 0 else team_models[1]
                    
                    player = self.player_service.repo.get_by_name(p_stats["name"])
                    if not player:
                        player = self.player_service.create(
                            name=p_stats["name"],
                            role=self.infer_role(p_stats["agent"]),
                            region=event["region"],
                            team_id=current_team.id,
                            base_price=10.0,
                            current_price=10.0
                        )
                    elif not player.team_id:
                        self.player_service.update(player.id, {"team_id": current_team.id})

                    if status == "completed":
                        # Limpiar stats previas por si acaso
                        self.db.query(PlayerMatchStats).filter(
                            PlayerMatchStats.match_id == existing_match.id,
                            PlayerMatchStats.player_id == player.id
                        ).delete()
                        
                        self.stats_service.create(
                            match_id=existing_match.id,
                            player_id=player.id,
                            agent=p_stats["agent"],
                            kills=p_stats["kills"],
                            death=p_stats["deaths"],
                            assists=p_stats["assists"],
                            acs=p_stats["acs"],
                            adr=p_stats["adr"],
                            hs_percent=p_stats["hs_percent"],
                            rating=p_stats["rating"],
                            first_kills=p_stats["first_kills"],
                            first_deaths=p_stats["first_deaths"],
                            clutches_won=0 # TODO: Scrape from performance tab if critical
                        )

                if status == "completed":
                    self.match_service.mark_as_processed(existing_match.id)
                    self.update_player_global_stats(existing_match)
                
                total_synced += 1
                
        return total_synced

    def sync_kickoff_2026(self):
        """Redirigir a la sincronización exhaustiva"""
        return self.sync_vct_kickoff_comprehensive()

    def update_player_global_stats(self, match: Match):
        """Actualiza los puntos totales y precios de los jugadores usando media móvil de 3 partidos"""
        for stats in match.player_stats:
            player = stats.player
            # 1. Sumar puntos al total histórico
            new_points = player.points + stats.fantasy_points_earned
            
            # 2. Obtener historial completo para cálculo preciso
            all_stats = self.db.query(PlayerMatchStats)\
                .join(Match)\
                .filter(PlayerMatchStats.player_id == player.id, Match.status == "completed")\
                .all()
            
            # 3. Recalcular precio usando la nueva fórmula estandarizada
            new_price = self.calculate_new_price(all_stats)
            
            self.player_service.update(player.id, {
                "points": round(new_points, 2),
                "current_price": new_price,
                "matches_played": player.matches_played + 1
            })

        # AFTER updating ALL players in the match, recalculate LeagueMember points
        self.recalculate_league_members_points_for_match(match)

    def recalculate_league_members_points_for_match(self, match: Match):
        """
        Calcula los puntos ganados por cada miembro de liga cuyo roster 
        contenga jugadores que participaron en este partido.
        """
        from app.db.models.league import Roster, LeagueMember
        from app.db.models.stats import UserPointsHistory
        from sqlalchemy import func

        # 1. Identificar miembros afectados
        player_ids = [s.player_id for s in match.player_stats]
        affected_rosters = self.db.query(Roster).filter(Roster.player_id.in_(player_ids)).all()
        member_ids = list(set(r.league_member_id for r in affected_rosters))

        for member_id in member_ids:
            member = self.db.query(LeagueMember).filter(LeagueMember.id == member_id).first()
            if not member: continue

            # Recalcular puntos totales del miembro basándose en sus jugadores actuales (o históricos si quisiéramos GW)
            # Por ahora simplificamos: total_points = suma de (player.points) para su roster actual
            # NOTA: En una versión real, esto sería por GameWeek.
            total = self.db.query(func.sum(Player.points))\
                .join(Roster)\
                .filter(Roster.league_member_id == member_id)\
                .scalar() or 0.0
            
            member.total_points = round(total, 2)
            
            # Grabar historial si es la primera vez hoy o tras un partido importante
            self.record_user_history(member.user_id)

    def record_user_history(self, user_id: int):
        """Graba una instantánea de los puntos totales del usuario"""
        from app.db.models.league import LeagueMember
        from app.db.models.stats import UserPointsHistory
        from sqlalchemy import func

        total_points = self.db.query(func.sum(LeagueMember.total_points))\
            .filter(LeagueMember.user_id == user_id)\
            .scalar() or 0.0
        
        # Guardar en historial
        history = UserPointsHistory(
            user_id=user_id,
            total_points=round(total_points, 2),
            recorded_at=datetime.utcnow()
        )
        self.db.add(history)
        self.db.flush()

    def calculate_new_price(self, player_stats_history: list) -> float:
        """
        Calcula el nuevo precio basado en:
        1. Media de puntos (Performance)
        2. Consistencia (Coefficient of Variation)
        3. Bonus por alto rendimiento
        4. Factor de Participación (Veterancy/Sample Size)
        """
        if not player_stats_history:
            return 10.0
            
        # Usar últimos 5 partidos para mayor muestra de consistencia
        recent_stats = sorted(player_stats_history, key=lambda x: x.match.date if x.match and x.match.date else datetime.min, reverse=True)[:5]
        
        if not recent_stats:
            return 10.0
            
        points = [s.fantasy_points_earned for s in recent_stats]
        avg_points = sum(points) / len(points)
        match_count = len(player_stats_history) # Total matches played matter for confidence
        
        # Calcular Desviación Estándar para Consistencia
        if len(points) > 1:
            variance = sum((x - avg_points) ** 2 for x in points) / (len(points) - 1)
            std_dev = variance ** 0.5
        else:
            std_dev = 0.0
            
        # Coeficiente de Variación (CV)
        safe_avg = max(1.0, avg_points)
        cv = std_dev / safe_avg
        
        # Factor de Consistencia: 1 / (1 + CV)
        consistency_factor = 1.0 / (1.0 + cv)
        
        # Performance Booster: Si promedia más de 15 puntos, bonificador extra
        performance_booster = 1.0
        if avg_points > 15.0:
            performance_booster = 1.1 + ((avg_points - 15.0) / 100.0)
            
        # Factor de Participación (Sample Size Penalty)
        # Queremos penalizar HEAVILY a los que tienen pocos partidos.
        # 1 match -> 0.5
        # 2 matches -> 0.7
        # 3 matches -> 0.85
        # 4 matches -> 0.95
        # 5+ matches -> 1.0
        if match_count == 1:
            participation_factor = 0.5
        elif match_count == 2:
            participation_factor = 0.7
        elif match_count == 3:
            participation_factor = 0.85
        elif match_count == 4:
            participation_factor = 0.95
        else:
            participation_factor = 1.0
            
        # Fórmula Final
        # Base (5M) + (Puntos * Multiplicador) * Consistencia * Participación * Booster
        # Multiplicador 2.2 para permitir llegar a 60M con ~25 avg points
        # Ejemplo 25 avg * 2.2 = 55 + 5 = 60
        raw_price = 5.0 + (avg_points * 2.2) * consistency_factor * participation_factor * performance_booster
        
        # Cap final: Min 1M, Max 60M (User Request)
        final_price = max(1.0, min(60.0, raw_price))
        
        return round(final_price, 2)

    def recalibrate_all_prices(self):
        """
        Recalibra PUNTOS y PRECIOS de todos los jugadores.
        1. Recalcula puntos de cada partido.
        2. Recalcula el precio actual basado en la nueva formula de consistencia.
        """
        from app.db.models.match import PlayerMatchStats, Match
        
        # 1. Recalcular puntos en todos los registros históricos de stats
        all_stats = self.db.query(PlayerMatchStats).all()
        logger.info(f"Recalculating points for {len(all_stats)} match stats registries...")
        for stat in all_stats:
            stat.fantasy_points_earned = self.stats_service.calculate_fantasy_points(stat, stat.match)
        self.db.commit()

        # 2. Recalcular precio, puntos totales y PARTIDOS de cada jugador
        players = self.player_service.repo.get_all(limit=1000)
        logger.info(f"Starting Consistency-based recalibration for {len(players)} players...")
        
        for player in players:
            # Obtener TODOS los partidos completados
            # Necesitamos 'match' en la query para ordenar por fecha
            actual_matches = self.db.query(PlayerMatchStats)\
                .join(Match)\
                .filter(PlayerMatchStats.player_id == player.id, Match.status == "completed")\
                .all()
            
            games_count = len(actual_matches)
            total_points = sum(ps.fantasy_points_earned for ps in actual_matches)
            
            # Calcular nuevo precio
            new_price = self.calculate_new_price(actual_matches)
            
            self.player_service.update(player.id, {
                "points": round(total_points, 2),
                "current_price": new_price,
                "matches_played": games_count
            })
        
        self.db.commit()
        logger.info("Universal recalibration (Consistency Weighted) completed.")
        return len(players)

    def infer_region(self, tournament_name: str) -> str:
        if "Pacific" in tournament_name: return "Pacific"
        if "EMEA" in tournament_name: return "EMEA"
        if "Americas" in tournament_name: return "Americas"
        if "China" in tournament_name or "CN" in tournament_name: return "CN"
        return "EMEA"

    def infer_role(self, agent: str) -> str:
        # Mapeo simple de roles por agente
        if not agent: return "Flex"

        roles = {
            "Duelist": ["Jett", "Raze", "Phoenix", "Reyna", "Yoru", "Neon", "Iso", "Waylay"],
            "Initiator": ["Sova", "Breach", "Skye", "KAY/O", "Fade", "Gekko", "Tejo"],
            "Controller": ["Brimstone", "Omen", "Viper", "Astra", "Harbor", "Clove"],
            "Sentinel": ["Killjoy", "Cypher", "Sage", "Chamber", "Deadlock", "Vyse", "Veto"]
        }
        
        agent_clean = agent.strip()
        for role, agents in roles.items():
            # Comparación insensible a mayúsculas
            if any(a.lower() == agent_clean.lower() for a in agents):
                return role
        return "Flex"

    def update_all_player_roles(self):
        """
        Recalcula el rol de todos los jugadores basándose en su historial.
        Lógica:
        - Si juega 3 o más roles distintos -> FLEX
        - Si hay empate en el rol más jugado -> FLEX
        - De lo contrario -> El rol más jugado
        """
        from app.db.models.professional import Player
        from app.db.models.match import PlayerMatchStats
        from collections import Counter

        players = self.db.query(Player).all()
        updated_count = 0

        for player in players:
            stats = self.db.query(PlayerMatchStats).filter(PlayerMatchStats.player_id == player.id).all()
            if not stats or not stats:
                continue
            
            role_counts = Counter()
            for s in stats:
                if s.agent:
                    role = self.infer_role(s.agent)
                    if role != "Flex":
                        role_counts[role] += 1
            
            if not role_counts:
                continue

            unique_roles = list(role_counts.keys())
            
            if len(unique_roles) >= 3:
                new_role = "Flex"
            else:
                counts = role_counts.most_common()
                # Check for tie
                if len(counts) > 1 and counts[0][1] == counts[1][1]:
                    new_role = "Flex"
                else:
                    new_role = counts[0][0]
            
            if player.role != new_role:
                logger.info(f"Updating role for {player.name}: {player.role} -> {new_role}")
                player.role = new_role
                updated_count += 1
        
        self.db.commit()
        logger.info(f"Updated roles for {updated_count} players.")
        return updated_count

    def parse_relative_date(self, time_str: str) -> Optional[datetime]:
        """Convierte strings como '4h 40m ago' o '3d 19h ago' a datetime"""
        if not time_str or "ago" not in time_str:
            return None
        
        now = datetime.utcnow()
        days = 0
        hours = 0
        minutes = 0
        
        # Regex para encontrar patrones
        match_days = re.search(r'(\d+)d', time_str)
        match_hours = re.search(r'(\d+)h', time_str)
        match_mins = re.search(r'(\d+)m', time_str)
        
        if match_days: days = int(match_days.group(1))
        if match_hours: hours = int(match_hours.group(1))
        if match_mins: minutes = int(match_mins.group(1))
        
        return now - timedelta(days=days, hours=hours, minutes=minutes)

    def deduce_format(self, score1: any, score2: any) -> str:
        """Deduce si el partido fue Bo3 o Bo5 basándose en los scores"""
        try:
            s1 = int(score1) if score1 else 0
            s2 = int(score2) if score2 else 0
            
            total = s1 + s2
            if s1 == 3 or s2 == 3 or total >= 4:
                return "Bo5"
            return "Bo3"
        except:
            return "Bo3"
