from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.auth.deps import get_async_db
from app.core.config import settings

# ============================================================================
# ENDPOINTS DE SALUD
# - /health: Check de salud general
# - /health/db: Check de salud de la base de datos
# ============================================================================

router = APIRouter(tags=["Health"])

@router.get("/health") # http://localhost:8000/api/health
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

@router.get("/health/db") # http://localhost:8000/api/health/db
async def health_check_db(db: AsyncSession = Depends(get_async_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }