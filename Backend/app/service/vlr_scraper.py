import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging
import asyncio
from typing import List, Optional, Dict, Any, Callable, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

def async_retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (httpx.HTTPError, httpx.TimeoutException, httpx.ConnectError)
):
    """
    Decorador para reintentos con Exponential Backoff en funciones async.
    
    Incluye manejo inteligente de:
    - 429 (Rate Limiting): Respeta header Retry-After si está presente
    - 503 (Service Unavailable): Backoff exponencial
    - Otros errores HTTP: No reintentar (fallar rápido)
    
    Args:
        max_retries: Número máximo de reintentos
        base_delay: Delay inicial en segundos
        max_delay: Delay máximo en segundos
        exponential_base: Base para el cálculo exponencial
        exceptions: Tupla de excepciones que disparan reintento
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                
                except httpx.HTTPStatusError as e:
                    last_exception = e
                    
                    # Manejo específico de 429 (Rate Limiting)
                    if e.response.status_code == 429:
                        # Intentar leer Retry-After header
                        retry_after = e.response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                delay = min(float(retry_after), max_delay)
                            except ValueError:
                                # Retry-After puede ser una fecha, usar backoff exponencial
                                delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        else:
                            delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        
                        logger.warning(
                            f"Rate limit hit (429) in {func.__name__}. "
                            f"Retrying after {delay:.2f}s (attempt {attempt + 1}/{max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    
                    # Manejo de 503 (Service Unavailable)
                    if e.response.status_code == 503:
                        if attempt == max_retries:
                            logger.error(f"Max retries reached for 503 in {func.__name__}")
                            raise
                        
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)
                        logger.warning(
                            f"Service unavailable (503) in {func.__name__}. "
                            f"Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})..."
                        )
                        await asyncio.sleep(delay)
                        continue
                    
                    # Otros errores HTTP: no reintentar (fail fast)
                    logger.error(
                        f"HTTP error {e.response.status_code} in {func.__name__}: {e}. "
                        f"Not retrying."
                    )
                    raise
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Max retries ({max_retries}) reached for {func.__name__}: {e}")
                        raise
                    
                    # Calcular delay con exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
            
            # Esto no debería alcanzarse, pero por seguridad
            raise last_exception
        
        return wrapper
    return decorator



class VLRScraper:
    """
    Scraper para VLR.gg con reintentos automáticos y manejo robusto de errores.
    
    Features:
    - User-Agent rotativo para evitar detección
    - Manejo inteligente de 429/503 con reintentos
    - Transaccionalidad delegada al servicio que lo usa
    
    NOTA IMPORTANTE - Transaccionalidad Atómica:
    ============================================
    Este scraper NO maneja transacciones de base de datos directamente.
    La transaccionalidad atómica debe implementarse en el servicio que use este scraper.
    
    Ejemplo de uso con transaccionalidad:
    
    ```python
    async def sync_match(self, match_url: str):
        scraper = VLRScraper()
        
        # Opción 1: Usar async with db.begin() para transacción automática
        async with self.db.begin():
            match_data = await scraper.scrape_match_details(match_url)
            if not match_data:
                raise Exception("Failed to scrape match")
            
            # Crear/actualizar todos los registros
            await self._save_teams(match_data['teams'])
            await self._save_players(match_data['players'])
            await self._save_match(match_data)
            # Si algo falla aquí, toda la transacción se revierte automáticamente
        
        # Opción 2: Manejo manual con rollback
        try:
            match_data = await scraper.scrape_match_details(match_url)
            await self._save_all_data(match_data)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise
    ```
    """
    
    # Pool de User-Agents para rotación (evitar detección)
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    ]
    
    def __init__(self):
        import random
        self.vlr_base_url = "https://www.vlr.gg"
        # User-Agent rotativo + headers para simular navegación orgánica
        self.headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.vlr.gg/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    @async_retry_with_backoff(max_retries=3, base_delay=2.0, max_delay=30.0)
    async def _fetch_with_retry(self, url: str) -> str:
        """
        Realiza una petición HTTP con reintentos automáticos.
        
        Args:
            url: URL completa a consultar
            
        Returns:
            Contenido HTML de la respuesta
            
        Raises:
            httpx.HTTPError: Si falla después de todos los reintentos
        """
        async with httpx.AsyncClient(headers=self.headers, timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    def _detect_match_status(self, soup: BeautifulSoup) -> str:
        """
        Detecta el estado actual del partido desde la página.
        
        Returns:
            "live", "upcoming", o "completed"
        """
        # Buscar indicador de LIVE en el header
        live_indicator = soup.select_one(".match-header-note .match-header-note-text")
        if live_indicator and "LIVE" in live_indicator.text.upper():
            return "live"
        
        # Alternativa: buscar badge en el vs-score
        live_badge = soup.select_one(".match-header-vs-note")
        if live_badge and "LIVE" in live_badge.text.upper():
            return "live"
        
        # Buscar badge o notificación de final
        final_badge = soup.select_one(".match-header-vs-note")
        if final_badge and ("FINAL" in final_badge.text.upper() or "COMPLETE" in final_badge.text.upper()):
            return "completed"
        
        # Si hay scores válidos (ambos > 0 y alguno ganó), probablemente es completed
        score_container = soup.select_one(".match-header-vs-score")
        if score_container:
            score_spans = score_container.select("span.js-spoiler")
            if len(score_spans) >= 2:
                try:
                    score_a = int(score_spans[0].text.strip())
                    score_b = int(score_spans[1].text.strip())
                    # Si hay un ganador (uno tiene 2 en BO3), es completed
                    if (score_a == 2 or score_b == 2) and (score_a != score_b):
                        return "completed"
                except (ValueError, AttributeError):
                    pass
        
        # Por defecto, upcoming
        return "upcoming"

    async def scrape_match_details(self, match_page_url: str) -> Optional[Dict[str, Any]]:
        full_url = f"{self.vlr_base_url}{match_page_url}"
        try:
            html_content = await self._fetch_with_retry(full_url)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. Get Teams
            header_links = soup.select(".match-header-link")
            teams = []
            for h in header_links:
                name_elem = h.select_one(".match-header-link-name")
                if not name_elem: continue
                name = name_elem.text.strip()
                
                # Skip empty or invalid team names immediately
                if not name or len(name) < 2:
                    continue
                    
                logo = h.select_one("img")["src"] if h.select_one("img") else None
                url = h.get("href")
                if logo and logo.startswith("//"):
                    logo = "https:" + logo
                teams.append({"name": name, "logo_url": logo, "url": url})
            
            # VALIDACIÓN CRÍTICA: Asegurar que tenemos exactamente 2 equipos
            if len(teams) != 2:
                logger.error(f"Team extraction failed for {match_page_url}: Found {len(teams)} teams, expected 2. Teams: {[t['name'] for t in teams]}")
                return None
            
            # Validar que los nombres no estén completamente vacíos
            # NOTA: Permitimos "TBD" para matches upcoming donde aún no se conocen los equipos
            for team in teams:
                if not team["name"] or len(team["name"]) < 2:
                    logger.error(f"Empty/invalid team name in {match_page_url}: '{team['name']}'")
                    return None


            # ---------------------------------------------------------
            # 2. Get Player Stats
            # ---------------------------------------------------------
            
            # Intento 1: Buscar el contenedor estándar 'all'
            all_maps_container = soup.select_one(".vm-stats-game[data-game-id='all']")
            
            # Intento 2: Si falla, buscar la pestaña que diga "All Maps" para obtener el ID correcto
            if not all_maps_container:
                nav_items = soup.select(".vm-stats-gamesnav-item")
                for item in nav_items:
                    # Buscamos texto "All Maps" o "Overall"
                    if "all" in item.text.lower() or "overall" in item.text.lower():
                        target_id = item.get("data-game-id")
                        if target_id:
                            all_maps_container = soup.select_one(f".vm-stats-game[data-game-id='{target_id}']")
                            break
            
            # Intento 3: Si sigue sin haber contenedor (ej. BO1), usamos el PRIMER contenedor de juego encontrado
            # pero NO 'soup' entero, para evitar mezclar tablas.
            if not all_maps_container:
                all_maps_container = soup.select_one(".vm-stats-game")

            # Si tras todo esto sigue siendo None, fallback a soup con precaución (caso muy raro)
            if not all_maps_container:
                all_maps_container = soup

            stats_tables = all_maps_container.select("table.wf-table-inset")
            if not stats_tables:
                stats_tables = all_maps_container.select(".wf-table-stats")
            
            players_stats = []
            # Usamos un set para evitar duplicados si por error leemos tablas parciales
            processed_players = set()

            for team_idx, table in enumerate(stats_tables):
                # IMPORTANTE: Si estamos en el modo "soup" (fallback total), solo queremos las 2 primeras.
                # Si hemos encontrado el contenedor correcto ('all'), procesamos lo que haya dentro (normalmente 2 tablas).
                if team_idx > 1 and all_maps_container == soup: 
                    break 
                
                # Validación extra: Asegurar que es una tabla de stats (tiene K/D/A)
                # Esto evita leer tablas de historial o economia
                headers_text = table.text.upper()
                if "K" not in headers_text or "D" not in headers_text or "A" not in headers_text:
                    continue

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
                for row in rows:
                    name_elem = row.select_one(".mod-player") or row.select_one(".text-of")
                    if not name_elem: continue
                    
                    player_name = name_elem.text.strip().split("\n")[0].strip()
                    if not player_name or len(player_name) < 2: continue
                    
                    # Evitar duplicados (si por error leemos la misma tabla dos veces)
                    if player_name in processed_players:
                        continue
                    processed_players.add(player_name)
                    
                    agent_img = row.select_one(".mod-agents img")
                    agent = "Unknown"
                    if agent_img:
                        agent = agent_img.get("title") or agent_img.get("alt") or "Unknown"
                    
                    cols = row.select("td")
                    
                    def get_val(key, is_int=False):
                        idx = col_map.get(key)
                        if idx is None or idx >= len(cols): return 0 if is_int else 0.0
                        raw_text = cols[idx].text.strip().replace("/", "").replace("%", "").strip()
                        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
                        if not lines: return 0 if is_int else 0.0
                        val_str = lines[0]
                        try:
                            return int(val_str) if is_int else float(val_str)
                        except: return 0 if is_int else 0.0

                    kast = get_val("kast")
                    rating = get_val("rating")
                    if rating == 0.0 and kast > 0:
                        rating = kast / 100.0

                    players_stats.append({
                        "name": player_name,
                        "agent": agent,
                        "team_index": team_idx % 2, # Asegurar que sea 0 o 1 incluso si hay multiples tablas
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

            # Upcoming Fallback 
            if not players_stats:
                match_players = soup.select(".match-header-vs .match-header-vs-players")
                for i, container in enumerate(match_players):
                    if i > 1: break
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

            # 3. Date and Scores
            date_info = soup.select_one(".moment-tz-convert")
            match_date = None
            if date_info and date_info.get("data-utc-ts"):
                try:
                    match_date = datetime.strptime(date_info.get("data-utc-ts"), "%Y-%m-%d %H:%M:%S")
                except: pass

            # Detectar status del partido
            status = self._detect_match_status(soup)
            
            # Mejorar extracción de scores con múltiples fallbacks
            scores = [0, 0]
            
            if status in ["live", "completed"]:
                score_container = soup.select_one(".match-header-vs-score")
                
                if score_container:
                    # Método 1: Buscar spans con clase js-spoiler
                    score_spans = score_container.select("span.js-spoiler")
                    if len(score_spans) >= 2:
                        try:
                            scores[0] = int(score_spans[0].text.strip())
                            scores[1] = int(score_spans[1].text.strip())
                            logger.debug(f"Scores extracted (method 1): {scores}")
                        except (ValueError, AttributeError):
                            pass
                    
                    # Método 2 (Fallback): Buscar divs hijos directos
                    if scores == [0, 0]:
                        score_divs = score_container.find_all("div", recursive=False)
                        score_texts = []
                        for div in score_divs:
                            text = div.get_text(strip=True)
                            # Filtrar solo números de 1 dígito (0-3 típicamente en BO3/BO5)
                            if text.isdigit() and len(text) == 1:
                                score_texts.append(int(text))
                        
                        if len(score_texts) >= 2:
                            scores[0] = score_texts[0]
                            scores[1] = score_texts[1]
                            logger.debug(f"Scores extracted (method 2): {scores}")
                    
                    # Método 3 (Último recurso): Regex pero solo números de 1 dígito
                    if scores == [0, 0]:
                        # Buscar solo dígitos individuales (0-9) evitando fechas/timestamps
                        single_digits = re.findall(r'\b(\d)\b', score_container.text)
                        if len(single_digits) >= 2:
                            scores[0] = int(single_digits[0])
                            scores[1] = int(single_digits[1])
                            logger.debug(f"Scores extracted (method 3): {scores}")
                    
                    # Validación final: scores deben ser razonables (0-3 normalmente)
                    if scores[0] > 5 or scores[1] > 5:
                        logger.warning(f"Invalid scores detected: {scores}, resetting to [0, 0]")
                        scores = [0, 0]

            return {
                "teams": teams,
                "players": players_stats,
                "date": match_date,
                "scores": scores,
                "status": status  # Incluir status detectado
            }
        except Exception as e:
            logger.error(f"Error scraping match {match_page_url}: {e}")
            return None

    @async_retry_with_backoff(max_retries=3, base_delay=1.5, max_delay=20.0)
    async def get_match_urls_from_event(self, event_path: str) -> List[Dict[str, str]]:
        """
        Scraps match URLs from an event page con reintentos automáticos.
        Retorna también el status detectado (live/upcoming/completed).
        
        Args:
            event_path: Path del evento (e.g., '/event/1234/champions-2024')
            
        Returns:
            Lista de dicts con {"url": str, "status": str}
        """
        url = f"{self.vlr_base_url}{event_path}"
        try:
            # Usar método con reintentos
            html_content = await self._fetch_with_retry(url)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            match_data = []
            processed_urls = set()
            
            # Buscar match cards (tienen la clase wf-module-item)
            all_links = soup.find_all("a", class_="wf-module-item")
            
            for match_card in all_links:
                href = match_card.get("href", "")
                match_pattern = re.search(r'^/(\d{5,})/', href) or re.search(r'/match/(\d{5,})/', href)
                
                if not match_pattern:
                    continue
                    
                if any(x in href for x in ["/news/", "/event/", "/rankings/", "/forum/", "/player/", "/team/"]):
                    continue
                
                clean_href = href.split("?")[0].split("#")[0]
                
                if clean_href in processed_urls:
                    continue
                
                processed_urls.add(clean_href)
                
                # Detectar status desde la card del partido
                status_elem = match_card.select_one(".ml-status")
                eta_elem = match_card.select_one(".ml-eta")
                
                status = "upcoming"  # Default
                if status_elem and "LIVE" in status_elem.text.upper():
                    status = "live"
                elif eta_elem and "ago" in eta_elem.text:
                    status = "completed"
                
                match_data.append({
                    "url": clean_href,
                    "status": status
                })
            
            logger.info(f"Found {len(match_data)} matches from {event_path} (live: {sum(1 for m in match_data if m['status'] == 'live')}, completed: {sum(1 for m in match_data if m['status'] == 'completed')}, upcoming: {sum(1 for m in match_data if m['status'] == 'upcoming')})")
            return match_data
        except Exception as e:
            logger.error(f"Error fetching match URLs from {event_path}: {e}")
            return []


    @async_retry_with_backoff(max_retries=3, base_delay=2.0)
    async def scrape_events_page(self) -> List[Dict[str, Any]]:
        """
        Scrapea https://www.vlr.gg/events/?tier=60 para obtener estado de torneos VCT.
        
        Returns:
            List[Dict]: [
                {
                    "name": "Valorant Masters Santiago 2026",
                    "vlr_event_id": 2760,
                    "vlr_event_path": "/event/2760/valorant-masters-santiago-2026",
                    "status": "upcoming" | "ongoing" | "completed",
                    "dates": "Feb 28–Mar 16"
                }
            ]
        """
        url = "https://www.vlr.gg/events/?tier=60"
        logger.info(f"🔍 Scraping events page: {url}")
        
        html = await self._fetch_with_retry(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        events = []
        
        # Filtrar torneos VCT principales:
        # - Kickoff 2026: 2682 (Americas), 2684 (EMEA), 2683 (Pacific), 2685 (China)
        # - Masters Santiago 2026: 2760
        # - Masters London 2026: 2765
        # - Champions 2026: 2766
        TARGET_EVENT_IDS = {2682, 2683, 2684, 2685, 2760, 2765, 2766}
        
        # VLR.gg organiza eventos en secciones: UPCOMING, ONGOING, COMPLETED
        # Buscar todas las secciones de eventos
        for section in soup.find_all('div', class_='events-container-col'):
            # Determinar el status de la sección desde el header
            status_header = section.find('div', class_='wf-label')
            if not status_header:
                continue
            
            status_text = status_header.text.strip().lower()
            
            # Mapear texto a status
            if 'upcoming' in status_text:
                status = 'UPCOMING'  # Uppercase for enum
            elif 'ongoing' in status_text:
                status = 'ONGOING'   # Uppercase for enum
            else:
                status = 'COMPLETED' # Uppercase for enum
            
            # Extraer eventos de esta sección
            for event_card in section.find_all('a', class_='event-item'):
                try:
                    # Nombre del evento
                    title_elem = event_card.find('div', class_='event-item-title')
                    if not title_elem:
                        continue
                    
                    event_name = title_elem.text.strip()
                    
                    # Extraer ID del evento desde href: /event/2760/...
                    href = event_card.get('href', '')
                    event_id_match = re.search(r'/event/(\d+)/', href)
                    if not event_id_match:
                        continue
                    
                    event_id = int(event_id_match.group(1))
                    
                    # Solo incluir los 3 torneos principales
                    if event_id not in TARGET_EVENT_IDS:
                        continue
                    
                    # Extraer fechas
                    dates_elem = event_card.find('div', class_='event-item-desc-item-value')
                    dates = dates_elem.text.strip() if dates_elem else "TBD"
                    
                    events.append({
                        "name": event_name,
                        "vlr_event_id": event_id,
                        "vlr_event_path": href,
                        "status": status,  # Already uppercase from mapping above
                        "dates": dates
                    })
                    
                    logger.info(f"  📅 {event_name} ({event_id}): {status}")
                
                except Exception as e:
                    logger.warning(f"Error parsing event card: {e}")
                    continue
        
        logger.info(f"✅ Scraped {len(events)} tournaments from events page")
        return events
    
    @async_retry_with_backoff(max_retries=3, base_delay=2.0)
    async def scrape_tournament_teams(self, event_path: str) -> List[str]:
        """
        Scrapea la página Overview de un torneo para obtener equipos participantes.
        
        Example: https://www.vlr.gg/event/2760/valorant-masters-santiago-2026
        
        Args:
            event_path: Path del evento (e.g., "/event/2760/valorant-masters-santiago-2026")
        
        Returns:
            List[str]: ["Team Liquid", "Fnatic", "Sentinels", "Leviatán", ...]
        """
        # Asegurarse de que la URL apunta a la página Overview (no /matches)
        if '/matches' in event_path:
            event_path = event_path.split('/matches')[0]
        
        url = f"https://www.vlr.gg{event_path}"
        logger.info(f"🔍 Scraping tournament teams from: {url}")
        
        html = await self._fetch_with_retry(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        teams = set()  # Usar set para evitar duplicados
        
        # Los equipos aparecen en la sección de bracket/participants
        # Buscar todos los elementos con nombre de equipo
        
        # Método 1: Buscar en el bracket
        for team_elem in soup.find_all('div', class_='event-team-name'):
            team_name = team_elem.text.strip()
            if team_name:
                teams.add(team_name)
        
        # Método 2: Buscar en la lista de participantes (si existe)
        for team_link in soup.find_all('a', class_='event-team'):
            team_name_elem = team_link.find('div', class_='event-team-name')
            if team_name_elem:
                team_name = team_name_elem.text.strip()
                if team_name:
                    teams.add(team_name)
        
        # Método 3: Buscar divs con wf-title (teams in groups)
        for group_section in soup.find_all('div', class_='event-group'):
            for team_div in group_section.find_all('div', class_='wf-title'):
                # Verificar que no sea un header de grupo
                if 'group' not in team_div.text.lower():
                    team_name = team_div.text.strip()
                    if team_name and len(team_name) > 2:  # Filtrar nombres muy cortos
                        teams.add(team_name)
        
        teams_list = sorted(list(teams))
        logger.info(f"✅ Found {len(teams_list)} teams: {', '.join(teams_list[:5])}{'...' if len(teams_list) > 5 else ''}")
        
        return teams_list
