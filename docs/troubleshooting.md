# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the AWS Meeting Scheduling Agent.

## Common Issues and Solutions

### Authentication Issues

#### Issue: "Invalid JWT token" error
**Symptoms:**
- API returns 401 Unauthorized
- Error message: "Invalid or expired JWT token"

**Solutions:**
1. **Check token expiration:**
   ```javascript
   import jwt_decode from 'jwt-decode';
   const decoded = jwt_decode(token);
   console.log('Token expires at:', new Date(decoded.exp * 1000));
   ```

2. **Refresh the token:**
   ```javascript
   import { Auth } from 'aws-amplify';
   const session = await Auth.currentSession();
   const newToken = session.getIdToken().getJwtToken();
   ```

3. **Verify Cognito configuration:**
   ```bash
   aws cognito-idp describe-user-pool --user-pool-id your-pool-id
   ```

#### Issue: OAuth callback fails
**Symptoms:**
- Redirect URI mismatch error
- "Invalid client" error from Google/Microsoft

**Solutions:**
1. **Verify redirect URIs match exactly:**
   - Google Console: Check authorized redirect URIs
   - Azure Portal: Check redirect URIs in app registration
   - Ensure no trailing slashes or HTTP/HTTPS mismatches

2. **Check OAuth client credentials:**
   ```bash
   # Verify secrets in AWS Secrets Manager
   aws secretsmanager get-secret-value --secret-id "meeting-agent/google-oauth"
   aws secretsmanager get-secret-value --secret-id "meeting-agent/microsoft-oauth"
   ```

3. **Test OAuth flow manually:**
   ```bash
   # Google OAuth test
   curl "https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code&scope=https://www.googleapis.com/auth/calendar"
   ```

### Calendar Integration Issues

#### Issue: Calendar sync fails
**Symptoms:**
- Events not appearing in the application
- "Failed to sync calendar" error messages
- Last sync timestamp not updating

**Solutions:**
1. **Check OAuth token validity:**
   ```python
   # Test Google Calendar API access
   import requests
   headers = {'Authorization': f'Bearer {access_token}'}
   response = requests.get('https://www.googleapis.com/calendar/v3/calendars/primary', headers=headers)
   print(response.status_code, response.json())
   ```

2. **Verify API permissions:**
   - Google: Ensure Calendar API is enabled
   - Microsoft: Check Graph API permissions are granted

3. **Check rate limiting:**
   ```bash
   # Monitor CloudWatch logs for rate limit errors
   aws logs filter-log-events --log-group-name "/aws/lambda/meeting-agent-calendar" --filter-pattern "rate limit"
   ```

4. **Force resync:**
   ```bash
   curl -X POST https://api.meeting-agent.example.com/calendar/sync \
     -H "Authorization: Bearer $JWT_TOKEN" \
     -d '{"connectionId": "conn-123", "forceSync": true}'
   ```

#### Issue: Events missing or duplicated
**Symptoms:**
- Some calendar events don't appear
- Duplicate events in the system
- Inconsistent event data

**Solutions:**
1. **Check sync filters:**
   ```python
   # Verify date range and filters
   start_time = datetime.now(timezone.utc)
   end_time = start_time + timedelta(days=30)
   print(f"Syncing from {start_time} to {end_time}")
   ```

2. **Clear cache and resync:**
   ```bash
   # Delete cached data and trigger full sync
   aws dynamodb scan --table-name MeetingAgent-Events --filter-expression "connectionId = :conn" --expression-attribute-values '{":conn":{"S":"conn-123"}}'
   ```

3. **Check event deduplication:**
   ```python
   # Verify event ID handling
   def generate_event_id(provider_id, connection_id):
       return f"{connection_id}#{provider_id}"
   ```

### AI Scheduling Issues

#### Issue: Bedrock API errors
**Symptoms:**
- "Model not found" errors
- "Insufficient permissions" for Bedrock
- AI scheduling requests timeout

**Solutions:**
1. **Verify Bedrock model access:**
   ```bash
   aws bedrock list-foundation-models --region eu-west-1
   aws bedrock get-model --model-identifier anthropic.claude-3-5-sonnet-20241022-v2:0
   ```

