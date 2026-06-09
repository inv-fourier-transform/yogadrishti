"""Pure-function database queries for MongoDB — users, jobs, and pose history."""
from __future__ import annotations
import json
from typing import Optional

from app.db.database import generate_id, now_iso, normalize_email


# ── Users ──────────────────────────────────────────────

async def create_user(display_name: str, email: str, db) -> dict:
    """Create a new user with email deduplication. Raises ValueError on duplicate."""
    email_normalized = normalize_email(email)

    # Check for duplicate normalized email
    existing = await db.users.find_one({"email_normalized": email_normalized})
    if existing:
        raise ValueError(
            f"An account with this email already exists (registered as '{existing['display_name']}'). "
            f"Please log in instead."
        )

    uid = generate_id()
    ts = now_iso()
    user_doc = {
        "_id": uid,
        "display_name": display_name.strip(),
        "email": email.strip().lower(),
        "email_normalized": email_normalized,
        "created_at": ts,
        "updated_at": ts,
    }
    await db.users.insert_one(user_doc)
    return _format_user(user_doc)


async def get_user(user_id: str, db) -> Optional[dict]:
    """Fetch user by ID."""
    doc = await db.users.find_one({"_id": user_id})
    return _format_user(doc) if doc else None


async def find_user_by_email(email: str, db) -> Optional[dict]:
    """Find user by normalized email (for cross-device login)."""
    email_normalized = normalize_email(email)
    doc = await db.users.find_one({"email_normalized": email_normalized})
    return _format_user(doc) if doc else None


async def find_user_by_name(display_name: str, db) -> Optional[dict]:
    """Find user by display name (case-insensitive, for login fallback)."""
    import re
    pattern = re.compile(f"^{re.escape(display_name.strip())}$", re.IGNORECASE)
    doc = await db.users.find_one({"display_name": pattern})
    return _format_user(doc) if doc else None


async def list_users(db) -> list[dict]:
    """List all users."""
    cursor = db.users.find().sort("created_at", -1)
    return [_format_user(doc) async for doc in cursor]


async def delete_user(user_id: str, db) -> bool:
    """Delete a user and ALL associated data (cascade delete)."""
    user = await db.users.find_one({"_id": user_id})
    if not user:
        return False

    # Cascade: delete all pose attempts, jobs, then user
    await db.pose_attempts.delete_many({"user_id": user_id})
    await db.analysis_jobs.delete_many({"user_id": user_id})
    await db.users.delete_one({"_id": user_id})
    return True


