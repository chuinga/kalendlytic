"""
Structured logging utilities for CloudWatch integration with PII redaction and agent decision tracking.
"""

import json
import logging
import uuid
import re
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AgentDecisionType(Enum):
    """Types of agent decisions for tracking."""
    SCHEDULING = "scheduling"
    CONFLICT_RESOLUTION = "conflict_resolution"
    PRIORITIZATION = "prioritization"
    PREFERENCE_EXTRACTION = "preference_extraction"
    TOOL_INVOCATION = "tool_invocation"
    ERROR_HANDLING = "error_handling"


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging with enhanced PII redaction."""
    
    def __init__(self):
        super().__init__()
        self.pii_patterns = self._compile_pii_patterns()
    
    def _compile_pii_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for PII detection."""
        return {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
            'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'access_token': re.compile(r'\b[A-Za-z0-9+/]{20,}={0,2}\b'),
            'api_key': re.compile(r'\b[A-Za-z0-9]{32,}\b'),
        }
    
    def _redact_pii_in_text(self, text: str) -> str:
        """Redact PII from text using regex patterns."""
        if not isinstance(text, str):
            return text
            
        redacted_text = text
        for pii_type, pattern in self.pii_patterns.items():
            redacted_text = pattern.sub(f'[REDACTED_{pii_type.upper()}]', redacted_text)
        
        return redacted_text
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON with PII redaction."""
        # Get AWS Lambda context information
        aws_request_id = getattr(record, 'aws_request_id', os.environ.get('AWS_REQUEST_ID'))
        function_name = getattr(record, 'function_name', os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
        function_version = getattr(record, 'function_version', os.environ.get('AWS_LAMBDA_FUNCTION_VERSION'))
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': self._redact_pii_in_text(record.getMessage()),
            'correlation_id': getattr(record, 'correlation_id', None),
            'user_id': getattr(record, 'user_id', None),
            'session_id': getattr(record, 'session_id', None),
            'aws_request_id': aws_request_id,
            'function_name': function_name,
            'function_version': function_version,
            'environment': os.environ.get('ENVIRONMENT', 'dev'),
            'service': 'meeting-scheduling-agent'
        }
        
        # Add agent-specific fields
        agent_fields = ['agent_run_id', 'decision_type', 'tool_name', 'execution_time_ms', 
                       'cost_estimate', 'rationale', 'alternatives_count', 'confidence_score']
        for field in agent_fields:
            if hasattr(record, field):
                value = getattr(record, field)
                if isinstance(value, str):
                    value = self._redact_pii_in_text(value)
                log_entry[field] = value
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': self._redact_pii_in_text(str(record.exc_info[1])) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add performance metrics
        if hasattr(record, 'performance_metrics'):
            log_entry['performance_metrics'] = getattr(record, 'performance_metrics')
        
        # Add extra fields with PII redaction
        excluded_fields = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
            'filename', 'module', 'lineno', 'funcName', 'created',
            'msecs', 'relativeCreated', 'thread', 'threadName',
            'processName', 'process', 'getMessage', 'exc_info',
            'exc_text', 'stack_info', 'correlation_id', 'user_id',
            'session_id', 'aws_request_id', 'function_name', 'function_version'
        } | set(agent_fields) | {'performance_metrics'}
        
        for key, value in record.__dict__.items():
            if key not in excluded_fields:
                if isinstance(value, (dict, list)):
                    log_entry[key] = self._redact_pii_recursive(value)
                elif isinstance(value, str):
                    log_entry[key] = self._redact_pii_in_text(value)
                else:
                    log_entry[key] = value
        
        return json.dumps(log_entry, default=str, separators=(',', ':'))
    
    def _redact_pii_recursive(self, data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
        """Recursively redact PII from nested data structures."""
        if isinstance(data, dict):
            return {k: self._redact_pii_recursive(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._redact_pii_recursive(item) for item in data]
        elif isinstance(data, str):
            return self._redact_pii_in_text(data)
        else:
            return data


class AgentLogger:
    """Enhanced logger for agent decision tracking and audit trails."""
    
    def __init__(self, name: str, correlation_id: Optional[str] = None, user_id: Optional[str] = None):
        self.logger = setup_logger(name)
        self.correlation_id = correlation_id or get_correlation_id()
        self.user_id = user_id
        self.agent_run_id: Optional[str] = None
        self.performance_start_time: Optional[float] = None
    
    def set_agent_run_id(self, run_id: str) -> None:
        """Set the agent run ID for tracking related operations."""
        self.agent_run_id = run_id
    
    def set_user_context(self, user_id: str, session_id: Optional[str] = None) -> None:
        """Set user context for all subsequent logs."""
        self.user_id = user_id
        self.session_id = session_id
    
    def start_performance_tracking(self) -> None:
        """Start performance tracking for the current operation."""
        import time
        self.performance_start_time = time.time()
    
    def log_agent_decision(
        self,
        decision_type: AgentDecisionType,
        rationale: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        confidence_score: Optional[float] = None,
        alternatives_count: Optional[int] = None,
        tool_name: Optional[str] = None,
        cost_estimate: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log agent decision with structured information for audit trails.
        
        Args:
            decision_type: Type of decision made
            rationale: Natural language explanation of the decision
            inputs: Input parameters that led to the decision
            outputs: Results of the decision
            confidence_score: Confidence level (0.0 to 1.0)
            alternatives_count: Number of alternatives considered
            tool_name: Name of the tool used
            cost_estimate: Estimated cost breakdown
        """
        execution_time_ms = None
        if self.performance_start_time:
            import time
            execution_time_ms = int((time.time() - self.performance_start_time) * 1000)
        
        extra = {
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'agent_run_id': self.agent_run_id,
            'decision_type': decision_type.value,
            'rationale': rationale,
            'inputs': inputs,
            'outputs': outputs,
            'confidence_score': confidence_score,
            'alternatives_count': alternatives_count,
            'tool_name': tool_name,
            'cost_estimate': cost_estimate,
            'execution_time_ms': execution_time_ms
        }
        
        self.logger.info(
            f"Agent decision: {decision_type.value} - {rationale}",
            extra=extra
        )
    
    def log_tool_invocation(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        success: bool,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log tool invocation for audit and debugging.
        
        Args:
            tool_name: Name of the invoked tool
            inputs: Tool input parameters
            outputs: Tool outputs
            success: Whether the tool execution was successful
            execution_time_ms: Execution time in milliseconds
            error_message: Error message if execution failed
        """
        extra = {
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'agent_run_id': self.agent_run_id,
            'tool_name': tool_name,
            'inputs': inputs,
            'outputs': outputs,
            'success': success,
            'execution_time_ms': execution_time_ms,
            'error_message': error_message
        }
        
        level = logging.INFO if success else logging.ERROR
        message = f"Tool invocation: {tool_name} - {'SUCCESS' if success else 'FAILED'}"
        if error_message:
            message += f" - {error_message}"
        
        self.logger.log(level, message, extra=extra)
    
    def log_performance_metrics(
        self,
        operation: str,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Log performance metrics for monitoring and optimization.
        
        Args:
            operation: Name of the operation being measured
            metrics: Performance metrics dictionary
        """
        extra = {
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'agent_run_id': self.agent_run_id,
            'operation': operation,
            'performance_metrics': metrics
        }
        
        self.logger.info(f"Performance metrics: {operation}", extra=extra)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def _log_with_context(self, level: int, message: str, **kwargs) -> None:
        """Log message with correlation context."""
        extra = kwargs.get('extra', {})
        extra.update({
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'agent_run_id': self.agent_run_id
        })
        kwargs['extra'] = extra
        self.logger.log(level, message, **kwargs)


def setup_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Set up structured logger for Lambda functions with enhanced formatting.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level from environment variable or parameter
    log_level = os.environ.get('LOG_LEVEL', level).upper()
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers to avoid duplicates
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


def create_agent_logger(
    name: str,
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> AgentLogger:
    """
    Create an enhanced agent logger with decision tracking capabilities.
    
    Args:
        name: Logger name
        correlation_id: Optional correlation ID for request tracking
        user_id: Optional user ID for context
        
    Returns:
        AgentLogger instance
    """
    return AgentLogger(name, correlation_id, user_id)


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
        'access_token', 'refresh_token', 'password', 'secret',
        'api_key', 'token', 'credential', 'auth'
    }
    
    def _redact_recursive(obj):
        if isinstance(obj, dict):
            redacted = {}
            for key, value in obj.items():
                if any(pii_field in key.lower() for pii_field in pii_fields):
                    redacted[key] = '[REDACTED]'
                else:
                    redacted[key] = _redact_recursive(value)
            return redacted
        elif isinstance(obj, list):
            return [_redact_recursive(item) for item in obj]
        elif isinstance(obj, str):
            # Apply regex-based PII redaction
            formatter = StructuredFormatter()
            return formatter._redact_pii_in_text(obj)
        else:
            return obj
    
    return _redact_recursive(data)


class LogAggregator:
    """Utility for aggregating and analyzing agent decision logs."""
    
    @staticmethod
    def create_decision_summary(
        decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a summary of agent decisions for reporting.
        
        Args:
            decisions: List of decision log entries
            
        Returns:
            Summary statistics and insights
        """
        if not decisions:
            return {'total_decisions': 0}
        
        decision_types = {}
        total_execution_time = 0
        successful_decisions = 0
        total_cost = 0.0
        
        for decision in decisions:
            # Count decision types
            decision_type = decision.get('decision_type', 'unknown')
            decision_types[decision_type] = decision_types.get(decision_type, 0) + 1
            
            # Aggregate execution time
            exec_time = decision.get('execution_time_ms', 0)
            if exec_time:
                total_execution_time += exec_time
            
            # Count successful decisions
            if decision.get('success', True):
                successful_decisions += 1
            
            # Aggregate costs
            cost_estimate = decision.get('cost_estimate', {})
            if isinstance(cost_estimate, dict) and 'estimated_cost_usd' in cost_estimate:
                total_cost += float(cost_estimate['estimated_cost_usd'])
        
        return {
            'total_decisions': len(decisions),
            'decision_types': decision_types,
            'success_rate': successful_decisions / len(decisions) if decisions else 0,
            'average_execution_time_ms': total_execution_time / len(decisions) if decisions else 0,
            'total_cost_usd': total_cost,
            'average_cost_per_decision_usd': total_cost / len(decisions) if decisions else 0
        }