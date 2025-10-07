"""
Comprehensive token error handling utilities and custom exceptions.
Provides structured error handling for OAuth token operations.
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class TokenErrorSeverity(Enum):
    """Severity levels for token errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TokenErrorCategory(Enum):
    """Categories of token errors for better classification."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    RATE_LIMITING = "rate_limiting"
    PROVIDER_ISSUE = "provider_issue"
    CONFIGURATION = "configuration"
    SYSTEM = "system"

@dataclass
class TokenErrorContext:
    """Context information for token errors."""
    user_id: str
    provider: str
    operation: str
    correlation_id: Optional[str] = None
    attempt_number: Optional[int] = None
    additional_data: Optional[Dict[str, Any]] = None

class TokenError(Exception):
    """Base class for token-related errors."""
    
    def __init__(self, message: str, error_code: str, category: TokenErrorCategory,
                 severity: TokenErrorSeverity, context: Optional[TokenErrorContext] = None,
                 is_retryable: bool = False, retry_after: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.context = context
        self.is_retryable = is_retryable
        self.retry_after = retry_after
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging and API responses."""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
            'is_retryable': self.is_retryable,
            'retry_after': self.retry_after,
            'context': {
                'user_id': self.context.user_id if self.context else None,
                'provider': self.context.provider if self.context else None,
                'operation': self.context.operation if self.context else None,
                'correlation_id': self.context.correlation_id if self.context else None,
                'attempt_number': self.context.attempt_number if self.context else None
            }
        }

class ExpiredAccessTokenError(TokenError):
    """Access token has expired and needs refresh."""
    
    def __init__(self, context: Optional[TokenErrorContext] = None):
        super().__init__(
            message="Access token has expired",
            error_code="EXPIRED_ACCESS_TOKEN",
            category=TokenErrorCategory.AUTHENTICATION,
            severity=TokenErrorSeverity.LOW,
            context=context,
            is_retryable=True
        )

class ExpiredRefreshTokenError(TokenError):
    """Refresh token has expired, re-authorization required."""
    
    def __init__(self, context: Optional[TokenErrorContext] = None):
        super().__init__(
            message="Refresh token has expired, re-authorization required",
            error_code="EXPIRED_REFRESH_TOKEN",
            category=TokenErrorCategory.AUTHENTICATION,
            severity=TokenErrorSeverity.HIGH,
            context=context,
            is_retryable=False
        )

class InvalidTokenError(TokenError):
    """Token is invalid or malformed."""
    
    def __init__(self, context: Optional[TokenErrorContext] = None):
        super().__init__(
            message="Token is invalid or malformed",
            error_code="INVALID_TOKEN",
            category=TokenErrorCategory.AUTHENTICATION,
            severity=TokenErrorSeverity.HIGH,
            context=context,
            is_retryable=False
        )

class RevokedTokenError(TokenError):
    """Token has been revoked by the user or provider."""
    
    def __init__(self, context: Optional[TokenErrorContext] = None):
        super().__init__(
            message="Token has been revoked",
            error_code="REVOKED_TOKEN",
            category=TokenErrorCategory.AUTHORIZATION,
            severity=TokenErrorSeverity.HIGH,
            context=context,
            is_retryable=False
        )

class InsufficientScopeError(TokenError):
    """Token does not have required scopes."""
    
    def __init__(self, required_scopes: List[str], context: Optional[TokenErrorContext] = None):
        self.required_scopes = required_scopes
        super().__init__(
            message=f"Token missing required scopes: {', '.join(required_scopes)}",
            error_code="INSUFFICIENT_SCOPE",
            category=TokenErrorCategory.AUTHORIZATION,
            severity=TokenErrorSeverity.MEDIUM,
            context=context,
            is_retryable=False
        )

