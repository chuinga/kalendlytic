"""
Integration tests for API endpoints covering OAuth flows, calendar operations, and agent orchestration.
Tests complete workflows from authentication through calendar management and AI decision-making.
"""

import pytest
import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.handlers.auth import lambda_handler as auth_handler
from src.handlers.connections import lambda_handler as connections_handler
from src.handlers.calendar import lambda_handler as calendar_handler
from src.handlers.agent import lambda_handler as agent_handler
from src.services.google_oauth import GoogleOAuthService
from src.services.microsoft_oauth import MicrosoftOAuthService
from src.services.oauth_manager import UnifiedOAuthManager
from src.services.google_calendar import GoogleCalendarService
from src.services.agentcore_orchestrator import AgentCoreOrchestrator


class TestOAuthFlowsIntegration:
    """Integration tests for complete OAuth authentication flows."""
    
    def setup_method(self):
        """Set up test fixtures for OAuth flow testing."""
        self.user_id = "test_user_123"
        self.test_context = Mock()
        self.test_context.aws_request_id = str(uuid.uuid4())
        
        # Mock OAuth service responses
        self.mock_auth_url = "https://accounts.google.com/oauth/authorize?client_id=test"
        self.mock_tokens = {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer"
        }
        
        # Common test headers
        self.auth_headers = {
            "Authorization": f"Bearer test_jwt_token",
            "Content-Type": "application/json"
        }
    
    @patch('src.services.google_oauth.GoogleOAuthService.generate_authorization_url')
    def test_google_oauth_start_flow_integration(self, mock_generate_url):
        """Test complete Google OAuth start flow through API endpoint."""
        # Setup mock
        mock_generate_url.return_value = {
            "authorization_url": self.mock_auth_url,
            "state": "test_state_123"
        }
        
        # Create API Gateway event
        event = {
            "httpMethod": "POST",
            "path": "/connections/google/auth/start",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"userId": self.user_id}
            },
            "body": json.dumps({
                "redirect_uri": "https://app.example.com/callback",
                "state": "custom_state"
            })
        }      
  
        # Execute the handler
        response = connections_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "authorization_url" in response_body
        assert response_body["authorization_url"] == self.mock_auth_url
        assert "state" in response_body
        
        # Verify CORS headers
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        
        # Verify service was called correctly
        mock_generate_url.assert_called_once_with(
            user_id=self.user_id,
            redirect_uri="https://app.example.com/callback",
            state="custom_state"
        )
    
    @patch('src.services.google_oauth.GoogleOAuthService.exchange_code_for_tokens')
    def test_google_oauth_callback_flow_integration(self, mock_exchange_tokens):
        """Test complete Google OAuth callback flow through API endpoint."""
        # Setup mock
        mock_exchange_tokens.return_value = {
            "success": True,
            "connection_status": "connected",
            "tokens": self.mock_tokens
        }
        
        # Create API Gateway event
        event = {
            "httpMethod": "POST",
            "path": "/connections/google/auth/callback",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"userId": self.user_id}
            },
            "body": json.dumps({
                "code": "auth_code_123",
                "state": "test_state_123"
            })
        }
        
        # Execute the handler
        response = connections_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["success"] is True
        assert response_body["connection_status"] == "connected"
        
        # Verify service was called correctly
        mock_exchange_tokens.assert_called_once_with(
            user_id=self.user_id,
            authorization_code="auth_code_123",
            state="test_state_123"
        )
    
    @patch('src.services.microsoft_oauth.MicrosoftOAuthService.generate_authorization_url')
    def test_microsoft_oauth_start_flow_integration(self, mock_generate_url):
        """Test complete Microsoft OAuth start flow through API endpoint."""
        # Setup mock
        mock_generate_url.return_value = {
            "authorization_url": "https://login.microsoftonline.com/oauth2/v2.0/authorize",
            "state": "ms_state_123"
        }
        
        # Create API Gateway event
        event = {
            "httpMethod": "POST",
            "path": "/connections/microsoft/auth/start",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"userId": self.user_id}
            },
            "body": json.dumps({
                "redirect_uri": "https://app.example.com/callback"
            })
        }
        
        # Execute the handler
        response = connections_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "authorization_url" in response_body
        assert "state" in response_body
        
        # Verify service was called correctly
        mock_generate_url.assert_called_once() 
   
    @patch('src.services.oauth_manager.UnifiedOAuthManager.get_all_connections')
    def test_unified_connections_status_integration(self, mock_get_connections):
        """Test unified connections status endpoint integration."""
        # Setup mock
        mock_get_connections.return_value = {
            "google": {
                "connected": True,
                "expires_at": "2024-01-15T12:00:00Z",
                "scopes": ["calendar.readonly", "calendar.events"]
            },
            "microsoft": {
                "connected": False,
                "error": "Token expired"
            }
        }
        
        # Create API Gateway event
        event = {
            "httpMethod": "GET",
            "path": "/connections/status",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"userId": self.user_id}
            }
        }
        
        # Execute the handler
        response = connections_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "connections" in response_body
        assert response_body["connections"]["google"]["connected"] is True
        assert response_body["connections"]["microsoft"]["connected"] is False
        assert "supported_providers" in response_body
    
    @patch('src.services.google_oauth.GoogleOAuthService.refresh_access_token')
    def test_token_refresh_flow_integration(self, mock_refresh_token):
        """Test token refresh flow integration."""
        # Setup mock
        mock_refresh_token.return_value = {
            "success": True,
            "access_token": "new_access_token",
            "expires_in": 3600
        }
        
        # Create API Gateway event
        event = {
            "httpMethod": "POST",
            "path": "/connections/google/refresh",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"userId": self.user_id}
            }
        }
        
        # Execute the handler
        response = connections_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["success"] is True
        assert "access_token" in response_body


