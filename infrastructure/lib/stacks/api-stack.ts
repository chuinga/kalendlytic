import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as events from 'aws-cdk-lib/aws-events';
import * as targets from 'aws-cdk-lib/aws-events-targets';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import { Construct } from 'constructs';
import { CoreStack } from './core-stack';

export interface ApiStackProps extends cdk.StackProps {
  coreStack: CoreStack;
}

export class ApiStack extends cdk.Stack {
  public restApi: apigateway.RestApi;
  public authHandler: lambda.Function;
  public connectionsHandler: lambda.Function;
  public agentHandler: lambda.Function;
  public calendarHandler: lambda.Function;
  public preferencesHandler: lambda.Function;
  // public sharedLayer: lambda.LayerVersion; // Will be added when implementing backend
  public periodicScanQueue: sqs.Queue;

  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);

    const { coreStack } = props;

    // Create Lambda functions
    this.createLambdaFunctions(coreStack);

    // Create API Gateway
    this.createApiGateway();

    // Create EventBridge rules and SQS queues for periodic processing
    this.createEventProcessing();

    // Create outputs
    this.createOutputs();
  }



  private createLambdaFunctions(coreStack: CoreStack): void {
    // Common environment variables for all Lambda functions
    // Using hardcoded table names to avoid circular dependencies
    const commonEnvironment = {
      USERS_TABLE: 'meeting-agent-users',
      CONNECTIONS_TABLE: 'meeting-agent-connections',
      PREFERENCES_TABLE: 'meeting-agent-preferences',
      MEETINGS_TABLE: 'meeting-agent-meetings',
      AGENT_RUNS_TABLE: 'meeting-agent-runs',
      AUDIT_LOGS_TABLE: 'meeting-agent-audit-logs',
      REGION: this.region,
      // Logging configuration
      LOG_LEVEL: 'INFO',
      ENVIRONMENT: 'dev',
      LOG_GROUP_PREFIX: '/aws/lambda/meeting-agent',
      AGENT_DECISION_LOG_GROUP: '/aws/lambda/meeting-agent-agent-decisions',
      PII_REDACTION_ENABLED: 'true',
      PERFORMANCE_LOGGING_ENABLED: 'true',
    };

    // Common Lambda configuration
    const commonLambdaProps = {
      runtime: lambda.Runtime.PYTHON_3_11,
      architecture: lambda.Architecture.ARM_64,
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      // layers: [this.sharedLayer], // Will be added when implementing backend
      environment: commonEnvironment,
      tracing: lambda.Tracing.ACTIVE,
    };

    // Create placeholder Lambda functions with inline code
    // These will be replaced with actual implementations in later tasks

    // Auth Handler - handles Cognito authentication and user management
    this.authHandler = new lambda.Function(this, 'AuthHandler', {
      ...commonLambdaProps,
      functionName: 'meeting-agent-auth-handler',
      code: lambda.Code.fromInline(`
import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Auth handler placeholder'})
    }
`),
      handler: 'index.lambda_handler',
      description: 'Handles user authentication and profile management',
    });

    // Connections Handler - manages OAuth connections to Google and Microsoft
    this.connectionsHandler = new lambda.Function(this, 'ConnectionsHandler', {
      ...commonLambdaProps,
      functionName: 'meeting-agent-connections-handler',
      code: lambda.Code.fromInline(`
import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Connections handler placeholder'})
    }
`),
      handler: 'index.lambda_handler',
      description: 'Manages OAuth connections to calendar providers',
      timeout: cdk.Duration.seconds(60), // Longer timeout for OAuth flows
    });

    // Agent Handler - orchestrates AI agent operations using Bedrock
    this.agentHandler = new lambda.Function(this, 'AgentHandler', {
      ...commonLambdaProps,
      functionName: 'meeting-agent-agent-handler',
      code: lambda.Code.fromInline(`
import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Agent handler placeholder'})
    }
`),
      handler: 'index.lambda_handler',
      description: 'Orchestrates AI agent operations using Amazon Bedrock',
      timeout: cdk.Duration.minutes(5), // Longer timeout for AI processing
      memorySize: 1024, // More memory for AI operations
    });

    // Calendar Handler - manages calendar operations and availability
    this.calendarHandler = new lambda.Function(this, 'CalendarHandler', {
      ...commonLambdaProps,
      functionName: 'meeting-agent-calendar-handler',
      code: lambda.Code.fromInline(`
import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Calendar handler placeholder'})
    }
`),
      handler: 'index.lambda_handler',
      description: 'Manages calendar operations and availability aggregation',
      timeout: cdk.Duration.seconds(60), // Longer timeout for calendar API calls
    });

    // Preferences Handler - manages user preferences and settings
    this.preferencesHandler = new lambda.Function(this, 'PreferencesHandler', {
      ...commonLambdaProps,
      functionName: 'meeting-agent-preferences-handler',
      code: lambda.Code.fromInline(`
import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Preferences handler placeholder'})
    }
`),
      handler: 'index.lambda_handler',
      description: 'Manages user preferences and scheduling settings',
    });

    // Grant permissions to Lambda functions
    this.grantLambdaPermissions(coreStack);
  }

  private grantLambdaPermissions(coreStack: CoreStack): void {
    const lambdaFunctions = [
      this.authHandler,
      this.connectionsHandler,
      this.agentHandler,
      this.calendarHandler,
      this.preferencesHandler,
    ];

    lambdaFunctions.forEach((fn) => {
      // Grant DynamoDB permissions using table names to avoid circular dependencies
      fn.addToRolePolicy(
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            'dynamodb:GetItem',
            'dynamodb:PutItem',
            'dynamodb:UpdateItem',
            'dynamodb:DeleteItem',
            'dynamodb:Query',
            'dynamodb:Scan',
          ],
          resources: [
            `arn:aws:dynamodb:${this.region}:${this.account}:table/meeting-agent-users`,
            `arn:aws:dynamodb:${this.region}:${this.account}:table/meeting-agent-connections`,
            `arn:aws:dynamodb:${this.region}:${this.account}:table/meeting-agent-preferences`,
            `arn:aws:dynamodb:${this.region}:${this.account}:table/meeting-agent-meetings`,
            `arn:aws:dynamodb:${this.region}:${this.account}:table/meeting-agent-runs`,
            `arn:aws:dynamodb:${this.region}:${this.account}:table/meeting-agent-audit-logs`,
            `arn:aws:dynamodb:${this.region}:${this.account}:table/meeting-agent-*/index/*`,
          ],
        })
      );

      // Grant KMS permissions
      fn.addToRolePolicy(
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            'kms:Encrypt',
            'kms:Decrypt',
            'kms:ReEncrypt*',
            'kms:GenerateDataKey*',
            'kms:DescribeKey',
          ],
          resources: [
            `arn:aws:kms:${this.region}:${this.account}:key/*`,
          ],
        })
      );

      // Grant Secrets Manager permissions
      fn.addToRolePolicy(
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            'secretsmanager:GetSecretValue',
            'secretsmanager:DescribeSecret',
          ],
          resources: [
            `arn:aws:secretsmanager:${this.region}:${this.account}:secret:meeting-agent/oauth/*`,
          ],
        })
      );

      // Grant Cognito permissions
      fn.addToRolePolicy(
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          actions: [
            'cognito-idp:AdminGetUser',
            'cognito-idp:AdminCreateUser',
            'cognito-idp:AdminUpdateUserAttributes',
            'cognito-idp:AdminSetUserPassword',
            'cognito-idp:AdminConfirmSignUp',
            'cognito-idp:ListUsers',
          ],
          resources: [
            `arn:aws:cognito-idp:${this.region}:${this.account}:userpool/*`,
          ],
        })
      );
    });

    // Additional permissions for Agent Handler
    this.agentHandler.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'bedrock:InvokeModel',
          'bedrock:InvokeAgent',
          'bedrock:GetAgent',
          'bedrock:ListAgents',
        ],
        resources: [
          `arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0`,
          `arn:aws:bedrock:*:*:agent/*`,
        ],
      })
    );

    // Additional permissions for Connections Handler (external API calls)
    this.connectionsHandler.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'logs:CreateLogGroup',
          'logs:CreateLogStream',
          'logs:PutLogEvents',
        ],
        resources: ['*'],
      })
    );
  }

  private createApiGateway(): void {
    // Create REST API with CORS configuration
    this.restApi = new apigateway.RestApi(this, 'RestApi', {
      restApiName: 'meeting-agent-api',
      description: 'REST API for AWS Meeting Scheduling Agent',
      defaultCorsPreflightOptions: {
        allowOrigins: [
          'http://localhost:3000', // Local development
          // Production origins will be added via environment variables
        ],
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: [
          'Content-Type',
          'Authorization',
          'X-Amz-Date',
          'X-Api-Key',
          'X-Amz-Security-Token',
        ],
        maxAge: cdk.Duration.days(1),
      },
      deployOptions: {
        stageName: 'api',
        throttlingRateLimit: 100,
        throttlingBurstLimit: 200,
      },
    });

    // Create Lambda integrations
    const authIntegration = new apigateway.LambdaIntegration(this.authHandler);
    const connectionsIntegration = new apigateway.LambdaIntegration(this.connectionsHandler);
    const agentIntegration = new apigateway.LambdaIntegration(this.agentHandler);
    const calendarIntegration = new apigateway.LambdaIntegration(this.calendarHandler);
    const preferencesIntegration = new apigateway.LambdaIntegration(this.preferencesHandler);

    // Create resource hierarchy
    // Auth routes
    const authResource = this.restApi.root.addResource('auth');
    authResource.addResource('login').addMethod('POST', authIntegration);
    authResource.addResource('register').addMethod('POST', authIntegration);
    authResource.addResource('health').addMethod('GET', authIntegration);
    const profileResource = authResource.addResource('profile');
    profileResource.addMethod('GET', authIntegration);
    profileResource.addMethod('PUT', authIntegration);

    // Connection routes
    const connectionsResource = this.restApi.root.addResource('connections');
    connectionsResource.addMethod('GET', connectionsIntegration);
    connectionsResource.addResource('health').addMethod('GET', connectionsIntegration);
    
    const providerResource = connectionsResource.addResource('{provider}');
    providerResource.addMethod('POST', connectionsIntegration);
    providerResource.addMethod('DELETE', connectionsIntegration);
    
    const callbackResource = providerResource.addResource('callback');
    callbackResource.addMethod('GET', connectionsIntegration);
    callbackResource.addMethod('POST', connectionsIntegration);

    // Agent routes
    const agentResource = this.restApi.root.addResource('agent');
    agentResource.addResource('schedule').addMethod('POST', agentIntegration);
    agentResource.addResource('health').addMethod('GET', agentIntegration);
    
    const runsResource = agentResource.addResource('runs');
    runsResource.addMethod('GET', agentIntegration);
    runsResource.addResource('{runId}').addMethod('GET', agentIntegration);

    // Calendar routes
    const calendarResource = this.restApi.root.addResource('calendar');
    calendarResource.addResource('availability').addMethod('GET', calendarIntegration);
    calendarResource.addResource('health').addMethod('GET', calendarIntegration);
    
    const eventsResource = calendarResource.addResource('events');
    eventsResource.addMethod('GET', calendarIntegration);
    eventsResource.addMethod('POST', calendarIntegration);
    
    const eventResource = eventsResource.addResource('{eventId}');
    eventResource.addMethod('GET', calendarIntegration);
    eventResource.addMethod('PUT', calendarIntegration);
    eventResource.addMethod('DELETE', calendarIntegration);

    // Preferences routes
    const preferencesResource = this.restApi.root.addResource('preferences');
    preferencesResource.addMethod('GET', preferencesIntegration);
    preferencesResource.addMethod('PUT', preferencesIntegration);
    preferencesResource.addResource('health').addMethod('GET', preferencesIntegration);
    
    const workingHoursResource = preferencesResource.addResource('working-hours');
    workingHoursResource.addMethod('GET', preferencesIntegration);
    workingHoursResource.addMethod('PUT', preferencesIntegration);
    
    const vipContactsResource = preferencesResource.addResource('vip-contacts');
    vipContactsResource.addMethod('GET', preferencesIntegration);
    vipContactsResource.addMethod('PUT', preferencesIntegration);
  }

  private createEventProcessing(): void {
    // Create SQS queue for periodic calendar scanning
    this.periodicScanQueue = new sqs.Queue(this, 'PeriodicScanQueue', {
      queueName: 'meeting-agent-periodic-scan',
      visibilityTimeout: cdk.Duration.minutes(6), // Longer than Lambda timeout
      retentionPeriod: cdk.Duration.days(14),
      deadLetterQueue: {
        queue: new sqs.Queue(this, 'PeriodicScanDLQ', {
          queueName: 'meeting-agent-periodic-scan-dlq',
          retentionPeriod: cdk.Duration.days(14),
        }),
        maxReceiveCount: 3,
      },
    });

    // Add SQS event source to calendar handler
    this.calendarHandler.addEventSource(
      new lambdaEventSources.SqsEventSource(this.periodicScanQueue, {
        batchSize: 10,
        maxBatchingWindow: cdk.Duration.seconds(5),
      })
    );

    // Create EventBridge rule for periodic calendar scanning (every 15 minutes)
    const periodicScanRule = new events.Rule(this, 'PeriodicScanRule', {
      ruleName: 'meeting-agent-periodic-scan',
      description: 'Triggers periodic calendar scanning for conflict detection',
      schedule: events.Schedule.rate(cdk.Duration.minutes(15)),
    });

    // Add SQS queue as target for EventBridge rule
    periodicScanRule.addTarget(
      new targets.SqsQueue(this.periodicScanQueue, {
        message: events.RuleTargetInput.fromObject({
          action: 'periodic_scan',
          timestamp: events.EventField.fromPath('$.time'),
        }),
      })
    );

    // Create EventBridge rule for daily preference learning (every day at 2 AM)
    const dailyLearningRule = new events.Rule(this, 'DailyLearningRule', {
      ruleName: 'meeting-agent-daily-learning',
      description: 'Triggers daily preference learning and optimization',
      schedule: events.Schedule.cron({
        minute: '0',
        hour: '2',
        day: '*',
        month: '*',
        year: '*',
      }),
    });

    // Add agent handler as target for daily learning
    dailyLearningRule.addTarget(
      new targets.LambdaFunction(this.agentHandler, {
        event: events.RuleTargetInput.fromObject({
          action: 'daily_learning',
          timestamp: events.EventField.fromPath('$.time'),
        }),
      })
    );
  }

  private createOutputs(): void {
    new cdk.CfnOutput(this, 'RestApiUrl', {
      value: this.restApi.url,
      description: 'REST API Gateway endpoint URL',
      exportName: 'meeting-agent-api-url',
    });

    new cdk.CfnOutput(this, 'RestApiId', {
      value: this.restApi.restApiId,
      description: 'REST API Gateway ID',
      exportName: 'meeting-agent-api-id',
    });

    // Lambda function ARNs for monitoring
    new cdk.CfnOutput(this, 'AuthHandlerArn', {
      value: this.authHandler.functionArn,
      description: 'Auth handler Lambda function ARN',
      exportName: 'meeting-agent-auth-handler-arn',
    });

    new cdk.CfnOutput(this, 'AgentHandlerArn', {
      value: this.agentHandler.functionArn,
      description: 'Agent handler Lambda function ARN',
      exportName: 'meeting-agent-agent-handler-arn',
    });

    new cdk.CfnOutput(this, 'CalendarHandlerArn', {
      value: this.calendarHandler.functionArn,
      description: 'Calendar handler Lambda function ARN',
      exportName: 'meeting-agent-calendar-handler-arn',
    });
  }
}