def _format_user(doc: dict) -> dict:
    """Convert MongoDB user document to API-friendly dict."""
    if not doc:
        return None
    return {
        "id": doc["_id"],
        "display_name": doc["display_name"],
        "email": doc.get("email", ""),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


# ── Analysis Jobs ──────────────────────────────────────

async def create_job(user_id: str, input_type: str, file_name: str, db) -> dict:
    """Create a new analysis job."""
    jid = generate_id()
    ts = now_iso()
    job_doc = {
        "_id": jid,
        "user_id": user_id,
        "input_type": input_type,
        "file_name": file_name,
        "status": "pending",
        "progress": 0.0,
        "result_json": None,
        "error_message": None,
        "created_at": ts,
        "updated_at": ts,
    }
    await db.analysis_jobs.insert_one(job_doc)
    return _format_job(job_doc)


async def update_job_status(job_id: str, status: str, progress: float,
                            result_json: str = None, error_message: str = None,
                            db=None) -> None:
    """Update job status and progress."""
    ts = now_iso()
    await db.analysis_jobs.update_one(
        {"_id": job_id},
        {"$set": {
            "status": status,
            "progress": progress,
            "result_json": result_json,
            "error_message": error_message,
            "updated_at": ts,
        }}
    )


async def get_job(job_id: str, db) -> Optional[dict]:
    """Fetch job by ID."""
    doc = await db.analysis_jobs.find_one({"_id": job_id})
    return _format_job(doc) if doc else None


def _format_job(doc: dict) -> dict:
    """Convert MongoDB job document to API-friendly dict."""
    if not doc:
        return None
    return {
        "id": doc["_id"],
        "user_id": doc.get("user_id"),
        "input_type": doc["input_type"],
        "file_name": doc["file_name"],
        "status": doc["status"],
        "progress": doc["progress"],
        "result_json": doc.get("result_json"),
        "error_message": doc.get("error_message"),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
    }


# ── Pose Attempts ──────────────────────────────────────

async def save_pose_attempt(
    user_id: str, analysis_job_id: str, pose_name: str, sanskrit_name: str,
    input_type: str, evaluation_status: str, pose_confidence: float,
    overall_score: float, correctness_label: str, reliability_reason: str,
    summary_json: dict, feedback_text: str, db,
    metrics: list[dict] = None,
) -> str:
    """Save a completed pose attempt with embedded metrics. Returns attempt ID."""
    aid = generate_id()
    ts = now_iso()
    attempt_doc = {
        "_id": aid,
        "user_id": user_id,
        "analysis_job_id": analysis_job_id,
        "pose_name": pose_name,
        "sanskrit_name": sanskrit_name,
        "input_type": input_type,
        "evaluation_status": evaluation_status,
        "pose_confidence": pose_confidence,
        "overall_score": overall_score,
        "correctness_label": correctness_label,
        "reliability_reason": reliability_reason,
        "summary_json": summary_json if isinstance(summary_json, dict) else json.loads(summary_json or "{}"),
        "feedback_text": feedback_text,
        "metrics": metrics or [],
        "created_at": ts,
    }
    await db.pose_attempts.insert_one(attempt_doc)
    return aid


async def save_pose_metrics(pose_attempt_id: str, metrics: list[dict], db) -> None:
    """Embed metrics into the pose attempt document."""
    await db.pose_attempts.update_one(
        {"_id": pose_attempt_id},
        {"$set": {"metrics": metrics}}
    )


async def delete_pose_attempt(attempt_id: str, user_id: str, db) -> bool:
    """Delete a specific pose attempt belonging to a user."""
    result = await db.pose_attempts.delete_one({"_id": attempt_id, "user_id": user_id})
    return result.deleted_count > 0


async def get_previous_attempt_for_pose(user_id: str, pose_name: str, db) -> Optional[dict]:
    """Get the most recent previous attempt for a specific pose by a user."""
    doc = await db.pose_attempts.find_one(
        {"user_id": user_id, "pose_name": pose_name},
        sort=[("created_at", -1)]
    )
    return _format_attempt(doc) if doc else None


async def get_best_attempt_for_pose(user_id: str, pose_name: str, db) -> Optional[dict]:
    """Get the best-scoring attempt for a specific pose by a user."""
    doc = await db.pose_attempts.find_one(
        {"user_id": user_id, "pose_name": pose_name, "evaluation_status": "evaluated"},
        sort=[("overall_score", -1)]
    )
    return _format_attempt(doc) if doc else None


async def get_pose_history(user_id: str, pose_name: str, db, limit: int = 20) -> list[dict]:
    """Get attempt history for a specific pose."""
    cursor = db.pose_attempts.find(
        {"user_id": user_id, "pose_name": pose_name}
    ).sort("created_at", -1).limit(limit)
    return [_format_attempt(doc) async for doc in cursor]


async def get_attempt_metrics(pose_attempt_id: str, db) -> list[dict]:
    """Get metrics for a pose attempt (embedded in the document)."""
    doc = await db.pose_attempts.find_one({"_id": pose_attempt_id})
    return doc.get("metrics", []) if doc else []


async def get_user_recent_attempts(user_id: str, db, limit: int = 10) -> list[dict]:
    """Get recent attempts for a user across all poses."""
    cursor = db.pose_attempts.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit)
    return [_format_attempt(doc) async for doc in cursor]


async def get_user_best_scores(user_id: str, db) -> dict[str, float]:
    """Get the best score per pose for a user."""
    pipeline = [
        {"$match": {"user_id": user_id, "evaluation_status": "evaluated"}},
        {"$group": {"_id": "$pose_name", "best": {"$max": "$overall_score"}}},
    ]
    result = {}
    async for doc in db.pose_attempts.aggregate(pipeline):
        result[doc["_id"]] = doc["best"]
    return result


def _format_attempt(doc: dict) -> dict:
    """Convert MongoDB attempt document to API-friendly dict."""
    if not doc:
        return None
    return {
        "id": doc["_id"],
        "user_id": doc.get("user_id"),
        "analysis_job_id": doc.get("analysis_job_id"),
        "pose_name": doc.get("pose_name", ""),
        "sanskrit_name": doc.get("sanskrit_name", ""),
        "input_type": doc.get("input_type", ""),
        "evaluation_status": doc.get("evaluation_status", "unknown"),
        "pose_confidence": doc.get("pose_confidence", 0.0),
        "overall_score": doc.get("overall_score", 0.0),
        "correctness_label": doc.get("correctness_label", "unknown"),
        "reliability_reason": doc.get("reliability_reason", ""),
        "summary_json": json.dumps(doc.get("summary_json", {})),
        "feedback_text": doc.get("feedback_text", ""),
        "created_at": doc.get("created_at", ""),
    }
