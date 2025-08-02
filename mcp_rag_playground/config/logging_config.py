"""
Centralized logging configuration for the mcp_rag_playground project.
"""

import logging
import sys
from typing import Optional
from pathlib import Path


class LoggingConfig:
    """Centralized logging configuration manager."""
    
    _loggers: dict[str, logging.Logger] = {}
    _configured = False
    
    @classmethod
    def setup_logging(cls, 
                     level: str = "INFO",
                     log_file: Optional[str] = None,
                     console_output: bool = True,
                     format_string: Optional[str] = None) -> None:
        """
        Setup centralized logging configuration.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path
            console_output: Whether to output to console
            format_string: Custom format string
        """
        if cls._configured:
            return
            
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        formatter = logging.Formatter(format_string)
        
        # Console handler - ALWAYS use stderr to avoid interfering with JSON output
        if console_output:
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance for the given module/class name.
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Configured logger instance
        """
        if not cls._configured:
            cls.setup_logging()
            
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
            
        return cls._loggers[name]
    
    @classmethod
    def set_level(cls, logger_name: str, level: str) -> None:
        """
        Set logging level for a specific logger.
        
        Args:
            logger_name: Name of the logger
            level: Logging level
        """
        if logger_name in cls._loggers:
            cls._loggers[logger_name].setLevel(getattr(logging, level.upper()))


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return LoggingConfig.get_logger(name)


def setup_project_logging(environment: str = "dev") -> None:
    """
    Setup logging configuration for different environments.
    
    Args:
        environment: Environment name (dev, test, prod)
    """
    config_map = {
        "dev": {
            "level": "DEBUG",
            "console_output": True,
            "log_file": "logs/mcp_rag_dev.log"
        },
        "test": {
            "level": "WARNING",
            "console_output": False,
            "log_file": "logs/mcp_rag_test.log"
        },
        "prod": {
            "level": "INFO",
            "console_output": True,
            "log_file": "logs/mcp_rag_prod.log"
        }
    }
    
    config = config_map.get(environment, config_map["dev"])
    LoggingConfig.setup_logging(**config)


def setup_mcp_logging(environment: str = "prod", log_level: str = "INFO") -> None:
    """
    Setup logging specifically for MCP server context.
    
    MCP servers must only output JSON to stdout, so all logging goes to stderr and files.
    
    Args:
        environment: Environment name 
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    LoggingConfig.setup_logging(
        level=log_level,
        log_file=f"logs/mcp_rag_{environment}.log",
        console_output=True,  # Will use stderr due to our configuration
        format_string='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )