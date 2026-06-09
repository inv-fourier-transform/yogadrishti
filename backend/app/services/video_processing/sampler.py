"""Video decoding, validation, frame sampling, and metadata extraction."""
import cv2
import numpy as np
from app.config import get_settings
from app.utils.exceptions import CorruptedFileError, VideoDurationError

SETTINGS = get_settings()


def get_video_metadata(video_path: str) -> dict:
    """Extract metadata from a video file. Raises on unreadable files."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise CorruptedFileError("Unable to open video file. It may be corrupted or unsupported.")
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        return {
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration_seconds": duration,
        }
    finally:
        cap.release()


def validate_video_duration(metadata: dict) -> None:
    """Raise if video exceeds max duration."""
    duration = metadata.get("duration_seconds", 0)
    if duration > SETTINGS.max_video_duration_seconds:
        raise VideoDurationError(
            f"Video duration ({duration:.1f}s) exceeds the maximum "
            f"({SETTINGS.max_video_duration_seconds}s). Please trim the video."
        )


def sample_frames(video_path: str, sample_fps: float = None, max_frames: int = None) -> list[tuple[int, float, np.ndarray]]:
    """
    Extract frames at a controlled rate from a video.
    Returns list of (frame_index, timestamp_sec, frame_bgr).
    """
    sample_fps = sample_fps or SETTINGS.video_sample_fps
    max_frames = max_frames or SETTINGS.max_analyzed_frames

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise CorruptedFileError("Unable to open video for frame sampling.")

    try:
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = max(1, int(video_fps / sample_fps))

        frames = []
        frame_idx = 0
        while frame_idx < total_frames and len(frames) < max_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break
            timestamp = frame_idx / video_fps
            frames.append((frame_idx, timestamp, frame))
            frame_idx += frame_interval

        return frames
    finally:
        cap.release()