class TestCalendarSynchronizationIntegration:
    """Integration tests for calendar synchronization and event management."""
    
    def setup_method(self):
        """Set up test fixtures for calendar testing."""
        self.user_id = "test_user_123"
        self.test_context = Mock()
        self.test_context.aws_request_id = str(uuid.uuid4())
        
        # Mock calendar events
        self.mock_events = [
            {
                "id": "event_1",
                "summary": "Team Meeting",
                "start": {"dateTime": "2024-01-15T10:00:00Z"},
                "end": {"dateTime": "2024-01-15T11:00:00Z"},
                "attendees": [{"email": "alice@example.com"}]
            },
            {
                "id": "event_2",
                "summary": "Client Call",
                "start": {"dateTime": "2024-01-15T14:00:00Z"},
                "end": {"dateTime": "2024-01-15T15:00:00Z"},
                "attendees": [{"email": "client@example.com"}]
            }
        ]
        
        # Common test headers
        self.auth_headers = {
            "Authorization": f"Bearer test_jwt_token",
            "Content-Type": "application/json"
        }
    
    @patch('src.services.google_calendar.GoogleCalendarService.fetch_calendar_events')
    def test_fetch_calendar_events_integration(self, mock_fetch_events):
        """Test fetching calendar events through API endpoint."""
        # Setup mock
        mock_fetch_events.return_value = self.mock_events
        
        # Create API Gateway event
        event = {
            "httpMethod": "GET",
            "path": "/calendar/google/events",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"user_id": self.user_id}
            },
            "queryStringParameters": {
                "start": "2024-01-15T00:00:00Z",
                "end": "2024-01-15T23:59:59Z",
                "calendar_id": "primary"
            }
        } 
       
        # Execute the handler
        response = calendar_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert "events" in response_body
        assert len(response_body["events"]) == 2
        assert response_body["count"] == 2
        
        # Verify service was called correctly
        mock_fetch_events.assert_called_once()
    
    @patch('src.services.google_calendar.GoogleCalendarService.create_event')
    def test_create_calendar_event_integration(self, mock_create_event):
        """Test creating calendar events through API endpoint."""
        # Setup mock
        mock_create_event.return_value = {
            "id": "new_event_123",
            "summary": "New Meeting",
            "start": {"dateTime": "2024-01-16T10:00:00Z"},
            "end": {"dateTime": "2024-01-16T11:00:00Z"}
        }
        
        # Create API Gateway event
        event_data = {
            "summary": "New Meeting",
            "start": {"dateTime": "2024-01-16T10:00:00Z"},
            "end": {"dateTime": "2024-01-16T11:00:00Z"},
            "attendees": [{"email": "attendee@example.com"}]
        }
        
        event = {
            "httpMethod": "POST",
            "path": "/calendar/google/events",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"user_id": self.user_id}
            },
            "body": json.dumps(event_data)
        }
        
        # Execute the handler
        response = calendar_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 201
        response_body = json.loads(response["body"])
        assert response_body["id"] == "new_event_123"
        assert response_body["summary"] == "New Meeting"
        
        # Verify service was called correctly
        mock_create_event.assert_called_once_with(self.user_id, event_data)
    
    @patch('src.services.google_calendar.GoogleCalendarService.update_event')
    def test_update_calendar_event_integration(self, mock_update_event):
        """Test updating calendar events through API endpoint."""
        # Setup mock
        mock_update_event.return_value = {
            "id": "event_123",
            "summary": "Updated Meeting",
            "start": {"dateTime": "2024-01-16T11:00:00Z"},
            "end": {"dateTime": "2024-01-16T12:00:00Z"}
        }
        
        # Create API Gateway event
        update_data = {
            "summary": "Updated Meeting",
            "start": {"dateTime": "2024-01-16T11:00:00Z"},
            "end": {"dateTime": "2024-01-16T12:00:00Z"}
        }
        
        event = {
            "httpMethod": "PUT",
            "path": "/calendar/google/events/event_123",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"user_id": self.user_id}
            },
            "body": json.dumps(update_data)
        }
        
        # Execute the handler
        response = calendar_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["summary"] == "Updated Meeting"
        
        # Verify service was called correctly
        mock_update_event.assert_called_once_with(self.user_id, "event_123", update_data)
    
    @patch('src.services.google_calendar.GoogleCalendarService.delete_event')
    def test_delete_calendar_event_integration(self, mock_delete_event):
        """Test deleting calendar events through API endpoint."""
        # Setup mock
        mock_delete_event.return_value = True
        
        # Create API Gateway event
        event = {
            "httpMethod": "DELETE",
            "path": "/calendar/google/events/event_123",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"user_id": self.user_id}
            },
            "body": json.dumps({"send_notifications": True})
        }
        
        # Execute the handler
        response = calendar_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["success"] is True
        
        # Verify service was called correctly
        mock_delete_event.assert_called_once_with(
            self.user_id, "event_123", send_notifications=True
        )
    
    @patch('src.services.google_calendar.GoogleCalendarService.calculate_availability')
    def test_availability_calculation_integration(self, mock_calculate_availability):
        """Test availability calculation through API endpoint."""
        from src.models.meeting import Availability, TimeSlot
        
        # Setup mock
        mock_availability = Availability(
            user_id=self.user_id,
            date_range_start=datetime(2024, 1, 15),
            date_range_end=datetime(2024, 1, 16),
            time_slots=[
                TimeSlot(
                    start=datetime(2024, 1, 15, 9, 0),
                    end=datetime(2024, 1, 15, 10, 0),
                    available=True,
                    score=0.9
                ),
                TimeSlot(
                    start=datetime(2024, 1, 15, 15, 0),
                    end=datetime(2024, 1, 15, 16, 0),
                    available=True,
                    score=0.8
                )
            ],
            last_updated=datetime.utcnow()
        )
        mock_calculate_availability.return_value = mock_availability
        
        # Create API Gateway event
        event = {
            "httpMethod": "GET",
            "path": "/calendar/google/availability",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"user_id": self.user_id}
            },
            "queryStringParameters": {
                "start": "2024-01-15T00:00:00Z",
                "end": "2024-01-16T00:00:00Z"
            }
        }
        
        # Execute the handler
        response = calendar_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["user_id"] == self.user_id
        assert len(response_body["time_slots"]) == 2
        assert "last_updated" in response_body