class RateLimitExceededError(TokenError):
    """Rate limit exceeded for token operations."""
    
    def __init__(self, retry_after: int, context: Optional[TokenErrorContext] = None):
        super().__init__(
            message=f"Rate limit exceeded, retry after {retry_after} seconds",
            error_code="RATE_LIMIT_EXCEEDED",
            category=TokenErrorCategory.RATE_LIMITING,
            severity=TokenErrorSeverity.MEDIUM,
            context=context,
            is_retryable=True,
            retry_after=retry_after
        )

class NetworkError(TokenError):
    """Network-related error during token operation."""
    
    def __init__(self, original_error: str, context: Optional[TokenErrorContext] = None):
        super().__init__(
            message=f"Network error: {original_error}",
            error_code="NETWORK_ERROR",
            category=TokenErrorCategory.NETWORK,
            severity=TokenErrorSeverity.MEDIUM,
            context=context,
            is_retryable=True
        )

class ProviderError(TokenError):
    """Error from OAuth provider."""
    
    def __init__(self, provider_error: str, provider_code: Optional[str] = None,
                 context: Optional[TokenErrorContext] = None):
        self.provider_code = provider_code
        super().__init__(
            message=f"Provider error: {provider_error}",
            error_code="PROVIDER_ERROR",
            category=TokenErrorCategory.PROVIDER_ISSUE,
            severity=TokenErrorSeverity.MEDIUM,
            context=context,
            is_retryable=True
        )

class ConfigurationError(TokenError):
    """OAuth configuration error."""
    
    def __init__(self, config_issue: str, context: Optional[TokenErrorContext] = None):
        super().__init__(
            message=f"Configuration error: {config_issue}",
            error_code="CONFIGURATION_ERROR",
            category=TokenErrorCategory.CONFIGURATION,
            severity=TokenErrorSeverity.CRITICAL,
            context=context,
            is_retryable=False
        )

class SystemError(TokenError):
    """System-level error during token operation."""
    
    def __init__(self, system_error: str, context: Optional[TokenErrorContext] = None):
        super().__init__(
            message=f"System error: {system_error}",
            error_code="SYSTEM_ERROR",
            category=TokenErrorCategory.SYSTEM,
            severity=TokenErrorSeverity.HIGH,
            context=context,
            is_retryable=True
        )

