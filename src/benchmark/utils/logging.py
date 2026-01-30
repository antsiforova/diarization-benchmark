"""Logging configuration for the benchmark system."""

import logging
import sys


def setup_logging(log_level: str = "INFO", log_format: str = "text") -> None:
    """Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Format type ("json" or "text")
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level.upper())
    
    # Set format
    if log_format == "json":
        # Simple JSON-like format
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        # Human-readable text format
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)-8s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)