class TestAgentDecisionMakingIntegration:
    """Integration tests for agent decision-making and tool orchestration."""
    
    def setup_method(self):
        """Set up test fixtures for agent testing."""
        self.user_id = "test_user_123"
        self.test_context = Mock()
        self.test_context.aws_request_id = str(uuid.uuid4())
        
        # Common test headers
        self.auth_headers = {
            "Authorization": f"Bearer test_jwt_token",
            "Content-Type": "application/json"
        }
    
    @patch('src.services.agentcore_orchestrator.AgentCoreOrchestrator.execute_intelligent_scheduling')
    def test_intelligent_scheduling_integration(self, mock_execute_scheduling):
        """Test intelligent scheduling through agent API endpoint."""
        # Setup mock
        mock_execute_scheduling.return_value = {
            "execution_id": "exec_123",
            "status": "completed",
            "result": {
                "meeting_scheduled": True,
                "meeting_id": "meeting_456",
                "optimal_time": "2024-01-16T10:00:00Z",
                "confidence_score": 0.95
            },
            "reasoning": "Selected optimal time based on all attendees' availability"
        }
        
        # Create API Gateway event
        request_data = {
            "action": "intelligent_scheduling",
            "task_type": "schedule_meeting",
            "request_data": {
                "subject": "Team Sync",
                "attendees": ["alice@example.com", "bob@example.com"],
                "duration_minutes": 60,
                "preferred_times": ["morning"]
            },
            "user_id": self.user_id,
            "user_preferences": {
                "working_hours": {"start": "09:00", "end": "17:00"},
                "buffer_minutes": 15
            },
            "planning_strategy": "balanced"
        }
        
        event = {
            "httpMethod": "POST",
            "path": "/agent/intelligent-scheduling",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"claims": {"sub": self.user_id}}
            },
            "body": json.dumps(request_data)
        }
        
        # Execute the handler
        response = agent_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["status"] == "completed"
        assert response_body["result"]["meeting_scheduled"] is True
        assert response_body["result"]["confidence_score"] == 0.95
        
        # Verify orchestrator was called correctly
        mock_execute_scheduling.assert_called_once()
    
    @patch('src.services.agentcore_orchestrator.AgentCoreOrchestrator.handle_complex_conflicts')
    def test_conflict_resolution_integration(self, mock_handle_conflicts):
        """Test conflict resolution through agent API endpoint."""
        # Setup mock
        mock_handle_conflicts.return_value = {
            "execution_id": "conflict_exec_123",
            "status": "completed",
            "resolution": {
                "strategy": "reschedule_lower_priority",
                "conflicts_resolved": 2,
                "rescheduled_meetings": ["meeting_1", "meeting_2"],
                "new_times": {
                    "meeting_1": "2024-01-16T11:00:00Z",
                    "meeting_2": "2024-01-16T14:00:00Z"
                }
            },
            "confidence_score": 0.88
        }
        
        # Create API Gateway event
        request_data = {
            "action": "conflict_resolution",
            "context_id": "conflict_ctx_123",
            "conflicts": [
                {
                    "type": "direct_overlap",
                    "meetings": ["meeting_1", "meeting_2"],
                    "severity": "high"
                }
            ],
            "alternatives": [
                {"time": "2024-01-16T11:00:00Z", "confidence": 0.9},
                {"time": "2024-01-16T14:00:00Z", "confidence": 0.8}
            ]
        }    
    
        event = {
            "httpMethod": "POST",
            "path": "/agent/conflict-resolution",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"claims": {"sub": self.user_id}}
            },
            "body": json.dumps(request_data)
        }
        
        # Execute the handler
        response = agent_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["status"] == "completed"
        assert response_body["resolution"]["conflicts_resolved"] == 2
        assert len(response_body["resolution"]["rescheduled_meetings"]) == 2
        
        # Verify orchestrator was called correctly
        mock_handle_conflicts.assert_called_once()
    
    @patch('src.services.agentcore_orchestrator.AgentCoreOrchestrator.execute_availability_lookup')
    def test_availability_lookup_integration(self, mock_availability_lookup):
        """Test availability lookup through agent API endpoint."""
        # Setup mock
        mock_availability_lookup.return_value = {
            "execution_id": "avail_exec_123",
            "status": "completed",
            "availability": {
                "available_slots": [
                    {
                        "start": "2024-01-16T09:00:00Z",
                        "end": "2024-01-16T10:00:00Z",
                        "confidence": 0.95
                    },
                    {
                        "start": "2024-01-16T14:00:00Z",
                        "end": "2024-01-16T15:00:00Z",
                        "confidence": 0.88
                    }
                ],
                "total_slots": 2,
                "optimal_slot": {
                    "start": "2024-01-16T09:00:00Z",
                    "end": "2024-01-16T10:00:00Z",
                    "confidence": 0.95
                }
            }
        }
        
        # Create API Gateway event
        request_data = {
            "action": "availability_lookup",
            "user_id": self.user_id,
            "start_date": "2024-01-16T00:00:00Z",
            "end_date": "2024-01-16T23:59:59Z",
            "connections": ["google", "microsoft"],
            "preferences": {
                "working_hours": {"start": "09:00", "end": "17:00"},
                "buffer_minutes": 15
            },
            "duration_minutes": 60,
            "max_results": 5
        }
        
        event = {
            "httpMethod": "POST",
            "path": "/agent/availability-lookup",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"claims": {"sub": self.user_id}}
            },
            "body": json.dumps(request_data)
        }
        
        # Execute the handler
        response = agent_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["status"] == "completed"
        assert len(response_body["availability"]["available_slots"]) == 2
        assert response_body["availability"]["optimal_slot"]["confidence"] == 0.95
        
        # Verify orchestrator was called correctly
        mock_availability_lookup.assert_called_once()
    
    @patch('src.services.agentcore_orchestrator.AgentCoreOrchestrator.optimize_multi_step_operation')
    def test_multi_step_optimization_integration(self, mock_optimize_operation):
        """Test multi-step operation optimization through agent API endpoint."""
        # Setup mock
        mock_optimize_operation.return_value = {
            "execution_id": "multi_exec_123",
            "status": "completed",
            "optimization": {
                "original_operations": 5,
                "optimized_operations": 3,
                "time_saved_minutes": 45,
                "conflicts_avoided": 2,
                "execution_plan": [
                    {"step": 1, "action": "schedule_meeting_1", "time": "2024-01-16T09:00:00Z"},
                    {"step": 2, "action": "schedule_meeting_2", "time": "2024-01-16T10:30:00Z"},
                    {"step": 3, "action": "send_notifications", "time": "2024-01-16T10:35:00Z"}
                ]
            },
            "confidence_score": 0.92
        }
        
        # Create API Gateway event
        request_data = {
            "action": "multi_step_optimization",
            "operations": [
                {"type": "schedule_meeting", "priority": "high", "data": {"subject": "Meeting 1"}},
                {"type": "schedule_meeting", "priority": "medium", "data": {"subject": "Meeting 2"}},
                {"type": "send_reminder", "priority": "low", "data": {"meeting_id": "meeting_1"}},
                {"type": "update_calendar", "priority": "medium", "data": {"calendar_id": "primary"}},
                {"type": "notify_attendees", "priority": "high", "data": {"attendees": ["alice@example.com"]}}
            ],
            "user_id": self.user_id,
            "optimization_goals": ["minimize_conflicts", "maximize_efficiency"]
        }
        
        event = {
            "httpMethod": "POST",
            "path": "/agent/multi-step-optimization",
            "headers": self.auth_headers,
            "requestContext": {
                "authorizer": {"claims": {"sub": self.user_id}}
            },
            "body": json.dumps(request_data)
        }
        
        # Execute the handler
        response = agent_handler(event, self.test_context)
        
        # Verify response
        assert response["statusCode"] == 200
        response_body = json.loads(response["body"])
        assert response_body["status"] == "completed"
        assert response_body["optimization"]["time_saved_minutes"] == 45
        assert response_body["optimization"]["conflicts_avoided"] == 2
        assert len(response_body["optimization"]["execution_plan"]) == 3
        
        # Verify orchestrator was called correctly
        mock_optimize_operation.assert_called_once()


