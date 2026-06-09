"""User management, pose history, dashboard, login, and deletion endpoints."""
from fastapi import APIRouter, HTTPException

from app.models.api_schemas import (
    UserCreate, UserLogin, UserResponse, PoseAttemptSummary, PoseHistoryResponse,
)
from app.db.database import get_db
from app.db.queries import (
    create_user, get_user, list_users, find_user_by_email, find_user_by_name,
    delete_user, delete_pose_attempt,
    get_pose_history, get_user_recent_attempts, get_user_best_scores,
)

router = APIRouter()


# ── Registration ───────────────────────────────────────

@router.post("/users", response_model=UserResponse)
async def create_new_user(body: UserCreate):
    """Create a new user profile with email deduplication."""
    db = await get_db()
    try:
        user = await create_user(body.display_name, body.email, db)
        return UserResponse(**user)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ── Login (Cross-Device) ──────────────────────────────

@router.post("/users/login", response_model=UserResponse)
async def login_user(body: UserLogin):
    """
    Log in by email or display name.
    Finds the existing user for cross-device access.
    """
    db = await get_db()

    if not body.email and not body.display_name:
        raise HTTPException(status_code=400, detail="Provide either email or display_name")

    user = None
    if body.email:
        user = await find_user_by_email(body.email, db)
    if not user and body.display_name:
        user = await find_user_by_name(body.display_name, db)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="No account found. Please register first."
        )

    return UserResponse(**user)


# ── User CRUD ──────────────────────────────────────────

@router.get("/users", response_model=list[UserResponse])
async def get_all_users():
    """List all users."""
    db = await get_db()
    users = await list_users(db)
    return [UserResponse(**u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_profile(user_id: str):
    """Get user profile."""
    db = await get_db()
    user = await get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)


@router.delete("/users/{user_id}")
async def delete_user_profile(user_id: str):
    """Delete a user profile and ALL associated data (cascade)."""
    db = await get_db()
    deleted = await delete_user(user_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Profile and all associated data deleted successfully."}


# ── Activity Deletion ─────────────────────────────────

@router.delete("/users/{user_id}/attempts/{attempt_id}")
async def delete_single_attempt(user_id: str, attempt_id: str):
    """Delete a specific activity log entry for a user."""
    db = await get_db()
    deleted = await delete_pose_attempt(attempt_id, user_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Attempt not found or does not belong to this user")
    return {"message": "Activity log entry deleted."}


# ── Pose History ──────────────────────────────────────

@router.get("/users/{user_id}/poses/{pose_name}/history", response_model=PoseHistoryResponse)
async def get_pose_attempt_history(user_id: str, pose_name: str):
    """Get pose-specific history for a user."""
    db = await get_db()
    attempts = await get_pose_history(user_id, pose_name, db)
    scores = [a["overall_score"] for a in attempts if a.get("evaluation_status") == "evaluated"]

    return PoseHistoryResponse(
        user_id=user_id,
        pose_name=pose_name,
        attempts=[
            PoseAttemptSummary(
                id=a["id"],
                pose_name=a["pose_name"],
                sanskrit_name=a.get("sanskrit_name", ""),
                input_type=a["input_type"],
                overall_score=a["overall_score"],
                correctness_label=a["correctness_label"],
                created_at=a["created_at"],
            ) for a in attempts
        ],
        best_score=max(scores) if scores else None,
        average_score=sum(scores) / len(scores) if scores else None,
        total_attempts=len(attempts),
    )


# ── Dashboard ─────────────────────────────────────────

@router.get("/users/{user_id}/dashboard")
async def get_user_dashboard(user_id: str):
    """Get user dashboard with recent attempts and best scores."""
    db = await get_db()
    user = await get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    recent = await get_user_recent_attempts(user_id, db)
    best_scores = await get_user_best_scores(user_id, db)

    return {
        "user": user,
        "total_attempts": len(recent),
        "recent_attempts": [
            {
                "id": a["id"],
                "pose_name": a["pose_name"],
                "sanskrit_name": a.get("sanskrit_name", ""),
                "input_type": a["input_type"],
                "overall_score": a["overall_score"],
                "correctness_label": a["correctness_label"],
                "created_at": a["created_at"],
            } for a in recent[:10]
        ],
        "best_scores": best_scores,
    }


# ── Config ────────────────────────────────────────────

@router.get("/config")
async def get_upload_config():
    """Return upload constraints for the frontend."""
    from app.config import get_settings
    s = get_settings()
    return {
        "max_image_size_mb": s.max_image_size_mb,
        "max_video_size_mb": s.max_video_size_mb,
        "max_video_duration_seconds": s.max_video_duration_seconds,
        "allowed_image_extensions": s.allowed_image_extensions,
        "allowed_video_extensions": s.allowed_video_extensions,
    }
