"""Image analysis endpoint — synchronous single-image analysis."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

from app.models.api_schemas import ImageAnalysisResponse, PoseIssueResponse, ProgressResponse
from app.utils.validation import validate_file_size, validate_file_extension
from app.utils.exceptions import YogaPoseError
from app.api.pipeline import run_image_pipeline
from app.db.database import get_db
from app.db.queries import (
    get_user, get_previous_attempt_for_pose, get_best_attempt_for_pose,
    save_pose_attempt, save_pose_metrics, create_job, update_job_status,
)
from app.utils.logging import logger

router = APIRouter()


@router.post("/analyze/image", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
):
    """Analyze a single uploaded yoga pose image."""
    try:
        # Validate file
        validate_file_extension(file.filename, is_video=False)
        file_bytes = await file.read()
        validate_file_size(len(file_bytes), is_video=False)

        db = await get_db()

        # Validate user exists
        if user_id:
            user = await get_user(user_id, db)
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail={"error_code": "USER_NOT_FOUND", "message": "The provided user ID does not exist."}
                )

        # Create analysis job
        job = await create_job(user_id, "image", file.filename, db)

        # Run pipeline
        evaluation, feedback_text, comparison = await run_image_pipeline(
            file_bytes=file_bytes,
            user_id=user_id,
        )

        # Look up history after classification
        if user_id and evaluation.pose_name:
            previous_attempt = await get_previous_attempt_for_pose(user_id, evaluation.pose_name, db)
            best_attempt = await get_best_attempt_for_pose(user_id, evaluation.pose_name, db)

            # Re-run comparison with actual history
            if previous_attempt or best_attempt:
                from app.core.feedback_generation.history_comparison import compare_attempts
                comparison = compare_attempts(
                    current_score=evaluation.overall_score,
                    current_angles=evaluation.angles,
                    current_issues=[{"body_part": i.body_part, "severity": i.severity} for i in evaluation.issues],
                    previous_attempt=previous_attempt,
                    best_attempt=best_attempt,
                )

                # Re-generate feedback with history
                from app.models.domain_schemas import FeedbackPayload
                from app.core.feedback_generation.prompt_builder import build_feedback_prompt
                from app.core.feedback_generation.gemini_client import generate_feedback
                from app.core.feedback_generation.response_parser import parse_feedback_response, validate_feedback
                from app.core.feedback_generation.fallback_templates import generate_fallback_feedback

                payload = FeedbackPayload(
                    pose_name=evaluation.pose_name,
                    sanskrit_name=evaluation.sanskrit_name,
                    evaluation=evaluation,
                    comparison=comparison,
                )
                try:
                    prompt = build_feedback_prompt(payload)
                    raw = await generate_feedback(prompt)
                    fb = parse_feedback_response(raw)
                    if validate_feedback(fb, evaluation.pose_name):
                        feedback_text = fb
                except Exception:
                    feedback_text = generate_fallback_feedback(evaluation, comparison)

        # Save attempt to history
        if user_id:
            summary = {
                "angles": evaluation.angles,
                "issues_count": len(evaluation.issues),
                "top_issues": [i.body_part for i in evaluation.issues[:3]],
            }
            metrics = [
                {
                    "metric_name": issue.body_part,
                    "metric_value": issue.measured_value,
                    "expected_min": issue.expected_min,
                    "expected_max": issue.expected_max,
                    "deviation": abs(issue.measured_value - (issue.expected_min + issue.expected_max) / 2),
                    "severity": issue.severity,
                }
                for issue in evaluation.issues
            ]
            attempt_id = await save_pose_attempt(
                user_id=user_id,
                analysis_job_id=job["id"],
                pose_name=evaluation.pose_name,
                sanskrit_name=evaluation.sanskrit_name,
                input_type="image",
                evaluation_status=evaluation.evaluation_status,
                pose_confidence=evaluation.pose_confidence,
                overall_score=evaluation.overall_score,
                correctness_label=evaluation.correctness_label,
                reliability_reason=evaluation.reliability_reason,
                summary_json=summary,
                feedback_text=feedback_text,
                db=db,
                metrics=metrics,
            )

        await update_job_status(job["id"], "completed", 100.0, db=db)

        # Build response
        progress = None
        if comparison and comparison.historical_context_available:
            progress = ProgressResponse(
                historical_context_available=comparison.historical_context_available,
                previous_attempt_exists=comparison.previous_attempt_exists,
                progress_summary=comparison.progress_summary,
                improved_areas=comparison.improved_areas,
                declined_areas=comparison.declined_areas,
                unchanged_areas=comparison.unchanged_areas,
                previous_score=comparison.previous_score,
                best_score=comparison.best_score,
                current_vs_previous_delta=comparison.current_vs_previous_delta,
                current_vs_best_delta=comparison.current_vs_best_delta,
            )

        return ImageAnalysisResponse(
            success=True,
            pose_name=evaluation.pose_name,
            sanskrit_name=evaluation.sanskrit_name,
            pose_confidence=round(evaluation.pose_confidence, 3),
            evaluation_status=evaluation.evaluation_status,
            overall_score=evaluation.overall_score,
            correctness_label=evaluation.correctness_label,
            issues=[
                PoseIssueResponse(
                    body_part=i.body_part,
                    measured_value=i.measured_value,
                    expected_min=i.expected_min,
                    expected_max=i.expected_max,
                    severity=i.severity,
                    instruction_key=i.instruction_key,
                    description=i.description,
                ) for i in evaluation.issues
            ],
            safety_flags=evaluation.safety_flags,
            feedback=feedback_text,
            reliability_reason=evaluation.reliability_reason,
            progress=progress,
            angles=evaluation.angles,
        )

    except YogaPoseError as e:
        raise HTTPException(status_code=422, detail={"error_code": e.error_code, "message": e.message})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": str(e)})
