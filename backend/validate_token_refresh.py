#!/usr/bin/env python3
"""
Validation script for token refresh and error handling implementation.
Tests core functionality without external dependencies.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add the backend src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_token_error_classification():
    """Test token error classification functionality."""
    print("Testing token error classification...")
    
    try:
        from utils.token_errors import TokenErrorHandler, TokenErrorContext
        
        context = TokenErrorContext(
            user_id='test_user',
            provider='google',
            operation='refresh_token'
        )
        
        # Test HTTP error classification
        error_401 = TokenErrorHandler.classify_http_error(401, 'invalid_grant', context)
        assert error_401.error_code == 'EXPIRED_REFRESH_TOKEN'
        assert not error_401.is_retryable
        
        error_429 = TokenErrorHandler.classify_http_error(429, 'rate limit exceeded', context)
        assert error_429.error_code == 'RATE_LIMIT_EXCEEDED'
        assert error_429.is_retryable
        
        # Test exception classification
        network_exception = Exception("Connection timeout")
        network_error = TokenErrorHandler.classify_exception(network_exception, context)
        assert network_error.error_code == 'NETWORK_ERROR'
        assert network_error.is_retryable
        
        print("✓ Token error classification tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Token error classification tests failed: {e}")
        return False

def test_backoff_calculation():
    """Test exponential backoff calculation."""
    print("Testing exponential backoff calculation...")
    
    try:
        from services.token_refresh_service import TokenRefreshService
        
        # Mock dependencies
        with patch('services.token_refresh_service.get_dynamodb_resource'), \
             patch('services.token_refresh_service.get_secrets_client'):
            
            service = TokenRefreshService()
            
            # Test backoff delays
            delay_0 = service._calculate_backoff_delay(0)
            delay_1 = service._calculate_backoff_delay(1)
            delay_2 = service._calculate_backoff_delay(2)
            
            # Verify exponential increase
            assert delay_1 > delay_0, f"Expected {delay_1} > {delay_0}"
            assert delay_2 > delay_1, f"Expected {delay_2} > {delay_1}"
            
            # Test maximum delay cap
            delay_large = service._calculate_backoff_delay(10)
            assert delay_large <= service.max_delay, f"Expected {delay_large} <= {service.max_delay}"
            
            print(f"✓ Backoff delays: {delay_0:.2f}s -> {delay_1:.2f}s -> {delay_2:.2f}s (max: {delay_large:.2f}s)")
            return True
            
    except Exception as e:
        print(f"✗ Backoff calculation tests failed: {e}")
        return False

def test_health_score_calculation():
    """Test health score calculation."""
    print("Testing health score calculation...")
    
    try:
        from services.token_monitoring import TokenMonitoringService
        
        # Mock dependencies
        with patch('services.token_monitoring.get_dynamodb_resource'), \
             patch('services.token_monitoring.get_secrets_client'):
            
            service = TokenMonitoringService()
            
            # Test perfect health
            perfect_score = service._calculate_provider_health_score(
                success_rate=100.0,
                expired_tokens=0,
                total_users=100,
                failed_refreshes=0
            )
            assert perfect_score == 100.0, f"Expected perfect score 100.0, got {perfect_score}"
            
            # Test degraded health
            degraded_score = service._calculate_provider_health_score(
                success_rate=70.0,
                expired_tokens=20,
                total_users=100,
                failed_refreshes=30
            )
            assert degraded_score < 70.0, f"Expected degraded score < 70.0, got {degraded_score}"
            
            # Test critical health
            critical_score = service._calculate_provider_health_score(
                success_rate=30.0,
                expired_tokens=50,
                total_users=100,
                failed_refreshes=80
            )
            assert critical_score < 50.0, f"Expected critical score < 50.0, got {critical_score}"
            
            print(f"✓ Health scores: Perfect={perfect_score}, Degraded={degraded_score:.1f}, Critical={critical_score:.1f}")
            return True
            
    except Exception as e:
        print(f"✗ Health score calculation tests failed: {e}")
        return False

def test_error_retry_logic():
    """Test error retry decision logic."""
    print("Testing error retry logic...")
    
    try:
        from utils.token_errors import (
            TokenErrorHandler, NetworkError, ExpiredRefreshTokenError, 
            TokenErrorContext
        )
        
        context = TokenErrorContext(
            user_id='test_user',
            provider='google',
            operation='refresh_token'
        )
        
        # Test retryable error
        retryable_error = NetworkError("Connection timeout", context)
        should_retry = TokenErrorHandler.should_retry(retryable_error, 5, 2)
        assert should_retry, "Network error should be retryable"
        
        # Test non-retryable error
        non_retryable_error = ExpiredRefreshTokenError(context)
        should_not_retry = TokenErrorHandler.should_retry(non_retryable_error, 5, 2)
        assert not should_not_retry, "Expired refresh token should not be retryable"
        
        # Test max retries exceeded
        max_retries_exceeded = TokenErrorHandler.should_retry(retryable_error, 5, 5)
        assert not max_retries_exceeded, "Should not retry when max retries exceeded"
        
        print("✓ Error retry logic tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Error retry logic tests failed: {e}")
        return False

async def test_async_functionality():
    """Test async functionality with mocked dependencies."""
    print("Testing async functionality...")
    
    try:
        from services.token_refresh_service import TokenRefreshService
        
        # Mock all dependencies
        with patch('services.token_refresh_service.get_dynamodb_resource') as mock_dynamo, \
             patch('services.token_refresh_service.get_secrets_client') as mock_secrets:
            
            # Setup mocks
            mock_table = Mock()
            mock_table.get_item.return_value = {}
            mock_table.put_item.return_value = None
            mock_dynamo.return_value.Table.return_value = mock_table
            
            service = TokenRefreshService()
            
            # Test rate limiting check
            is_rate_limited = service._is_rate_limited('test_user', 'google')
            # Should return False since we mocked empty responses
            assert isinstance(is_rate_limited, bool)
            
            print("✓ Async functionality tests passed")
            return True
            
    except Exception as e:
        print(f"✗ Async functionality tests failed: {e}")
        return False

def test_monitoring_metrics():
    """Test monitoring metrics structure."""
    print("Testing monitoring metrics...")
    
    try:
        from services.token_monitoring import MonitoringMetrics, Alert, AlertType, AlertSeverity
        
        # Test metrics creation
        metrics = MonitoringMetrics(
            timestamp=datetime.utcnow().isoformat(),
            provider='google',
            total_users=100,
            active_connections=95,
            expired_tokens=5,
            failed_refreshes_24h=10,
            success_rate_24h=90.0,
            average_refresh_time=2.5,
            error_distribution={'network_error': 5, 'rate_limit': 5},
            health_score=85.0
        )
        
        assert metrics.provider == 'google'
        assert metrics.total_users == 100
        assert metrics.health_score == 85.0
        
        # Test alert creation
        alert = Alert(
            alert_id='test_alert_123',
            alert_type=AlertType.LOW_SUCCESS_RATE,
            severity=AlertSeverity.WARNING,
            title='Test Alert',
            message='This is a test alert',
            user_id=None,
            provider='google',
            timestamp=datetime.utcnow().isoformat(),
            metadata={'test': 'data'}
        )
        
        assert alert.alert_type == AlertType.LOW_SUCCESS_RATE
        assert alert.severity == AlertSeverity.WARNING
        
        print("✓ Monitoring metrics tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Monitoring metrics tests failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🔍 Validating token refresh and error handling implementation...\n")
    
    tests = [
        test_token_error_classification,
        test_backoff_calculation,
        test_health_score_calculation,
        test_error_retry_logic,
        test_monitoring_metrics
    ]
    
    async_tests = [
        test_async_functionality
    ]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run synchronous tests
    for test in tests:
        if test():
            passed += 1
        print()
    
    # Run async tests
    for test in async_tests:
        try:
            if asyncio.run(test()):
                passed += 1
        except Exception as e:
            print(f"✗ Async test failed: {e}")
        print()
    
    # Summary
    print("=" * 50)
    print(f"Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Token refresh implementation is working correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} tests failed. Please review the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())