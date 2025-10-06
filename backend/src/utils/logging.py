"""
Structured logging utilities for CloudWatch integration.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', None),
            'user_id': getattr(record, 'user_id', None),
            'function_name': getattr(record, 'aws_request_id', None)
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_entry[key] = value
                
        return json.dumps(log_entry, default=str)


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Set up structured logger for Lambda functions.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add structured handler
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    
    # Prevent duplicate logs
    logger.propagate = False
    
    return logger


def get_correlation_id() -> str:
    """Generate a new correlation ID for request tracking."""
    return str(uuid.uuid4())


def redact_pii(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Redact personally identifiable information from log data.
    
    Args:
        data: Dictionary containing potentially sensitive data
        
    Returns:
        Dictionary with PII redacted
    """
    pii_fields = {
        'email', 'phone', 'address', 'ssn', 'credit_card',
        'access_token', 'refresh_token', 'password', 'secret'
    }
    
    redacted_data = {}
    for key, value in data.items():
        if any(pii_field in key.lower() for pii_field in pii_fields):
            redacted_data[key] = '[REDACTED]'
        elif isinstance(value, dict):
            redacted_data[key] = redact_pii(value)
        elif isinstance(value, list):
            redacted_data[key] = [redact_pii(item) if isinstance(item, dict) else item for item in value]
        else:
            redacted_data[key] = value
            
    return redacted_data