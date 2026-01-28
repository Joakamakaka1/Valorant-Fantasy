from typing import Generic, TypeVar, Type, Optional, List, Any, Union, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError
from app.db.base import Base
from app.core.exceptions import AlreadyExistsException
import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any, options: Optional[List[Any]] = None) -> Optional[ModelType]:
        query = select(self.model).where(self.model.id == id)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_id(self, id: Any, options: Optional[List[Any]] = None) -> Optional[ModelType]:
        return await self.get(id, options)

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        options: Optional[List[Any]] = None
    ) -> List[ModelType]:
        query = select(self.model).offset(skip).limit(limit)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: ModelType, refresh: bool = True, options: Optional[List[Any]] = None) -> ModelType:
        """
        Crea un nuevo registro en la base de datos.
        
        Args:
            obj_in: Instancia del modelo a crear
            refresh: Si es True, recarga el objeto desde la BD después de crearlo
            options: Opciones de carga para relaciones (ej: selectinload)
        
        Returns:
            ModelType: El objeto creado
            
        Raises:
            AlreadyExistsException: Si ya existe un registro que viola una restricción UNIQUE
        
        Example:
            try:
                new_member = await league_member_repo.create(LeagueMember(...))
            except AlreadyExistsException as e:
                # El usuario ya está en esta liga
                return {"error": "Usuario ya está en la liga"}
        """
        try:
            self.db.add(obj_in)
            await self.db.flush()
            if refresh:
                await self.db.refresh(obj_in)
                if options:
                    # If options are provided, re-fetch with those options to ensure relationships are loaded
                    # This replaces the need for manual populate_existing workarounds in simple cases
                    return await self.get(obj_in.id, options=options)
            return obj_in
        except IntegrityError as e:
            # Rollback para limpiar la sesión asíncrona
            await self.db.rollback()
            
            # Extraer información del error
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            
            # Determinar qué constraint fue violada
            constraint_name = "desconocida"
            if "uq_league_user" in error_msg:
                constraint_name = "usuario en liga"
                details = {"constraint": "uq_league_user", "message": "El usuario ya está en esta liga"}
            elif "uq_roster_player" in error_msg:
                constraint_name = "jugador en roster"
                details = {"constraint": "uq_roster_player", "message": "El jugador ya está en este roster"}
            elif "uq_player_match_stats" in error_msg:
                constraint_name = "estadísticas de jugador"
                details = {"constraint": "uq_player_match_stats", "message": "Las estadísticas de este jugador en este partido ya existen"}
            elif "Duplicate entry" in error_msg or "UNIQUE constraint" in error_msg:
                constraint_name = "registro"
                details = {"message": "Ya existe un registro con estos datos"}
            else:
                # Otro tipo de IntegrityError (FK, NOT NULL, etc.)
                logger.error(f"IntegrityError no relacionado con duplicados: {error_msg}")
                raise  # Re-lanzar para que sea manejado por el handler global
            
            # Loggear advertencia
            logger.warning(
                f"Intento de insertar duplicado en {self.model.__tablename__}: {constraint_name}. "
                f"Error: {error_msg}"
            )
            
            # Lanzar excepción personalizada
            raise AlreadyExistsException(
                resource=self.model.__tablename__,
                details=details
            )

    async def get_by_fields(
        self, 
        options: Optional[List[Any]] = None, 
        **filters
    ) -> Optional[ModelType]:
        """
        Búsqueda genérica usando filtros dinámicos.
        
        Args:
            options: Lista de opciones de carga (e.g., selectinload, joinedload)
            **filters: Pares clave-valor para filtrar (e.g., email='test@test.com', username='john')
        
        Returns:
            Primer objeto que coincida con los filtros o None
        
        Example:
            user = await repo.get_by_fields(email='test@example.com')
            team = await repo.get_by_fields(options=[selectinload(Team.players)], name='TH')
        """
        query = select(self.model).filter_by(**filters)
        if options:
            query = query.options(*options)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update(
        self, 
        id: Any, 
        obj_in: Union[Dict[str, Any], ModelType], 
        options: Optional[List[Any]] = None
    ) -> Optional[ModelType]:
        obj = await self.get(id)
        if not obj:
            return None
        
        # Pydantic V2: usar model_dump() en lugar de dict()
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Verificar si es un modelo Pydantic V2
            update_data = (
                obj_in.model_dump(exclude_unset=True) 
                if hasattr(obj_in, 'model_dump') 
                else obj_in.dict(exclude_unset=True)
            )
        
        for field, value in update_data.items():
            if hasattr(obj, field) and value is not None:
                setattr(obj, field, value)
        
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        
        if options:
             return await self.get(id, options=options)
             
        return obj

    async def delete(self, id: Any) -> bool:
        obj = await self.get(id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.flush()
        return True
