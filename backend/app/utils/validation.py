"""File and upload validation utilities."""
from pathlib import Path
from app.config import get_settings
from app.utils.exceptions import (
    FileTooLargeError,
    UnsupportedFormatError,
)

SETTINGS = get_settings()

IMAGE_MIME_MAP = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png", ".webp": "image/webp",
}

VIDEO_MIME_MAP = {
    ".mp4": "video/mp4", ".avi": "video/avi",
    ".mov": "video/quicktime", ".webm": "video/webm",
}


def validate_file_size(file_size: int, is_video: bool = False) -> None:
    """Raise if file exceeds size limit."""
    limit_mb = SETTINGS.max_video_size_mb if is_video else SETTINGS.max_image_size_mb
    limit_bytes = limit_mb * 1024 * 1024
    if file_size > limit_bytes:
        raise FileTooLargeError(
            f"File size ({file_size / 1024 / 1024:.1f} MB) exceeds the "
            f"{limit_mb} MB limit."
        )


def validate_file_extension(filename: str, is_video: bool = False) -> str:
    """Validate extension and return the lowercase extension. Raises on unsupported."""
    ext = Path(filename).suffix.lower()
    allowed = SETTINGS.allowed_video_extensions if is_video else SETTINGS.allowed_image_extensions
    if ext not in allowed:
        raise UnsupportedFormatError(
            f"Unsupported file format '{ext}'. Allowed: {', '.join(allowed)}"
        )
    return ext


def guess_content_type(filename: str) -> str:
    """Guess MIME type from filename extension."""
    ext = Path(filename).suffix.lower()
    return IMAGE_MIME_MAP.get(ext, VIDEO_MIME_MAP.get(ext, "application/octet-stream"))


def is_image_file(filename: str) -> bool:
    """Check if filename has an image extension."""
    ext = Path(filename).suffix.lower()
    return ext in SETTINGS.allowed_image_extensions


def is_video_file(filename: str) -> bool:
    """Check if filename has a video extension."""
    ext = Path(filename).suffix.lower()
    return ext in SETTINGS.allowed_video_extensions