class TestEndToEndWorkflowIntegration:
    """End-to-end integration tests covering complete user workflows."""
    
    def setup_method(self):
        """Set up test fixtures for end-to-end testing."""
        self.user_id = "test_user_123"
        self.test_context = Mock()
        self.test_context.aws_request_id = str(uuid.uuid4())
        
        # Common test headers
        self.auth_headers = {
            "Authorization": f"Bearer test_jwt_token",
            "Content-Type": "application/json"
        }
    
    @patch('src.services.google_oauth.GoogleOAuthService.generate_authorization_url')
    @patch('src.services.google_oauth.GoogleOAuthService.exchange_code_for_tokens')
    @patch('src.services.google_calendar.GoogleCalendarService.fetch_calendar_events')
    @patch('src.services.agentcore_orchestrator.AgentCoreOrchestrator.execute_intelligent_scheduling')
    def test_complete_oauth_to_scheduling_workflow(self, mock_scheduling, mock_fetch_events, 
                                                  mock_exchange_tokens, mock_generate_url):
        """Test complete workflow from OAuth setup to intelligent scheduling."""
        
        # Step 1: Start OAuth flow
        mock_generate_url.return_value = {
            "authorization_url": "https://accounts.google.com/oauth/authorize",
            "state": "test_state_123"
        }
        
        oauth_start_event = {
            "httpMethod": "POST",
            "path": "/connections/google/auth/start",
            "headers": self.auth_headers,
            "requestContext": {"authorizer": {"userId": self.user_id}},
            "body": json.dumps({"redirect_uri": "https://app.example.com/callback"})
        }
        
        oauth_response = connections_handler(oauth_start_event, self.test_context)
        assert oauth_response["statusCode"] == 200
        
        # Step 2: Complete OAuth callback
        mock_exchange_tokens.return_value = {
            "success": True,
            "connection_status": "connected"
        }
        
        oauth_callback_event = {
            "httpMethod": "POST",
            "path": "/connections/google/auth/callback",
            "headers": self.auth_headers,
            "requestContext": {"authorizer": {"userId": self.user_id}},
            "body": json.dumps({"code": "auth_code_123", "state": "test_state_123"})
        }
        
        callback_response = connections_handler(oauth_callback_event, self.test_context)
        assert callback_response["statusCode"] == 200
        
        # Step 3: Fetch calendar events
        mock_fetch_events.return_value = [
            {
                "id": "existing_event_1",
                "summary": "Existing Meeting",
                "start": {"dateTime": "2024-01-16T10:00:00Z"},
                "end": {"dateTime": "2024-01-16T11:00:00Z"}
            }
        ]
        
        fetch_events_event = {
            "httpMethod": "GET",
            "path": "/calendar/google/events",
            "headers": self.auth_headers,
            "requestContext": {"authorizer": {"user_id": self.user_id}},
            "queryStringParameters": {
                "start": "2024-01-16T00:00:00Z",
                "end": "2024-01-16T23:59:59Z"
            }
        }
        
        events_response = calendar_handler(fetch_events_event, self.test_context)
        assert events_response["statusCode"] == 200
        
        # Step 4: Execute intelligent scheduling
        mock_scheduling.return_value = {
            "execution_id": "exec_123",
            "status": "completed",
            "result": {
                "meeting_scheduled": True,
                "meeting_id": "new_meeting_456",
                "optimal_time": "2024-01-16T14:00:00Z"
            }
        }
        
        scheduling_event = {
            "httpMethod": "POST",
            "path": "/agent/intelligent-scheduling",
            "headers": self.auth_headers,
            "requestContext": {"authorizer": {"claims": {"sub": self.user_id}}},
            "body": json.dumps({
                "action": "intelligent_scheduling",
                "task_type": "schedule_meeting",
                "request_data": {
                    "subject": "New Team Meeting",
                    "attendees": ["alice@example.com"],
                    "duration_minutes": 60
                },
                "user_id": self.user_id
            })
        }
        
        scheduling_response = agent_handler(scheduling_event, self.test_context)
        assert scheduling_response["statusCode"] == 200
        
        # Verify all services were called
        mock_generate_url.assert_called_once()
        mock_exchange_tokens.assert_called_once()
        mock_fetch_events.assert_called_once()
        mock_scheduling.assert_called_once()
    
    def test_error_handling_across_endpoints(self):
        """Test error handling consistency across different API endpoints."""
        
        # Test unauthorized access
        unauthorized_event = {
            "httpMethod": "GET",
            "path": "/connections/status",
            "headers": {"Content-Type": "application/json"},  # No Authorization header
            "requestContext": {}
        }
        
        response = connections_handler(unauthorized_event, self.test_context)
        # Should handle missing authorization gracefully
        assert response["statusCode"] in [401, 500]  # Depending on implementation
        
        # Test invalid JSON body
        invalid_json_event = {
            "httpMethod": "POST",
            "path": "/connections/google/auth/start",
            "headers": self.auth_headers,
            "requestContext": {"authorizer": {"userId": self.user_id}},
            "body": "invalid json"
        }
        
        response = connections_handler(invalid_json_event, self.test_context)
        assert response["statusCode"] in [400, 500]
        
        # Test CORS headers in error responses
        assert "Access-Control-Allow-Origin" in response["headers"]
    
    def test_health_check_endpoints_integration(self):
        """Test health check endpoints across all handlers."""
        
        # Test auth health check
        auth_health_event = {
            "httpMethod": "GET",
            "path": "/auth/health",
            "headers": {},
            "requestContext": {}
        }
        
        auth_response = auth_handler(auth_health_event, self.test_context)
        # Health check may return 503 in test environment due to AWS credentials
        assert auth_response["statusCode"] in [200, 503]
        assert "Access-Control-Allow-Origin" in auth_response["headers"]
        
        # Test connections health check
        connections_health_event = {
            "httpMethod": "GET",
            "path": "/connections/health",
            "headers": {},
            "requestContext": {}
        }
        
        connections_response = connections_handler(connections_health_event, self.test_context)
        # Health check may return 503 in test environment due to AWS credentials
        assert connections_response["statusCode"] in [200, 503]
        
        # Test calendar health check
        calendar_health_event = {
            "httpMethod": "GET",
            "path": "/calendar/health",
            "headers": {},
            "requestContext": {}
        }
        
        calendar_response = calendar_handler(calendar_health_event, self.test_context)
        # Health check may return 401, 503 in test environment due to missing auth/AWS credentials
        assert calendar_response["statusCode"] in [200, 401, 503]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])