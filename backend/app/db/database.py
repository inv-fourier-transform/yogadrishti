"""Database connection management for MongoDB Atlas."""
from __future__ import annotations
import re
import uuid
from datetime import datetime, timezone
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings
from app.utils.logging import logger

SETTINGS = get_settings()

_client: AsyncIOMotorClient | None = None
_db = None


def generate_id() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


def now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def normalize_email(email: str) -> str:
    """
    Normalize an email address for deduplication.

    Rules:
    1. Lowercase the entire email
    2. For Gmail/Googlemail: remove dots from local part, strip + aliases
    3. For other providers: strip + aliases only
    """
    email = email.strip().lower()
    if not email or "@" not in email:
        return email

    local, domain = email.rsplit("@", 1)

    # Strip + alias for all providers
    local = local.split("+")[0]

    # Gmail-specific: remove dots from local part
    gmail_domains = {"gmail.com", "googlemail.com"}
    if domain in gmail_domains:
        local = local.replace(".", "")

    return f"{local}@{domain}"


async def get_db():
    """Return the MongoDB database instance, creating the client if needed."""
    global _client, _db
    if _db is not None:
        return _db

    if not SETTINGS.mongodb_uri:
        raise RuntimeError("MONGODB_URI not configured. Set it in .env")

    _client = AsyncIOMotorClient(
        SETTINGS.mongodb_uri,
        serverSelectionTimeoutMS=5000,
        tlsCAFile=certifi.where(),
    )
    _db = _client[SETTINGS.mongodb_db_name]
    logger.info(f"Connected to MongoDB Atlas: {SETTINGS.mongodb_db_name}")
    return _db


async def init_db() -> None:
    """Initialize MongoDB collections and indexes."""
    db = await get_db()

    # Ensure indexes for performance and uniqueness
    await db.users.create_index("email_normalized", unique=True, sparse=True)
    await db.users.create_index("display_name")
    await db.analysis_jobs.create_index("user_id")
    await db.pose_attempts.create_index([("user_id", 1), ("pose_name", 1)])
    await db.pose_attempts.create_index([("user_id", 1), ("created_at", -1)])

    logger.info("MongoDB indexes initialized.")


async def close_db() -> None:
    """Close the MongoDB client connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed.")
