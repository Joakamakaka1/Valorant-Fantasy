from typing import Generic, TypeVar, Type, Optional, List, Any, Union, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload
from app.db.base import Base

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
        self.db.add(obj_in)
        await self.db.flush()
        if refresh:
            await self.db.refresh(obj_in)
            if options:
                # If options are provided, re-fetch with those options to ensure relationships are loaded
                # This replaces the need for manual populate_existing workarounds in simple cases
                return await self.get(obj_in.id, options=options)
        return obj_in

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
