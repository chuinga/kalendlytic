import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { ApiStack } from './api-stack';

export interface WebStackProps extends cdk.StackProps {
  apiStack: ApiStack;
}

export class WebStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: WebStackProps) {
    super(scope, id, props);

    // TODO: Implement S3 bucket and CloudFront distribution
    // This will be implemented in task 2.3
  }
}