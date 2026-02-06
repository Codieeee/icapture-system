"""
Logging Utility for iCapture System
Provides consistent logging across all modules with file and console output
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

class Logger:
    """Centralized logging manager"""
    
    _loggers = {}
    
    @staticmethod
    def get_logger(name, log_dir='data/logs', level=logging.INFO):
        """
        Get or create a logger instance
        
        Args:
            name: Logger name (usually module name)
            log_dir: Directory to store log files
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
        Returns:
            logging.Logger instance
        """
        if name in Logger._loggers:
            return Logger._loggers[name]
        
        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # Create log directory
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # File handler (rotating)
        log_file = log_path / f'icapture_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        Logger._loggers[name] = logger
        return logger

    @staticmethod
    def log_to_database(db_manager, level, module, message, details=None):
        """
        Log message to database system_logs table
        
        Args:
            db_manager: DatabaseManager instance
            level: Log level (INFO, WARNING, ERROR, CRITICAL)
            module: Module name
            message: Log message
            details: Optional JSON details
        """
        try:
            import json
            db_manager.execute(
                """
                INSERT INTO system_logs (log_level, module, message, details)
                VALUES (%s, %s, %s, %s)
                """,
                (level, module, message, json.dumps(details) if details else None)
            )
        except Exception as e:
            # Fallback to file logging if database fails
            logger = Logger.get_logger('database_logger')
            logger.error(f"Failed to log to database: {e}")

# Convenience functions
def get_logger(name):
    """Quick access to logger"""
    return Logger.get_logger(name)

if __name__ == '__main__':
    # Test logging
    logger = get_logger('test_module')
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
