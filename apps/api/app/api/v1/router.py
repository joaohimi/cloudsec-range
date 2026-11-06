from fastapi import APIRouter

from app.api.v1 import auth, curriculum, learning, system, users

api_router = APIRouter()
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(curriculum.router, prefix="/curriculum", tags=["curriculum"])
api_router.include_router(users.router, prefix="/users", tags=["user-management"])
api_router.include_router(learning.router, prefix="/learning", tags=["learning-progress"])
