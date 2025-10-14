import * as cdk from 'aws-cdk-lib';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as cloudwatchActions from 'aws-cdk-lib/aws-cloudwatch-actions';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as subscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import { Construct } from 'constructs';
import { CoreStack } from './core-stack';
import { ApiStack } from './api-stack';
import { WebStack } from './web-stack';

export interface MonitoringStackProps extends cdk.StackProps {
  coreStack: CoreStack;
  apiStack: ApiStack;
  webStack: WebStack;
}

export class MonitoringStack extends cdk.Stack {
  public logArchiveBucket: s3.Bucket;
  public logAggregatorFunction: lambda.Function;
  public agentDecisionLogGroup: logs.LogGroup;
  public healthCheckFunction: lambda.Function;
  public alertingTopic: sns.Topic;
  public systemDashboard: cloudwatch.Dashboard;

  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    const { coreStack, apiStack, webStack } = props;

    // Create log retention and archival infrastructure
    this.createLogRetentionPolicies(apiStack);
    
    // Create log aggregation infrastructure
    this.createLogAggregation();
    
    // Create agent decision tracking
    this.createAgentDecisionTracking();

    // Create health check endpoints and monitoring
    this.createHealthCheckEndpoints(apiStack);
    
    // Create CloudWatch metrics and custom metrics
    this.createCustomMetrics();
    
    // Create CloudWatch dashboard
    this.createDashboard(apiStack, webStack);
    
