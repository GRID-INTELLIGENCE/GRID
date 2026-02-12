"""
Logging configuration for workspace utilities.

Provides structured JSON logging for Cascade integration and debugging.
"""

import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from .config import config


class CascadeJSONFormatter(logging.Formatter):
    """JSON formatter for Cascade-friendly logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Add Cascade context if available
        if hasattr(record, 'cascade_context'):
            log_entry["cascade_context"] = record.cascade_context
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if record.args:
            log_entry["args"] = str(record.args)
        
        return json.dumps(log_entry)


class CascadeContextAdapter(logging.LoggerAdapter):
    """Logger adapter that adds Cascade context to log records."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add Cascade context to log records."""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        if 'cascade_context' not in kwargs['extra']:
            kwargs['extra']['cascade_context'] = {}
        
        # Add default context
        cascade_context = kwargs['extra']['cascade_context']
        cascade_context.update({
            'command': getattr(self, 'command', 'unknown'),
            'workspace_root': str(config.get_workspace_root()),
            'output_dir': str(config.get_output_dir()),
        })
        
        # Merge with adapter context
        if hasattr(self, 'context'):
            cascade_context.update(self.context)
        
        return msg, kwargs


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    json_output: Optional[bool] = None
) -> logging.Logger:
    """Set up logging for workspace utilities.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        json_output: Whether to use JSON format (default: from config)
    
    Returns:
        Configured logger instance
    """
    # Get log level from config or parameter
    if log_level is None:
        log_level = config.get("log_level", "INFO")
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Determine output format
    if json_output is None:
        json_output = config.should_output_json()
    
    # Create logger
    logger = logging.getLogger("workspace_utils")
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if json_output:
        console_handler.setFormatter(CascadeJSONFormatter())
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
    
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        # Always use JSON format for file logs (for Cascade)
        file_handler.setFormatter(CascadeJSONFormatter())
        
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    
    return logger


def get_logger(name: str, command: Optional[str] = None) -> CascadeContextAdapter:
    """Get logger with Cascade context adapter.
    
    Args:
        name: Logger name
        command: Command name for context
    
    Returns:
        Logger adapter with Cascade context
    """
    logger = logging.getLogger(f"workspace_utils.{name}")
    
    adapter = CascadeContextAdapter(logger, {})
    if command:
        adapter.command = command
    
    return adapter


# Default logger instance
_logger: Optional[logging.Logger] = None


def get_default_logger() -> logging.Logger:
    """Get default logger instance."""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


def log_command_start(command: str, args: Dict[str, Any]) -> None:
    """Log command start with context."""
    logger = get_default_logger()
    logger.info(
        f"Starting command: {command}",
        extra={
            'cascade_context': {
                'command': command,
                'arguments': args,
                'action': 'start'
            }
        }
    )


def log_command_end(command: str, success: bool, **kwargs) -> None:
    """Log command end with context."""
    logger = get_default_logger()
    level = logging.INFO if success else logging.ERROR
    
    logger.log(
        level,
        f"Command {command} {'completed' if success else 'failed'}",
        extra={
            'cascade_context': {
                'command': command,
                'action': 'end',
                'success': success,
                **kwargs
            }
        }
    )


def log_progress(stage: str, current: int, total: int, **context) -> None:
    """Log progress for long-running operations."""
    logger = get_default_logger()
    percentage = (current / total * 100) if total > 0 else 0
    
    logger.info(
        f"Progress: {stage} ({current}/{total} - {percentage:.1f}%)",
        extra={
            'cascade_context': {
                'action': 'progress',
                'stage': stage,
                'current': current,
                'total': total,
                'percentage': percentage,
                **context
            }
        }
    )