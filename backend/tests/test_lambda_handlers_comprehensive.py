"""
Comprehensive unit tests for Lambda handlers.
Tests agent handler, calendar handler, and other Lambda functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta

# Test imports
from src.handlers.agent import lambda_handler as agent_handler
from src.handlers.calendar import lambda_handler as calendar_handler
from src.handlers.auth import lambda_handler as auth_handler
from src.handlers.preferences import lambda_handler as preferences_handler


class TestAgentLambdaHandler:
    """Comprehensive tests for agent Lambda handler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = Mock()
        self.context.aws_request_id = 'test-request-123'
        self.context.function_name = 'agent-handler'
        self.context.memory_limit_in_mb = 512
        
    def test_schedule_meeting_request(self):
        """Test schedule meeting request handling."""
        event = {
            'httpMethod': 'POST',
            'path': '/agent/schedule',
            'body': json.dumps({
                'action': 'schedule_meeting',
                'attendees': ['attendee1@example.com', 'attendee2@example.com'],
                'duration': 60,
                'subject': 'Project Kickoff Meeting',
                'preferred_times': ['2024-01-15T10:00:00Z', '2024-01-15T14:00:00Z']
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            },
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        with patch('src.handlers.agent.handle_schedule_meeting') as mock_handle:
            mock_handle.return_value = {
                'action': 'schedule_meeting',
                'status': 'completed',
                'meeting_id': 'meeting-456',
                'scheduled_time': '2024-01-15T10:00:00Z'
            }
            
            response = agent_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['action'] == 'schedule_meeting'
            assert body['status'] == 'completed'
            assert 'meeting_id' in body
            
            # Verify headers
            assert 'X-Correlation-ID' in response['headers']
            assert 'X-Agent-Run-ID' in response['headers']
    
    def test_resolve_conflict_request(self):
        """Test conflict resolution request handling."""
        event = {
            'httpMethod': 'POST',
            'path': '/agent/resolve-conflict',
            'body': json.dumps({
                'action': 'resolve_conflict',
                'conflict_id': 'conflict-789',
                'strategy': 'reschedule_lower_priority',
                'meetings': [
                    {'id': 'meeting-1', 'priority': 0.9},
                    {'id': 'meeting-2', 'priority': 0.3}
                ]
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        with patch('src.handlers.agent.handle_resolve_conflict') as mock_handle:
            mock_handle.return_value = {
                'action': 'resolve_conflict',
                'status': 'completed',
                'conflict_id': 'conflict-789',
                'resolution': 'reschedule_lower_priority',
                'kept_meeting': 'meeting-1',
                'rescheduled_meeting': 'meeting-2'
            }
            
            response = agent_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['action'] == 'resolve_conflict'
            assert body['kept_meeting'] == 'meeting-1'
            assert body['rescheduled_meeting'] == 'meeting-2'
    
    def test_daily_learning_request(self):
        """Test daily learning request handling."""
        event = {
            'httpMethod': 'POST',
            'path': '/agent/learn',
            'body': json.dumps({
                'action': 'daily_learning',
                'timestamp': '2024-01-15T00:00:00Z',
                'analyze_period_days': 7
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        with patch('src.handlers.agent.handle_daily_learning') as mock_handle:
            mock_handle.return_value = {
                'action': 'daily_learning',
                'status': 'completed',
                'insights_generated': 5,
                'preferences_updated': 3,
                'patterns_discovered': ['prefers_morning_meetings', 'avoids_friday_afternoons']
            }
            
            response = agent_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['insights_generated'] == 5
            assert body['preferences_updated'] == 3
            assert len(body['patterns_discovered']) == 2
    
    def test_intelligent_scheduling_request(self):
        """Test intelligent scheduling request handling."""
        event = {
            'httpMethod': 'POST',
            'path': '/agent/intelligent-schedule',
            'body': json.dumps({
                'task_type': 'schedule_meeting',
                'request_data': {
                    'title': 'AI-Optimized Meeting',
                    'duration': 30,
                    'attendees': ['ai@example.com']
                },
                'user_id': 'user-123',
                'user_preferences': {
                    'working_hours': {'start': '09:00', 'end': '17:00'},
                    'buffer_minutes': 15
                },
                'planning_strategy': 'balanced'
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        with patch('src.handlers.agent.handle_intelligent_scheduling') as mock_handle:
            mock_handle.return_value = {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'execution_id': 'exec-456',
                    'status': 'completed',
                    'optimal_time': '2024-01-15T10:00:00Z',
                    'confidence_score': 0.92,
                    'alternatives': [
                        {'time': '2024-01-15T14:00:00Z', 'score': 0.87},
                        {'time': '2024-01-15T15:30:00Z', 'score': 0.81}
                    ]
                })
            }
            
            response = agent_handler(event, self.context)
            
            assert response['statusCode'] == 200
    
    def test_error_handling(self):
        """Test error handling in agent handler."""
        event = {
            'httpMethod': 'POST',
            'path': '/agent/schedule',
            'body': json.dumps({
                'action': 'invalid_action'
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        response = agent_handler(event, self.context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'Unknown action' in body['error']
    
    def test_missing_user_context(self):
        """Test handling of missing user context."""
        event = {
            'httpMethod': 'POST',
            'path': '/agent/schedule',
            'body': json.dumps({
                'action': 'schedule_meeting'
            }),
            'requestContext': {}  # Missing authorizer
        }
        
        # Should still process but with anonymous user
        with patch('src.handlers.agent.handle_schedule_meeting') as mock_handle:
            mock_handle.return_value = {
                'action': 'schedule_meeting',
                'status': 'completed'
            }
            
            response = agent_handler(event, self.context)
            
            assert response['statusCode'] == 200


class TestCalendarLambdaHandler:
    """Comprehensive tests for calendar Lambda handler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = Mock()
        self.context.aws_request_id = 'test-request-456'
        
    def test_fetch_google_calendar_events(self):
        """Test fetching Google Calendar events."""
        event = {
            'httpMethod': 'GET',
            'path': '/calendar/google/events',
            'queryStringParameters': {
                'start': '2024-01-15T00:00:00Z',
                'end': '2024-01-22T23:59:59Z',
                'calendar_id': 'primary'
            },
            'requestContext': {
                'authorizer': {
                    'user_id': 'user-123'
                }
            }
        }
        
        mock_events = [
            {
                'id': 'event-1',
                'title': 'Meeting 1',
                'start': '2024-01-15T10:00:00Z',
                'end': '2024-01-15T11:00:00Z'
            },
            {
                'id': 'event-2',
                'title': 'Meeting 2',
                'start': '2024-01-16T14:00:00Z',
                'end': '2024-01-16T15:00:00Z'
            }
        ]
        
        with patch('src.handlers.calendar.GoogleCalendarService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.fetch_calendar_events.return_value = mock_events
            
            response = calendar_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['count'] == 2
            assert len(body['events']) == 2
            assert body['events'][0]['id'] == 'event-1'
    
    def test_create_google_calendar_event(self):
        """Test creating Google Calendar event."""
        event = {
            'httpMethod': 'POST',
            'path': '/calendar/google/events',
            'body': json.dumps({
                'title': 'New Meeting',
                'start': '2024-01-15T10:00:00Z',
                'end': '2024-01-15T11:00:00Z',
                'attendees': ['attendee@example.com'],
                'description': 'Test meeting description'
            }),
            'requestContext': {
                'authorizer': {
                    'user_id': 'user-123'
                }
            }
        }
        
        mock_created_event = {
            'id': 'new-event-123',
            'title': 'New Meeting',
            'start': '2024-01-15T10:00:00Z',
            'end': '2024-01-15T11:00:00Z',
            'status': 'confirmed'
        }
        
        with patch('src.handlers.calendar.GoogleCalendarService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.create_event.return_value = mock_created_event
            
            response = calendar_handler(event, self.context)
            
            assert response['statusCode'] == 201
            body = json.loads(response['body'])
            assert body['id'] == 'new-event-123'
            assert body['title'] == 'New Meeting'
    
    def test_update_google_calendar_event(self):
        """Test updating Google Calendar event."""
        event = {
            'httpMethod': 'PUT',
            'path': '/calendar/google/events/event-123',
            'body': json.dumps({
                'title': 'Updated Meeting Title',
                'start': '2024-01-15T11:00:00Z',
                'end': '2024-01-15T12:00:00Z'
            }),
            'requestContext': {
                'authorizer': {
                    'user_id': 'user-123'
                }
            }
        }
        
        mock_updated_event = {
            'id': 'event-123',
            'title': 'Updated Meeting Title',
            'start': '2024-01-15T11:00:00Z',
            'end': '2024-01-15T12:00:00Z'
        }
        
        with patch('src.handlers.calendar.GoogleCalendarService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.update_event.return_value = mock_updated_event
            
            response = calendar_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['title'] == 'Updated Meeting Title'
    
    def test_delete_google_calendar_event(self):
        """Test deleting Google Calendar event."""
        event = {
            'httpMethod': 'DELETE',
            'path': '/calendar/google/events/event-123',
            'body': json.dumps({
                'send_notifications': True
            }),
            'requestContext': {
                'authorizer': {
                    'user_id': 'user-123'
                }
            }
        }
        
        with patch('src.handlers.calendar.GoogleCalendarService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.delete_event.return_value = True
            
            response = calendar_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['success'] is True
    
    def test_calculate_availability(self):
        """Test availability calculation endpoint."""
        event = {
            'httpMethod': 'GET',
            'path': '/calendar/google/availability',
            'queryStringParameters': {
                'start': '2024-01-15T00:00:00Z',
                'end': '2024-01-22T23:59:59Z',
                'working_hours': json.dumps({
                    'start': '09:00',
                    'end': '17:00',
                    'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
                })
            },
            'requestContext': {
                'authorizer': {
                    'user_id': 'user-123'
                }
            }
        }
        
        mock_availability = Mock()
        mock_availability.dict.return_value = {
            'user_id': 'user-123',
            'date_range_start': '2024-01-15T00:00:00Z',
            'date_range_end': '2024-01-22T23:59:59Z',
            'time_slots': [
                {
                    'start': '2024-01-15T10:00:00Z',
                    'end': '2024-01-15T10:30:00Z',
                    'available': True,
                    'score': 0.9
                }
            ]
        }
        
        with patch('src.handlers.calendar.GoogleCalendarService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.calculate_availability.return_value = mock_availability
            
            response = calendar_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['user_id'] == 'user-123'
            assert len(body['time_slots']) == 1
    
    def test_unauthorized_request(self):
        """Test handling of unauthorized requests."""
        event = {
            'httpMethod': 'GET',
            'path': '/calendar/google/events',
            'requestContext': {}  # Missing user_id
        }
        
        response = calendar_handler(event, self.context)
        
        assert response['statusCode'] == 401
        body = json.loads(response['body'])
        assert body['error'] == 'Unauthorized'
    
    def test_health_check_endpoint(self):
        """Test calendar health check endpoint."""
        event = {
            'httpMethod': 'GET',
            'path': '/calendar/health',
            'requestContext': {
                'authorizer': {
                    'user_id': 'user-123'
                }
            }
        }
        
        with patch('src.handlers.calendar.handle_health_check') as mock_health:
            mock_health.return_value = {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'status': 'healthy',
                    'service': 'calendar',
                    'timestamp': '2024-01-15T10:00:00Z'
                })
            }
            
            response = calendar_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['status'] == 'healthy'
            assert body['service'] == 'calendar'


class TestAuthLambdaHandler:
    """Comprehensive tests for auth Lambda handler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = Mock()
        self.context.aws_request_id = 'test-request-789'
    
    def test_google_oauth_authorization_url(self):
        """Test Google OAuth authorization URL generation."""
        event = {
            'httpMethod': 'POST',
            'path': '/auth/google/authorize',
            'body': json.dumps({
                'redirect_uri': 'https://example.com/callback'
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        mock_auth_result = {
            'authorization_url': 'https://accounts.google.com/oauth2/auth?...',
            'state': 'state-123',
            'expires_at': '2024-01-15T10:15:00Z'
        }
        
        with patch('src.handlers.auth.GoogleOAuthService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.generate_authorization_url.return_value = mock_auth_result
            
            response = auth_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert 'authorization_url' in body
            assert 'state' in body
    
    def test_google_oauth_token_exchange(self):
        """Test Google OAuth token exchange."""
        event = {
            'httpMethod': 'POST',
            'path': '/auth/google/callback',
            'body': json.dumps({
                'authorization_code': 'auth-code-123',
                'state': 'state-123'
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        mock_token_result = {
            'connection_id': 'user-123#google',
            'provider': 'google',
            'status': 'active',
            'profile': {
                'email': 'user@example.com',
                'name': 'Test User'
            },
            'scopes': ['calendar', 'gmail']
        }
        
        with patch('src.handlers.auth.GoogleOAuthService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.exchange_code_for_tokens.return_value = mock_token_result
            
            response = auth_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['provider'] == 'google'
            assert body['status'] == 'active'
    
    def test_token_refresh(self):
        """Test token refresh endpoint."""
        event = {
            'httpMethod': 'POST',
            'path': '/auth/refresh',
            'body': json.dumps({
                'provider': 'google'
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        mock_refresh_result = {
            'connection_id': 'user-123#google',
            'status': 'active',
            'expires_at': '2024-01-15T11:00:00Z',
            'last_refresh': '2024-01-15T10:00:00Z'
        }
        
        with patch('src.handlers.auth.GoogleOAuthService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.refresh_access_token.return_value = mock_refresh_result
            
            response = auth_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['status'] == 'active'
            assert 'expires_at' in body


class TestPreferencesLambdaHandler:
    """Comprehensive tests for preferences Lambda handler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = Mock()
        self.context.aws_request_id = 'test-request-101'
    
    def test_get_user_preferences(self):
        """Test retrieving user preferences."""
        event = {
            'httpMethod': 'GET',
            'path': '/preferences',
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        mock_preferences = {
            'user_id': 'user-123',
            'working_hours': {
                'monday': {'start': '09:00', 'end': '17:00'},
                'tuesday': {'start': '09:00', 'end': '17:00'}
            },
            'buffer_minutes': 15,
            'vip_contacts': ['boss@company.com'],
            'meeting_types': {
                'standup': {'duration': 15, 'priority': 'medium'}
            }
        }
        
        with patch('src.handlers.preferences.PreferenceManagementTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool_class.return_value = mock_tool
            mock_tool.retrieve_preferences.return_value = mock_preferences
            
            response = preferences_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['user_id'] == 'user-123'
            assert body['buffer_minutes'] == 15
    
    def test_update_user_preferences(self):
        """Test updating user preferences."""
        event = {
            'httpMethod': 'PUT',
            'path': '/preferences',
            'body': json.dumps({
                'working_hours': {
                    'monday': {'start': '08:00', 'end': '16:00'}
                },
                'buffer_minutes': 20,
                'vip_contacts': ['boss@company.com', 'client@external.com']
            }),
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123'
                    }
                }
            }
        }
        
        mock_updated_preferences = {
            'user_id': 'user-123',
            'working_hours': {
                'monday': {'start': '08:00', 'end': '16:00'}
            },
            'buffer_minutes': 20,
            'vip_contacts': ['boss@company.com', 'client@external.com'],
            'last_updated': '2024-01-15T10:00:00Z'
        }
        
        with patch('src.handlers.preferences.PreferenceManagementTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool_class.return_value = mock_tool
            mock_tool.update_preferences.return_value = mock_updated_preferences
            
            response = preferences_handler(event, self.context)
            
            assert response['statusCode'] == 200
            body = json.loads(response['body'])
            assert body['buffer_minutes'] == 20
            assert len(body['vip_contacts']) == 2


if __name__ == '__main__':
    pytest.main([__file__])