2. **Check IAM permissions:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel",
           "bedrock:InvokeModelWithResponseStream"
         ],
         "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
       }
     ]
   }
   ```

3. **Test Bedrock connectivity:**
   ```python
   import boto3
   bedrock = boto3.client('bedrock-runtime', region_name='eu-west-1')
   response = bedrock.invoke_model(
       modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
       body=json.dumps({
           "anthropic_version": "bedrock-2023-05-31",
           "max_tokens": 100,
           "messages": [{"role": "user", "content": "Hello"}]
       })
   )
   ```

#### Issue: Poor scheduling suggestions
**Symptoms:**
- AI suggests conflicting times
- Suggestions don't respect preferences
- Low confidence scores

**Solutions:**
1. **Review prompt engineering:**
   ```python
   # Check prompt template and context
   def build_scheduling_prompt(context):
       return f"""
       Given the following calendar data and preferences:
       {context}
       
       Find the optimal meeting time considering:
       - All attendee availability
       - User preferences and working hours
       - Existing conflicts and priorities
       """
   ```

2. **Validate input data:**
   ```python
   # Ensure complete context is provided
   required_fields = ['attendees', 'duration', 'preferences', 'existing_events']
   for field in required_fields:
       assert field in context, f"Missing {field} in context"
   ```

3. **Adjust AI parameters:**
   ```python
   # Fine-tune model parameters
   bedrock_params = {
       "max_tokens": 1000,
       "temperature": 0.1,  # Lower for more deterministic results
       "top_p": 0.9
   }
   ```

### Performance Issues

#### Issue: Slow API responses
**Symptoms:**
- API requests taking >5 seconds
- Timeout errors
- High Lambda duration in CloudWatch

**Solutions:**
1. **Check Lambda performance:**
   ```bash
   # Monitor Lambda metrics
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Duration \
     --dimensions Name=FunctionName,Value=meeting-agent-scheduler \
     --start-time 2024-01-15T00:00:00Z \
     --end-time 2024-01-15T23:59:59Z \
     --period 300 \
     --statistics Average,Maximum
   ```

2. **Optimize Lambda memory:**
   ```bash
   # Increase Lambda memory allocation
   aws lambda update-function-configuration \
     --function-name meeting-agent-scheduler \
     --memory-size 1024
   ```

3. **Enable DynamoDB DAX:**
   ```bash
   # Check DAX cluster status
   aws dax describe-clusters --cluster-names meeting-agent-cache
   ```

4. **Review database queries:**
   ```python
   # Optimize DynamoDB queries
   response = dynamodb.query(
       TableName='MeetingAgent-Events',
       IndexName='UserTimeIndex',  # Use GSI for better performance
       KeyConditionExpression='userId = :uid AND startTime BETWEEN :start AND :end',
       ExpressionAttributeValues={
           ':uid': user_id,
           ':start': start_time,
           ':end': end_time
       }
   )
   ```

#### Issue: High costs
**Symptoms:**
- Unexpected AWS bills
- High Bedrock token usage
- Excessive DynamoDB read/write units

**Solutions:**
1. **Monitor Bedrock usage:**
   ```bash
   # Check Bedrock costs
   aws ce get-cost-and-usage \
     --time-period Start=2024-01-01,End=2024-01-31 \
     --granularity MONTHLY \
     --metrics BlendedCost \
     --group-by Type=DIMENSION,Key=SERVICE
   ```

2. **Optimize AI calls:**
   ```python
   # Cache AI responses
   import hashlib
   
   def get_cached_ai_response(prompt):
       cache_key = hashlib.md5(prompt.encode()).hexdigest()
       cached = redis.get(f"ai_response:{cache_key}")
       if cached:
           return json.loads(cached)
       
       response = call_bedrock(prompt)
       redis.setex(f"ai_response:{cache_key}", 3600, json.dumps(response))
       return response
   ```

3. **Set up billing alerts:**
   ```bash
   aws budgets create-budget \
     --account-id 123456789012 \
     --budget '{
       "BudgetName": "MeetingAgentBudget",
       "BudgetLimit": {"Amount": "100", "Unit": "USD"},
       "TimeUnit": "MONTHLY",
       "BudgetType": "COST"
     }'
   ```

### Deployment Issues

#### Issue: CDK deployment fails
**Symptoms:**
- Stack creation/update failures
- Resource limit errors
- Permission denied errors

**Solutions:**
1. **Check CDK bootstrap:**
   ```bash
   cdk bootstrap aws://ACCOUNT-ID/REGION
   ```

2. **Verify IAM permissions:**
   ```bash
   # Check current user permissions
   aws sts get-caller-identity
   aws iam get-user
   ```

3. **Review CloudFormation events:**
   ```bash
   aws cloudformation describe-stack-events --stack-name CoreStack
   ```

4. **Clean up failed stacks:**
   ```bash
   # Delete failed stack and retry
   cdk destroy CoreStack
   cdk deploy CoreStack
   ```

#### Issue: Lambda deployment package too large
**Symptoms:**
- "Unzipped size must be smaller than 262144000 bytes"
- Deployment timeouts

**Solutions:**
1. **Use Lambda layers:**
   ```python
   # Create layer for dependencies
   mkdir python
   pip install -r requirements.txt -t python/
   zip -r dependencies-layer.zip python/
   ```

2. **Optimize package size:**
   ```bash
   # Remove unnecessary files
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -type d -exec rm -rf {} +
   ```

3. **Use container images:**
   ```dockerfile
   FROM public.ecr.aws/lambda/python:3.11
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["app.handler"]
   ```

### Data Issues

#### Issue: Data inconsistency
**Symptoms:**
- Meeting data doesn't match calendar
- Conflicting information between providers
- Missing or corrupted data

**Solutions:**
1. **Run data validation:**
   ```python
   def validate_meeting_data(meeting):
       assert meeting.get('startTime'), "Missing start time"
       assert meeting.get('endTime'), "Missing end time"
       assert meeting['startTime'] < meeting['endTime'], "Invalid time range"
       return True
   ```

2. **Implement data reconciliation:**
   ```python
   def reconcile_calendar_data(user_id):
       # Compare data across providers
       google_events = get_google_events(user_id)
       outlook_events = get_outlook_events(user_id)
       
       # Identify discrepancies
       conflicts = find_data_conflicts(google_events, outlook_events)
       return conflicts
   ```

3. **Set up data monitoring:**
   ```python
   # Monitor data quality metrics
   def check_data_quality():
       total_events = count_total_events()
       invalid_events = count_invalid_events()
       quality_score = (total_events - invalid_events) / total_events
       
       if quality_score < 0.95:
           send_alert("Data quality below threshold")
   ```

## Debugging Tools

### CloudWatch Logs Analysis

**View Lambda logs:**
```bash
# Tail logs in real-time
aws logs tail /aws/lambda/meeting-agent-scheduler --follow

