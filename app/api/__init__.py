from fastapi import APIRouter

# Import all routers
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router
from app.api.province import router as province_router
from app.api.market import router as market_router
from app.api.player import router as player_router
from app.api.world import router as world_router
from app.api.army import router as army_router
from app.api.gamelog import router as gamelog_router
from app.api.messages import router as messages_router
from app.api.city_grid import router as city_grid_router
from app.api.help import router as help_router
from app.api.crawler import router as crawler_router

# Create main API router (without /api prefix, since sub-routers have their own prefixes)
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(province_router)
api_router.include_router(market_router)
api_router.include_router(player_router)
api_router.include_router(world_router)
api_router.include_router(army_router)
api_router.include_router(gamelog_router)
api_router.include_router(messages_router)
api_router.include_router(city_grid_router)
api_router.include_router(help_router)
api_router.include_router(crawler_router)

__all__ = ["api_router"]