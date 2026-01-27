'''
Dependencias para inyección de servicios en endpoints.

Cada función crea una instancia del servicio con su sesión de BD.
Se usan como dependencias de FastAPI con Depends().
'''

from fastapi import Depends
from sqlalchemy.orm import Session
from app.auth.deps import get_db
from app.service.user import UserService

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)
