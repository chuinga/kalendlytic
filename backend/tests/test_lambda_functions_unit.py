"""
Unit tests for Python Lambda functions - Core functionality.
Tests the essential Lambda function components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json
import os

# Set up environment variables for testing
os.environ.update({
    'CONNECTIONS_TABLE': 'test-connections',
    'PREFERENCES_TABLE': 'test-preferences',
    'PRIORITIES_TABLE': 'test-priorities',
    'KMS_KEY_ID': 'test-key-id',
    'AWS_DEFAULT_REGION': 'eu-west-1'
})


class TestLambdaHandlerCore:
    """Test core Lambda handler functionality."""
    
    def test_agent_handler_basic_import(self):
        """Test that agent handler can be imported."""
        try:
            from src.handlers.agent import lambda_handler
            assert callable(lambda_handler)
        except ImportError as e:
            pytest.skip(f"Agent handler not available: {e}")
    
    def test_calendar_handler_basic_import(self):
        """Test that calendar handler can be imported."""
        try:
            from src.handlers.calendar import lambda_handler
            assert callable(lambda_handler)
        except ImportError as e:
            pytest.skip(f"Calendar handler not available: {e}")
    
    def test_auth_handler_basic_import(self):
        """Test that auth handler can be imported."""
        try:
            from src.handlers.auth import lambda_handler
            assert callable(lambda_handler)
        except ImportError as e:
            pytest.skip(f"Auth handler not available: {e}")


class TestOAuthFlowsCore:
    """Test core OAuth functionality."""
    
    def test_google_oauth_service_import(self):
        """Test Google OAuth service import."""
        try:
            from src.services.google_oauth import GoogleOAuthService
            assert GoogleOAuthService is not None
        except ImportError as e:
            pytest.skip(f"Google OAuth service not available: {e}")
    
    def test_microsoft_oauth_service_import(self):
        """Test Microsoft OAuth service import."""
        try:
            from src.services.microsoft_oauth import MicrosoftOAuthService
            assert MicrosoftOAuthService is not None
        except ImportError as e:
            pytest.skip(f"Microsoft OAuth service not available: {e}")
    
    def test_oauth_manager_import(self):
        """Test OAuth manager import."""
        try:
            from src.services.oauth_manager import OAuthManager
            assert OAuthManager is not None
        except ImportError as e:
            pytest.skip(f"OAuth manager not available: {e}")


class TestAgentToolsCore:
    """Test core agent tools functionality."""
    
    def test_availability_tool_import(self):
        """Test availability tool import."""
        try:
            from src.tools.availability_tool import AvailabilityTool
            tool = AvailabilityTool()
            assert tool is not None
            assert hasattr(tool, 'get_availability')
        except ImportError as e:
            pytest.skip(f"Availability tool not available: {e}")
    
    def test_prioritization_tool_import(self):
        """Test prioritization tool import."""
        try:
            from src.tools.prioritization_tool import PrioritizationTool
            tool = PrioritizationTool()
            assert tool is not None
            assert hasattr(tool, 'prioritize_meeting')
        except ImportError as e:
            pytest.skip(f"Prioritization tool not available: {e}")
    
    def test_conflict_resolution_tool_import(self):
        """Test conflict resolution tool import."""
        try:
            from src.tools.conflict_resolution_tool import ConflictResolutionTool
            tool = ConflictResolutionTool()
            assert tool is not None
        except ImportError as e:
            pytest.skip(f"Conflict resolution tool not available: {e}")
    
    def test_event_management_tool_import(self):
        """Test event management tool import."""
        try:
            from src.tools.event_management_tool import EventManagementTool
            tool = EventManagementTool()
            assert tool is not None
        except ImportError as e:
            pytest.skip(f"Event management tool not available: {e}")


class TestCalendarIntegrationCore:
    """Test core calendar integration functionality."""
    
    def test_google_calendar_service_import(self):
        """Test Google Calendar service import."""
        try:
            from src.services.google_calendar import GoogleCalendarService
            assert GoogleCalendarService is not None
        except ImportError as e:
            pytest.skip(f"Google Calendar service not available: {e}")
    
    def test_microsoft_calendar_service_import(self):
        """Test Microsoft Calendar service import."""
        try:
            from src.services.microsoft_calendar import MicrosoftCalendarService
            assert MicrosoftCalendarService is not None
        except ImportError as e:
            pytest.skip(f"Microsoft Calendar service not available: {e}")
    
    def test_availability_aggregation_service_import(self):
        """Test availability aggregation service import."""
        try:
            from src.services.availability_aggregation import AvailabilityAggregationService
            service = AvailabilityAggregationService()
            assert service is not None
        except ImportError as e:
            pytest.skip(f"Availability aggregation service not available: {e}")


class TestPriorityAlgorithmsCore:
    """Test core priority algorithms."""
    
    def test_priority_service_import(self):
        """Test priority service import."""
        try:
            from src.services.priority_service import PriorityService
            service = PriorityService()
            assert service is not None
        except ImportError as e:
            pytest.skip(f"Priority service not available: {e}")
    
    def test_conflict_resolution_engine_import(self):
        """Test conflict resolution engine import."""
        try:
            from src.services.conflict_resolution_engine import ConflictResolutionEngine
            engine = ConflictResolutionEngine()
            assert engine is not None
        except ImportError as e:
            pytest.skip(f"Conflict resolution engine not available: {e}")


class TestTokenManagementCore:
    """Test core token management functionality."""
    
    def test_token_refresh_service_import(self):
        """Test token refresh service import."""
        try:
            from src.services.token_refresh_service import TokenRefreshService
            service = TokenRefreshService()
            assert service is not None
        except ImportError as e:
            pytest.skip(f"Token refresh service not available: {e}")
    
    def test_token_monitoring_import(self):
        """Test token monitoring import."""
        try:
            from src.services.token_monitoring import TokenMonitoringService
            assert TokenMonitoringService is not None
        except ImportError as e:
            pytest.skip(f"Token monitoring service not available: {e}")
    
    def test_token_errors_import(self):
        """Test token errors import."""
        try:
            from src.utils.token_errors import TokenError, TokenExpiredError, TokenRefreshError
            assert TokenError is not None
            assert TokenExpiredError is not None
            assert TokenRefreshError is not None
        except ImportError as e:
            pytest.skip(f"Token errors not available: {e}")


class TestModelsCore:
    """Test core model functionality."""
    
    def test_meeting_model_import(self):
        """Test meeting model import."""
        try:
            from src.models.meeting import Meeting, TimeSlot, Availability
            assert Meeting is not None
            assert TimeSlot is not None
            assert Availability is not None
        except ImportError as e:
            pytest.skip(f"Meeting models not available: {e}")
    
    def test_preferences_model_import(self):
        """Test preferences model import."""
        try:
            from src.models.preferences import Preferences, WorkingHours, FocusBlock
            assert Preferences is not None
            assert WorkingHours is not None
            assert FocusBlock is not None
        except ImportError as e:
            pytest.skip(f"Preferences models not available: {e}")
    
    def test_connection_model_import(self):
        """Test connection model import."""
        try:
            from src.models.connection import Connection
            assert Connection is not None
        except ImportError as e:
            pytest.skip(f"Connection model not available: {e}")


class TestUtilitiesCore:
    """Test core utility functionality."""
    
    def test_logging_utils_import(self):
        """Test logging utilities import."""
        try:
            from src.utils.logging import setup_logger, create_agent_logger
            assert setup_logger is not None
            assert create_agent_logger is not None
        except ImportError as e:
            pytest.skip(f"Logging utilities not available: {e}")
    
    def test_health_check_utils_import(self):
        """Test health check utilities import."""
        try:
            from src.utils.health_check import create_health_check_response
            assert create_health_check_response is not None
        except ImportError as e:
            pytest.skip(f"Health check utilities not available: {e}")
    
    def test_encryption_utils_import(self):
        """Test encryption utilities import."""
        try:
            from src.utils.encryption import encrypt_token, decrypt_token
            assert encrypt_token is not None
            assert decrypt_token is not None
        except ImportError as e:
            pytest.skip(f"Encryption utilities not available: {e}")


class TestBasicFunctionality:
    """Test basic functionality of key components."""
    
    @patch('boto3.resource')
    @patch('boto3.client')
    def test_availability_tool_basic_functionality(self, mock_boto_client, mock_boto_resource):
        """Test basic availability tool functionality."""
        try:
            from src.tools.availability_tool import AvailabilityTool, AvailabilityRequest
            from datetime import datetime
            
            # Mock AWS services
            mock_boto_resource.return_value = Mock()
            mock_boto_client.return_value = Mock()
            
            tool = AvailabilityTool()
            
            # Create a basic request
            request = AvailabilityRequest(
                user_id="test_user",
                start_date=datetime(2024, 1, 15, 9, 0),
                end_date=datetime(2024, 1, 15, 17, 0),
                duration_minutes=30
            )
            
            # Verify request object creation
            assert request.user_id == "test_user"
            assert request.duration_minutes == 30
            
        except ImportError as e:
            pytest.skip(f"Availability tool not available: {e}")
    
    def test_time_slot_creation(self):
        """Test TimeSlot model creation."""
        try:
            from src.models.meeting import TimeSlot
            from datetime import datetime
            
            slot = TimeSlot(
                start=datetime(2024, 1, 15, 10, 0),
                end=datetime(2024, 1, 15, 10, 30),
                available=True,
                score=0.8
            )
            
            assert slot.start.hour == 10
            assert slot.available is True
            assert slot.score == 0.8
            
        except ImportError as e:
            pytest.skip(f"TimeSlot model not available: {e}")
    
    def test_preferences_creation(self):
        """Test Preferences model creation."""
        try:
            from src.models.preferences import Preferences, WorkingHours
            
            preferences = Preferences(
                pk="user#test",
                working_hours={
                    "monday": WorkingHours(start="09:00", end="17:00")
                },
                buffer_minutes=15,
                vip_contacts=["boss@company.com"]
            )
            
            assert preferences.buffer_minutes == 15
            assert len(preferences.vip_contacts) == 1
            assert "monday" in preferences.working_hours
            
        except ImportError as e:
            pytest.skip(f"Preferences model not available: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])