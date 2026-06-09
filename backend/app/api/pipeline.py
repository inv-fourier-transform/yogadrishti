"""Pipeline orchestrator — runs the complete analysis pipeline for image or video."""
from __future__ import annotations
import numpy as np
from typing import Optional

from app.models.domain_schemas import (
    PoseEvaluation, FeedbackPayload, AttemptComparison,
    FrameResult, VideoAnalysisResult,
)
from app.services.image_processing.decode import (
    decode_image, resize_if_needed, preprocess_for_mediapipe,
)
from app.core.pose_detection.mediapipe_runner import extract_landmarks
from app.core.pose_detection.person_gate import validate_single_person
from app.core.pose_detection.classifier import classify_pose
from app.core.pose_evaluation.scoring import evaluate_pose
from app.core.pose_evaluation.confidence_gate import apply_reliability_gate
from app.core.feedback_generation.prompt_builder import build_feedback_prompt
from app.core.feedback_generation.gemini_client import generate_feedback
from app.core.feedback_generation.response_parser import parse_feedback_response, validate_feedback
from app.core.feedback_generation.fallback_templates import generate_fallback_feedback
from app.core.feedback_generation.history_comparison import compare_attempts
from app.services.video_processing.sampler import (
    get_video_metadata, validate_video_duration, sample_frames,
)
from app.services.video_processing.aggregate import aggregate_frame_results
from app.utils.logging import logger


async def run_image_pipeline(
    file_bytes: bytes,
    user_id: str = None,
    previous_attempt: dict = None,
    best_attempt: dict = None,
) -> tuple[PoseEvaluation, str, AttemptComparison | None]:
    """
    Run the full image analysis pipeline.
    Returns (evaluation, feedback_text, comparison).
    """
    # 1. Decode image
    image = decode_image(file_bytes)

    # 2. Validate/resize dimensions
    image = resize_if_needed(image)

    # 3. Preprocess for MediaPipe
    image_rgb = preprocess_for_mediapipe(image)

    # 4. Extract landmarks & validate single person
    landmark_sets, person_count = extract_landmarks(image_rgb)
    landmarks = validate_single_person(landmark_sets, person_count)

    # 5. Classify pose
    pose_key, confidence, top3 = classify_pose(landmarks, image_rgb)

    # 6. Evaluate pose correctness
    evaluation = evaluate_pose(landmarks, pose_key, confidence)

    # 7. Apply reliability gate
    evaluation = apply_reliability_gate(evaluation, landmarks, image)

    # 8. Compare with history
    comparison = None
    if user_id:
        comparison = compare_attempts(
            current_score=evaluation.overall_score,
            current_angles=evaluation.angles,
            current_issues=[{"body_part": i.body_part, "severity": i.severity} for i in evaluation.issues],
            previous_attempt=previous_attempt,
            best_attempt=best_attempt,
        )

    # 9. Generate feedback
    payload = FeedbackPayload(
        pose_name=evaluation.pose_name,
        sanskrit_name=evaluation.sanskrit_name,
        evaluation=evaluation,
        comparison=comparison,
    )
    feedback_text = await _generate_feedback_safe(payload, evaluation, comparison)

    return evaluation, feedback_text, comparison


async def run_video_pipeline(
    video_path: str,
    user_id: str = None,
    previous_attempt: dict = None,
    best_attempt: dict = None,
    progress_callback=None,
) -> tuple[VideoAnalysisResult, str, AttemptComparison | None]:
    """
    Run the full video analysis pipeline.
    Returns (video_result, feedback_text, comparison).
    """
    # 1. Get metadata and validate
    metadata = get_video_metadata(video_path)
    validate_video_duration(metadata)

    # 2. Sample frames
    frames = sample_frames(video_path)
    total_frames = metadata["frame_count"]

    # 3. Analyze each sampled frame
    frame_results: list[FrameResult] = []
    for i, (frame_idx, timestamp, frame_bgr) in enumerate(frames):
        if progress_callback:
            progress = (i + 1) / len(frames) * 100
            await progress_callback(progress)

        try:
            frame_rgb = preprocess_for_mediapipe(frame_bgr)
            landmark_sets, person_count = extract_landmarks(frame_rgb)

            if person_count != 1 or not landmark_sets:
                continue

            landmarks = landmark_sets[0]
            pose_key, confidence, _ = classify_pose(landmarks)
            evaluation = evaluate_pose(landmarks, pose_key, confidence)
            evaluation = apply_reliability_gate(evaluation, landmarks, frame_bgr)

            frame_results.append(FrameResult(
                frame_index=frame_idx,
                timestamp_sec=timestamp,
                evaluation=evaluation,
            ))
        except Exception as e:
            logger.error(f"Frame {frame_idx} analysis failed: {e}")
            continue

    # 4. Aggregate results
    video_result = aggregate_frame_results(frame_results, total_frames)

    # 5. Compare with history
    comparison = None
    if user_id and video_result.evaluation_status == "evaluated":
        best_eval = None
        if video_result.best_frame:
            best_eval = video_result.best_frame.evaluation
        comparison = compare_attempts(
            current_score=video_result.overall_score,
            current_angles=best_eval.angles if best_eval else {},
            current_issues=[],
            previous_attempt=previous_attempt,
            best_attempt=best_attempt,
        )

    # 6. Generate feedback
    best_eval = video_result.best_frame.evaluation if video_result.best_frame else PoseEvaluation()
    payload = FeedbackPayload(
        pose_name=video_result.dominant_pose,
        sanskrit_name=video_result.dominant_pose_sanskrit,
        evaluation=best_eval,
        comparison=comparison,
        is_video=True,
        video_result=video_result,
    )
    feedback_text = await _generate_feedback_safe(payload, best_eval, comparison)

    return video_result, feedback_text, comparison


async def _generate_feedback_safe(
    payload: FeedbackPayload,
    evaluation: PoseEvaluation,
    comparison: AttemptComparison | None,
) -> str:
    """Generate feedback with LLM, falling back to templates on failure."""
    try:
        prompt = build_feedback_prompt(payload)
        raw_feedback = await generate_feedback(prompt)
        feedback = parse_feedback_response(raw_feedback)
        if validate_feedback(feedback, evaluation.pose_name):
            return feedback
        logger.error("LLM feedback failed validation, using fallback")
    except Exception as e:
        logger.error(f"LLM feedback generation failed: {e}")

    return generate_fallback_feedback(evaluation, comparison)
