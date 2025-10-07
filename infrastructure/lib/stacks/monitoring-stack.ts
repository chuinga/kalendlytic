import * as cdk from 'aws-cdk-lib';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
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

  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    const { coreStack, apiStack, webStack } = props;

    // Create log retention and archival infrastructure
    this.createLogRetentionPolicies(apiStack);
    
    // Create log aggregation infrastructure
    this.createLogAggregation();
    
    // Create agent decision tracking
    this.createAgentDecisionTracking();

    // TODO: Implement CloudWatch dashboards, metrics, and alarms
    // This will be implemented in task 9.3
  }

  private createLogRetentionPolicies(apiStack: ApiStack): void {
    // Create S3 bucket for log archival
    this.logArchiveBucket = new s3.Bucket(this, 'LogArchiveBucket', {
      bucketName: `meeting-agent-logs-archive-${this.account}-${this.region}`,
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
      functionName: 'meeting-agent-log-aggregator',
      runtime: lambda.Runtime.PYTHON_3_11,
      architecture: lambda.Architecture.ARM_64,
      handler: 'index.lambda_handler',
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        LOG_ARCHIVE_BUCKET: this.logArchiveBucket.bucketName,
        AGENT_DECISION_LOG_GROUP: '/aws/lambda/meeting-agent-agent-decisions',
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
      ruleName: 'meeting-agent-log-aggregation',
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
      logGroupName: '/aws/lambda/meeting-agent-agent-decisions',
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
}