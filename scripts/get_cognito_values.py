#!/usr/bin/env python3
"""
Alternative script to help extract Cognito values from CDK outputs
when AWS credentials are not available in the current session.
"""

import json
import os
import re

def extract_from_cdk_outputs():
    """Extract Cognito values from CDK output files."""
    
    # Check CDK output directory
    cdk_out_dir = "infrastructure/cdk.out"
    
    if not os.path.exists(cdk_out_dir):
        print("❌ CDK output directory not found. Run 'cdk deploy' first.")
        return None
    
    # Look for core stack template
    core_template_path = os.path.join(cdk_out_dir, "meeting-scheduling-agent-dev-core.template.json")
    
    if not os.path.exists(core_template_path):
        print("❌ Core stack template not found.")
        print("Available files in cdk.out:")
        for file in os.listdir(cdk_out_dir):
            if file.endswith('.json'):
                print(f"   {file}")
        return None
    
    try:
        with open(core_template_path, 'r') as f:
            template = json.load(f)
        
        # Extract outputs section
        outputs = template.get('Outputs', {})
        
        user_pool_id_output = None
        user_pool_client_id_output = None
        
        # Find the outputs
        for key, value in outputs.items():
            if 'UserPoolId' in key:
                user_pool_id_output = value
            elif 'UserPoolClientId' in key:
                user_pool_client_id_output = value
        
        if user_pool_id_output and user_pool_client_id_output:
            print("✅ Found Cognito outputs in CDK template:")
            print(f"   User Pool ID Output: {user_pool_id_output}")
            print(f"   Client ID Output: {user_pool_client_id_output}")
            
            # The actual values will be references, we need to resolve them
            # This is complex without deployment, so we'll provide instructions
            return {
                'user_pool_id_ref': user_pool_id_output,
                'user_pool_client_id_ref': user_pool_client_id_output
            }
        else:
            print("❌ Could not find Cognito outputs in template")
            return None
            
    except Exception as e:
        print(f"❌ Error reading CDK template: {e}")
        return None

def show_manual_instructions():
    """Show manual instructions for getting Cognito values."""
    
    print("\n" + "="*70)
    print("📋 MANUAL INSTRUCTIONS TO GET COGNITO VALUES")
    print("="*70)
    
    print("\n🔧 **Option 1: Using AWS CLI (if credentials are available)**")
    print("   aws cloudformation describe-stacks \\")
    print("     --stack-name meeting-scheduling-agent-dev-core \\")
    print("     --region eu-west-1 \\")
    print("     --query 'Stacks[0].Outputs'")
    
    print("\n🌐 **Option 2: Using AWS Console**")
    print("   1. Go to AWS CloudFormation console")
    print("   2. Select region: eu-west-1")
    print("   3. Find stack: meeting-scheduling-agent-dev-core")
    print("   4. Click on the stack name")
    print("   5. Go to 'Outputs' tab")
    print("   6. Look for:")
    print("      - UserPoolId")
    print("      - UserPoolClientId")
    
    print("\n🔧 **Option 3: Using CDK CLI**")
    print("   cd infrastructure")
    print("   cdk deploy meeting-scheduling-agent-dev-core --outputs-file outputs.json")
    print("   # Then check outputs.json file")
    
    print("\n📝 **Option 4: Direct Cognito Console**")
    print("   1. Go to AWS Cognito console")
    print("   2. Select region: eu-west-1")
    print("   3. Click 'User pools'")
    print("   4. Find pool: meeting-agent-users")
    print("   5. Copy the User Pool ID")
    print("   6. Go to 'App integration' tab")
    print("   7. Find client: meeting-agent-web-client")
    print("   8. Copy the Client ID")

def create_env_template():
    """Create a template showing what needs to be updated."""
    
    print("\n📝 **UPDATE YOUR .ENV FILE**")
    print("Replace these lines in your .env file:")
    print()
    print("# BEFORE (current placeholder values):")
    print("NEXT_PUBLIC_COGNITO_USER_POOL_ID=eu-west-1_xxxxxxxxx")
    print("NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx")
    print()
    print("# AFTER (replace with actual values):")
    print("NEXT_PUBLIC_COGNITO_USER_POOL_ID=eu-west-1_YourActualPoolId")
    print("NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=YourActualClientId")
    print()
    print("💡 The User Pool ID will start with 'eu-west-1_'")
    print("💡 The Client ID will be a long alphanumeric string")

def main():
    """Main function."""
    print("AWS Meeting Scheduling Agent - Cognito Value Extractor")
    print("=" * 60)
    
    print("This script helps you get the Cognito User Pool values needed")
    print("to fix the 'Auth UserPool not configured' issue.")
    print()
    
    # Try to extract from CDK outputs
    print("🔍 Checking CDK outputs...")
    cdk_result = extract_from_cdk_outputs()
    
    if cdk_result:
        print("\n✅ Found CDK template, but need deployed values...")
    
    # Show manual instructions
    show_manual_instructions()
    
    # Show env template
    create_env_template()
    
    print("\n" + "="*60)
    print("🎯 **SUMMARY**")
    print("="*60)
    print("Your Cognito User Pool is properly defined in the CDK infrastructure,")
    print("but your .env file needs the actual deployed values.")
    print()
    print("1. Use one of the methods above to get the actual values")
    print("2. Update your .env file with the real Cognito IDs")
    print("3. Restart your frontend development server")
    print()
    print("Once updated, your Auth UserPool will be properly configured! 🚀")

if __name__ == "__main__":
    main()