    // Create alerting infrastructure
    this.createAlerting(apiStack);
  }

  private createLogRetentionPolicies(apiStack: ApiStack): void {
    // Create S3 bucket for log archival
    this.logArchiveBucket = new s3.Bucket(this, 'LogArchiveBucket', {
      bucketName: `kalendlytic-logs-archive-${this.account}-${this.region}`,
      versioned: false,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [
        {
          id: 'log-archival-lifecycle',
          enabled: true,
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(30),
            },
            {
              storageClass: s3.StorageClass.GLACIER,
              transitionAfter: cdk.Duration.days(90),
            },
            {
              storageClass: s3.StorageClass.DEEP_ARCHIVE,
              transitionAfter: cdk.Duration.days(365),
            },
          ],
          expiration: cdk.Duration.days(2555), // 7 years retention
        },
      ],
    });

    // Configure log groups for Lambda functions with retention policies
    const lambdaFunctions = [
      { name: 'AuthHandler', function: apiStack.authHandler },
      { name: 'ConnectionsHandler', function: apiStack.connectionsHandler },
      { name: 'AgentHandler', function: apiStack.agentHandler },
      { name: 'CalendarHandler', function: apiStack.calendarHandler },
      { name: 'PreferencesHandler', function: apiStack.preferencesHandler },
    ];

    lambdaFunctions.forEach(({ name, function: lambdaFunction }) => {
      // Create log group with retention policy
      const logGroup = new logs.LogGroup(this, `${name}LogGroup`, {
        logGroupName: `/aws/lambda/${lambdaFunction.functionName}`,
        retention: logs.RetentionDays.ONE_MONTH, // 30 days in CloudWatch
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      });

      // Create log stream for structured logging
      new logs.LogStream(this, `${name}LogStream`, {
        logGroup: logGroup,
        logStreamName: 'structured-logs',
        removalPolicy: cdk.RemovalPolicy.DESTROY,
      });

      // Create subscription filter for log archival
      const logArchivalRole = new iam.Role(this, `${name}LogArchivalRole`, {
        assumedBy: new iam.ServicePrincipal('logs.amazonaws.com'),
        inlinePolicies: {
          S3WritePolicy: new iam.PolicyDocument({
            statements: [
              new iam.PolicyStatement({
                effect: iam.Effect.ALLOW,
                actions: [
                  's3:PutObject',
                  's3:PutObjectAcl',
                ],
                resources: [
                  `${this.logArchiveBucket.bucketArn}/*`,
                ],
              }),
            ],
          }),
        },
      });

      // Create subscription filter to archive logs to S3
      new logs.CfnSubscriptionFilter(this, `${name}LogArchivalFilter`, {
        logGroupName: logGroup.logGroupName,
        filterPattern: '', // Archive all logs
        destinationArn: `arn:aws:s3:::${this.logArchiveBucket.bucketName}/lambda-logs/${name}/`,
        roleArn: logArchivalRole.roleArn,
      });
    });
  }

  private createLogAggregation(): void {
    // Create Lambda function for log aggregation and analysis
    this.logAggregatorFunction = new lambda.Function(this, 'LogAggregatorFunction', {
      functionName: 'kalendlytic-log-aggregator',
      runtime: lambda.Runtime.PYTHON_3_11,
      architecture: lambda.Architecture.ARM_64,
      handler: 'index.lambda_handler',
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        LOG_ARCHIVE_BUCKET: this.logArchiveBucket.bucketName,
        AGENT_DECISION_LOG_GROUP: '/aws/lambda/kalendlytic-agent-decisions',
      },
      code: lambda.Code.fromInline(`
import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

def lambda_handler(event, context):
    """
    Aggregate and analyze agent decision logs for insights and reporting.
    """
    logs_client = boto3.client('logs')
    s3_client = boto3.client('s3')
    
    try:
        # Get log events from the past hour
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        log_group = os.environ['AGENT_DECISION_LOG_GROUP']
        
        # Query logs for agent decisions
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            filterPattern='{ $.decision_type = * }'
        )
        
        # Process and aggregate log events
        decisions = []
        for event in response.get('events', []):
            try:
                log_data = json.loads(event['message'])
                if 'decision_type' in log_data:
                    decisions.append(log_data)
            except json.JSONDecodeError:
                continue
        
        # Create aggregation summary
        summary = create_decision_summary(decisions)
        
        # Store aggregated data in S3
        bucket = os.environ['LOG_ARCHIVE_BUCKET']
        key = f"aggregated-logs/{end_time.strftime('%Y/%m/%d/%H')}/decisions-summary.json"
        
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(summary, default=str),
            ContentType='application/json'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Log aggregation completed',
                'decisions_processed': len(decisions),
                'summary': summary
            })
        }
        
    except Exception as e:
        print(f"Error in log aggregation: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def create_decision_summary(decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create summary of agent decisions."""
    if not decisions:
        return {'total_decisions': 0}
    
    decision_types = {}
    total_execution_time = 0
    successful_decisions = 0
    total_cost = 0.0
    
    for decision in decisions:
        decision_type = decision.get('decision_type', 'unknown')
        decision_types[decision_type] = decision_types.get(decision_type, 0) + 1
        
        exec_time = decision.get('execution_time_ms', 0)
        if exec_time:
            total_execution_time += exec_time
        
        if decision.get('success', True):
            successful_decisions += 1
        
        cost_estimate = decision.get('cost_estimate', {})
        if isinstance(cost_estimate, dict) and 'estimated_cost_usd' in cost_estimate:
            total_cost += float(cost_estimate['estimated_cost_usd'])
    
    return {
        'total_decisions': len(decisions),
        'decision_types': decision_types,
        'success_rate': successful_decisions / len(decisions),
        'average_execution_time_ms': total_execution_time / len(decisions),
        'total_cost_usd': total_cost,
        'timestamp': datetime.utcnow().isoformat()
    }
`),
    });

    // Grant permissions to log aggregator
    this.logAggregatorFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'logs:FilterLogEvents',
          'logs:DescribeLogGroups',
          'logs:DescribeLogStreams',
        ],
        resources: [
          `arn:aws:logs:${this.region}:${this.account}:log-group:/aws/lambda/meeting-agent-*`,
        ],
      })
    );

    this.logArchiveBucket.grantWrite(this.logAggregatorFunction);

    // Schedule log aggregation to run every hour
    const aggregationRule = new events.Rule(this, 'LogAggregationRule', {
      ruleName: 'kalendlytic-log-aggregation',
      description: 'Triggers hourly log aggregation and analysis',
      schedule: events.Schedule.rate(cdk.Duration.hours(1)),
    });

    aggregationRule.addTarget(
      new targets.LambdaFunction(this.logAggregatorFunction, {
        event: events.RuleTargetInput.fromObject({
          action: 'aggregate_logs',
          timestamp: events.EventField.fromPath('$.time'),
        }),
      })
    );
  }

  private createAgentDecisionTracking(): void {
    // Create dedicated log group for agent decisions
    this.agentDecisionLogGroup = new logs.LogGroup(this, 'AgentDecisionLogGroup', {
      logGroupName: '/aws/lambda/kalendlytic-agent-decisions',
      retention: logs.RetentionDays.THREE_MONTHS, // Longer retention for audit trails
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Create log stream for agent decisions
    new logs.LogStream(this, 'AgentDecisionLogStream', {
      logGroup: this.agentDecisionLogGroup,
      logStreamName: 'agent-decisions',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Create subscription filter for agent decision archival
    const agentDecisionArchivalRole = new iam.Role(this, 'AgentDecisionArchivalRole', {
      assumedBy: new iam.ServicePrincipal('logs.amazonaws.com'),
      inlinePolicies: {
        S3WritePolicy: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              effect: iam.Effect.ALLOW,
              actions: [
                's3:PutObject',
                's3:PutObjectAcl',
              ],
              resources: [
                `${this.logArchiveBucket.bucketArn}/agent-decisions/*`,
              ],
            }),
          ],
        }),
      },
    });

    // Archive agent decisions to S3 for long-term storage
    new logs.CfnSubscriptionFilter(this, 'AgentDecisionArchivalFilter', {
      logGroupName: this.agentDecisionLogGroup.logGroupName,
      filterPattern: '{ $.decision_type = * }', // Only archive decision logs
      destinationArn: `arn:aws:s3:::${this.logArchiveBucket.bucketName}/agent-decisions/`,
      roleArn: agentDecisionArchivalRole.roleArn,
    });
  }

  private createHealthCheckEndpoints(apiStack: ApiStack): void {
    // Create health check Lambda function
    this.healthCheckFunction = new lambda.Function(this, 'HealthCheckFunction', {
      functionName: 'kalendlytic-health-check',
      runtime: lambda.Runtime.PYTHON_3_11,
      architecture: lambda.Architecture.ARM_64,
      handler: 'index.lambda_handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        USERS_TABLE: 'kalendlytic-users',
        CONNECTIONS_TABLE: 'kalendlytic-connections',
        REGION: this.region,
      },
      code: lambda.Code.fromInline(`
import json
import boto3
import time
from datetime import datetime
from typing import Dict, Any

def lambda_handler(event, context):
    """
    Health check endpoint that validates system components.
    """
    health_status = {
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'healthy',
        'checks': {},
        'version': '1.0.0'
    }
    
    try:
        # Check DynamoDB connectivity
        health_status['checks']['dynamodb'] = check_dynamodb()
        
        # Check Bedrock connectivity
        health_status['checks']['bedrock'] = check_bedrock()
        
        # Check Secrets Manager connectivity
        health_status['checks']['secrets_manager'] = check_secrets_manager()
        
        # Check CloudWatch Logs connectivity
        health_status['checks']['cloudwatch_logs'] = check_cloudwatch_logs()
        
        # Determine overall health
        failed_checks = [name for name, check in health_status['checks'].items() if not check['healthy']]
        if failed_checks:
            health_status['status'] = 'unhealthy'
            health_status['failed_checks'] = failed_checks
        
        # Publish custom metrics
        publish_health_metrics(health_status)
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            },
            'body': json.dumps(health_status)
        }
        
    except Exception as e:
        error_response = {
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'error',
            'error': str(e)
        }
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            },
            'body': json.dumps(error_response)
        }

def check_dynamodb() -> Dict[str, Any]:
    """Check DynamoDB connectivity and basic operations."""
    try:
        dynamodb = boto3.client('dynamodb')
        
        start_time = time.time()
        response = dynamodb.describe_table(TableName='kalendlytic-users')
        response_time = (time.time() - start_time) * 1000
        
        return {
            'healthy': True,
            'response_time_ms': round(response_time, 2),
            'table_status': response['Table']['TableStatus']
        }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }

def check_bedrock() -> Dict[str, Any]:
    """Check Bedrock connectivity."""
    try:
        bedrock = boto3.client('bedrock')
        
        start_time = time.time()
        response = bedrock.list_foundation_models(byProvider='anthropic')
        response_time = (time.time() - start_time) * 1000
        
        return {
            'healthy': True,
            'response_time_ms': round(response_time, 2),
            'models_available': len(response.get('modelSummaries', []))
        }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }

def check_secrets_manager() -> Dict[str, Any]:
    """Check Secrets Manager connectivity."""
    try:
        secrets = boto3.client('secretsmanager')
        
        start_time = time.time()
        response = secrets.list_secrets(MaxResults=1)
        response_time = (time.time() - start_time) * 1000
        
        return {
            'healthy': True,
            'response_time_ms': round(response_time, 2)
        }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }

def check_cloudwatch_logs() -> Dict[str, Any]:
    """Check CloudWatch Logs connectivity."""
    try:
        logs_client = boto3.client('logs')
        
        start_time = time.time()
        response = logs_client.describe_log_groups(limit=1)
        response_time = (time.time() - start_time) * 1000
        
        return {
            'healthy': True,
            'response_time_ms': round(response_time, 2)
        }
    except Exception as e:
        return {
            'healthy': False,
            'error': str(e)
        }

def publish_health_metrics(health_status: Dict[str, Any]) -> None:
    """Publish health check metrics to CloudWatch."""
    try:
        cloudwatch = boto3.client('cloudwatch')
        
        # Overall health metric
        cloudwatch.put_metric_data(
            Namespace='MeetingAgent/Health',
            MetricData=[
                {
                    'MetricName': 'SystemHealth',
                    'Value': 1 if health_status['status'] == 'healthy' else 0,
                    'Unit': 'Count',
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
        
        # Individual component metrics
        for component, check in health_status['checks'].items():
            cloudwatch.put_metric_data(
                Namespace='MeetingAgent/Health',
                MetricData=[
                    {
                        'MetricName': f'{component.title()}Health',
                        'Value': 1 if check['healthy'] else 0,
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
            
            # Response time metrics
            if 'response_time_ms' in check:
                cloudwatch.put_metric_data(
                    Namespace='MeetingAgent/Performance',
                    MetricData=[
                        {
                            'MetricName': f'{component.title()}ResponseTime',
                            'Value': check['response_time_ms'],
                            'Unit': 'Milliseconds',
                            'Timestamp': datetime.utcnow()
                        }
                    ]
                )
    except Exception as e:
        print(f"Failed to publish health metrics: {str(e)}")
`),
    });

    // Grant permissions to health check function
    this.healthCheckFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'dynamodb:DescribeTable',
          'bedrock:ListFoundationModels',
          'secretsmanager:ListSecrets',
          'logs:DescribeLogGroups',
          'cloudwatch:PutMetricData',
        ],
        resources: ['*'],
      })
    );

    // Note: Health check endpoint is available as a standalone Lambda function
    // Individual service health checks are available at /auth/health, /agent/health, etc.

    // Create EventBridge rule for periodic health checks (every 5 minutes)
    const healthCheckRule = new events.Rule(this, 'HealthCheckRule', {
      ruleName: 'kalendlytic-health-check',
      description: 'Triggers periodic health checks',
      schedule: events.Schedule.rate(cdk.Duration.minutes(5)),
    });

    healthCheckRule.addTarget(
      new targets.LambdaFunction(this.healthCheckFunction, {
        event: events.RuleTargetInput.fromObject({
          action: 'scheduled_health_check',
          timestamp: events.EventField.fromPath('$.time'),
        }),
      })
    );
  }

  private createCustomMetrics(): void {
    // Custom metrics are published by Lambda functions and health checks
    // This method creates metric filters for log-based metrics
    
    // Create metric filter for Bedrock token usage
    new logs.MetricFilter(this, 'BedrockTokenUsageFilter', {
      logGroup: this.agentDecisionLogGroup,
      filterPattern: logs.FilterPattern.exists('$.bedrock_usage.input_tokens'),
      metricNamespace: 'Kalendlytic/Bedrock',
      metricName: 'InputTokens',
      metricValue: '$.bedrock_usage.input_tokens',
    });

    // Create metric filter for Bedrock costs
    new logs.MetricFilter(this, 'BedrockCostFilter', {
      logGroup: this.agentDecisionLogGroup,
      filterPattern: logs.FilterPattern.exists('$.cost_estimate.estimated_cost_usd'),
      metricNamespace: 'Kalendlytic/Bedrock',
      metricName: 'EstimatedCostUSD',
      metricValue: '$.cost_estimate.estimated_cost_usd',
    });

    // Create metric filter for agent decision success rate
    new logs.MetricFilter(this, 'AgentSuccessFilter', {
      logGroup: this.agentDecisionLogGroup,
      filterPattern: logs.FilterPattern.stringValue('$.success', '=', 'true'),
      metricNamespace: 'Kalendlytic/Agent',
      metricName: 'SuccessfulDecisions',
      metricValue: '1',
    });

    new logs.MetricFilter(this, 'AgentFailureFilter', {
      logGroup: this.agentDecisionLogGroup,
      filterPattern: logs.FilterPattern.stringValue('$.success', '=', 'false'),
      metricNamespace: 'Kalendlytic/Agent',
      metricName: 'FailedDecisions',
      metricValue: '1',
    });
  }

  private createDashboard(apiStack: ApiStack, webStack: WebStack): void {
    this.systemDashboard = new cloudwatch.Dashboard(this, 'SystemDashboard', {
      dashboardName: 'kalendlytic-system-overview',
    });

    // API Gateway metrics
    const apiGatewayWidget = new cloudwatch.GraphWidget({
      title: 'API Gateway Metrics',
      left: [
        new cloudwatch.Metric({
          namespace: 'AWS/ApiGateway',
          metricName: 'Count',
          dimensionsMap: {
            ApiName: apiStack.restApi.restApiName,
          },
          statistic: 'Sum',
        }),
        new cloudwatch.Metric({
          namespace: 'AWS/ApiGateway',
          metricName: '4XXError',
          dimensionsMap: {
            ApiName: apiStack.restApi.restApiName,
          },
          statistic: 'Sum',
        }),
        new cloudwatch.Metric({
          namespace: 'AWS/ApiGateway',
          metricName: '5XXError',
          dimensionsMap: {
            ApiName: apiStack.restApi.restApiName,
          },
          statistic: 'Sum',
        }),
      ],
      right: [
        new cloudwatch.Metric({
          namespace: 'AWS/ApiGateway',
          metricName: 'Latency',
          dimensionsMap: {
            ApiName: apiStack.restApi.restApiName,
          },
          statistic: 'Average',
        }),
      ],
    });

    // Lambda function metrics
    const lambdaFunctions = [
      { name: 'Auth Handler', function: apiStack.authHandler },
      { name: 'Agent Handler', function: apiStack.agentHandler },
      { name: 'Calendar Handler', function: apiStack.calendarHandler },
      { name: 'Connections Handler', function: apiStack.connectionsHandler },
      { name: 'Preferences Handler', function: apiStack.preferencesHandler },
    ];

    const lambdaMetrics = lambdaFunctions.map(({ function: fn }) => [
      new cloudwatch.Metric({
        namespace: 'AWS/Lambda',
        metricName: 'Invocations',
        dimensionsMap: {
          FunctionName: fn.functionName,
        },
        statistic: 'Sum',
      }),
      new cloudwatch.Metric({
        namespace: 'AWS/Lambda',
        metricName: 'Errors',
        dimensionsMap: {
          FunctionName: fn.functionName,
        },
        statistic: 'Sum',
      }),
      new cloudwatch.Metric({
        namespace: 'AWS/Lambda',
        metricName: 'Duration',
        dimensionsMap: {
          FunctionName: fn.functionName,
        },
        statistic: 'Average',
      }),
    ]).flat();

    const lambdaWidget = new cloudwatch.GraphWidget({
      title: 'Lambda Function Metrics',
      left: lambdaMetrics.filter((_, index) => index % 3 === 0 || index % 3 === 1), // Invocations and Errors
      right: lambdaMetrics.filter((_, index) => index % 3 === 2), // Duration
    });

    // Custom application metrics
    const customMetricsWidget = new cloudwatch.GraphWidget({
      title: 'Application Metrics',
      left: [
        new cloudwatch.Metric({
          namespace: 'MeetingAgent/Health',
          metricName: 'SystemHealth',
          statistic: 'Average',
        }),
        new cloudwatch.Metric({
          namespace: 'MeetingAgent/Agent',
          metricName: 'SuccessfulDecisions',
          statistic: 'Sum',
        }),
        new cloudwatch.Metric({
          namespace: 'MeetingAgent/Agent',
          metricName: 'FailedDecisions',
          statistic: 'Sum',
        }),
      ],
      right: [
        new cloudwatch.Metric({
          namespace: 'MeetingAgent/Bedrock',
          metricName: 'InputTokens',
          statistic: 'Sum',
        }),
        new cloudwatch.Metric({
          namespace: 'MeetingAgent/Bedrock',
          metricName: 'EstimatedCostUSD',
          statistic: 'Sum',
        }),
      ],
    });

    // Performance metrics
    const performanceWidget = new cloudwatch.GraphWidget({
      title: 'System Performance',
      left: [
        new cloudwatch.Metric({
          namespace: 'MeetingAgent/Performance',
          metricName: 'DynamodbResponseTime',
          statistic: 'Average',
        }),
        new cloudwatch.Metric({
          namespace: 'MeetingAgent/Performance',
          metricName: 'BedrockResponseTime',
          statistic: 'Average',
        }),
      ],
      right: [
        new cloudwatch.Metric({
          namespace: 'MeetingAgent/Performance',
          metricName: 'SecretsManagerResponseTime',
          statistic: 'Average',
        }),
        new cloudwatch.Metric({
          namespace: 'MeetingAgent/Performance',
          metricName: 'CloudwatchLogsResponseTime',
          statistic: 'Average',
        }),
      ],
    });

    // Add widgets to dashboard
    this.systemDashboard.addWidgets(
      apiGatewayWidget,
      lambdaWidget,
      customMetricsWidget,
      performanceWidget
    );
  }

  private createAlerting(apiStack: ApiStack): void {
    // Create SNS topic for alerts
    this.alertingTopic = new sns.Topic(this, 'AlertingTopic', {
      topicName: 'meeting-agent-alerts',
      displayName: 'Kalendlytic System Alerts',
    });

    // Add email subscription (placeholder - should be configured via environment variables)
    // this.alertingTopic.addSubscription(
    //   new subscriptions.EmailSubscription('admin@example.com')
    // );

    // Create alarms for system health
    const systemHealthAlarm = new cloudwatch.Alarm(this, 'SystemHealthAlarm', {
      alarmName: 'kalendlytic-system-unhealthy',
      alarmDescription: 'System health check is failing',
      metric: new cloudwatch.Metric({
        namespace: 'MeetingAgent/Health',
        metricName: 'SystemHealth',
        statistic: 'Average',
      }),
      threshold: 1,
      comparisonOperator: cloudwatch.ComparisonOperator.LESS_THAN_THRESHOLD,
      evaluationPeriods: 2,
      datapointsToAlarm: 2,
      treatMissingData: cloudwatch.TreatMissingData.BREACHING,
    });

    systemHealthAlarm.addAlarmAction(new cloudwatchActions.SnsAction(this.alertingTopic));

    // Create alarms for API Gateway errors
    const apiErrorAlarm = new cloudwatch.Alarm(this, 'ApiErrorAlarm', {
      alarmName: 'kalendlytic-api-high-error-rate',
      alarmDescription: 'API Gateway error rate is too high',
      metric: new cloudwatch.Metric({
        namespace: 'AWS/ApiGateway',
        metricName: '5XXError',
        dimensionsMap: {
          ApiName: apiStack.restApi.restApiName,
        },
        statistic: 'Sum',
      }),
      threshold: 10,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      evaluationPeriods: 2,
      datapointsToAlarm: 2,
    });

    apiErrorAlarm.addAlarmAction(new cloudwatchActions.SnsAction(this.alertingTopic));

    // Create alarms for Lambda function errors
    const lambdaFunctions = [
      { name: 'Auth Handler', function: apiStack.authHandler },
      { name: 'Agent Handler', function: apiStack.agentHandler },
      { name: 'Calendar Handler', function: apiStack.calendarHandler },
      { name: 'Connections Handler', function: apiStack.connectionsHandler },
      { name: 'Preferences Handler', function: apiStack.preferencesHandler },
    ];

    lambdaFunctions.forEach(({ name, function: lambdaFunction }) => {
      const errorAlarm = new cloudwatch.Alarm(this, `${name}ErrorAlarm`, {
        alarmName: `kalendlytic-${name.toLowerCase().replace(' ', '-')}-errors`,
        alarmDescription: `${name} Lambda function error rate is too high`,
        metric: new cloudwatch.Metric({
          namespace: 'AWS/Lambda',
          metricName: 'Errors',
          dimensionsMap: {
            FunctionName: lambdaFunction.functionName,
          },
          statistic: 'Sum',
        }),
        threshold: 5,
        comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        evaluationPeriods: 2,
        datapointsToAlarm: 2,
      });

      errorAlarm.addAlarmAction(new cloudwatchActions.SnsAction(this.alertingTopic));

      // Duration alarm for performance monitoring
      const durationAlarm = new cloudwatch.Alarm(this, `${name}DurationAlarm`, {
        alarmName: `kalendlytic-${name.toLowerCase().replace(' ', '-')}-high-duration`,
        alarmDescription: `${name} Lambda function duration is too high`,
        metric: new cloudwatch.Metric({
          namespace: 'AWS/Lambda',
          metricName: 'Duration',
          dimensionsMap: {
            FunctionName: lambdaFunction.functionName,
          },
          statistic: 'Average',
        }),
        threshold: 30000, // 30 seconds
        comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
        evaluationPeriods: 3,
        datapointsToAlarm: 2,
      });

      durationAlarm.addAlarmAction(new cloudwatchActions.SnsAction(this.alertingTopic));
    });

    // Create alarm for Bedrock costs
    const bedrockCostAlarm = new cloudwatch.Alarm(this, 'BedrockCostAlarm', {
      alarmName: 'kalendlytic-bedrock-high-cost',
      alarmDescription: 'Bedrock usage costs are exceeding threshold',
      metric: new cloudwatch.Metric({
        namespace: 'MeetingAgent/Bedrock',
        metricName: 'EstimatedCostUSD',
        statistic: 'Sum',
      }),
      threshold: 100, // $100 per hour
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      evaluationPeriods: 1,
      datapointsToAlarm: 1,
    });

    bedrockCostAlarm.addAlarmAction(new cloudwatchActions.SnsAction(this.alertingTopic));

    // Create alarm for agent decision failure rate
    const agentFailureAlarm = new cloudwatch.Alarm(this, 'AgentFailureAlarm', {
      alarmName: 'kalendlytic-high-failure-rate',
      alarmDescription: 'Agent decision failure rate is too high',
      metric: new cloudwatch.Metric({
        namespace: 'MeetingAgent/Agent',
        metricName: 'FailedDecisions',
        statistic: 'Sum',
      }),
      threshold: 20,
      comparisonOperator: cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
      evaluationPeriods: 2,
      datapointsToAlarm: 2,
    });

    agentFailureAlarm.addAlarmAction(new cloudwatchActions.SnsAction(this.alertingTopic));
  }
}