"""Video analysis endpoint — async job-based video analysis."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
import json

from app.models.api_schemas import VideoJobCreatedResponse
from app.utils.validation import validate_file_size, validate_file_extension
from app.utils.exceptions import YogaPoseError
from app.utils.file_io import save_temp_file, cleanup_temp_file
from app.api.pipeline import run_video_pipeline
from app.db.database import get_db
from app.db.queries import (
    get_user, create_job, update_job_status,
    get_previous_attempt_for_pose, get_best_attempt_for_pose,
    save_pose_attempt,
)
from app.utils.logging import logger

router = APIRouter()


async def _process_video(job_id: str, video_path: str, user_id: str, file_name: str):
    """Background task for video processing."""
    db = await get_db()
    try:
        async def progress_cb(progress: float):
            await update_job_status(job_id, "processing", progress, db=db)

        await update_job_status(job_id, "processing", 0.0, db=db)

        video_result, feedback_text, comparison = await run_video_pipeline(
            video_path=video_path,
            user_id=user_id if user_id else None,
            progress_callback=progress_cb,
        )

        # Look up history if user provided
        if user_id and video_result.dominant_pose:
            prev = await get_previous_attempt_for_pose(user_id, video_result.dominant_pose, db)
            best = await get_best_attempt_for_pose(user_id, video_result.dominant_pose, db)

            if prev or best:
                from app.core.feedback_generation.history_comparison import compare_attempts
                comparison = compare_attempts(
                    current_score=video_result.overall_score,
                    current_angles={},
                    current_issues=[],
                    previous_attempt=prev,
                    best_attempt=best,
                )

        # Save attempt
        if user_id and video_result.evaluation_status == "evaluated":
            summary = {
                "dominant_pose": video_result.dominant_pose,
                "consistency_score": video_result.consistency_score,
                "analyzed_frames": video_result.analyzed_frame_count,
            }
            await save_pose_attempt(
                user_id=user_id,
                analysis_job_id=job_id,
                pose_name=video_result.dominant_pose,
                sanskrit_name=video_result.dominant_pose_sanskrit,
                input_type="video",
                evaluation_status=video_result.evaluation_status,
                pose_confidence=0.0,
                overall_score=video_result.overall_score,
                correctness_label="evaluated",
                reliability_reason=video_result.reliability_reason or "",
                summary_json=summary,
                feedback_text=feedback_text,
                db=db,
            )

        # Build result JSON
        result = {
            "dominant_pose": video_result.dominant_pose,
            "dominant_pose_sanskrit": video_result.dominant_pose_sanskrit,
            "overall_score": video_result.overall_score,
            "consistency_score": video_result.consistency_score,
            "frame_count": video_result.frame_count,
            "analyzed_frame_count": video_result.analyzed_frame_count,
            "evaluation_status": video_result.evaluation_status,
            "reliability_reason": video_result.reliability_reason or "",
            "feedback": feedback_text,
            "frame_summaries": video_result.frame_summaries,
        }

        if comparison and comparison.historical_context_available:
            result["progress"] = {
                "historical_context_available": comparison.historical_context_available,
                "previous_attempt_exists": comparison.previous_attempt_exists,
                "progress_summary": comparison.progress_summary,
                "improved_areas": comparison.improved_areas,
                "declined_areas": comparison.declined_areas,
                "previous_score": comparison.previous_score,
                "best_score": comparison.best_score,
                "current_vs_previous_delta": comparison.current_vs_previous_delta,
                "current_vs_best_delta": comparison.current_vs_best_delta,
            }

        await update_job_status(job_id, "completed", 100.0, result_json=json.dumps(result), db=db)

    except YogaPoseError as e:
        await update_job_status(job_id, "failed", 0.0, error_message=e.message, db=db)
    except Exception as e:
        logger.error(f"Video processing error: {e}")
        await update_job_status(job_id, "failed", 0.0, error_message=str(e), db=db)
    finally:
        cleanup_temp_file(video_path)


@router.post("/analyze/video", response_model=VideoJobCreatedResponse)
async def analyze_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
):
    """Submit a video for async pose analysis."""
    try:
        validate_file_extension(file.filename, is_video=True)
        file_bytes = await file.read()
        validate_file_size(len(file_bytes), is_video=True)

        # Save to temp file
        ext = "." + file.filename.rsplit(".", 1)[-1] if "." in file.filename else ".mp4"
        video_path = save_temp_file(file_bytes, suffix=ext)

        db = await get_db()

        if user_id:
            user = await get_user(user_id, db)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail={"error_code": "USER_NOT_FOUND", "message": "The provided user ID does not exist."}
                )

        actual_user_id = user_id if user_id else None
        job = await create_job(actual_user_id, "video", file.filename, db)

        # Start background processing
        background_tasks.add_task(_process_video, job["id"], video_path, actual_user_id, file.filename)

        return VideoJobCreatedResponse(
            job_id=job["id"],
            status="accepted",
            message="Video analysis job created. Poll /api/v1/jobs/{job_id} for progress.",
        )

    except YogaPoseError as e:
        raise HTTPException(status_code=422, detail={"error_code": e.error_code, "message": e.message})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video upload error: {e}")
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": str(e)})
