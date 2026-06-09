"""Pydantic API request/response schemas for all endpoints."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# ── Health ─────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"


# ── Users ──────────────────────────────────────────────
class UserCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr

class UserLogin(BaseModel):
    """Login by email or display_name."""
    email: Optional[str] = None
    display_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    display_name: str
    email: str = ""
    created_at: str
    updated_at: str

class UserDashboard(BaseModel):
    user: UserResponse
    total_attempts: int = 0
    recent_attempts: list[PoseAttemptSummary] = []
    best_scores: dict[str, float] = {}


# ── Pose Issue ─────────────────────────────────────────
class PoseIssueResponse(BaseModel):
    body_part: str
    measured_value: float
    expected_min: float
    expected_max: float
    severity: str
    instruction_key: str
    description: str = ""


# ── Progress / Comparison ──────────────────────────────
class ProgressResponse(BaseModel):
    historical_context_available: bool = False
    previous_attempt_exists: bool = False
    progress_summary: str = ""
    improved_areas: list[str] = []
    declined_areas: list[str] = []
    unchanged_areas: list[str] = []
    previous_score: Optional[float] = None
    best_score: Optional[float] = None
    current_vs_previous_delta: Optional[float] = None
    current_vs_best_delta: Optional[float] = None


# ── Image Analysis ─────────────────────────────────────
class ImageAnalysisResponse(BaseModel):
    success: bool = True
    pose_name: str = ""
    sanskrit_name: str = ""
    pose_confidence: float = 0.0
    evaluation_status: str = ""
    overall_score: float = 0.0
    correctness_label: str = ""
    issues: list[PoseIssueResponse] = []
    safety_flags: list[str] = []
    feedback: str = ""
    reliability_reason: str = ""
    progress: Optional[ProgressResponse] = None
    angles: dict[str, float] = {}


# ── Video Analysis ─────────────────────────────────────
class VideoJobCreatedResponse(BaseModel):
    job_id: str
    status: str = "accepted"
    message: str = "Video analysis job created."

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    created_at: str = ""
    updated_at: str = ""

class FrameSummaryResponse(BaseModel):
    frame_index: int
    timestamp_sec: float
    pose_name: str
    overall_score: float
    correctness_label: str

class VideoAnalysisResultResponse(BaseModel):
    success: bool = True
    job_id: str
    dominant_pose: str = ""
    dominant_pose_sanskrit: str = ""
    overall_score: float = 0.0
    consistency_score: float = 0.0
    frame_count: int = 0
    analyzed_frame_count: int = 0
    evaluation_status: str = ""
    reliability_reason: str = ""
    feedback: str = ""
    frame_summaries: list[FrameSummaryResponse] = []
    best_frame: Optional[FrameSummaryResponse] = None
    worst_frame: Optional[FrameSummaryResponse] = None
    progress: Optional[ProgressResponse] = None


# ── Pose History ───────────────────────────────────────
class PoseAttemptSummary(BaseModel):
    id: str
    pose_name: str
    sanskrit_name: str = ""
    input_type: str
    overall_score: float
    correctness_label: str
    created_at: str

class PoseHistoryResponse(BaseModel):
    user_id: str
    pose_name: str
    attempts: list[PoseAttemptSummary] = []
    best_score: Optional[float] = None
    average_score: Optional[float] = None
    total_attempts: int = 0


# ── Error ──────────────────────────────────────────────
class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: Optional[str] = None


# ── Config ─────────────────────────────────────────────
class UploadConfigResponse(BaseModel):
    max_image_size_mb: int
    max_video_size_mb: int
    max_video_duration_seconds: int
    allowed_image_extensions: list[str]
    allowed_video_extensions: list[str]


# Fix forward reference
UserDashboard.model_rebuild()
