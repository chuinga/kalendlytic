#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CoreStack } from './stacks/core-stack';
import { ApiStack } from './stacks/api-stack';
import { WebStack } from './stacks/web-stack';
import { MonitoringStack } from './stacks/monitoring-stack';

const app = new cdk.App();

// Get environment configuration from CDK context
const region = app.node.tryGetContext('kalendlytic:region') || 'eu-west-1';
const environment = app.node.tryGetContext('kalendlytic:environment') || 'dev';
const account = process.env.CDK_DEFAULT_ACCOUNT;

const env = {
  account,
  region,
};

// Stack naming convention: {project}-{environment}-{stack-name}
const stackPrefix = `kalendlytic-${environment}`;

// Core infrastructure stack (DynamoDB, Cognito, KMS, Secrets Manager)
const coreStack = new CoreStack(app, `${stackPrefix}-core`, {
  env,
  description: 'Core infrastructure for Kalendlytic - AI meeting scheduler',
  tags: {
    Project: 'kalendlytic',
    Environment: environment,
    Stack: 'core'
  }
});

// API infrastructure stack (API Gateway, Lambda functions, EventBridge)
const apiStack = new ApiStack(app, `${stackPrefix}-api`, {
  env,
  description: 'API infrastructure for Kalendlytic - AI meeting scheduler',
  coreStack,
  tags: {
    Project: 'kalendlytic',
    Environment: environment,
    Stack: 'api'
  }
});

// Web infrastructure stack (S3, CloudFront)
const webStack = new WebStack(app, `${stackPrefix}-web`, {
  env,
  description: 'Web infrastructure for Kalendlytic - AI meeting scheduler',
  apiStack,
  tags: {
    Project: 'kalendlytic',
    Environment: environment,
    Stack: 'web'
  }
});

// Monitoring infrastructure stack (CloudWatch, Alarms, Dashboards)
const monitoringStack = new MonitoringStack(app, `${stackPrefix}-monitoring`, {
  env,
  description: 'Monitoring infrastructure for Kalendlytic - AI meeting scheduler',
  coreStack,
  apiStack,
  webStack,
  tags: {
    Project: 'kalendlytic',
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