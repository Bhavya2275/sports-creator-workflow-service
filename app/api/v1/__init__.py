from fastapi import APIRouter
from app.api.v1.creators import router as creators_router
from app.api.v1.qualification import router as qualification_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(creators_router)
api_router.include_router(qualification_router)
