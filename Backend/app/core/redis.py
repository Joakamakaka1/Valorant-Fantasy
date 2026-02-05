import json
import logging
from typing import Optional
from redis import asyncio as aioredis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

class RedisCache:
    """
    Manager de caché Redis con graceful degradation.
    
    Si Redis falla, la aplicación hace fallback a BD sin caerse.
    Incluye logging de CACHE_HIT y CACHE_MISS para monitoreo.
    """
    
    def __init__(self, redis_url: str, decode_responses: bool = True):
        """
        Inicializa conexión a Redis.
        
        Args:
            redis_url: URL de conexión (redis://host:port/db)
            decode_responses: Si True, decodifica bytes a strings automáticamente
        """
        self.redis_url = redis_url
        self.decode_responses = decode_responses
        self._client: Optional[aioredis.Redis] = None
        self._connected = False
    
    async def _ensure_connection(self) -> bool:
        """
        Asegura que hay conexión a Redis.
        
        Returns:
            True si está conectado, False si falló (graceful degradation)
        """
        if self._client is None:
            try:
                self._client = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=self.decode_responses
                )
                # Test de conexión
                await self._client.ping()
                self._connected = True
                logger.info("Redis connection established successfully")
                return True
            except (ConnectionError, TimeoutError, RedisError) as e:
                logger.error(f"Redis connection failed: {type(e).__name__} - {str(e)}")
                logger.warning("Graceful degradation: Application will fallback to database")
                self._connected = False
                self._client = None
                return False
        
        if not self._connected:
            return False
        
        return True
    
    async def get(self, key: str) -> Optional[dict]:
        """
        Obtiene valor de Redis deserializado como JSON.
        
        Args:
            key: Clave a buscar
            
        Returns:
            dict si existe y Redis está disponible, None si no existe o hay error
        """
        if not await self._ensure_connection():
            # Redis no disponible, fallback a DB (caller manejará)
            return None
        
        try:
            value = await self._client.get(key)
            if value is None:
                logger.info(f"CACHE_MISS: {key}")
                return None
            
            # Deserializar JSON
            data = json.loads(value) if isinstance(value, str) else value
            logger.info(f"CACHE_HIT: {key}")
            return data
        
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Redis GET error for key '{key}': {type(e).__name__} - {str(e)}")
            return None
    
    async def set(self, key: str, value: dict, ttl: Optional[int] = None) -> bool:
        """
        Guarda valor en Redis serializado como JSON.
        
        Args:
            key: Clave
            value: Diccionario a guardar (será serializado a JSON)
            ttl: Tiempo de vida en segundos (None = sin expiración)
            
        Returns:
            True si se guardó exitosamente, False si hubo error
        """
        if not await self._ensure_connection():
            # Redis no disponible, no cachear (no es fatal)
            logger.debug(f"Cannot cache key '{key}': Redis unavailable")
            return False
        
        try:
            # Serializar a JSON
            serialized = json.dumps(value, ensure_ascii=False)
            
            if ttl:
                await self._client.setex(key, ttl, serialized)
                logger.debug(f"CACHE_SET: {key} (TTL: {ttl}s)")
            else:
                await self._client.set(key, serialized)
                logger.debug(f"CACHE_SET: {key} (No TTL)")
            
            return True
        
        except (RedisError, TypeError) as e:
            logger.error(f"Redis SET error for key '{key}': {type(e).__name__} - {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Elimina una clave de Redis.
        
        Args:
            key: Clave a eliminar
            
        Returns:
            True si se eliminó o no existía, False si hubo error
        """
        if not await self._ensure_connection():
            logger.debug(f"Cannot delete key '{key}': Redis unavailable")
            return False
        
        try:
            deleted = await self._client.delete(key)
            if deleted > 0:
                logger.info(f"CACHE_DELETE: {key}")
            else:
                logger.debug(f"CACHE_DELETE (not found): {key}")
            return True
        
        except RedisError as e:
            logger.error(f"Redis DELETE error for key '{key}': {type(e).__name__} - {str(e)}")
            return False
    
    async def delete_by_prefix(self, prefix: str) -> int:
        """
        Elimina todas las claves que comienzan con un prefijo.
        
        Args:
            prefix: Prefijo de las claves a eliminar (ej: "stats:match:")
            
        Returns:
            Número de claves eliminadas, 0 si hubo error o no hay claves
        """
        if not await self._ensure_connection():
            logger.debug(f"Cannot delete by prefix '{prefix}*': Redis unavailable")
            return 0
        
        try:
            # Buscar todas las claves con el prefijo
            pattern = f"{prefix}*"
            keys = []
            async for key in self._client.scan_iter(match=pattern, count=100):
                keys.append(key)
            
            if not keys:
                logger.debug(f"CACHE_DELETE_PREFIX (no keys found): {prefix}*")
                return 0
            
            # Eliminar en batch
            deleted = await self._client.delete(*keys)
            logger.info(f"CACHE_DELETE_PREFIX: {prefix}* ({deleted} keys deleted)")
            return deleted
        
        except RedisError as e:
            logger.error(f"Redis DELETE_PREFIX error for '{prefix}*': {type(e).__name__} - {str(e)}")
            return 0
    
    async def close(self):
        """Cierra la conexión a Redis."""
        if self._client:
            try:
                await self._client.close()
                logger.info("Redis connection closed")
            except RedisError as e:
                logger.error(f"Error closing Redis connection: {type(e).__name__} - {str(e)}")
            finally:
                self._client = None
                self._connected = False
