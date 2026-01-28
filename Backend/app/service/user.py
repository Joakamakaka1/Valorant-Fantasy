from sqlalchemy.ext.asyncio import AsyncSession
from typing import cast, List, Optional
from app.db.models.user import User
from app.auth.security import verify_password, hash_password
from app.core.exceptions import AppError
from app.core.constants import ErrorCode
from app.core.decorators import transactional
from app.repository.user import UserRepository
from app.auth.jwt import decode_refresh_token, create_access_token, create_refresh_token
import jwt
from fastapi import status

class UserService:
    '''
    Servicio que maneja la lógica de negocio de usuarios (Asíncrono).
    '''
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.repo.get_by_email(email)

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.repo.get_by_username(username)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.repo.get(user_id)
    
    async def get_by_id_light(self, user_id: int) -> Optional[User]:
        return await self.repo.get_by_id_light(user_id)

    @transactional
    async def create(self, *, email: str, username: str, password: str, role: str = "user") -> User:
        if await self.repo.get_by_email(email):
            raise AppError(409, ErrorCode.EMAIL_DUPLICATED, "El email ya está registrado")
        
        if await self.repo.get_by_username(username):
            raise AppError(409, ErrorCode.USERNAME_DUPLICATED, "El nombre de usuario ya está registrado")
        
        hashed_pwd = hash_password(password)
        user = User(email=email, username=username, hashed_password=hashed_pwd, role=role)
        return await self.repo.create(user)

    async def authenticate(self, *, email: str, password: str) -> User:
        try:
            user = await self.repo.get_by_email(email)
            if not user:
                raise AppError(404, ErrorCode.EMAIL_NOT_FOUND, "El email no existe")

            if not verify_password(password, cast(str, user.hashed_password)):
                raise AppError(400, ErrorCode.INVALID_PASSWORD, "La contraseña no es correcta")
            return user
        except AppError: raise
        except Exception as e:
            raise AppError(500, ErrorCode.INTERNAL_SERVER_ERROR, str(e))

    async def login(self, *, email: str, password: str) -> dict:
        user = await self.authenticate(email=email, password=password)
        
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }

    @transactional
    async def update(self, user_id: int, user_data: dict) -> User:
        user = await self.repo.get(user_id)
        if not user:
            raise AppError(404, ErrorCode.USER_NOT_FOUND, "El usuario no existe")
        
        if 'email' in user_data and user_data['email'] is not None:
            existing_user = await self.repo.get_by_email(user_data['email'])
            if existing_user and existing_user.id != user_id:
                raise AppError(409, ErrorCode.EMAIL_DUPLICATED, "El email ya está registrado por otro usuario")
        
        if 'username' in user_data and user_data['username'] is not None:
            existing_user = await self.repo.get_by_username(user_data['username'])
            if existing_user and existing_user.id != user_id:
                raise AppError(409, ErrorCode.USERNAME_DUPLICATED, "El nombre de usuario ya está registrado por otro usuario")
        
        if 'password' in user_data and user_data['password'] is not None:
            user_data['hashed_password'] = hash_password(user_data['password'])
            del user_data['password']

        return await self.repo.update(user_id, user_data)

    async def refresh_token(self, refresh_token: str) -> dict:
        try:
            token_data = decode_refresh_token(refresh_token)
            user_id = token_data.get("user_id")
            user = await self.repo.get(user_id)
            if not user:
                raise AppError(status.HTTP_401_UNAUTHORIZED, "USER_NOT_FOUND", "Usuario no encontrado")
                
            new_token_data = {"user_id": user.id, "username": user.username, "role": user.role}
            return {
                "access_token": create_access_token(data=new_token_data),
                "refresh_token": create_refresh_token(data=new_token_data),
                "token_type": "bearer",
                "user": user
            }
        except jwt.ExpiredSignatureError:
            raise AppError(status.HTTP_401_UNAUTHORIZED, "REFRESH_TOKEN_EXPIRED", "Token expirado")
        except jwt.InvalidTokenError:
            raise AppError(status.HTTP_401_UNAUTHORIZED, "INVALID_REFRESH_TOKEN", "Token inválido")

    @transactional
    async def delete(self, user_id: int) -> None:
        if not await self.repo.delete(user_id):
            raise AppError(404, ErrorCode.USER_NOT_FOUND, "El usuario no existe")
