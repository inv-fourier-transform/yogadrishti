"""Application configuration from environment variables."""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized settings with env-var override support."""

    # Gemini API (replaces Groq)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash-lite"
    gemini_fallback_model: str = "gemini-3.1-flash-lite"

    # MongoDB Atlas
    mongodb_uri: str = ""
    mongodb_db_name: str = "yoga_pose_detector"

    # Upload limits
    max_image_size_mb: int = 10
    max_video_size_mb: int = 300
    max_video_duration_seconds: int = 120
    max_image_dimension: int = 4096
    min_image_dimension: int = 64

    # Supported formats
    allowed_image_types: list[str] = ["image/jpeg", "image/png", "image/webp"]
    allowed_video_types: list[str] = ["video/mp4", "video/avi", "video/mov", "video/webm"]
    allowed_image_extensions: list[str] = [".jpg", ".jpeg", ".png", ".webp"]
    allowed_video_extensions: list[str] = [".mp4", ".avi", ".mov", ".webm"]

    # Model paths
    pose_classifier_model_path: str = "./models/pose_classifier.joblib"
    pose_label_encoder_path: str = "./models/label_encoder.joblib"

    # Video processing
    video_sample_fps: float = 1.0
    max_analyzed_frames: int = 30

    # Pose evaluation
    min_landmark_visibility: float = 0.5
    min_pose_confidence: float = 0.3
    reliability_threshold: float = 0.4

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    frontend_url: str = "http://localhost:5173"

    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    upload_dir: Path = Path("./uploads")
    models_dir: Path = Path("./models")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
