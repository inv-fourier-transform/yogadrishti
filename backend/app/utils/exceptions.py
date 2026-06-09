"""Custom exception hierarchy for the yoga pose detector."""


class YogaPoseError(Exception):
    """Base exception for all yoga pose errors."""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class FileValidationError(YogaPoseError):
    """Raised when uploaded file fails validation."""
    def __init__(self, message: str):
        super().__init__(message, "FILE_VALIDATION_ERROR")


class FileTooLargeError(FileValidationError):
    """Raised when file exceeds size limit."""
    def __init__(self, message: str):
        self.error_code = "FILE_TOO_LARGE"
        super().__init__(message)


class UnsupportedFormatError(FileValidationError):
    """Raised when file format is not supported."""
    def __init__(self, message: str):
        self.error_code = "UNSUPPORTED_FORMAT"
        super().__init__(message)


class ImageTooSmallError(FileValidationError):
    """Raised when image dimensions are below minimum."""
    def __init__(self, message: str):
        self.error_code = "IMAGE_TOO_SMALL"
        super().__init__(message)


class ImageTooLargeError(FileValidationError):
    """Raised when image dimensions exceed maximum."""
    def __init__(self, message: str):
        self.error_code = "IMAGE_TOO_LARGE"
        super().__init__(message)


class VideoDurationError(FileValidationError):
    """Raised when video exceeds duration limit."""
    def __init__(self, message: str):
        self.error_code = "VIDEO_TOO_LONG"
        super().__init__(message)


class CorruptedFileError(FileValidationError):
    """Raised when file is corrupted or unreadable."""
    def __init__(self, message: str):
        self.error_code = "CORRUPTED_FILE"
        super().__init__(message)


class PersonDetectionError(YogaPoseError):
    """Raised for person-count validation failures."""
    def __init__(self, message: str, error_code: str = "PERSON_DETECTION_ERROR"):
        super().__init__(message, error_code)


class NoPersonDetectedError(PersonDetectionError):
    """Raised when no person is detected in the frame."""
    def __init__(self, message: str = "No person detected in the image. Please upload an image with a person performing a yoga pose."):
        super().__init__(message, "NO_PERSON_DETECTED")


class MultiplePersonsError(PersonDetectionError):
    """Raised when multiple people are detected."""
    def __init__(self, message: str = "Multiple people detected. Please upload an image with only one person."):
        super().__init__(message, "MULTIPLE_PERSONS")


class PoseDetectionError(YogaPoseError):
    """Raised when pose detection fails."""
    def __init__(self, message: str):
        super().__init__(message, "POSE_DETECTION_ERROR")


class LowConfidenceError(YogaPoseError):
    """Raised when pose cannot be reliably evaluated."""
    def __init__(self, message: str, reason: str = ""):
        self.reason = reason
        super().__init__(message, "LOW_CONFIDENCE")


class LLMError(YogaPoseError):
    """Raised when LLM feedback generation fails."""
    def __init__(self, message: str):
        super().__init__(message, "LLM_ERROR")


class JobNotFoundError(YogaPoseError):
    """Raised when a job ID is not found."""
    def __init__(self, job_id: str):
        super().__init__(f"Job '{job_id}' not found.", "JOB_NOT_FOUND")


class UserNotFoundError(YogaPoseError):
    """Raised when a user ID is not found."""
    def __init__(self, user_id: str):
        super().__init__(f"User '{user_id}' not found.", "USER_NOT_FOUND")
