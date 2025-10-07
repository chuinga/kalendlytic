"""
Comprehensive tests for token refresh and error handling functionality.
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# Mock AWS services for testing
class MockDynamoDBTable:
    def __init__(self):
        self.items = {}
    
    def put_item(self, Item):
        key = Item.get('pk', str(len(self.items)))
        self.items[key] = Item
    
    def get_item(self, Key):
        key = Key.get('pk')
        if key in self.items:
            return {'Item': self.items[key]}
        return {}
    
    def scan(self, **kwargs):
        return {'Items': list(self.items.values()), 'Count': len(self.items)}
    
    def query(self, **kwargs):
        return {'Items': [], 'Count': 0}
    
    def update_item(self, **kwargs):
        pass
    
    def delete_item(self, **kwargs):
        pass

# Import the services we're testing
try:
    from backend.src.services.token_refresh_service import (
        TokenRefreshService, TokenRefreshStatus, TokenErrorType, RefreshAttempt
    )
    from backend.src.services.token_monitoring import TokenMonitoringService, AlertType, AlertSeverity
    from backend.src.utils.token_errors import (
        ExpiredRefreshTokenError, InvalidTokenError, RateLimitExceededError,
        NetworkError, TokenErrorContext, TokenErrorHandler
    )
except ImportError as e:
    # Create mock classes if imports fail
    class TokenRefreshService:
        pass
    class TokenMonitoringService:
        pass
    class TokenRefreshStatus:
        SUCCESS = "success"
        FAILED_RETRYABLE = "failed_retryable"
        EXPIRED_REFRESH_TOKEN = "expired_refresh_token"
        RATE_LIMITED = "rate_limited"
    class TokenErrorType:
        EXPIRED_REFRESH_TOKEN = "expired_refresh_token"
    class ExpiredRefreshTokenError(Exception):
        pass
    class NetworkError(Exception):
        pass

@pytest.fixture
def mock_aws_services():
    """Set up mocked AWS services."""
    return {
        'connections_table': MockDynamoDBTable(),
        'metrics_table': MockDynamoDBTable(),
        'alerts_table': MockDynamoDBTable(),
        'secrets_client': MagicMock()
    }

@pytest.fixture
def sample_connection():
    """Sample connection data for testing."""
    return {
        'pk': 'user123#google',
        'user_id': 'user123',
        'provider': 'google',
        'access_token_encrypted': 'encrypted_access_token',
        'refresh_token_encrypted': 'encrypted_refresh_token',
        'expires_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat(),
        'status': 'active',
        'scopes': ['calendar', 'email'],
        'created_at': datetime.utcnow().isoformat(),
        'last_refresh': datetime.utcnow().isoformat()
    }

class TestTokenRefreshService:
    """Test cases for TokenRefreshService."""
    
    @pytest.mark.asyncio
    async def test_successful_token_refresh(self, mock_aws_services, sample_connection):
        """Test successful token refresh with exponential backoff."""
        # Setup
        connections_table = mock_aws_services['connections_table']
        connections_table.put_item(Item=sample_connection)
        
        service = TokenRefreshService()
        
        # Mock successful OAuth refresh
        with patch.object(service.oauth_manager, 'refresh_access_token') as mock_refresh:
            mock_refresh.return_value = {
                'connection_id': 'user123#google',
                'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                'status': 'active'
            }
            
            # Execute
            result = await service.refresh_token_with_backoff('user123', 'google')
            
            # Verify
            assert result['success'] is True
            assert result['status'] == TokenRefreshStatus.SUCCESS
            assert result['attempt_number'] == 1
            assert 'refresh_time' in result
            
            # Verify metrics were recorded
            metrics_response = mock_aws_services['metrics_table'].scan()
            assert len(metrics_response['Items']) > 0
    
    @pytest.mark.asyncio
    async def test_token_refresh_with_retries(self, mock_aws_services, sample_connection):
        """Test token refresh with retries on transient errors."""
        # Setup
        connections_table = mock_aws_services['connections_table']
        connections_table.put_item(Item=sample_connection)
        
        service = TokenRefreshService()
        
        # Mock network error followed by success
        with patch.object(service.oauth_manager, 'refresh_access_token') as mock_refresh:
            mock_refresh.side_effect = [
                NetworkError("Connection timeout"),
                NetworkError("Connection timeout"),
                {
                    'connection_id': 'user123#google',
                    'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                    'status': 'active'
                }
            ]
            
            # Execute
            result = await service.refresh_token_with_backoff('user123', 'google')
            
            # Verify
            assert result['success'] is True
            assert result['status'] == TokenRefreshStatus.SUCCESS
            assert result['attempt_number'] == 3  # Third attempt succeeded
            
            # Verify retry attempts were recorded
            metrics_response = mock_aws_services['metrics_table'].scan()
            refresh_attempts = [item for item in metrics_response['Items'] 
                             if 'refresh_attempts#' in item['pk']]
            assert len(refresh_attempts) == 3  # All attempts recorded
    
    @pytest.mark.asyncio
    async def test_permanent_error_no_retry(self, mock_aws_services, sample_connection):
        """Test that permanent errors don't trigger retries."""
        # Setup
        connections_table = mock_aws_services['connections_table']
        connections_table.put_item(Item=sample_connection)
        
        service = TokenRefreshService()
        
        # Mock expired refresh token error
        with patch.object(service.oauth_manager, 'refresh_access_token') as mock_refresh:
            mock_refresh.side_effect = ExpiredRefreshTokenError()
            
            # Execute
            result = await service.refresh_token_with_backoff('user123', 'google')
            
            # Verify
            assert result['success'] is False
            assert result['status'] == TokenRefreshStatus.EXPIRED_REFRESH_TOKEN
            assert result['attempt_number'] == 1  # No retries
            assert result['requires_reauth'] is True
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_aws_services, sample_connection):
        """Test rate limiting functionality."""
        # Setup
        connections_table = mock_aws_services['connections_table']
        connections_table.put_item(Item=sample_connection)
        
        service = TokenRefreshService()
        service.max_refresh_attempts_per_hour = 2  # Lower limit for testing
        
        # Create multiple refresh attempts to trigger rate limit
        current_time = datetime.utcnow()
        for i in range(3):
            attempt = RefreshAttempt(
                timestamp=(current_time - timedelta(minutes=i*10)).isoformat(),
                attempt_number=1,
                status=TokenRefreshStatus.SUCCESS,
                error_type=None,
                error_message=None,
                backoff_delay=0,
                correlation_id=f"test_corr_{i}"
            )
            service._record_refresh_attempt('user123', 'google', attempt)
        
        # Execute
        result = await service.refresh_token_with_backoff('user123', 'google')
        
        # Verify
        assert result['success'] is False
        assert result['status'] == TokenRefreshStatus.RATE_LIMITED
        assert 'retry_after' in result
    
    @pytest.mark.asyncio
    async def test_backoff_calculation(self, mock_aws_services):
        """Test exponential backoff calculation."""
        service = TokenRefreshService()
        
        # Test backoff delays
        delay_0 = service._calculate_backoff_delay(0)
        delay_1 = service._calculate_backoff_delay(1)
        delay_2 = service._calculate_backoff_delay(2)
        
        # Verify exponential increase
        assert delay_1 > delay_0
        assert delay_2 > delay_1
        
        # Test maximum delay cap
        delay_large = service._calculate_backoff_delay(10)
        assert delay_large <= service.max_delay
    
    @pytest.mark.asyncio
    async def test_bulk_refresh_tokens(self, mock_aws_services):
        """Test bulk token refresh functionality."""
        # Setup multiple connections
        connections_table = mock_aws_services['connections_table']
        
        # Create connections with different expiry times
        for i in range(3):
            connection = {
                'pk': f'user{i}#google',
                'user_id': f'user{i}',
                'provider': 'google',
                'access_token_encrypted': f'encrypted_token_{i}',
                'refresh_token_encrypted': f'encrypted_refresh_{i}',
                'expires_at': (datetime.utcnow() - timedelta(minutes=30)).isoformat(),  # Expired
                'status': 'active'
            }
            connections_table.put_item(Item=connection)
        
        service = TokenRefreshService()
        
        # Mock successful refreshes
        with patch.object(service, 'refresh_token_with_backoff') as mock_refresh:
            mock_refresh.return_value = {'success': True}
            
            # Execute
            result = await service.bulk_refresh_tokens('google')
            
            # Verify
            assert result['total_connections'] == 3
            assert result['successful_refreshes'] == 3
            assert result['failed_refreshes'] == 0

