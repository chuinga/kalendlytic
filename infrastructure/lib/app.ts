#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CoreStack } from './stacks/core-stack';
import { ApiStack } from './stacks/api-stack';
import { WebStack } from './stacks/web-stack';
import { MonitoringStack } from './stacks/monitoring-stack';

const app = new cdk.App();

// Get environment configuration from CDK context
const region = app.node.tryGetContext('meeting-scheduling-agent:region') || 'us-east-1';
const environment = app.node.tryGetContext('meeting-scheduling-agent:environment') || 'dev';
const account = process.env.CDK_DEFAULT_ACCOUNT;

const env = {
  account,
  region,
};

// Stack naming convention: {project}-{environment}-{stack-name}
const stackPrefix = `meeting-scheduling-agent-${environment}`;

// Core infrastructure stack (DynamoDB, Cognito, KMS, Secrets Manager)
const coreStack = new CoreStack(app, `${stackPrefix}-core`, {
  env,
  description: 'Core infrastructure for AWS Meeting Scheduling Agent',
  tags: {
    Project: 'meeting-scheduling-agent',
    Environment: environment,
    Stack: 'core'
  }
});

// API infrastructure stack (API Gateway, Lambda functions, EventBridge)
const apiStack = new ApiStack(app, `${stackPrefix}-api`, {
  env,
  description: 'API infrastructure for AWS Meeting Scheduling Agent',
  coreStack,
  tags: {
    Project: 'meeting-scheduling-agent',
    Environment: environment,
    Stack: 'api'
  }
});

// Web infrastructure stack (S3, CloudFront)
const webStack = new WebStack(app, `${stackPrefix}-web`, {
  env,
  description: 'Web infrastructure for AWS Meeting Scheduling Agent',
  apiStack,
  tags: {
    Project: 'meeting-scheduling-agent',
    Environment: environment,
    Stack: 'web'
  }
});

// Monitoring infrastructure stack (CloudWatch, Alarms, Dashboards)
const monitoringStack = new MonitoringStack(app, `${stackPrefix}-monitoring`, {
  env,
  description: 'Monitoring infrastructure for AWS Meeting Scheduling Agent',
  coreStack,
  apiStack,
  webStack,
  tags: {
    Project: 'meeting-scheduling-agent',
    Environment: environment,
    Stack: 'monitoring'
  }
});

// Add stack dependencies
apiStack.addDependency(coreStack);
webStack.addDependency(apiStack);
monitoringStack.addDependency(coreStack);
monitoringStack.addDependency(apiStack);
monitoringStack.addDependency(webStack);