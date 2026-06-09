"""Domain schemas for internal data flow — landmarks, evaluation results, comparisons."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Landmark:
    """Single pose landmark point."""
    x: float
    y: float
    z: float
    visibility: float
    name: str = ""


@dataclass(frozen=True)
class LandmarkSet:
    """Complete set of 33 MediaPipe landmarks for one person."""
    landmarks: tuple[Landmark, ...]
    overall_visibility: float = 0.0

    def get(self, index: int) -> Landmark:
        return self.landmarks[index]

    def visibility_ratio(self, min_vis: float = 0.5) -> float:
        """Fraction of landmarks above min visibility."""
        if not self.landmarks:
            return 0.0
        visible = sum(1 for lm in self.landmarks if lm.visibility >= min_vis)
        return visible / len(self.landmarks)


@dataclass(frozen=True)
class JointAngle:
    """Computed angle at a joint."""
    joint_name: str
    angle_degrees: float
    landmark_indices: tuple[int, int, int]


@dataclass(frozen=True)
class PoseIssue:
    """A single detected issue in the pose."""
    body_part: str
    measured_value: float
    expected_min: float
    expected_max: float
    severity: str  # "minor", "moderate", "major"
    instruction_key: str
    description: str = ""


@dataclass
class PoseEvaluation:
    """Complete evaluation result for a single frame/image."""
    pose_name: str = ""
    sanskrit_name: str = ""
    pose_confidence: float = 0.0
    evaluation_status: str = "unknown"  # "evaluated", "low_confidence", "not_evaluable"
    overall_score: float = 0.0
    correctness_label: str = "unknown"  # "correct", "needs_adjustment", "incorrect", "not_reliably_evaluable"
    issues: list[PoseIssue] = field(default_factory=list)
    safety_flags: list[str] = field(default_factory=list)
    landmark_visibility_ratio: float = 0.0
    reliability_reason: str = ""
    angles: dict[str, float] = field(default_factory=dict)


@dataclass
class FrameResult:
    """Result of analyzing a single video frame."""
    frame_index: int
    timestamp_sec: float
    evaluation: PoseEvaluation


@dataclass
class VideoAnalysisResult:
    """Aggregated result from video analysis."""
    dominant_pose: str = ""
    dominant_pose_sanskrit: str = ""
    overall_score: float = 0.0
    consistency_score: float = 0.0
    frame_count: int = 0
    analyzed_frame_count: int = 0
    best_frame: Optional[FrameResult] = None
    worst_frame: Optional[FrameResult] = None
    median_frame: Optional[FrameResult] = None
    evaluation_status: str = "unknown"
    reliability_reason: str = ""
    frame_summaries: list[dict] = field(default_factory=list)


@dataclass
class AttemptComparison:
    """Comparison between current and previous pose attempt."""
    historical_context_available: bool = False
    previous_attempt_exists: bool = False
    previous_score: Optional[float] = None
    best_score: Optional[float] = None
    current_vs_previous_delta: Optional[float] = None
    current_vs_best_delta: Optional[float] = None
    improved_areas: list[str] = field(default_factory=list)
    declined_areas: list[str] = field(default_factory=list)
    unchanged_areas: list[str] = field(default_factory=list)
    progress_summary: str = ""


@dataclass
class FeedbackPayload:
    """Complete payload sent to the LLM for feedback generation."""
    pose_name: str = ""
    sanskrit_name: str = ""
    evaluation: Optional[PoseEvaluation] = None
    comparison: Optional[AttemptComparison] = None
    is_video: bool = False
    video_result: Optional[VideoAnalysisResult] = None
