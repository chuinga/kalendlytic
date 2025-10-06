import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

export class CoreStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // TODO: Implement DynamoDB tables, KMS keys, Cognito User Pool, and Secrets Manager
    // This will be implemented in task 2.1
  }
}