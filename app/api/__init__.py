from fastapi import APIRouter

# Import all routers
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.province import router as province_router
from app.api.market import router as market_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(province_router)
api_router.include_router(market_router)

__all__ = ["api_router"]