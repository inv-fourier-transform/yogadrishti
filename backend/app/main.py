"""FastAPI application factory and main entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.database import init_db, close_db
from app.api.endpoints import health, analyze_image, analyze_video, jobs, users
from app.utils.logging import logger

SETTINGS = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing MongoDB...")
    await init_db()
    logger.info("Yoga Pose Detector API ready.")
    yield
    logger.info("Shutting down...")
    await close_db()


app = FastAPI(
    title="Yoga AI Pose Detector",
    description="AI-powered yoga pose detection and posture feedback API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[SETTINGS.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(analyze_image.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(analyze_video.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=SETTINGS.host, port=SETTINGS.port, reload=SETTINGS.debug)
