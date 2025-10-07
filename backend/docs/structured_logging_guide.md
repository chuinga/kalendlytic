# Structured Logging System Guide

## Overview

The AWS Meeting Scheduling Agent uses a comprehensive structured logging system with JSON formatting, PII redaction, and agent decision tracking. This system is designed for CloudWatch integration with automatic log retention and archival policies.

## Key Features

- **JSON Structured Logging**: All logs are formatted as JSON for easy parsing and analysis
- **PII Redaction**: Automatic redaction of personally identifiable information
- **Agent Decision Tracking**: Specialized logging for AI agent decisions and rationales
- **Correlation IDs**: Request tracking across distributed components
- **Performance Metrics**: Automatic performance tracking and slow operation detection
- **CloudWatch Integration**: Seamless integration with AWS CloudWatch Logs
- **Log Archival**: Automatic archival to S3 with lifecycle policies

## Basic Usage

### Setting up a Logger

```python
from src.utils.logging import create_agent_logger, setup_logger

# Basic logger
logger = setup_logger('my_service')

# Enhanced agent logger with context
agent_logger = create_agent_logger(
    'agent_service',
    correlation_id='req-123',
    user_id='user-456'
)
```

### Basic Logging

```python
# Standard log levels
logger.info("Processing request")
logger.warning("Rate limit approaching")
logger.error("Failed to connect to external API")

# With context
agent_logger.info("Starting calendar sync", extra={
    'calendar_count': 3,
    'sync_type': 'full'
})
```

## Agent Decision Logging

### Logging Agent Decisions

```python
from src.utils.logging import AgentDecisionType

agent_logger.log_agent_decision(
    decision_type=AgentDecisionType.SCHEDULING,
    rationale="Selected 2 PM slot based on all attendees' availability and user preferences",
    inputs={
        'attendees': ['user1@example.com', 'user2@example.com'],
        'duration': 60,
        'preferred_times': ['14:00', '15:00', '16:00']
    },
    outputs={
        'selected_time': '14:00',
        'meeting_id': 'meeting-123',
        'confidence_score': 0.85
    },
    confidence_score=0.85,
    alternatives_count=3,
    tool_name='availability_tool'
)
```

### Logging Tool Invocations

```python
agent_logger.log_tool_invocation(
    tool_name='google_calendar_api',
    inputs={
        'action': 'get_events',
        'date_range': '2024-01-01 to 2024-01-07'
    },
    outputs={
        'events_found': 15,
        'conflicts_detected': 2
    },
    success=True,
    execution_time_ms=1250
)
```

### Performance Metrics

```python
# Start performance tracking
agent_logger.start_performance_tracking()

# ... perform operations ...

# Log performance metrics
agent_logger.log_performance_metrics(
    operation='calendar_synchronization',
    metrics={
        'calendars_synced': 3,
        'events_processed': 150,
        'api_calls_made': 12,
        'cache_hits': 8,
        'cache_misses': 4
    }
)
```

## PII Redaction

The system automatically redacts PII from logs:

```python
# This log message will have PII redacted
logger.info("User john.doe@example.com called from 555-123-4567")
# Output: "User [REDACTED_EMAIL] called from [REDACTED_PHONE]"

# PII in structured data is also redacted
logger.info("User data processed", extra={
    'user_email': 'john.doe@example.com',  # Will be redacted
    'user_name': 'John Doe',               # Will be preserved
    'phone': '555-123-4567'                # Will be redacted
})
```

## Configuration

### Environment Variables

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Environment (dev, staging, prod)
ENVIRONMENT=dev

# Enable/disable PII redaction
PII_REDACTION_ENABLED=true

# Enable/disable performance logging
PERFORMANCE_LOGGING_ENABLED=true
```

### Programmatic Configuration

```python
from src.config.logging_config import LoggingConfig, apply_environment_config

# Apply environment-specific configuration
apply_environment_config()

# Check configuration
print(f"Log level: {LoggingConfig.get_log_level()}")
print(f"Environment: {LoggingConfig.get_environment()}")
print(f"PII redaction enabled: {LoggingConfig.PII_REDACTION_ENABLED}")
```

## CloudWatch Integration

### Log Groups

The system creates the following log groups:

- `/aws/lambda/meeting-agent-auth-handler`
- `/aws/lambda/meeting-agent-connections-handler`
- `/aws/lambda/meeting-agent-agent-handler`
- `/aws/lambda/meeting-agent-calendar-handler`
- `/aws/lambda/meeting-agent-preferences-handler`
- `/aws/lambda/meeting-agent-agent-decisions` (for agent decision audit trails)

### Log Retention

- **CloudWatch**: 30 days (configurable per environment)
- **S3 Archive**: 7 years with lifecycle transitions
  - Standard → IA: 30 days
  - IA → Glacier: 90 days
  - Glacier → Deep Archive: 365 days

### Querying Logs

```bash
# Query agent decisions
aws logs filter-log-events \
  --log-group-name "/aws/lambda/meeting-agent-agent-decisions" \
  --filter-pattern "{ $.decision_type = \"scheduling\" }"

