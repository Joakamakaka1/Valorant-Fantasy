from typing import List
from fastapi import APIRouter, Depends, status

from fastapi import APIRouter, Depends, status, UploadFile, File, HTTPException
from app.service.image import image_service
from app.service.user import UserService
from app.schemas.user import UserCreate, UserUpdate, UserOut, UserLogin, Token, RoleUpdate, TokenRefresh
from app.core.exceptions import AppError
from app.api.deps import get_user_service
from app.auth.deps import get_current_user, allow_admin, check_self_or_admin

from app.schemas.responses import StandardResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/me", response_model=StandardResponse[UserOut], status_code=status.HTTP_200_OK)
async def get_me(current_user = Depends(get_current_user), service: UserService = Depends(get_user_service)):
    """
    Obtener el perfil del usuario actual autenticado.
    """
    user = await service.get_by_id(current_user.user_id)
    return {"success": True, "data": user}


@router.get("/", response_model=StandardResponse[List[UserOut]], status_code=status.HTTP_200_OK)
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    service: UserService = Depends(get_user_service),
    admin_user = Depends(allow_admin)
):
    """
    Obtener todos los usuarios.
    Solo accesible para administradores.
    """
    users = await service.get_all(skip=skip, limit=limit)
    return {"success": True, "data": users}

@router.get("/username/{username}", response_model=StandardResponse[UserOut], status_code=status.HTTP_200_OK)
async def get_user_by_username(
    username: str, 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    user = await service.get_by_username(username=username.strip())
    if not user:
        raise AppError(404, "USER_NOT_FOUND", "El usuario no existe")
        
    check_self_or_admin(current_user, user.id)
    return {"success": True, "data": user}

@router.get("/email/{email}", response_model=StandardResponse[UserOut], status_code=status.HTTP_200_OK)
async def get_user_by_email(
    email: str, 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    user = await service.get_by_email(email=email.strip())
    if not user:
        raise AppError(404, "USER_NOT_FOUND", "El usuario no existe")
        
    check_self_or_admin(current_user, user.id)
    return {"success": True, "data": user}

@router.get("/id/{user_id}", response_model=StandardResponse[UserOut], status_code=status.HTTP_200_OK)
async def get_user_by_id(
    user_id: int, 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    user = await service.get_by_id(user_id=user_id)
    if not user:
        raise AppError(404, "USER_NOT_FOUND", "El usuario no existe")
        
    check_self_or_admin(current_user, user.id)
    return {"success": True, "data": user}

@router.post("/register", response_model=StandardResponse[UserOut], status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, service: UserService = Depends(get_user_service)):
    '''
    Registra un nuevo usuario.
    '''
    user = await service.create(
        email=payload.email, 
        username=payload.username, 
        password=payload.password,
        role="user"
    )
    return {"success": True, "data": user}

@router.post("/login", response_model=StandardResponse[Token], status_code=status.HTTP_200_OK)
async def login(payload: UserLogin, service: UserService = Depends(get_user_service)):
    '''
    Autentica un usuario y genera un token JWT.
    '''
    token = await service.login(email=payload.email, password=payload.password)
    return {"success": True, "data": token}

@router.post("/refresh", response_model=StandardResponse[Token], status_code=status.HTTP_200_OK)
async def refresh_token(payload: TokenRefresh, service: UserService = Depends(get_user_service)):
    """
    Renueva un Access Token usando un Refresh Token válido.
    """
    token = await service.refresh_token(payload.refresh_token)
    return {"success": True, "data": token}

# Se usa patch porque solo se actualiza un campo: el role
@router.patch("/{user_id}/change-role", response_model=StandardResponse[UserOut], status_code=status.HTTP_200_OK)
async def change_user_role(
    user_id: int,
    payload: RoleUpdate,
    service: UserService = Depends(get_user_service),
    admin_user = Depends(allow_admin)
):
    user = await service.update(user_id=user_id, user_data={"role": payload.role})
    return {"success": True, "data": user}

@router.put("/{user_id}", response_model=StandardResponse[UserOut], status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int, 
    payload: UserUpdate, 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    check_self_or_admin(current_user, user_id)
    update_data = payload.model_dump(exclude_unset=True)
    if "role" in update_data:
        del update_data["role"]
        
    user = await service.update(user_id=user_id, user_data=update_data)
    return {"success": True, "data": user}

@router.delete("/{user_id}", response_model=StandardResponse[None], status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int, 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    check_self_or_admin(current_user, user_id)
    await service.delete(user_id=user_id)
    return {"success": True, "data": None}

@router.post("/update-image", response_model=StandardResponse[UserOut], status_code=status.HTTP_200_OK)
async def upload_profile_image(
    file: UploadFile = File(...), 
    service: UserService = Depends(get_user_service),
    current_user = Depends(get_current_user)
):
    """
    Sube una imagen de perfil para el usuario actual.
    La imagen se aloja en Cloudinary.
    """
    image_url = await image_service.upload_image(file)
    user = await service.update(user_id=current_user.user_id, user_data={"image_url": image_url})
    return {"success": True, "data": user}
