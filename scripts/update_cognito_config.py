#!/usr/bin/env python3
"""
Script to extract Cognito User Pool configuration from deployed AWS infrastructure
and update the .env file with the correct values.
"""

import boto3
import json
import os
import sys
import re
from typing import Dict, Optional

def get_stack_outputs(stack_name: str, region: str) -> Dict[str, str]:
    """Get CloudFormation stack outputs."""
    try:
        cf_client = boto3.client('cloudformation', region_name=region)
        
        response = cf_client.describe_stacks(StackName=stack_name)
        
        if not response['Stacks']:
            print(f"❌ Stack '{stack_name}' not found")
            return {}
        
        stack = response['Stacks'][0]
        outputs = {}
        
        if 'Outputs' in stack:
            for output in stack['Outputs']:
                outputs[output['OutputKey']] = output['OutputValue']
        
        return outputs
        
    except Exception as e:
        print(f"❌ Error getting stack outputs: {e}")
        return {}

def get_cognito_config(region: str) -> Optional[Dict[str, str]]:
    """Extract Cognito configuration from deployed infrastructure."""
    
    # Try to get from CloudFormation stack outputs
    stack_name = "meeting-scheduling-agent-dev-core"
    outputs = get_stack_outputs(stack_name, region)
    
    if outputs:
        user_pool_id = outputs.get('UserPoolId')
        user_pool_client_id = outputs.get('UserPoolClientId')
        
        if user_pool_id and user_pool_client_id:
            print(f"✅ Found Cognito config in stack outputs:")
            print(f"   User Pool ID: {user_pool_id}")
            print(f"   Client ID: {user_pool_client_id}")
            
            return {
                'user_pool_id': user_pool_id,
                'user_pool_client_id': user_pool_client_id
            }
    
    # Fallback: Try to find Cognito resources directly
    print("🔍 Searching for Cognito User Pools directly...")
    
    try:
        cognito_client = boto3.client('cognito-idp', region_name=region)
        
        # List user pools
        response = cognito_client.list_user_pools(MaxResults=50)
        
        # Look for our user pool by name
        target_pool_name = "meeting-agent-users"
        
        for pool in response['UserPools']:
            if pool['Name'] == target_pool_name:
                user_pool_id = pool['Id']
                
                # Get user pool clients
                clients_response = cognito_client.list_user_pool_clients(
                    UserPoolId=user_pool_id,
                    MaxResults=50
                )
                
                # Look for our client
                target_client_name = "meeting-agent-web-client"
                
                for client in clients_response['UserPoolClients']:
                    if client['ClientName'] == target_client_name:
                        user_pool_client_id = client['ClientId']
                        
                        print(f"✅ Found Cognito resources:")
                        print(f"   User Pool ID: {user_pool_id}")
                        print(f"   Client ID: {user_pool_client_id}")
                        
                        return {
                            'user_pool_id': user_pool_id,
                            'user_pool_client_id': user_pool_client_id
                        }
        
        print(f"❌ Could not find User Pool '{target_pool_name}' or Client '{target_client_name}'")
        return None
        
    except Exception as e:
        print(f"❌ Error searching for Cognito resources: {e}")
        return None

def update_env_file(cognito_config: Dict[str, str], env_file_path: str = '.env') -> bool:
    """Update the .env file with Cognito configuration."""
    
    try:
        # Read current .env file
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                content = f.read()
        else:
            print(f"❌ .env file not found at {env_file_path}")
            return False
        
        # Update Cognito values
        user_pool_id = cognito_config['user_pool_id']
        user_pool_client_id = cognito_config['user_pool_client_id']
        
        # Replace placeholder values
        content = re.sub(
            r'NEXT_PUBLIC_COGNITO_USER_POOL_ID=.*',
            f'NEXT_PUBLIC_COGNITO_USER_POOL_ID={user_pool_id}',
            content
        )
        
        content = re.sub(
            r'NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=.*',
            f'NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID={user_pool_client_id}',
            content
        )
        
        # Write updated content back
        with open(env_file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {env_file_path} with Cognito configuration")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def verify_aws_credentials() -> bool:
    """Verify AWS credentials are configured."""
    try:
        sts_client = boto3.client('sts')
        response = sts_client.get_caller_identity()
        
        print(f"✅ AWS credentials verified:")
        print(f"   Account: {response.get('Account')}")
        print(f"   User/Role: {response.get('Arn', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        print("\n💡 To configure AWS credentials:")
        print("   aws configure")
        print("   # Or set environment variables:")
        print("   # export AWS_ACCESS_KEY_ID=your_key")
        print("   # export AWS_SECRET_ACCESS_KEY=your_secret")
        print("   # export AWS_DEFAULT_REGION=eu-west-1")
        
        return False

def main():
    """Main function."""
    print("AWS Meeting Scheduling Agent - Cognito Configuration Updater")
    print("=" * 65)
    
    # Get region from environment or use default
    region = os.environ.get('AWS_REGION', 'eu-west-1')
    print(f"🌍 Using AWS region: {region}")
    
    # Verify AWS credentials
    if not verify_aws_credentials():
        return 1
    
    # Get Cognito configuration
    print("\n🔍 Extracting Cognito configuration...")
    cognito_config = get_cognito_config(region)
    
    if not cognito_config:
        print("\n❌ Could not find Cognito configuration")
        print("\n💡 Possible solutions:")
        print("   1. Ensure the infrastructure is deployed: cd infrastructure && cdk deploy")
        print("   2. Check the stack name matches: meeting-scheduling-agent-dev-core")
        print("   3. Verify you're using the correct AWS region")
        return 1
    
    # Update .env file
    print("\n📝 Updating .env file...")
    if update_env_file(cognito_config):
        print("\n🎉 Cognito configuration updated successfully!")
        print("\n📋 Updated values:")
        print(f"   NEXT_PUBLIC_COGNITO_USER_POOL_ID={cognito_config['user_pool_id']}")
        print(f"   NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID={cognito_config['user_pool_client_id']}")
        
        print("\n✅ Your Auth UserPool is now properly configured!")
        print("\n🚀 Next steps:")
        print("   1. Restart your frontend development server")
        print("   2. Test authentication in your application")
        
        return 0
    else:
        print("\n❌ Failed to update .env file")
        return 1

if __name__ == "__main__":
    sys.exit(main())