class TestTokenMonitoringService:
    """Test cases for TokenMonitoringService."""
    
    @pytest.mark.asyncio
    async def test_collect_metrics(self, mock_aws_services):
        """Test metrics collection functionality."""
        # Setup test data
        connections_table = mock_aws_services['connections_table']
        
        # Create test connections
        for i in range(5):
            connection = {
                'pk': f'user{i}#google',
                'user_id': f'user{i}',
                'provider': 'google',
                'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                'status': 'active'
            }
            connections_table.put_item(Item=connection)
        
        service = TokenMonitoringService()
        
        # Execute
        metrics = await service.collect_metrics('google')
        
        # Verify
        assert len(metrics) == 1
        google_metrics = metrics[0]
        assert google_metrics.provider == 'google'
        assert google_metrics.total_users == 5
        assert google_metrics.active_connections == 5
        assert google_metrics.expired_tokens == 0
    
    @pytest.mark.asyncio
    async def test_alert_generation(self, mock_aws_services):
        """Test alert generation based on metrics."""
        service = TokenMonitoringService()
        
        # Create metrics that should trigger alerts
        from backend.src.services.token_monitoring import MonitoringMetrics
        
        bad_metrics = MonitoringMetrics(
            timestamp=datetime.utcnow().isoformat(),
            provider='google',
            total_users=100,
            active_connections=80,
            expired_tokens=30,  # High number of expired tokens
            failed_refreshes_24h=50,  # High failure rate
            success_rate_24h=50.0,  # Low success rate
            average_refresh_time=5.0,
            error_distribution={'expired_refresh_token': 25, 'network_error': 25},
            health_score=30.0  # Low health score
        )
        
        # Execute
        alerts = await service.check_alerts([bad_metrics])
        
        # Verify alerts were generated
        assert len(alerts) > 0
        
        # Check for specific alert types
        alert_types = [alert.alert_type for alert in alerts]
        assert AlertType.LOW_SUCCESS_RATE in alert_types
        assert AlertType.EXPIRED_TOKENS in alert_types
        assert AlertType.HIGH_ERROR_RATE in alert_types
    
    @pytest.mark.asyncio
    async def test_health_score_calculation(self, mock_aws_services):
        """Test health score calculation logic."""
        service = TokenMonitoringService()
        
        # Test perfect health
        perfect_score = service._calculate_provider_health_score(
            success_rate=100.0,
            expired_tokens=0,
            total_users=100,
            failed_refreshes=0
        )
        assert perfect_score == 100.0
        
        # Test degraded health
        degraded_score = service._calculate_provider_health_score(
            success_rate=70.0,
            expired_tokens=20,
            total_users=100,
            failed_refreshes=30
        )
        assert degraded_score < 70.0

