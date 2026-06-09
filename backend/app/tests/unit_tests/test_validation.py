"""Tests for file validation utilities and person gate."""
import pytest
from app.utils.validation import (
    validate_file_size, validate_file_extension,
    guess_content_type, is_image_file, is_video_file,
)
from app.utils.exceptions import FileTooLargeError, UnsupportedFormatError
from app.core.pose_detection.person_gate import validate_single_person
from app.utils.exceptions import NoPersonDetectedError, MultiplePersonsError
from app.models.domain_schemas import Landmark, LandmarkSet


# ── File size validation ─────────────────────────────

class TestValidateFileSize:
    def test_valid_image_size(self):
        """Small image should pass."""
        validate_file_size(1024 * 1024, is_video=False)  # 1 MB

    def test_image_too_large(self):
        """Image exceeding limit should raise."""
        with pytest.raises(FileTooLargeError):
            validate_file_size(20 * 1024 * 1024, is_video=False)  # 20MB > 10MB limit

    def test_valid_video_size(self):
        """Moderate video should pass."""
        validate_file_size(50 * 1024 * 1024, is_video=True)  # 50 MB

    def test_video_too_large(self):
        """Video exceeding limit should raise."""
        with pytest.raises(FileTooLargeError):
            validate_file_size(200 * 1024 * 1024, is_video=True)  # 200MB > 100MB limit

    def test_zero_size_passes(self):
        """Zero-byte file should not raise (validation is for max only)."""
        validate_file_size(0, is_video=False)


# ── File extension validation ────────────────────────

class TestValidateFileExtension:
    def test_valid_jpg(self):
        assert validate_file_extension("photo.jpg", is_video=False) == ".jpg"

    def test_valid_jpeg(self):
        assert validate_file_extension("photo.jpeg", is_video=False) == ".jpeg"

    def test_valid_png(self):
        assert validate_file_extension("photo.png", is_video=False) == ".png"

    def test_valid_webp(self):
        assert validate_file_extension("photo.webp", is_video=False) == ".webp"

    def test_valid_mp4(self):
        assert validate_file_extension("video.mp4", is_video=True) == ".mp4"

    def test_unsupported_image(self):
        with pytest.raises(UnsupportedFormatError):
            validate_file_extension("photo.bmp", is_video=False)

    def test_unsupported_video(self):
        with pytest.raises(UnsupportedFormatError):
            validate_file_extension("video.flv", is_video=True)

    def test_case_insensitive(self):
        assert validate_file_extension("photo.JPG", is_video=False) == ".jpg"


# ── MIME type guessing ───────────────────────────────

class TestGuessContentType:
    def test_jpg(self):
        assert guess_content_type("img.jpg") == "image/jpeg"

    def test_png(self):
        assert guess_content_type("img.png") == "image/png"

    def test_mp4(self):
        assert guess_content_type("vid.mp4") == "video/mp4"

    def test_unknown(self):
        assert guess_content_type("file.xyz") == "application/octet-stream"


# ── File type checks ────────────────────────────────

class TestFileTypeChecks:
    def test_is_image_true(self):
        assert is_image_file("photo.png") is True

    def test_is_image_false(self):
        assert is_image_file("video.mp4") is False

    def test_is_video_true(self):
        assert is_video_file("clip.mp4") is True

    def test_is_video_false(self):
        assert is_video_file("photo.jpg") is False


# ── Person gate ──────────────────────────────────────

def _lm(x=0.0, y=0.0, z=0.0, vis=1.0) -> Landmark:
    return Landmark(x=x, y=y, z=z, visibility=vis, name="")


def _make_lms() -> LandmarkSet:
    return LandmarkSet(
        landmarks=tuple(_lm() for _ in range(33)),
        overall_visibility=1.0,
    )


class TestPersonGate:
    def test_single_person(self):
        ls = [_make_lms()]
        result = validate_single_person(ls, 1)
        assert isinstance(result, LandmarkSet)

    def test_no_person(self):
        with pytest.raises(NoPersonDetectedError):
            validate_single_person([], 0)

    def test_multiple_persons(self):
        with pytest.raises(MultiplePersonsError):
            validate_single_person([_make_lms(), _make_lms()], 2)

    def test_empty_list_with_zero_count(self):
        with pytest.raises(NoPersonDetectedError):
            validate_single_person([], 0)

    def test_count_mismatch_empty(self):
        """Even if count says 1, empty list should fail."""
        with pytest.raises(NoPersonDetectedError):
            validate_single_person([], 1)
