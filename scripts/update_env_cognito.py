#!/usr/bin/env python3
"""
Simple script to update .env file with Cognito values
Usage: python scripts/update_env_cognito.py <user_pool_id> <client_id>
"""

import sys
import re
import os

def update_env_file(user_pool_id: str, client_id: str, env_file_path: str = '.env') -> bool:
    """Update the .env file with Cognito configuration."""
    
    try:
        # Validate inputs
        if not user_pool_id.startswith('eu-west-1_'):
            print(f"⚠️  Warning: User Pool ID should start with 'eu-west-1_', got: {user_pool_id}")
        
        if len(client_id) < 20:
            print(f"⚠️  Warning: Client ID seems too short, got: {client_id}")
        
        # Read current .env file
        if not os.path.exists(env_file_path):
            print(f"❌ .env file not found at {env_file_path}")
            return False
        
        with open(env_file_path, 'r') as f:
            content = f.read()
        
        # Show current values
        current_pool_match = re.search(r'NEXT_PUBLIC_COGNITO_USER_POOL_ID=(.*)', content)
        current_client_match = re.search(r'NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=(.*)', content)
        
        if current_pool_match:
            print(f"📋 Current User Pool ID: {current_pool_match.group(1)}")
        if current_client_match:
            print(f"📋 Current Client ID: {current_client_match.group(1)}")
        
        # Update Cognito values
        content = re.sub(
            r'NEXT_PUBLIC_COGNITO_USER_POOL_ID=.*',
            f'NEXT_PUBLIC_COGNITO_USER_POOL_ID={user_pool_id}',
            content
        )
        
        content = re.sub(
            r'NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID=.*',
            f'NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID={client_id}',
            content
        )
        
        # Write updated content back
        with open(env_file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated {env_file_path} with new Cognito configuration:")
        print(f"   NEXT_PUBLIC_COGNITO_USER_POOL_ID={user_pool_id}")
        print(f"   NEXT_PUBLIC_COGNITO_USER_POOL_CLIENT_ID={client_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def main():
    """Main function."""
    if len(sys.argv) != 3:
        print("AWS Meeting Scheduling Agent - .env Cognito Updater")
        print("=" * 55)
        print()
        print("Usage:")
        print("  python scripts/update_env_cognito.py <user_pool_id> <client_id>")
        print()
        print("Example:")
        print("  python scripts/update_env_cognito.py eu-west-1_abc123def 1a2b3c4d5e6f7g8h9i0j")
        print()
        print("💡 Get these values from:")
        print("   - AWS CloudFormation console (stack outputs)")
        print("   - AWS Cognito console")
        print("   - AWS CLI: aws cloudformation describe-stacks")
        return 1
    
    user_pool_id = sys.argv[1]
    client_id = sys.argv[2]
    
    print("AWS Meeting Scheduling Agent - .env Cognito Updater")
    print("=" * 55)
    print(f"🔧 Updating .env with:")
    print(f"   User Pool ID: {user_pool_id}")
    print(f"   Client ID: {client_id}")
    print()
    
    if update_env_file(user_pool_id, client_id):
        print("\n🎉 Auth UserPool configuration updated successfully!")
        print("\n🚀 Next steps:")
        print("   1. Restart your frontend development server")
        print("   2. Test authentication in your application")
        print("   3. The 'Auth UserPool not configured' error should be resolved")
        return 0
    else:
        print("\n❌ Failed to update .env file")
        return 1

if __name__ == "__main__":
    sys.exit(main())