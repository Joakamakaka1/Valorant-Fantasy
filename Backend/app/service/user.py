from sqlalchemy.orm import Session
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
    Servicio que maneja la lógica de negocio de usuarios.
    
    Responsabilidades:
    - Validación de duplicados (email, username)
    - Hasheo y verificación de contraseñas
    - Autenticación de usuarios
    - CRUD con validaciones de negocio
    '''
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.repo.get_all(skip=skip, limit=limit)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.repo.get_by_email(email)

    def get_by_username(self, username: str) -> Optional[User]:
        return self.repo.get_by_username(username)

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.repo.get_by_id(user_id)
    
    def get_by_id_light(self, user_id: int) -> Optional[User]:
        """Versión ligera sin relaciones para validaciones rápidas"""
        return self.repo.get_by_id_light(user_id)

    @transactional
    def create(self, *, email: str, username: str, password: str, role: str = "user") -> User:
        '''
        Crea un nuevo usuario validando duplicados y hasheando la contraseña.
        
        Validaciones:
        1. Verifica que el email no esté registrado
        2. Verifica que el username no esté en uso
        3. Hashea la contraseña con bcrypt
        4. Crea el usuario en la base de datos
        '''
        # Validar duplicados
        if self.repo.get_by_email(email):
            raise AppError(409, ErrorCode.EMAIL_DUPLICATED, "El email ya está registrado")
        
        if self.repo.get_by_username(username):
            raise AppError(409, ErrorCode.USERNAME_DUPLICATED, "El nombre de usuario ya está registrado")
        
        # HASHEAR LA CONTRASEÑA
        hashed_pwd = hash_password(password)
        
        # Crear usuario
        user = User(email=email, username=username, hashed_password=hashed_pwd, role=role)
        return self.repo.create(user)

    def authenticate(self, *, email: str, password: str) -> User:
        '''
        Autentica a un usuario verificando email y contraseña.
        
        Proceso:
        1. Busca el usuario por email
        2. Verifica que la contraseña coincida con el hash almacenado
        3. Retorna el usuario si la autenticación es exitosa
        '''
        try:
            user = self.repo.get_by_email(email)
            if not user:
                raise AppError(404, ErrorCode.EMAIL_NOT_FOUND, "El email no existe")

            # VERIFICAR CONTRASEÑA HASHEADA
            if not verify_password(password, cast(str, user.hashed_password)):
                raise AppError(400, ErrorCode.INVALID_PASSWORD, "La contraseña no es correcta")
            return user
        except AppError:
            raise
        except Exception as e:
            raise AppError(500, ErrorCode.INTERNAL_SERVER_ERROR, str(e))

    def login(self, *, email: str, password: str) -> dict:
        '''
        Autentica un usuario y genera tokens JWT.
        
        Proceso:
        1. Autentica al usuario (email + contraseña)
        2. Genera tokens JWT (access + refresh)
        3. Retorna los tokens y datos del usuario
        '''
        # Autenticar usuario
        user = self.authenticate(email=email, password=password)
        
        # Crear tokens JWT
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
        
        # Retornar token y datos del usuario
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }

    @transactional
    def update(self, user_id: int, user_data: dict) -> User:
        '''
        Actualiza un usuario validando duplicados en email y username.
        Si se actualiza la contraseña, la hashea automáticamente.
        '''
        user = self.repo.get_by_id(user_id)
        if not user:
            raise AppError(404, ErrorCode.USER_NOT_FOUND, "El usuario no existe")
        
        # Validar email duplicado
        if 'email' in user_data and user_data['email'] is not None:
            existing_user = self.repo.get_by_email(user_data['email'])
            if existing_user and existing_user.id != user_id:
                raise AppError(409, ErrorCode.EMAIL_DUPLICATED, "El email ya está registrado por otro usuario")
        
        # Validar username duplicado
        if 'username' in user_data and user_data['username'] is not None:
            existing_user = self.repo.get_by_username(user_data['username'])
            if existing_user and existing_user.id != user_id:
                raise AppError(409, ErrorCode.USERNAME_DUPLICATED, "El nombre de usuario ya está registrado por otro usuario")
        
        # SI SE ESTÁ ACTUALIZANDO LA CONTRASEÑA, HASHEARLA PRIMERO
        if 'password' in user_data and user_data['password'] is not None:
            hashed = hash_password(user_data['password'])
            user_data['hashed_password'] = hashed
            del user_data['password']

        return self.repo.update(user_id, user_data)

    def refresh_token(self, refresh_token: str) -> dict:
        '''
        Renueva un Access Token usando un Refresh Token válido.
        
        Valida que:
        1. El refresh token sea válido y no haya expirado
        2. El usuario aún exista en la base de datos
        3. Genera nuevos tokens (access y refresh)
        '''
        try:
            # Decodificar y validar el refresh token
            token_data = decode_refresh_token(refresh_token)
                
            # Verificar que el usuario aún existe en la BD
            user_id = token_data.get("user_id")
            user = self.repo.get_by_id(user_id)
            if not user:
                raise AppError(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    code="USER_NOT_FOUND",
                    message="Usuario no encontrado"
                )
                
            # Crear nuevos tokens
            new_token_data = {
                "user_id": user.id,
                "username": user.username,
                "role": user.role
            }
            access_token = create_access_token(data=new_token_data)
            new_refresh_token = create_refresh_token(data=new_token_data)
            
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "user": user
            }
        
        except jwt.ExpiredSignatureError:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="REFRESH_TOKEN_EXPIRED",
                message="El refresh token ha expirado. Por favor, inicia sesión de nuevo."
            )
        except jwt.InvalidTokenError as e:
            raise AppError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_REFRESH_TOKEN",
                message=f"Refresh token inválido: {str(e)}"
            )

    @transactional
    def delete(self, user_id: int) -> None:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise AppError(404, ErrorCode.USER_NOT_FOUND, "El usuario no existe")

        self.repo.delete(user)