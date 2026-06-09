"""Minimal structured logging for essential system events."""
import logging
import sys


def setup_logger(name: str = "yoga_pose", level: int = logging.INFO) -> logging.Logger:
    """Create a logger with consistent formatting. Only essential events logged."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = setup_logger()
