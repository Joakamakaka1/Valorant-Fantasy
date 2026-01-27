from sqlalchemy.orm import Session, joinedload
from app.db.models.user import User
from typing import List, Optional

class UserRepository:
    '''
    Repositorio de usuarios - Capa de acceso a datos.
    
    Todas las consultas usan joinedload para cargar trips y comments
    de forma eficiente (eager loading) y evitar el problema N+1.
    '''
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        return (
            self.db.query(User)

            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_email(self, email: str) -> Optional[User]:
        return (
            self.db.query(User)

            .filter(User.email == email)
            .first()
        )

    def get_by_username(self, username: str) -> Optional[User]:
        return (
            self.db.query(User)

            .filter(User.username == username)
            .first()
        )

    def get_by_id(self, user_id: int) -> Optional[User]:
        return (
            self.db.query(User)

            .filter(User.id == user_id)
            .first()
        )
    
    def get_by_id_light(self, user_id: int) -> Optional[User]:
        """
        Versión ligera de get_by_id sin cargar relaciones.
        Útil para verificaciones rápidas como validación de tokens.
        """
        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def create(self, user: User) -> User:
        # Nota: No hacemos commit aquí, lo maneja el servicio con el decorador @transactional
        self.db.add(user)
        self.db.flush()  # Genera el ID antes de retornar
        return user

        
    def update(self, user_id: int, user_data: dict) -> User:
        user = self.get_by_id(user_id)
        
        # Actualizar campos
        for key, value in user_data.items():
            if value is not None:
                setattr(user, key, value)
        
        # El commit lo hace el decorador
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)