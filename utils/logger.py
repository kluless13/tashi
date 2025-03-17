"""
Logging configuration for the Tashi bot.
"""
import sys
import os
from loguru import logger
import config

# Configure logger
logger.remove()  # Remove default handler

# Add console handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Add file handler
logger.add(
    config.LOG_FILE,
    rotation="10 MB",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    backtrace=True,
    diagnose=True
)

def get_logger(name):
    """
    Get a logger for a specific module.
    
    Args:
        name (str): Name of the module
        
    Returns:
        logger: Configured logger instance
    """
    return logger.bind(name=name) 