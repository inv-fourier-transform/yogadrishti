"""Image decoding, validation, and preprocessing."""
import cv2
import numpy as np
from app.config import get_settings
from app.utils.exceptions import (
    CorruptedFileError,
    ImageTooSmallError,
)

SETTINGS = get_settings()


def decode_image(file_bytes: bytes) -> np.ndarray:
    """Decode raw bytes into a BGR numpy array. Raises on corruption."""
    arr = np.frombuffer(file_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise CorruptedFileError("Unable to decode image. The file may be corrupted.")
    return img


def resize_if_needed(image: np.ndarray) -> np.ndarray:
    """Check image dimensions are within allowed range. Auto-resize if too large."""
    h, w = image.shape[:2]
    if h < SETTINGS.min_image_dimension or w < SETTINGS.min_image_dimension:
        raise ImageTooSmallError(
            f"Image dimensions ({w}×{h}) are below the minimum "
            f"({SETTINGS.min_image_dimension}×{SETTINGS.min_image_dimension}). "
            "Please upload a higher resolution image."
        )
    if h > SETTINGS.max_image_dimension or w > SETTINGS.max_image_dimension:
        # Scale down while maintaining aspect ratio
        scaling_factor = min(SETTINGS.max_image_dimension / w, SETTINGS.max_image_dimension / h)
        new_w = int(w * scaling_factor)
        new_h = int(h * scaling_factor)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return image


def preprocess_for_mediapipe(image: np.ndarray) -> np.ndarray:
    """Convert BGR to RGB for MediaPipe processing."""
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def estimate_blur(image: np.ndarray) -> float:
    """Return the Laplacian variance as a blur metric. Lower = blurrier."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_blurry(image: np.ndarray, threshold: float = 50.0) -> bool:
    """Check if image is too blurry for reliable analysis."""
    return estimate_blur(image) < threshold
