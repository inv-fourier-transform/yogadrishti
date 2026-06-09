"""Job status and result retrieval endpoints."""
from fastapi import APIRouter, HTTPException
import json

from app.models.api_schemas import JobStatusResponse
from app.db.database import get_db
from app.db.queries import get_job

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get video analysis job status and progress."""
    db = await get_db()
    job = await get_job(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail={"error_code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' not found."})

    return JobStatusResponse(
        job_id=job["id"],
        status=job["status"],
        progress=job["progress"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )


@router.get("/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """Get the final result of a completed video analysis job."""
    db = await get_db()
    job = await get_job(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail={"error_code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' not found."})

    if job["status"] in ("pending", "processing"):
        return {
            "success": False,
            "job_id": job_id,
            "status": job["status"],
            "progress": job["progress"],
            "message": "Job is still processing. Please check back later.",
        }

    if job["status"] == "failed":
        return {
            "success": False,
            "job_id": job_id,
            "status": "failed",
            "message": job.get("error_message", "Analysis failed."),
        }

    # Parse completed result
    result = json.loads(job.get("result_json", "{}")) if job.get("result_json") else {}

    return {
        "success": True,
        "job_id": job_id,
        **result,
    }