# Query performance issues
aws logs filter-log-events \
  --log-group-name "/aws/lambda/meeting-agent-calendar-handler" \
  --filter-pattern "{ $.execution_time_ms > 5000 }"
```

## Log Aggregation

### Automated Aggregation

The system includes automated log aggregation that runs hourly:

```python
from src.utils.log_aggregation import create_log_aggregator, AggregationPeriod

aggregator = create_log_aggregator()

# Aggregate agent decisions for the last hour
metrics = aggregator.aggregate_agent_decisions(
    log_group='/aws/lambda/meeting-agent-agent-decisions',
    start_time=datetime.utcnow() - timedelta(hours=1),
    end_time=datetime.utcnow()
)

print(f"Total decisions: {metrics.total_decisions}")
print(f"Success rate: {metrics.success_rate:.2%}")
print(f"Average cost: ${metrics.average_cost_per_decision_usd:.4f}")
```

### Manual Analysis

```python
# Get aggregated metrics from S3
historical_metrics = aggregator.get_aggregated_metrics(
    bucket='meeting-agent-logs-archive-123456789012-us-east-1',
    period=AggregationPeriod.DAILY,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

for daily_metrics in historical_metrics:
    print(f"Date: {daily_metrics['timestamp']}")
    print(f"Decisions: {daily_metrics['total_decisions']}")
    print(f"Success rate: {daily_metrics['success_rate']:.2%}")
```

## Best Practices

### 1. Use Appropriate Log Levels

```python
# DEBUG: Detailed diagnostic information
logger.debug("Parsing calendar event", extra={'event_id': 'evt-123'})

# INFO: General operational information
logger.info("Calendar sync completed successfully")

# WARNING: Something unexpected but recoverable
logger.warning("Rate limit reached, implementing backoff")

# ERROR: Error condition that needs attention
logger.error("Failed to create calendar event", exc_info=True)

# CRITICAL: Serious error that may cause system failure
logger.critical("Database connection lost")
```

### 2. Include Relevant Context

```python
# Good: Includes relevant context
logger.info("Meeting scheduled", extra={
    'meeting_id': 'mtg-123',
    'attendee_count': 5,
    'duration_minutes': 60,
    'calendar_provider': 'google'
})

# Avoid: Too little context
logger.info("Meeting scheduled")
```

### 3. Use Correlation IDs

```python
# In Lambda handlers
correlation_id = get_correlation_id()
logger = create_agent_logger('handler_name', correlation_id=correlation_id)

# Include in responses
return {
    'statusCode': 200,
    'headers': {'X-Correlation-ID': correlation_id},
    'body': json.dumps(result)
}
```

### 4. Log Agent Decisions for Audit

```python
# Always log important agent decisions
agent_logger.log_agent_decision(
    decision_type=AgentDecisionType.CONFLICT_RESOLUTION,
    rationale="Rescheduled lower priority meeting to resolve conflict",
    inputs={'conflict_id': 'conf-123'},
    outputs={'resolution': 'reschedule', 'new_time': '15:00'},
    confidence_score=0.9
)
```

## Troubleshooting

### Common Issues

1. **Logs not appearing in CloudWatch**
   - Check IAM permissions for Lambda execution role
   - Verify log group exists and has correct name
   - Check CloudWatch Logs service availability

2. **PII not being redacted**
   - Verify `PII_REDACTION_ENABLED=true` environment variable
   - Check if PII patterns match your data format
   - Review custom PII fields in configuration

3. **Performance impact**
   - Reduce log level in production (`WARNING` or `ERROR`)
   - Disable performance logging for high-throughput operations
   - Use sampling for detailed debug logs

### Monitoring Log Health

```python
# Check log aggregation health
from src.utils.log_aggregation import create_log_aggregator

aggregator = create_log_aggregator()
recent_metrics = aggregator.aggregate_agent_decisions(
    log_group='/aws/lambda/meeting-agent-agent-decisions',
    start_time=datetime.utcnow() - timedelta(minutes=15),
    end_time=datetime.utcnow()
)

if recent_metrics.total_decisions == 0:
    logger.warning("No agent decisions logged in the last 15 minutes")
```

This structured logging system provides comprehensive observability for the AWS Meeting Scheduling Agent while maintaining security through PII redaction and enabling detailed analysis through structured data and automated aggregation.