"""Temporary file I/O helpers."""
from __future__ import annotations
import tempfile
import os
from pathlib import Path


def save_temp_file(content: bytes, suffix: str = "") -> str:
    """Save bytes to a temporary file and return the path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, content)
    finally:
        os.close(fd)
    return path


def cleanup_temp_file(path: str) -> None:
    """Remove a temporary file if it exists."""
    try:
        if path and Path(path).exists():
            os.unlink(path)
    except OSError:
        pass


def ensure_directory(path: str | Path) -> Path:
    """Create directory if it doesn't exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
