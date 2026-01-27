'''
Configuración de la aplicación Aurevia API

Este módulo centraliza todas las configuraciones de la aplicación,
cargadas desde variables de entorno (.env file).

Incluye:
- Configuración de JWT (SECRET_KEY, algoritmo, expiración)
- Configuración de base de datos MySQL
- Configuración de CORS
- Variables de entorno (DEBUG, ENVIRONMENT)
'''

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Settings:
    """Configuración de la aplicación desde variables de entorno"""
    
    # Application Settings (needed first for validation)
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    
    # JWT Settings
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # RSA Keys (Loaded dynamically)
    PRIVATE_KEY: str = ""
    PUBLIC_KEY: str = ""
    
    def __init__(self):
        """Cargar claves RSA al iniciar configuración"""
        from app.core.security_keys import get_rsa_keys
        self.PRIVATE_KEY, self.PUBLIC_KEY = get_rsa_keys()

    
    # Database
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "valorantfantasy")
    
    @property
    def database_url(self) -> str:
        '''
        Construye la URL de conexión a MySQL dinámicamente.
        Formato: mysql+mysqlconnector://usuario:password@host:puerto/database
        '''
        return f"mysql+mysqlconnector://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
    
    # CORS
    @property
    def allowed_origins(self) -> list[str]:
        '''
        Parsea los orígenes permitidos para CORS desde variable de entorno.
        Formato en .env: "http://localhost:8100,http://127.0.0.1:8100"
        Retorna una lista de URLs permitidas.
        '''
        origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8100,http://127.0.0.1:8100")
        return [origin.strip() for origin in origins.split(",")]
    
    # External APIs (VLRGGAPI)
    VLR_API_BASE_URL: str = os.getenv("VLR_API_BASE_URL", "https://vlrggapi.vercel.app")
    VALORANT_API_BASE_URL: str = os.getenv("VALORANT_API_BASE_URL", "https://valorant-api.com/v1")
    
    # @property
    # def vct_event_ids(self) -> list[str]:
    #     """IDs de eventos VCT para filtrar (EMEA, Americas, Pacific, etc.)"""
    #     ids = os.getenv("VCT_EVENT_IDS", "")
    #     return [id.strip() for id in ids.split(",") if id.strip()]

    # Image Upload (Cloudinary)
    CLOUDINARY_CLOUD_NAME: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv("CLOUDINARY_API_SECRET", "")

settings = Settings()