from typing import List
from fastapi import APIRouter, Depends, status

from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from app.service.image import image_service
from app.service.user import UserService
from app.schemas.user import UserCreate, UserUpdate, UserOut, UserLogin, Token, RoleUpdate, TokenRefresh
from app.core.exceptions import AppError
from app.api.deps import get_user_service
from app.auth.deps import get_current_user, allow_admin, check_self_or_admin

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_me(current_user = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    """
    Obtener el perfil del usuario actual autenticado.
    """
    return service.get_by_id(current_user.user_id)


@router.get("/", response_model=List[UserOut], status_code=status.HTTP_200_OK)
def get_all_users(
    skip: int = 0,
    limit: int = 50,
    service: UserService = Depends(get_user_service),
    admin_user = Depends(allow_admin)
):
    """
    Obtener todos los usuarios.
    Solo accesible para administradores.
    """
    return service.get_all(skip=skip, limit=limit)

@router.get("/username/{username}", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_user_by_username(
    username: str, 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    user = service.get_by_username(username=username.strip())
    if not user:
        raise AppError(404, "USER_NOT_FOUND", "El usuario no existe")
        
    check_self_or_admin(current_user, user.id)
    return user

@router.get("/email/{email}", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_user_by_email(
    email: str, 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    user = service.get_by_email(email=email.strip())
    if not user:
        raise AppError(404, "USER_NOT_FOUND", "El usuario no existe")
        
    check_self_or_admin(current_user, user.id)
    return user

@router.get("/id/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_user_by_id(
    user_id: int, 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    user = service.get_by_id(user_id=user_id)
    if not user:
        raise AppError(404, "USER_NOT_FOUND", "El usuario no existe")
        
    check_self_or_admin(current_user, user.id)
    return user

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, service: UserService = Depends(get_user_service)):
    '''
    Registra un nuevo usuario.
    
    Validaciones automáticas en UserService:
    - Email y username únicos
    - Contraseña hasheada con bcrypt
    - SIEMPRE se crea con role "user" por seguridad
    '''
    return service.create(
        email=payload.email, 
        username=payload.username, 
        password=payload.password,
        role="user"  # SIEMPRE crear como user, ignorar el role del payload
    )

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(payload: UserLogin, service: UserService = Depends(get_user_service)):
    '''
    Autentica un usuario y genera un token JWT.
    
    Proceso:
    1. Verifica email y contraseña
    2. Genera token JWT con datos del usuario (user_id, username, role)
    3. Retorna el token y datos del usuario
    '''
    return service.login(email=payload.email, password=payload.password)

@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
def refresh_token(payload: TokenRefresh, service: UserService = Depends(get_user_service)):
    """
    Renueva un Access Token usando un Refresh Token válido.
    """
    return service.refresh_token(payload.refresh_token)

# Se usa patch porque solo se actualiza un campo: el role
@router.patch("/{user_id}/change-role", response_model=UserOut, status_code=status.HTTP_200_OK)
def change_user_role(
    user_id: int,
    payload: RoleUpdate,
    service: UserService = Depends(get_user_service),
    admin_user = Depends(allow_admin)
):
    '''
    Cambia el role de un usuario. Solo accesible para admins.
    
    Permite promocionar usuarios a admin o degradar admins a user.
    '''
    return service.update(user_id=user_id, user_data={"role": payload.role})

@router.put("/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
def update_user(
    user_id: int, 
    payload: UserUpdate, 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    # Validar que el usuario solo pueda editarse a sí mismo (salvo que sea admin)
    check_self_or_admin(current_user, user_id)
    
    # Asegurar que no se puede cambiar el role desde aquí
    update_data = payload.model_dump(exclude_unset=True)
    if "role" in update_data:
        del update_data["role"]  # Eliminar role si viene en el payload
        
    return service.update(user_id=user_id, user_data=update_data)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int, 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    # Validar que el usuario solo pueda borrarse a sí mismo (salvo que sea admin)
    check_self_or_admin(current_user, user_id)
    service.delete(user_id=user_id)

@router.post("/update-image", response_model=UserOut, status_code=status.HTTP_200_OK)
def upload_profile_image(
    file: UploadFile = File(...), 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    """
    Sube una imagen de perfil para el usuario actual.
    La imagen se aloja en Cloudinary.
    """
    image_url = image_service.upload_image(file)
    
    # Actualizar usuario con la nueva URL
    # current_user es TokenData, tiene user_id
    return service.update(user_id=current_user.user_id, user_data={"image_url": image_url})