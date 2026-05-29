from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.database import create_tables
from app.api.v1 import api_router
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", app=settings.APP_NAME, version=settings.APP_VERSION)
    await create_tables()
    yield
    logger.info("shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend workflow service for managing creator onboarding on a sports platform.",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


# Global exception handler — catches unexpected 500s and logs them
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=str(request.url), error=str(exc), exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
