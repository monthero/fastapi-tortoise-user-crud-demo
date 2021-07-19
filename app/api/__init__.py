from fastapi import APIRouter

from app.api.endpoints import users_router


api_router = APIRouter()
api_router.include_router(users_router, prefix="/users", tags=["users"])
