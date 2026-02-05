from fastapi import APIRouter
from .endpoints import user, healthy, professional, leagues, matches, admin, dashboard, proxy

api_router = APIRouter(prefix="/v1")
api_router.include_router(user.router)
api_router.include_router(healthy.router)
api_router.include_router(professional.router)
api_router.include_router(leagues.router)
api_router.include_router(matches.router)
api_router.include_router(admin.router)
api_router.include_router(proxy.router)
# api_router.include_router(dashboard.router)