class TestTokenErrorHandler:
    """Test cases for TokenErrorHandler."""
    
    def test_classify_http_errors(self):
        """Test HTTP error classification."""
        context = TokenErrorContext(
            user_id='test_user',
            provider='google',
            operation='refresh_token'
        )
        
        # Test 401 errors
        error_401 = TokenErrorHandler.classify_http_error(
            401, 'invalid_grant', context
        )
        assert isinstance(error_401, ExpiredRefreshTokenError)
        
        # Test 429 rate limit
        error_429 = TokenErrorHandler.classify_http_error(
            429, 'rate limit exceeded', context
        )
        assert isinstance(error_429, RateLimitExceededError)
        
        # Test 500 server error
        error_500 = TokenErrorHandler.classify_http_error(
            500, 'internal server error', context
        )
        assert error_500.is_retryable is True
    
    def test_classify_exceptions(self):
        """Test exception classification."""
        context = TokenErrorContext(
            user_id='test_user',
            provider='google',
            operation='refresh_token'
        )
        
        # Test network exception
        network_exception = Exception("Connection timeout")
        error = TokenErrorHandler.classify_exception(network_exception, context)
        assert isinstance(error, NetworkError)
        assert error.is_retryable is True
        
        # Test invalid grant exception
        invalid_grant_exception = Exception("invalid_grant: refresh token expired")
        error = TokenErrorHandler.classify_exception(invalid_grant_exception, context)
        assert isinstance(error, ExpiredRefreshTokenError)
        assert error.is_retryable is False
    
    def test_retry_logic(self):
        """Test retry decision logic."""
        context = TokenErrorContext(
            user_id='test_user',
            provider='google',
            operation='refresh_token'
        )
        
        # Retryable error should allow retries
        retryable_error = NetworkError("timeout", context)
        assert TokenErrorHandler.should_retry(retryable_error, 5, 2) is True
        
        # Non-retryable error should not allow retries
        non_retryable_error = ExpiredRefreshTokenError(context)
        assert TokenErrorHandler.should_retry(non_retryable_error, 5, 2) is False
        
        # Max retries exceeded
        assert TokenErrorHandler.should_retry(retryable_error, 5, 5) is False
    
    def test_retry_delay_calculation(self):
        """Test retry delay calculation."""
        context = TokenErrorContext(
            user_id='test_user',
            provider='google',
            operation='refresh_token'
        )
        
        # Test exponential backoff
        network_error = NetworkError("timeout", context)
        delay_0 = TokenErrorHandler.get_retry_delay(network_error, 0)
        delay_1 = TokenErrorHandler.get_retry_delay(network_error, 1)
        delay_2 = TokenErrorHandler.get_retry_delay(network_error, 2)
        
        assert delay_1 > delay_0
        assert delay_2 > delay_1
        
        # Test rate limit with retry-after
        rate_limit_error = RateLimitExceededError(300, context)
        delay = TokenErrorHandler.get_retry_delay(rate_limit_error, 0)
        assert delay == 300.0

@pytest.mark.asyncio
async def test_integration_token_refresh_flow(mock_aws_services, sample_connection):
    """Integration test for complete token refresh flow."""
    # Setup
    connections_table = mock_aws_services['connections_table']
    connections_table.put_item(Item=sample_connection)
    
    refresh_service = TokenRefreshService()
    monitoring_service = TokenMonitoringService()
    
    # Mock successful OAuth refresh
    with patch.object(refresh_service.oauth_manager, 'refresh_access_token') as mock_refresh:
        mock_refresh.return_value = {
            'connection_id': 'user123#google',
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            'status': 'active'
        }
        
        # 1. Perform token refresh
        refresh_result = await refresh_service.refresh_token_with_backoff('user123', 'google')
        assert refresh_result['success'] is True
        
        # 2. Collect metrics
        metrics = await monitoring_service.collect_metrics('google')
        assert len(metrics) == 1
        
        # 3. Check for alerts (should be none for healthy system)
        alerts = await monitoring_service.check_alerts(metrics)
        assert len(alerts) == 0  # No alerts for healthy system
        
        # 4. Get health status
        health_status = await refresh_service.get_token_health_status('user123', 'google')
        assert health_status['health_status'] in ['healthy', 'unknown']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])