from fastapi import APIRouter
from app.api.admin.users import router as users_router
from app.api.admin.armies import router as armies_router

router = APIRouter()
router.include_router(users_router)
router.include_router(armies_router)