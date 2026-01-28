from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user import User
from typing import List, Optional
from app.repository.base import BaseRepository

class UserRepository(BaseRepository[User]):
    '''
    Repositorio de usuarios - Capa de acceso a datos (Asíncrona).
    '''
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_by_id_light(self, user_id: int) -> Optional[User]:
        # Alias or specialized query if 'light' meant avoiding some joins (though User usually doesn't have default eager loads here)
        return await self.get(user_id)
