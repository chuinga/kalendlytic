"""
Tests for structured logging system with PII redaction and agent decision tracking.
"""

import json
import logging
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.utils.logging import (
    StructuredFormatter, 
    AgentLogger, 
    AgentDecisionType,
    setup_logger,
    create_agent_logger,
    redact_pii
)
from src.config.logging_config import LoggingConfig


class TestStructuredFormatter:
    """Test structured JSON logging formatter."""
    
    def test_basic_log_formatting(self):
        """Test basic log record formatting."""
        formatter = StructuredFormatter()
        
        # Create a log record
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        # Format the record
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # Verify structure
        assert 'timestamp' in log_data
        assert log_data['level'] == 'INFO'
        assert log_data['logger'] == 'test_logger'
        assert log_data['message'] == 'Test message'
        assert log_data['service'] == 'meeting-scheduling-agent'
    
    def test_pii_redaction_in_message(self):
        """Test PII redaction in log messages."""
        formatter = StructuredFormatter()
        
        # Create log record with PII
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='User email: user@example.com, phone: 555-123-4567',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # Verify PII is redacted
        assert 'user@example.com' not in log_data['message']
        assert '555-123-4567' not in log_data['message']
        assert '[REDACTED_EMAIL]' in log_data['message']
        assert '[REDACTED_PHONE]' in log_data['message']
    
    def test_agent_fields_inclusion(self):
        """Test inclusion of agent-specific fields."""
        formatter = StructuredFormatter()
        
        record = logging.LogRecord(
            name='agent_logger',
            level=logging.INFO,
            pathname='agent.py',
            lineno=50,
            msg='Agent decision made',
            args=(),
            exc_info=None
        )
        
        # Add agent-specific attributes
        record.agent_run_id = 'run-123'
        record.decision_type = 'scheduling'
        record.confidence_score = 0.85
        record.execution_time_ms = 1500
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        # Verify agent fields are included
        assert log_data['agent_run_id'] == 'run-123'
        assert log_data['decision_type'] == 'scheduling'
        assert log_data['confidence_score'] == 0.85
        assert log_data['execution_time_ms'] == 1500


class TestAgentLogger:
    """Test enhanced agent logger functionality."""
    
    def test_agent_logger_creation(self):
        """Test agent logger creation with context."""
        logger = create_agent_logger('test_agent', user_id='user-123')
        
        assert logger.user_id == 'user-123'
        assert logger.correlation_id is not None
        assert logger.agent_run_id is None
    
    def test_agent_decision_logging(self):
        """Test agent decision logging."""
        logger = create_agent_logger('test_agent')
        logger.set_agent_run_id('run-456')
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_agent_decision(
                decision_type=AgentDecisionType.SCHEDULING,
                rationale="Scheduling meeting based on availability",
                inputs={'attendees': ['user1@example.com']},
                outputs={'meeting_id': 'meeting-123'},
                confidence_score=0.9,
                alternatives_count=3
            )
            
            # Verify the log call
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            
            # Check the extra fields
            extra = call_args[1]['extra']
            assert extra['decision_type'] == 'scheduling'
            assert extra['confidence_score'] == 0.9
            assert extra['alternatives_count'] == 3
            assert extra['agent_run_id'] == 'run-456'
    
    def test_tool_invocation_logging(self):
        """Test tool invocation logging."""
        logger = create_agent_logger('test_agent')
        
        with patch.object(logger.logger, 'log') as mock_log:
            logger.log_tool_invocation(
                tool_name='availability_tool',
                inputs={'date_range': '2024-01-01 to 2024-01-07'},
                outputs={'available_slots': 5},
                success=True,
                execution_time_ms=250
            )
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            
            # Check log level (should be INFO for successful invocation)
            assert call_args[0][0] == logging.INFO
            
            extra = call_args[1]['extra']
            assert extra['tool_name'] == 'availability_tool'
            assert extra['success'] is True
            assert extra['execution_time_ms'] == 250
    
    def test_performance_metrics_logging(self):
        """Test performance metrics logging."""
        logger = create_agent_logger('test_agent')
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_performance_metrics(
                operation='calendar_sync',
                metrics={
                    'events_processed': 100,
                    'sync_duration_ms': 2500,
                    'api_calls': 5
                }
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args
            
            extra = call_args[1]['extra']
            assert extra['operation'] == 'calendar_sync'
            assert extra['performance_metrics']['events_processed'] == 100


class TestPIIRedaction:
    """Test PII redaction functionality."""
    
    def test_redact_pii_basic(self):
        """Test basic PII redaction."""
        data = {
            'user_email': 'user@example.com',
            'phone_number': '555-123-4567',
            'safe_field': 'safe_value',
            'nested': {
                'access_token': 'secret_token_123',
                'public_info': 'public_value'
            }
        }
        
        redacted = redact_pii(data)
        
        assert redacted['user_email'] == '[REDACTED]'
        assert redacted['phone_number'] == '[REDACTED]'
        assert redacted['safe_field'] == 'safe_value'
        assert redacted['nested']['access_token'] == '[REDACTED]'
        assert redacted['nested']['public_info'] == 'public_value'
    
    def test_redact_pii_in_strings(self):
        """Test PII redaction in string values."""
        data = {
            'message': 'Contact user at user@example.com or call 555-123-4567',
            'description': 'Meeting with important client'
        }
        
        redacted = redact_pii(data)
        
        # Check that email and phone are redacted in the message
        assert 'user@example.com' not in redacted['message']
        assert '555-123-4567' not in redacted['message']
        assert '[REDACTED_EMAIL]' in redacted['message']
        assert '[REDACTED_PHONE]' in redacted['message']
        
        # Check that safe content is preserved
        assert 'Meeting with important client' == redacted['description']


class TestLoggingConfig:
    """Test logging configuration."""
    
    def test_environment_detection(self):
        """Test environment detection."""
        with patch.dict('os.environ', {'ENVIRONMENT': 'prod'}):
            assert LoggingConfig.get_environment() == 'prod'
            assert LoggingConfig.is_production() is True
    
    def test_log_level_from_environment(self):
        """Test log level configuration from environment."""
        with patch.dict('os.environ', {'LOG_LEVEL': 'DEBUG'}):
            assert LoggingConfig.get_log_level() == 'DEBUG'
    
    def test_log_group_name_generation(self):
        """Test log group name generation."""
        log_group = LoggingConfig.get_log_group_name('auth-handler')
        assert log_group == '/aws/lambda/meeting-agent-auth-handler'
    
    def test_archive_bucket_name_generation(self):
        """Test archive bucket name generation."""
        bucket_name = LoggingConfig.get_archive_bucket_name('123456789012', 'eu-west-1')
        assert bucket_name == 'meeting-agent-logs-archive-123456789012-eu-west-1'


if __name__ == '__main__':
    pytest.main([__file__])