# Search for specific errors
aws logs filter-log-events \
  --log-group-name "/aws/lambda/meeting-agent-scheduler" \
  --filter-pattern "ERROR" \
  --start-time 1642204800000
```

**Custom log queries:**
```bash
# Find slow requests
aws logs start-query \
  --log-group-name "/aws/lambda/meeting-agent-scheduler" \
  --start-time 1642204800 \
  --end-time 1642291200 \
  --query-string 'fields @timestamp, @duration | filter @duration > 5000'
```

### X-Ray Tracing

**Enable X-Ray tracing:**
```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

# Patch AWS SDK calls
patch_all()

@xray_recorder.capture('schedule_meeting')
def schedule_meeting(event, context):
    # Function implementation
    pass
```

**Analyze traces:**
```bash
# Get trace summaries
aws xray get-trace-summaries \
  --time-range-type TimeRangeByStartTime \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z
```

### Database Debugging

**DynamoDB query analysis:**
```python
import boto3

def analyze_dynamodb_performance():
    cloudwatch = boto3.client('cloudwatch')
    
    # Get consumed capacity metrics
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/DynamoDB',
        MetricName='ConsumedReadCapacityUnits',
        Dimensions=[{'Name': 'TableName', 'Value': 'MeetingAgent-Events'}],
        StartTime=datetime.utcnow() - timedelta(hours=1),
        EndTime=datetime.utcnow(),
        Period=300,
        Statistics=['Sum', 'Average']
    )
    
    return response['Datapoints']
```

**Check table health:**
```bash
# Monitor table metrics
aws dynamodb describe-table --table-name MeetingAgent-Events
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ThrottledRequests \
  --dimensions Name=TableName,Value=MeetingAgent-Events \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 300 \
  --statistics Sum
```

## Monitoring and Alerting

### CloudWatch Alarms

**Set up critical alarms:**
```bash
# Lambda error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "MeetingAgent-HighErrorRate" \
  --alarm-description "High error rate in Lambda functions" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# DynamoDB throttling alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "MeetingAgent-DynamoDBThrottling" \
  --alarm-description "DynamoDB throttling detected" \
  --metric-name ThrottledRequests \
  --namespace AWS/DynamoDB \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1
```

### Custom Metrics

**Application-level monitoring:**
```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def put_custom_metric(metric_name, value, unit='Count'):
    cloudwatch.put_metric_data(
        Namespace='MeetingAgent/Application',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }
        ]
    )

# Usage examples
put_custom_metric('MeetingsScheduled', 1)
put_custom_metric('ConflictsResolved', 1)
put_custom_metric('AIResponseTime', response_time, 'Milliseconds')
```

## Getting Help

### Log Collection

When reporting issues, collect the following information:

1. **Error details:**
   ```bash
   # Get recent error logs
   aws logs filter-log-events \
     --log-group-name "/aws/lambda/meeting-agent-scheduler" \
     --filter-pattern "ERROR" \
     --start-time $(date -d '1 hour ago' +%s)000
   ```

2. **System status:**
   ```bash
   # Check service health
   curl https://api.meeting-agent.example.com/health
   ```

3. **Configuration:**
   ```bash
   # Export relevant configuration (remove sensitive data)
   aws lambda get-function-configuration --function-name meeting-agent-scheduler
   ```

### Support Channels

1. **GitHub Issues**: Report bugs and feature requests
2. **CloudWatch Insights**: Use for log analysis and debugging
3. **AWS Support**: For infrastructure-related issues
4. **Documentation**: Check this guide and API documentation

### Emergency Procedures

**Service outage response:**
1. Check AWS Service Health Dashboard
2. Review CloudWatch alarms and metrics
3. Examine recent deployments
4. Implement rollback if necessary:
   ```bash
   # Rollback to previous version
   cdk deploy --previous-parameters
   ```

**Data recovery:**
1. Check DynamoDB point-in-time recovery
2. Restore from backup if available
3. Re-sync calendar data from providers

## Next Steps

1. Set up comprehensive monitoring using the examples above
2. Create runbooks for common operational procedures
3. Implement automated health checks and recovery procedures
4. Review the [Architecture Documentation](./architecture.md) for system design details