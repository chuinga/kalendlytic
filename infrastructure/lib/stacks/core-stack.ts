import * as cdk from 'aws-cdk-lib';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as path from 'path';
import { Construct } from 'constructs';

export interface CoreStackProps extends cdk.StackProps {
  // Additional props can be added here if needed
}

export class CoreStack extends cdk.Stack {
  // Public properties for other stacks to reference
  public userPool: cognito.UserPool;
  public userPoolClient: cognito.UserPoolClient;
  public identityPool: cognito.CfnIdentityPool;
  public dataEncryptionKey: kms.Key;
  public tokenEncryptionKey: kms.Key;
  public usersTable: dynamodb.Table;
  public connectionsTable: dynamodb.Table;
  public preferencesTable: dynamodb.Table;
  public meetingsTable: dynamodb.Table;
  public agentRunsTable: dynamodb.Table;
  public auditLogsTable: dynamodb.Table;
  public googleOAuthSecret: secretsmanager.Secret;
  public microsoftOAuthSecret: secretsmanager.Secret;
  public cognitoTriggersFunction: lambda.Function;

  constructor(scope: Construct, id: string, props?: CoreStackProps) {
    super(scope, id, props);

    // Create KMS keys for encryption
    this.createKMSKeys();
    
    // Create DynamoDB tables
    this.createDynamoDBTables();
    
    // Create Lambda functions for Cognito triggers
    this.createCognitoTriggerFunction();
    
    // Create Cognito User Pool and Identity Pool
    this.createCognitoResources();
    
    // Create Secrets Manager secrets for OAuth credentials
    this.createSecretsManagerSecrets();
    
    // Output important values
    this.createOutputs();
  }

  private createKMSKeys(): void {
    // KMS key for general data encryption (DynamoDB, etc.)
    this.dataEncryptionKey = new kms.Key(this, 'DataEncryptionKey', {
      description: 'KMS key for encrypting meeting scheduling agent data',
      enableKeyRotation: true,
      keySpec: kms.KeySpec.SYMMETRIC_DEFAULT,
      keyUsage: kms.KeyUsage.ENCRYPT_DECRYPT,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev environment
    });

    this.dataEncryptionKey.addAlias('alias/meeting-agent-data');

    // Separate KMS key for OAuth token encryption
    this.tokenEncryptionKey = new kms.Key(this, 'TokenEncryptionKey', {
      description: 'KMS key for encrypting OAuth tokens',
      enableKeyRotation: true,
      keySpec: kms.KeySpec.SYMMETRIC_DEFAULT,
      keyUsage: kms.KeyUsage.ENCRYPT_DECRYPT,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev environment
    });

    this.tokenEncryptionKey.addAlias('alias/meeting-agent-tokens');
  }

