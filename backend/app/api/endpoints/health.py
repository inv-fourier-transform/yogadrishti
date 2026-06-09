"""Health check endpoint."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Service health check."""
    return {"status": "ok", "version": "1.0.0", "service": "yoga-pose-detector"}
