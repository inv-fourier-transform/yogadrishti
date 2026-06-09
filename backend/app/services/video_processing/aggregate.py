"""Aggregate frame-level pose results into a video-level analysis."""
from collections import Counter
from app.models.domain_schemas import FrameResult, VideoAnalysisResult


def aggregate_frame_results(frame_results: list[FrameResult], total_frames: int) -> VideoAnalysisResult:
    """
    Combine per-frame evaluations into an overall video result.
    Selects dominant pose, computes consistency, picks representative frames.
    """
    if not frame_results:
        return VideoAnalysisResult(
            evaluation_status="not_evaluable",
            reliability_reason="No frames could be analyzed from this video.",
        )

    # Only use evaluated frames
    evaluated = [fr for fr in frame_results if fr.evaluation.evaluation_status == "evaluated"]
    if not evaluated:
        return VideoAnalysisResult(
            frame_count=total_frames,
            analyzed_frame_count=len(frame_results),
            evaluation_status="not_evaluable",
            reliability_reason="No frames produced reliable pose evaluations.",
        )

    # Dominant pose by frequency
    pose_counts = Counter(fr.evaluation.pose_name for fr in evaluated)
    dominant_pose = pose_counts.most_common(1)[0][0]
    dominant_frames = [fr for fr in evaluated if fr.evaluation.pose_name == dominant_pose]

    # Scores
    scores = [fr.evaluation.overall_score for fr in dominant_frames]
    avg_score = sum(scores) / len(scores) if scores else 0.0

    # Consistency: 1 - (stdev / max_possible_stdev)
    if len(scores) > 1:
        mean = avg_score
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        stdev = variance ** 0.5
        consistency = max(0.0, 1.0 - (stdev / 50.0)) * 100
    else:
        consistency = 100.0

    # Representative frames
    sorted_by_score = sorted(dominant_frames, key=lambda fr: fr.evaluation.overall_score)
    worst = sorted_by_score[0]
    best = sorted_by_score[-1]
    median_idx = len(sorted_by_score) // 2
    median = sorted_by_score[median_idx]

    # Sanskrit name from dominant
    sanskrit = dominant_frames[0].evaluation.sanskrit_name if dominant_frames else ""

    # Frame summaries
    summaries = [
        {
            "frame_index": fr.frame_index,
            "timestamp_sec": round(fr.timestamp_sec, 2),
            "pose_name": fr.evaluation.pose_name,
            "overall_score": round(fr.evaluation.overall_score, 1),
            "correctness_label": fr.evaluation.correctness_label,
        }
        for fr in frame_results
    ]

    return VideoAnalysisResult(
        dominant_pose=dominant_pose,
        dominant_pose_sanskrit=sanskrit,
        overall_score=round(avg_score, 1),
        consistency_score=round(consistency, 1),
        frame_count=total_frames,
        analyzed_frame_count=len(frame_results),
        best_frame=best,
        worst_frame=worst,
        median_frame=median,
        evaluation_status="evaluated",
        frame_summaries=summaries,
    )