  private createDynamoDBTables(): void {
    // Users table
    this.usersTable = new dynamodb.Table(this, 'UsersTable', {
      tableName: 'meeting-agent-users',
      partitionKey: {
        name: 'pk',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: this.dataEncryptionKey,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev environment
    });

    // Connections table for OAuth tokens
    this.connectionsTable = new dynamodb.Table(this, 'ConnectionsTable', {
      tableName: 'meeting-agent-connections',
      partitionKey: {
        name: 'pk',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: this.tokenEncryptionKey,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: 'ttl', // For automatic token cleanup
    });

    // Add GSI for querying by provider
    this.connectionsTable.addGlobalSecondaryIndex({
      indexName: 'provider-index',
      partitionKey: {
        name: 'provider',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'created_at',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // Preferences table
    this.preferencesTable = new dynamodb.Table(this, 'PreferencesTable', {
      tableName: 'meeting-agent-preferences',
      partitionKey: {
        name: 'pk',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: this.dataEncryptionKey,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Meetings table
    this.meetingsTable = new dynamodb.Table(this, 'MeetingsTable', {
      tableName: 'meeting-agent-meetings',
      partitionKey: {
        name: 'pk',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'sk',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: this.dataEncryptionKey,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Add GSI for querying meetings by date range
    this.meetingsTable.addGlobalSecondaryIndex({
      indexName: 'date-index',
      partitionKey: {
        name: 'pk',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'start',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // Agent runs table for tracking AI operations
    this.agentRunsTable = new dynamodb.Table(this, 'AgentRunsTable', {
      tableName: 'meeting-agent-runs',
      partitionKey: {
        name: 'pk',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: this.dataEncryptionKey,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: 'ttl', // For automatic cleanup of old runs
    });

    // Add GSI for querying runs by user
    this.agentRunsTable.addGlobalSecondaryIndex({
      indexName: 'user-index',
      partitionKey: {
        name: 'user_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'created_at',
        type: dynamodb.AttributeType.STRING,
      },
    });

    // Audit logs table
    this.auditLogsTable = new dynamodb.Table(this, 'AuditLogsTable', {
      tableName: 'meeting-agent-audit-logs',
      partitionKey: {
        name: 'pk',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'sk',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: this.dataEncryptionKey,
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: 'ttl', // For automatic cleanup of old logs
    });

    // Add GSI for querying logs by run ID
    this.auditLogsTable.addGlobalSecondaryIndex({
      indexName: 'run-index',
      partitionKey: {
        name: 'run_id',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'sk',
        type: dynamodb.AttributeType.STRING,
      },
    });
  }

  private createCognitoTriggerFunction(): void {
    // Create Lambda function for Cognito triggers
    this.cognitoTriggersFunction = new lambda.Function(this, 'CognitoTriggersFunction', {
      functionName: 'meeting-agent-cognito-triggers',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'cognito_triggers.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../../backend/src/lambda_functions')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        USERS_TABLE_NAME: this.usersTable.tableName,
        PREFERENCES_TABLE_NAME: this.preferencesTable.tableName,
        LOG_LEVEL: 'INFO'
      },
      description: 'Handles Cognito user lifecycle events and creates user profiles'
    });

    // Grant permissions to write to DynamoDB tables
    this.usersTable.grantWriteData(this.cognitoTriggersFunction);
    this.preferencesTable.grantWriteData(this.cognitoTriggersFunction);

    // Grant permissions for CloudWatch logging
    this.cognitoTriggersFunction.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        'logs:CreateLogGroup',
        'logs:CreateLogStream',
        'logs:PutLogEvents'
      ],
      resources: [`arn:aws:logs:${this.region}:${this.account}:log-group:/aws/lambda/meeting-agent-cognito-triggers:*`]
    }));
  }

  private createCognitoResources(): void {
    // Create Cognito User Pool
    this.userPool = new cognito.UserPool(this, 'UserPool', {
      userPoolName: 'meeting-agent-users',
      selfSignUpEnabled: true,
      signInAliases: {
        email: true,
      },
      autoVerify: {
        email: true,
      },
      standardAttributes: {
        email: {
          required: true,
          mutable: true,
        },
        givenName: {
          required: false,
          mutable: true,
        },
        familyName: {
          required: false,
          mutable: true,
        },
      },
      customAttributes: {
        timezone: new cognito.StringAttribute({
          minLen: 1,
          maxLen: 50,
          mutable: true,
        }),
      },
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: false,
      },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For dev environment
      lambdaTriggers: {
        postConfirmation: this.cognitoTriggersFunction,
        preSignUp: this.cognitoTriggersFunction,
      },
      userVerification: {
        emailSubject: 'Verify your AWS Meeting Scheduler account',
        emailBody: `<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;"><div style="background-color: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"><div style="text-align: center; margin-bottom: 30px;"><div style="display: inline-block; width: 64px; height: 64px; background-color: #2563eb; border-radius: 16px; margin-bottom: 16px; position: relative;"><svg style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 32px; height: 32px; fill: white;" viewBox="0 0 24 24"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z"/></svg></div><h1 style="color: #1f2937; margin: 0; font-size: 28px; font-weight: bold;">AWS Meeting Scheduler</h1><p style="color: #6b7280; margin: 8px 0 0 0; font-size: 16px;">AI-powered meeting management</p></div><div style="text-align: center; margin-bottom: 30px;"><h2 style="color: #1f2937; margin: 0 0 16px 0; font-size: 24px;">Verify Your Email Address</h2><p style="color: #4b5563; margin: 0; font-size: 16px; line-height: 1.5;">Welcome to AWS Meeting Scheduler! Please use the verification code below to complete your account setup.</p></div><div style="background-color: #f3f4f6; padding: 24px; border-radius: 8px; text-align: center; margin-bottom: 30px;"><p style="color: #374151; margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">Your verification code:</p><div style="font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; color: #2563eb; letter-spacing: 8px; margin: 16px 0;">{####}</div><p style="color: #6b7280; margin: 0; font-size: 12px;">This code will expire in 24 hours</p></div><div style="text-align: center; margin-bottom: 30px;"><p style="color: #4b5563; margin: 0 0 16px 0; font-size: 14px; line-height: 1.5;">Click the button below to open the verification page and enter your code:</p><a href="https://d1tveh74k4yy31.cloudfront.net/verify?email={email}" style="display: inline-block; background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">Verify Email Address</a></div><div style="border-top: 1px solid #e5e7eb; padding-top: 20px; text-align: center;"><p style="color: #9ca3af; margin: 0; font-size: 12px;">If you didn't create an account with AWS Meeting Scheduler, you can safely ignore this email.</p><p style="color: #9ca3af; margin: 8px 0 0 0; font-size: 12px;">© 2024 AWS Meeting Scheduler. All rights reserved.</p></div></div></div>`,
        emailStyle: cognito.VerificationEmailStyle.CODE,
      },
    });

    // Add custom email configuration using L1 construct for more control
    const cfnUserPool = this.userPool.node.defaultChild as cognito.CfnUserPool;
    cfnUserPool.emailConfiguration = {
      emailSendingAccount: 'COGNITO_DEFAULT',
    };

    // Create User Pool Client
    this.userPoolClient = this.userPool.addClient('UserPoolClient', {
      userPoolClientName: 'meeting-agent-web-client',
      generateSecret: false, // For SPA applications
      authFlows: {
        userSrp: true,
        userPassword: false, // Disable less secure flows
        adminUserPassword: false,
      },
      oAuth: {
        flows: {
          authorizationCodeGrant: true,
        },
        scopes: [
          cognito.OAuthScope.EMAIL,
          cognito.OAuthScope.OPENID,
          cognito.OAuthScope.PROFILE,
        ],
        callbackUrls: [
          'http://localhost:3000/auth/callback', // For local development
          // Production URLs will be added via environment variables
        ],
        logoutUrls: [
          'http://localhost:3000/auth/logout',
        ],
      },
      preventUserExistenceErrors: true,
      refreshTokenValidity: cdk.Duration.days(30),
      accessTokenValidity: cdk.Duration.hours(1),
      idTokenValidity: cdk.Duration.hours(1),
    });

    // Create Identity Pool for AWS resource access
    this.identityPool = new cognito.CfnIdentityPool(this, 'IdentityPool', {
      identityPoolName: 'meeting-agent-identity-pool',
      allowUnauthenticatedIdentities: false,
      cognitoIdentityProviders: [
        {
          clientId: this.userPoolClient.userPoolClientId,
          providerName: this.userPool.userPoolProviderName,
        },
      ],
    });

    // Create IAM role for authenticated users
    const authenticatedRole = new iam.Role(this, 'AuthenticatedRole', {
      assumedBy: new iam.FederatedPrincipal(
        'cognito-identity.amazonaws.com',
        {
          StringEquals: {
            'cognito-identity.amazonaws.com:aud': this.identityPool.ref,
          },
          'ForAnyValue:StringLike': {
            'cognito-identity.amazonaws.com:amr': 'authenticated',
          },
        },
        'sts:AssumeRoleWithWebIdentity'
      ),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonCognitoPowerUser'),
      ],
    });

    // Attach the role to the identity pool
    new cognito.CfnIdentityPoolRoleAttachment(this, 'IdentityPoolRoleAttachment', {
      identityPoolId: this.identityPool.ref,
      roles: {
        authenticated: authenticatedRole.roleArn,
      },
    });
  }

  private createSecretsManagerSecrets(): void {
    // Google OAuth credentials
    this.googleOAuthSecret = new secretsmanager.Secret(this, 'GoogleOAuthSecret', {
      secretName: 'meeting-agent/oauth/google',
      description: 'Google OAuth 2.0 client credentials for calendar and Gmail access',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({
          client_id: '',
          client_secret: '',
          redirect_uris: ['http://localhost:3000/auth/google/callback'],
        }),
        generateStringKey: 'placeholder',
        excludeCharacters: '"@/\\',
      },
      encryptionKey: this.tokenEncryptionKey,
    });

    // Microsoft OAuth credentials
    this.microsoftOAuthSecret = new secretsmanager.Secret(this, 'MicrosoftOAuthSecret', {
      secretName: 'meeting-agent/oauth/microsoft',
      description: 'Microsoft Graph OAuth 2.0 client credentials for calendar and mail access',
      generateSecretString: {
        secretStringTemplate: JSON.stringify({
          client_id: '',
          client_secret: '',
          tenant_id: '',
          redirect_uris: ['http://localhost:3000/auth/microsoft/callback'],
        }),
        generateStringKey: 'placeholder',
        excludeCharacters: '"@/\\',
      },
      encryptionKey: this.tokenEncryptionKey,
    });

    // Grant read access to secrets for Lambda functions (will be used in API stack)
    // This policy will be referenced by other stacks through the public properties
  }

  private createOutputs(): void {
    // Cognito outputs
    new cdk.CfnOutput(this, 'UserPoolId', {
      value: this.userPool.userPoolId,
      description: 'Cognito User Pool ID',
      exportName: 'meeting-agent-user-pool-id',
    });

    new cdk.CfnOutput(this, 'UserPoolClientId', {
      value: this.userPoolClient.userPoolClientId,
      description: 'Cognito User Pool Client ID',
      exportName: 'meeting-agent-user-pool-client-id',
    });

    new cdk.CfnOutput(this, 'IdentityPoolId', {
      value: this.identityPool.ref,
      description: 'Cognito Identity Pool ID',
      exportName: 'meeting-agent-identity-pool-id',
    });

    // DynamoDB table outputs
    new cdk.CfnOutput(this, 'UsersTableName', {
      value: this.usersTable.tableName,
      description: 'Users DynamoDB table name',
      exportName: 'meeting-agent-users-table',
    });

    new cdk.CfnOutput(this, 'ConnectionsTableName', {
      value: this.connectionsTable.tableName,
      description: 'Connections DynamoDB table name',
      exportName: 'meeting-agent-connections-table',
    });

    new cdk.CfnOutput(this, 'PreferencesTableName', {
      value: this.preferencesTable.tableName,
      description: 'Preferences DynamoDB table name',
      exportName: 'meeting-agent-preferences-table',
    });

    new cdk.CfnOutput(this, 'MeetingsTableName', {
      value: this.meetingsTable.tableName,
      description: 'Meetings DynamoDB table name',
      exportName: 'meeting-agent-meetings-table',
    });

    new cdk.CfnOutput(this, 'AgentRunsTableName', {
      value: this.agentRunsTable.tableName,
      description: 'Agent Runs DynamoDB table name',
      exportName: 'meeting-agent-runs-table',
    });

    new cdk.CfnOutput(this, 'AuditLogsTableName', {
      value: this.auditLogsTable.tableName,
      description: 'Audit Logs DynamoDB table name',
      exportName: 'meeting-agent-audit-logs-table',
    });

    // KMS key outputs
    new cdk.CfnOutput(this, 'DataEncryptionKeyId', {
      value: this.dataEncryptionKey.keyId,
      description: 'Data encryption KMS key ID',
      exportName: 'meeting-agent-data-key-id',
    });

    new cdk.CfnOutput(this, 'TokenEncryptionKeyId', {
      value: this.tokenEncryptionKey.keyId,
      description: 'Token encryption KMS key ID',
      exportName: 'meeting-agent-token-key-id',
    });

    // Secrets Manager outputs
    new cdk.CfnOutput(this, 'GoogleOAuthSecretArn', {
      value: this.googleOAuthSecret.secretArn,
      description: 'Google OAuth secret ARN',
      exportName: 'meeting-agent-google-oauth-secret',
    });

    new cdk.CfnOutput(this, 'MicrosoftOAuthSecretArn', {
      value: this.microsoftOAuthSecret.secretArn,
      description: 'Microsoft OAuth secret ARN',
      exportName: 'meeting-agent-microsoft-oauth-secret',
    });

    // Lambda function outputs
    new cdk.CfnOutput(this, 'CognitoTriggersFunctionArn', {
      value: this.cognitoTriggersFunction.functionArn,
      description: 'Cognito triggers Lambda function ARN',
      exportName: 'meeting-agent-cognito-triggers-function',
    });
  }
}