import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
    
    def __init__(self):
        self.vlr_base_url = "https://www.vlr.gg"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
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

    async def scrape_match_details(self, match_page_url: str) -> Optional[Dict[str, Any]]:
        """
        Scraps match details from VLR.gg con reintentos automáticos.
        
        Args:
            match_page_url: Path relativo del partido (e.g., '/12345/heretics-vs-fnatic')
            
        Returns:
            Diccionario con datos del partido o None si falla
        """
        full_url = f"{self.vlr_base_url}{match_page_url}"
        try:
            # Usar método con reintentos
            html_content = await self._fetch_with_retry(full_url)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. Get Teams
            header_links = soup.select(".match-header-link")
            teams = []
            for h in header_links:
                name_elem = h.select_one(".match-header-link-name")
                if not name_elem: continue
                
                name = name_elem.text.strip()
                logo = h.select_one("img")["src"] if h.select_one("img") else None
                url = h.get("href")
                if logo and logo.startswith("//"):
                    logo = "https:" + logo
                teams.append({"name": name, "logo_url": logo, "url": url})

            # 2. Get Player Stats
            all_maps_container = soup.select_one(".vm-stats-game[data-game-id='all']")
            if not all_maps_container:
                all_maps_container = soup
            
            stats_tables = all_maps_container.select("table.wf-table-inset")
            if not stats_tables:
                stats_tables = all_maps_container.select(".wf-table-stats")
            
            players_stats = []
            for team_idx, table in enumerate(stats_tables):
                if team_idx > 1: break # Only first 2 tables
                
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

    @async_retry_with_backoff(max_retries=3, base_delay=1.5, max_delay=20.0)
    async def get_match_urls_from_event(self, event_path: str) -> List[str]:
        """
        Scraps match URLs from an event page con reintentos automáticos.
        
        Args:
            event_path: Path del evento (e.g., '/event/1234/champions-2024')
            
        Returns:
            Lista de URLs de partidos encontrados
        """
        url = f"{self.vlr_base_url}{event_path}"
        try:
            # Usar método con reintentos
            html_content = await self._fetch_with_retry(url)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            match_links = []
            all_links = soup.find_all("a")
            for a in all_links:
                href = a.get("href", "")
                match_pattern = re.search(r'^/(\d{5,})/', href) or re.search(r'/match/(\d{5,})/', href)
                
                if match_pattern and not any(x in href for x in ["/news/", "/event/", "/rankings/", "/forum/", "/player/", "/team/"]):
                    clean_href = href.split("?")[0].split("#")[0]
                    if clean_href not in match_links:
                        match_links.append(clean_href)
            
            return match_links
        except Exception as e:
            logger.error(f"Error fetching match URLs from {event_path}: {e}")
            return []
