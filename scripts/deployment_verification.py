#!/usr/bin/env python3
"""
Deployment Verification Script for AWS Meeting Scheduling Agent

This script verifies that all AWS resources are properly deployed and configured.
"""

import argparse
import boto3
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

class DeploymentVerifier:
    """Comprehensive deployment verification for the meeting scheduling agent."""
    
    def __init__(self, region: str = "eu-west-1", stack_prefix: str = "MeetingScheduler"):
        self.region = region
        self.stack_prefix = stack_prefix
        
        # Initialize AWS clients
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.apigateway = boto3.client('apigateway', region_name=region)
        self.cognito_idp = boto3.client('cognito-idp', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.cloudfront = boto3.client('cloudfront', region_name=region)
        self.secretsmanager = boto3.client('secretsmanager', region_name=region)
        self.bedrock = boto3.client('bedrock', region_name=region)
        
        self.verification_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'region': region,
            'stack_prefix': stack_prefix,
            'checks': {},
            'overall_status': 'UNKNOWN'
        }

    def verify_cloudformation_stacks(self) -> bool:
        """Verify CloudFormation stacks are deployed and in good state."""
        try:
            stacks = self.cloudformation.list_stacks(
                StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE']
            )
            
            relevant_stacks = [
                stack for stack in stacks['StackSummaries']
                if self.stack_prefix.lower() in stack['StackName'].lower()
            ]
            
            if not relevant_stacks:
                self.verification_results['checks']['cloudformation'] = {
                    'status': 'FAILED',
                    'message': f'No stacks found with prefix {self.stack_prefix}'
                }
                return False
            
            self.verification_results['checks']['cloudformation'] = {
                'status': 'PASSED',
                'stacks': [stack['StackName'] for stack in relevant_stacks],
                'count': len(relevant_stacks)
            }
            return True
            
        except Exception as e:
            self.verification_results['checks']['cloudformation'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return False

    def verify_dynamodb_tables(self) -> bool:
        """Verify DynamoDB tables exist and are active."""
        expected_tables = [
            'Users', 'Connections', 'Calendars', 'Meetings', 
            'Preferences', 'Priorities', 'AgentLogs'
        ]
        
        try:
            tables = self.dynamodb.list_tables()['TableNames']
            
            found_tables = []
            missing_tables = []
            
            for expected_table in expected_tables:
                # Look for tables that contain the expected name (accounting for prefixes)
                matching_tables = [t for t in tables if expected_table.lower() in t.lower()]
                if matching_tables:
                    found_tables.extend(matching_tables)
                else:
                    missing_tables.append(expected_table)
            
            if missing_tables:
                self.verification_results['checks']['dynamodb'] = {
                    'status': 'FAILED',
                    'found_tables': found_tables,
                    'missing_tables': missing_tables
                }
                return False
            
            self.verification_results['checks']['dynamodb'] = {
                'status': 'PASSED',
                'tables': found_tables
            }
            return True
            
        except Exception as e:
            self.verification_results['checks']['dynamodb'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return False

    def verify_lambda_functions(self) -> bool:
        """Verify Lambda functions are deployed."""
        try:
            functions = self.lambda_client.list_functions()['Functions']
            
            # Look for functions related to meeting scheduling
            relevant_functions = [
                func for func in functions
                if any(keyword in func['FunctionName'].lower() 
                      for keyword in ['meeting', 'schedule', 'oauth', 'agent'])
            ]
            
            if not relevant_functions:
                self.verification_results['checks']['lambda'] = {
                    'status': 'FAILED',
                    'message': 'No relevant Lambda functions found'
                }
                return False
            
            self.verification_results['checks']['lambda'] = {
                'status': 'PASSED',
                'functions': [func['FunctionName'] for func in relevant_functions],
                'count': len(relevant_functions)
            }
            return True
            
        except Exception as e:
            self.verification_results['checks']['lambda'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return False

    def verify_api_gateway(self) -> bool:
        """Verify API Gateway is deployed and accessible."""
        try:
            apis = self.apigateway.get_rest_apis()['items']
            
            # Look for APIs related to meeting scheduling
            relevant_apis = [
                api for api in apis
                if any(keyword in api['name'].lower() 
                      for keyword in ['meeting', 'schedule', 'agent'])
            ]
            
            if not relevant_apis:
                self.verification_results['checks']['apigateway'] = {
                    'status': 'FAILED',
                    'message': 'No relevant API Gateway found'
                }
                return False
            
            self.verification_results['checks']['apigateway'] = {
                'status': 'PASSED',
                'apis': [{'name': api['name'], 'id': api['id']} for api in relevant_apis]
            }
            return True
            
        except Exception as e:
            self.verification_results['checks']['apigateway'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return False

    def verify_cognito_user_pool(self) -> bool:
        """Verify Cognito User Pool is configured."""
        try:
            user_pools = self.cognito_idp.list_user_pools(MaxResults=50)['UserPools']
            
            # Look for user pools related to meeting scheduling
            relevant_pools = [
                pool for pool in user_pools
                if any(keyword in pool['Name'].lower() 
                      for keyword in ['meeting', 'schedule', 'agent'])
            ]
            
            if not relevant_pools:
                self.verification_results['checks']['cognito'] = {
                    'status': 'FAILED',
                    'message': 'No relevant Cognito User Pool found'
                }
                return False
            
            self.verification_results['checks']['cognito'] = {
                'status': 'PASSED',
                'user_pools': [{'name': pool['Name'], 'id': pool['Id']} for pool in relevant_pools]
            }
            return True
            
        except Exception as e:
            self.verification_results['checks']['cognito'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return False

    def verify_bedrock_access(self) -> bool:
        """Verify Bedrock model access."""
        try:
            # Try to list foundation models to verify access
            models = self.bedrock.list_foundation_models()
            
            # Check for specific models we use
            model_ids = [model['modelId'] for model in models['modelSummaries']]
            required_models = ['amazon.nova-pro-v1:0']
            
            available_models = [model for model in required_models if model in model_ids]
            
            if not available_models:
                self.verification_results['checks']['bedrock'] = {
                    'status': 'FAILED',
                    'message': 'Required Bedrock models not available',
                    'required_models': required_models,
                    'available_models': available_models
                }
                return False
            
            self.verification_results['checks']['bedrock'] = {
                'status': 'PASSED',
                'available_models': available_models
            }
            return True
            
        except Exception as e:
            self.verification_results['checks']['bedrock'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return False

    def run_all_verifications(self) -> bool:
        """Run all verification checks."""
        print(f"🔍 Starting deployment verification for region: {self.region}")
        print(f"📋 Stack prefix: {self.stack_prefix}")
        print("-" * 60)
        
        checks = [
            ("CloudFormation Stacks", self.verify_cloudformation_stacks),
            ("DynamoDB Tables", self.verify_dynamodb_tables),
            ("Lambda Functions", self.verify_lambda_functions),
            ("API Gateway", self.verify_api_gateway),
            ("Cognito User Pool", self.verify_cognito_user_pool),
            ("Bedrock Access", self.verify_bedrock_access),
        ]
        
        all_passed = True
        
        for check_name, check_function in checks:
            print(f"Checking {check_name}...", end=" ")
            try:
                result = check_function()
                if result:
                    print("✅ PASSED")
                else:
                    print("❌ FAILED")
                    all_passed = False
            except Exception as e:
                print(f"💥 ERROR: {str(e)}")
                all_passed = False
        
        print("-" * 60)
        
        if all_passed:
            print("🎉 All verification checks passed!")
            self.verification_results['overall_status'] = 'PASSED'
        else:
            print("❌ Some verification checks failed. Please review the issues above.")
            self.verification_results['overall_status'] = 'FAILED'
        
        return all_passed

    def save_report(self, output_file: str):
        """Save verification report to file."""
        with open(output_file, 'w') as f:
            json.dump(self.verification_results, f, indent=2)
        print(f"📄 Verification report saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Verify AWS Meeting Scheduling Agent deployment")
    parser.add_argument("--region", default="eu-west-1", help="AWS region")
    parser.add_argument("--stack-prefix", default="MeetingScheduler", help="CloudFormation stack prefix")
    parser.add_argument("--output", default="verification_report.json", help="Output file for verification report")
    
    args = parser.parse_args()
    
    verifier = DeploymentVerifier(region=args.region, stack_prefix=args.stack_prefix)
    
    success = verifier.run_all_verifications()
    
    verifier.save_report(args.output)
    
    if success:
        print("\n✅ DEPLOYMENT VERIFICATION PASSED")
        return 0
    else:
        print("\n❌ DEPLOYMENT VERIFICATION FAILED")
        print("Please review the issues above and redeploy as needed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())