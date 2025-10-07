"""
Logging configuration for the meeting scheduling agent.
"""

import os
from typing import Dict, Any
from enum import Enum


class LogLevel(Enum):
    """Log levels for the application."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingConfig:
    """Configuration class for logging settings."""
    
    # Default log level
    DEFAULT_LOG_LEVEL = LogLevel.INFO
    
    # Log retention periods (in days)
    CLOUDWATCH_RETENTION_DAYS = 30
    AGENT_DECISION_RETENTION_DAYS = 90
    ARCHIVE_RETENTION_YEARS = 7
    
    # Log group names
    LOG_GROUP_PREFIX = "/aws/lambda/meeting-agent"
    AGENT_DECISION_LOG_GROUP = f"{LOG_GROUP_PREFIX}-agent-decisions"
    
    # S3 archival settings
    ARCHIVE_BUCKET_PREFIX = "meeting-agent-logs-archive"
    
    # PII redaction settings
    PII_REDACTION_ENABLED = True
    REDACTION_PLACEHOLDER = "[REDACTED]"
    
    # Performance logging settings
    PERFORMANCE_LOGGING_ENABLED = True
    SLOW_OPERATION_THRESHOLD_MS = 5000
    
    # Agent decision logging settings
    AGENT_DECISION_LOGGING_ENABLED = True
    CONFIDENCE_SCORE_THRESHOLD = 0.5  # Log decisions below this confidence
    
    @classmethod
    def get_log_level(cls) -> str:
        """Get log level from environment or default."""
        return os.environ.get('LOG_LEVEL', cls.DEFAULT_LOG_LEVEL.value).upper()
    
    @classmethod
    def get_environment(cls) -> str:
        """Get current environment."""
        return os.environ.get('ENVIRONMENT', 'dev')
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls.get_environment().lower() == 'prod'
    
    @classmethod
    def get_log_group_name(cls, service_name: str) -> str:
        """Get log group name for a service."""
        return f"{cls.LOG_GROUP_PREFIX}-{service_name}"
    
    @classmethod
    def get_archive_bucket_name(cls, account_id: str, region: str) -> str:
        """Get S3 archive bucket name."""
        return f"{cls.ARCHIVE_BUCKET_PREFIX}-{account_id}-{region}"
    
    @classmethod
    def should_log_performance(cls, execution_time_ms: int) -> bool:
        """Determine if performance should be logged based on execution time."""
        return (
            cls.PERFORMANCE_LOGGING_ENABLED and 
            execution_time_ms > cls.SLOW_OPERATION_THRESHOLD_MS
        )
    
    @classmethod
    def should_log_agent_decision(cls, confidence_score: float = None) -> bool:
        """Determine if agent decision should be logged."""
        if not cls.AGENT_DECISION_LOGGING_ENABLED:
            return False
        
        # Always log if no confidence score provided
        if confidence_score is None:
            return True
        
        # Log low-confidence decisions for review
        return confidence_score < cls.CONFIDENCE_SCORE_THRESHOLD
    
    @classmethod
    def get_structured_logging_config(cls) -> Dict[str, Any]:
        """Get structured logging configuration."""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'structured': {
                    '()': 'src.utils.logging.StructuredFormatter',
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'structured',
                    'level': cls.get_log_level(),
                },
            },
            'loggers': {
                'meeting_agent': {
                    'handlers': ['console'],
                    'level': cls.get_log_level(),
                    'propagate': False,
                },
                'agent_decisions': {
                    'handlers': ['console'],
                    'level': 'INFO',
                    'propagate': False,
                },
                'tool_invocations': {
                    'handlers': ['console'],
                    'level': 'INFO',
                    'propagate': False,
                },
            },
            'root': {
                'level': cls.get_log_level(),
                'handlers': ['console'],
            },
        }


# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    'dev': {
        'log_level': LogLevel.DEBUG,
        'cloudwatch_retention_days': 7,
        'pii_redaction_enabled': False,  # Disabled for easier debugging
        'performance_logging_enabled': True,
    },
    'staging': {
        'log_level': LogLevel.INFO,
        'cloudwatch_retention_days': 14,
        'pii_redaction_enabled': True,
        'performance_logging_enabled': True,
    },
    'prod': {
        'log_level': LogLevel.WARNING,
        'cloudwatch_retention_days': 30,
        'pii_redaction_enabled': True,
        'performance_logging_enabled': False,  # Reduce noise in production
    },
}


def get_environment_config() -> Dict[str, Any]:
    """Get configuration for current environment."""
    env = LoggingConfig.get_environment().lower()
    return ENVIRONMENT_CONFIGS.get(env, ENVIRONMENT_CONFIGS['dev'])


def apply_environment_config() -> None:
    """Apply environment-specific configuration to LoggingConfig."""
    config = get_environment_config()
    
    # Update LoggingConfig with environment-specific values
    if 'log_level' in config:
        LoggingConfig.DEFAULT_LOG_LEVEL = config['log_level']
    
    if 'cloudwatch_retention_days' in config:
        LoggingConfig.CLOUDWATCH_RETENTION_DAYS = config['cloudwatch_retention_days']
    
    if 'pii_redaction_enabled' in config:
        LoggingConfig.PII_REDACTION_ENABLED = config['pii_redaction_enabled']
    
    if 'performance_logging_enabled' in config:
        LoggingConfig.PERFORMANCE_LOGGING_ENABLED = config['performance_logging_enabled']