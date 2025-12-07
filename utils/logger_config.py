"""Centralized logging configuration."""
import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler
from .config import LOG_DIR, LOG_LEVEL

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional log file name (defaults to service name)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        log_path = LOG_DIR / log_file
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    return logger