class TokenErrorHandler:
    """Utility class for handling and classifying token errors."""
    
    @staticmethod
    def classify_http_error(status_code: int, response_body: str, 
                          context: Optional[TokenErrorContext] = None) -> TokenError:
        """
        Classify HTTP error responses into appropriate token errors.
        
        Args:
            status_code: HTTP status code
            response_body: Response body text
            context: Error context
            
        Returns:
            Appropriate TokenError subclass
        """
        response_lower = response_body.lower()
        
        if status_code == 401:
            if 'invalid_grant' in response_lower or 'refresh' in response_lower:
                return ExpiredRefreshTokenError(context)
            elif 'invalid_token' in response_lower:
                return InvalidTokenError(context)
            elif 'revoked' in response_lower:
                return RevokedTokenError(context)
            else:
                return ExpiredAccessTokenError(context)
        
        elif status_code == 403:
            if 'scope' in response_lower or 'permission' in response_lower:
                return InsufficientScopeError([], context)
            else:
                return RevokedTokenError(context)
        
        elif status_code == 429:
            # Try to extract retry-after from response
            retry_after = 60  # Default to 60 seconds
            if 'retry-after' in response_lower:
                try:
                    import re
                    match = re.search(r'retry-after[:\s]+(\d+)', response_lower)
                    if match:
                        retry_after = int(match.group(1))
                except:
                    pass
            
            return RateLimitExceededError(retry_after, context)
        
        elif status_code >= 500:
            return ProviderError(f"Server error (HTTP {status_code})", str(status_code), context)
        
        else:
            return ProviderError(f"HTTP {status_code}: {response_body}", str(status_code), context)
    
    @staticmethod
    def classify_exception(exception: Exception, 
                         context: Optional[TokenErrorContext] = None) -> TokenError:
        """
        Classify generic exceptions into appropriate token errors.
        
        Args:
            exception: Original exception
            context: Error context
            
        Returns:
            Appropriate TokenError subclass
        """
        error_str = str(exception).lower()
        
        # Network-related errors
        if any(keyword in error_str for keyword in ['timeout', 'connection', 'network', 'dns']):
            return NetworkError(str(exception), context)
        
        # OAuth-specific errors
        if 'invalid_grant' in error_str:
            return ExpiredRefreshTokenError(context)
        elif 'invalid_token' in error_str:
            return InvalidTokenError(context)
        elif 'revoked' in error_str:
            return RevokedTokenError(context)
        elif 'scope' in error_str:
            return InsufficientScopeError([], context)
        elif 'rate limit' in error_str or 'too many requests' in error_str:
            return RateLimitExceededError(60, context)
        
        # Configuration errors
        elif any(keyword in error_str for keyword in ['config', 'credential', 'secret']):
            return ConfigurationError(str(exception), context)
        
        # Default to system error
        else:
            return SystemError(str(exception), context)
    
    @staticmethod
    def should_retry(error: TokenError, max_retries: int, current_attempt: int) -> bool:
        """
        Determine if an operation should be retried based on the error.
        
        Args:
            error: Token error
            max_retries: Maximum number of retries allowed
            current_attempt: Current attempt number (0-based)
            
        Returns:
            True if operation should be retried
        """
        if not error.is_retryable:
            return False
        
        if current_attempt >= max_retries:
            return False
        
        # Don't retry critical errors
        if error.severity == TokenErrorSeverity.CRITICAL:
            return False
        
        return True
    
    @staticmethod
    def get_retry_delay(error: TokenError, attempt: int, base_delay: float = 1.0) -> float:
        """
        Calculate appropriate retry delay for an error.
        
        Args:
            error: Token error
            attempt: Current attempt number (0-based)
            base_delay: Base delay in seconds
            
        Returns:
            Delay in seconds
        """
        if error.retry_after:
            return float(error.retry_after)
        
        # Exponential backoff based on error severity
        multiplier = {
            TokenErrorSeverity.LOW: 1.0,
            TokenErrorSeverity.MEDIUM: 1.5,
            TokenErrorSeverity.HIGH: 2.0,
            TokenErrorSeverity.CRITICAL: 3.0
        }.get(error.severity, 1.0)
        
        delay = base_delay * multiplier * (2 ** attempt)
        
        # Cap delay based on error category
        max_delays = {
            TokenErrorCategory.NETWORK: 60.0,
            TokenErrorCategory.RATE_LIMITING: 300.0,
            TokenErrorCategory.PROVIDER_ISSUE: 120.0
        }
        
        max_delay = max_delays.get(error.category, 30.0)
        return min(delay, max_delay)

def log_token_error(error: TokenError, logger_instance: logging.Logger) -> None:
    """
    Log token error with appropriate level and structured data.
    
    Args:
        error: Token error to log
        logger_instance: Logger instance to use
    """
    log_level = {
        TokenErrorSeverity.LOW: logging.INFO,
        TokenErrorSeverity.MEDIUM: logging.WARNING,
        TokenErrorSeverity.HIGH: logging.ERROR,
        TokenErrorSeverity.CRITICAL: logging.CRITICAL
    }.get(error.severity, logging.ERROR)
    
    logger_instance.log(
        log_level,
        f"Token error: {error.message}",
        extra={
            'error_code': error.error_code,
            'category': error.category.value,
            'severity': error.severity.value,
            'is_retryable': error.is_retryable,
            'retry_after': error.retry_after,
            'user_id': error.context.user_id if error.context else None,
            'provider': error.context.provider if error.context else None,
            'operation': error.context.operation if error.context else None,
            'correlation_id': error.context.correlation_id if error.context else None
        }
    )