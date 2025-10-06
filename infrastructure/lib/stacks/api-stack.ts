import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { CoreStack } from './core-stack';

export interface ApiStackProps extends cdk.StackProps {
  coreStack: CoreStack;
}

export class ApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);

    // TODO: Implement API Gateway, Lambda functions, and EventBridge
    // This will be implemented in task 2.2
  }
}