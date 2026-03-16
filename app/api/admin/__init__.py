from fastapi import APIRouter
from app.api.admin.users import router as users_router
from app.api.admin.armies import router as armies_router
from app.api.admin.dashboard import router as dashboard_router
from app.api.admin.players import router as players_router
from app.api.admin.gamelog import router as gamelog_router
from app.api.admin.broadcast import router as broadcast_router
from app.api.admin.data_editors import router as data_editors_router
from app.api.admin.world import router as world_router
from app.api.admin.city_grid import router as city_grid_router

router = APIRouter(prefix="/admin")
router.include_router(users_router)
router.include_router(armies_router)
router.include_router(dashboard_router)
router.include_router(players_router)
router.include_router(gamelog_router)
router.include_router(broadcast_router)
router.include_router(data_editors_router)
router.include_router(world_router)
router.include_router(city_grid_router)