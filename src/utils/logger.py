"""
Logger - Console output only, no file creation
Compatible with existing imports: from src.utils.logger import Logger
"""

import logging
import sys


class Logger:
    """
    Logger class that prints to console only.
    No log files created!

    Usage:
        from src.utils.logger import Logger

        logger = Logger(__name__)
        logger.info("This goes to console only")
        logger.error("No files created!")
    """

    def __init__(self, name):
        """
        Initialize logger.

        Args:
            name: Logger name (usually __name__)
        """
        self.logger = logging.getLogger(name)

        # Only configure if not already configured
        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)

            # Console handler only (no file handler!)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)

            # Format
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)

            # Add only console handler - NO FILE HANDLER!
            self.logger.addHandler(console_handler)

    def debug(self, message):
        """Log debug message to console"""
        self.logger.debug(message)

    def info(self, message):
        """Log info message to console"""
        self.logger.info(message)

    def warning(self, message):
        """Log warning message to console"""
        self.logger.warning(message)

    def error(self, message):
        """Log error message to console"""
        self.logger.error(message)

    def critical(self, message):
        """Log critical message to console"""
        self.logger.critical(message)

    def exception(self, param):
        pass


# Alternative: function-based (if needed)
def get_logger(name):
    """
    Get logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return Logger(name)