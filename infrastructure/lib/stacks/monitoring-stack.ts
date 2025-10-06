import * as cdk from 'aws-cdk-lib';
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
  constructor(scope: Construct, id: string, props: MonitoringStackProps) {
    super(scope, id, props);

    // TODO: Implement CloudWatch dashboards, metrics, and alarms
    // This will be implemented in task 9.3
  }
}