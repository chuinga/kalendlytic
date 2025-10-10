#!/usr/bin/env python3
"""
Interactive OAuth credentials setup script
"""

import json
import os
import subprocess
import sys
from typing import Dict, Any

class OAuthSetup:
    def __init__(self):
        self.credentials = {
            "google": {},
            "microsoft": {}
        }
        
    def welcome(self):
        """Show welcome message."""
        print("🔐 OAuth Credentials Setup for Meeting Scheduler")
        print("="*60)
        print("This script will help you configure Google and Microsoft OAuth")
        print("credentials for calendar integration.")
        print()
        
    def setup_google_oauth(self):
        """Interactive Google OAuth setup."""
        print("🟦 **Google Calendar OAuth Setup**")
        print("-" * 40)
        
        print("\n📋 **Prerequisites:**")
        print("1. Google Cloud Console account")
        print("2. Project created with Calendar API enabled")
        print("3. OAuth consent screen configured")
        print("4. OAuth 2.0 credentials created")
        print()
        
        print("📖 **Detailed instructions:** https://console.cloud.google.com/")
        print("   - Go to APIs & Services → Credentials")
        print("   - Create OAuth 2.0 Client ID")
        print("   - Application type: Web application")
        print()
        
        # Get Google credentials
        print("🔑 **Enter your Google OAuth credentials:**")
        
        client_id = input("Google Client ID: ").strip()
        if not client_id:
            print("❌ Client ID is required")
            return False
            
        client_secret = input("Google Client Secret: ").strip()
        if not client_secret:
            print("❌ Client Secret is required")
            return False
        
        # Validate format
        if not client_id.endswith('.apps.googleusercontent.com'):
            print("⚠️ Warning: Google Client ID should end with '.apps.googleusercontent.com'")
        
        self.credentials["google"] = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        print("✅ Google OAuth credentials saved")
        return True
    
    def setup_microsoft_oauth(self):
        """Interactive Microsoft OAuth setup."""
        print("\n🟦 **Microsoft Outlook OAuth Setup**")
        print("-" * 40)
        
        print("\n📋 **Prerequisites:**")
        print("1. Azure Portal account")
        print("2. App registration created")
        print("3. API permissions configured (Calendar.ReadWrite, User.Read)")
        print("4. Client secret created")
        print()
        
        print("📖 **Detailed instructions:** https://portal.azure.com/")
        print("   - Go to App registrations")
        print("   - Create new registration")
        print("   - Add Microsoft Graph permissions")
        print()
        
        # Get Microsoft credentials
        print("🔑 **Enter your Microsoft OAuth credentials:**")
        
        client_id = input("Microsoft Client ID (Application ID): ").strip()
        if not client_id:
            print("❌ Client ID is required")
            return False
            
        client_secret = input("Microsoft Client Secret: ").strip()
        if not client_secret:
            print("❌ Client Secret is required")
            return False
        
        # Validate format (Microsoft client IDs are UUIDs)
        if len(client_id) != 36 or client_id.count('-') != 4:
            print("⚠️ Warning: Microsoft Client ID should be a UUID format")
        
        self.credentials["microsoft"] = {
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        print("✅ Microsoft OAuth credentials saved")
        return True
    
    def update_env_file(self):
        """Update .env file with OAuth credentials."""
        print("\n⚙️ **Updating Environment Configuration**")
        print("-" * 40)
        
        env_file = ".env"
        env_lines = []
        
        # Read existing .env file
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                env_lines = f.readlines()
        
        # Remove existing OAuth entries
        env_lines = [line for line in env_lines if not any(
            oauth_key in line for oauth_key in [
                'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET',
                'MICROSOFT_CLIENT_ID', 'MICROSOFT_CLIENT_SECRET',
                'NEXT_PUBLIC_GOOGLE_CLIENT_ID', 'NEXT_PUBLIC_MICROSOFT_CLIENT_ID'
            ]
        )]
        
        # Add OAuth configuration section
        oauth_config = [
            "\n# OAuth Configuration\n",
            f"GOOGLE_CLIENT_ID={self.credentials['google'].get('client_id', '')}\n",
            f"GOOGLE_CLIENT_SECRET={self.credentials['google'].get('client_secret', '')}\n",
            f"MICROSOFT_CLIENT_ID={self.credentials['microsoft'].get('client_id', '')}\n",
            f"MICROSOFT_CLIENT_SECRET={self.credentials['microsoft'].get('client_secret', '')}\n",
            "\n# Frontend OAuth Configuration\n",
            f"NEXT_PUBLIC_GOOGLE_CLIENT_ID={self.credentials['google'].get('client_id', '')}\n",
            f"NEXT_PUBLIC_MICROSOFT_CLIENT_ID={self.credentials['microsoft'].get('client_id', '')}\n"
        ]
        
        # Write updated .env file
        with open(env_file, 'w') as f:
            f.writelines(env_lines)
            f.writelines(oauth_config)
        
        print(f"✅ Updated {env_file} with OAuth credentials")
        
        # Also update frontend .env.local
        frontend_env = os.path.join("frontend", ".env.local")
        frontend_config = [
            f"NEXT_PUBLIC_GOOGLE_CLIENT_ID={self.credentials['google'].get('client_id', '')}\n",
            f"NEXT_PUBLIC_MICROSOFT_CLIENT_ID={self.credentials['microsoft'].get('client_id', '')}\n"
        ]
        
        try:
            os.makedirs("frontend", exist_ok=True)
            with open(frontend_env, 'w') as f:
                f.writelines(frontend_config)
            print(f"✅ Updated {frontend_env} with frontend OAuth config")
        except Exception as e:
            print(f"⚠️ Could not update frontend config: {e}")
    
    def store_in_aws_secrets(self):
        """Store credentials in AWS Secrets Manager."""
        print("\n☁️ **AWS Secrets Manager Storage**")
        print("-" * 40)
        
        store_aws = input("Store credentials in AWS Secrets Manager? (y/N): ").strip().lower()
        if store_aws not in ['y', 'yes']:
            print("⏭️ Skipping AWS Secrets Manager storage")
            return
        
        try:
            # Store Google credentials
            if self.credentials["google"]:
                google_secret = json.dumps(self.credentials["google"])
                result = subprocess.run([
                    'aws', 'secretsmanager', 'create-secret',
                    '--name', 'google-oauth-credentials',
                    '--description', 'Google OAuth credentials for Meeting Scheduler',
                    '--secret-string', google_secret,
                    '--region', 'eu-west-1'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Google credentials stored in AWS Secrets Manager")
                else:
                    print(f"⚠️ Failed to store Google credentials: {result.stderr}")
            
            # Store Microsoft credentials
            if self.credentials["microsoft"]:
                microsoft_secret = json.dumps(self.credentials["microsoft"])
                result = subprocess.run([
                    'aws', 'secretsmanager', 'create-secret',
                    '--name', 'microsoft-oauth-credentials',
                    '--description', 'Microsoft OAuth credentials for Meeting Scheduler',
                    '--secret-string', microsoft_secret,
                    '--region', 'eu-west-1'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Microsoft credentials stored in AWS Secrets Manager")
                else:
                    print(f"⚠️ Failed to store Microsoft credentials: {result.stderr}")
                    
        except Exception as e:
            print(f"❌ Error storing credentials in AWS: {e}")
            print("💡 Make sure AWS CLI is configured and you have permissions")
    
    def test_oauth_setup(self):
        """Test OAuth configuration."""
        print("\n🧪 **Testing OAuth Configuration**")
        print("-" * 40)
        
        # Test Google OAuth
        if self.credentials["google"]:
            print("🟦 Testing Google OAuth configuration...")
            print(f"   Client ID: {self.credentials['google']['client_id'][:20]}...")
            print("   ✅ Google credentials configured")
        
        # Test Microsoft OAuth
        if self.credentials["microsoft"]:
            print("🟦 Testing Microsoft OAuth configuration...")
            print(f"   Client ID: {self.credentials['microsoft']['client_id'][:20]}...")
            print("   ✅ Microsoft credentials configured")
        
        print("\n💡 **Next Steps for Testing:**")
        print("1. Start your API server: cd backend && python simple_api_server.py")
        print("2. Start your frontend: cd frontend && npm run dev")
        print("3. Visit http://localhost:3000 and test OAuth flows")
        print("4. Check browser developer tools for any errors")
    
    def show_redirect_uris(self):
        """Show required redirect URIs for OAuth apps."""
        print("\n🔗 **Required Redirect URIs**")
        print("-" * 40)
        
        print("📋 **Add these redirect URIs to your OAuth applications:**")
        
        print("\n🟦 **Google Cloud Console:**")
        print("   Development:")
        print("   - http://localhost:3000/auth/google/callback")
        print("   - http://localhost:8000/connections/google/callback")
        print("   Production:")
        print("   - https://your-domain.com/auth/google/callback")
        print("   - https://your-api-id.execute-api.eu-west-1.amazonaws.com/connections/google/callback")
        
        print("\n🟦 **Azure Portal (App Registration):**")
        print("   Development:")
        print("   - http://localhost:3000/auth/microsoft/callback")
        print("   - http://localhost:8000/connections/microsoft/callback")
        print("   Production:")
        print("   - https://your-domain.com/auth/microsoft/callback")
        print("   - https://your-api-id.execute-api.eu-west-1.amazonaws.com/connections/microsoft/callback")
    
    def show_summary(self):
        """Show setup summary."""
        print("\n" + "="*60)
        print("🎉 **OAuth Setup Complete!**")
        print("="*60)
        
        print("\n✅ **What's Configured:**")
        if self.credentials["google"]:
            print("   🟦 Google Calendar OAuth - Ready")
        if self.credentials["microsoft"]:
            print("   🟦 Microsoft Outlook OAuth - Ready")
        
        print("\n📁 **Files Updated:**")
        print("   • .env - Backend OAuth credentials")
        print("   • frontend/.env.local - Frontend OAuth config")
        
        print("\n🔧 **Next Steps:**")
        print("1. Add redirect URIs to your OAuth applications")
        print("2. Test OAuth flows in development")
        print("3. Deploy to AWS with updated credentials")
        print("4. Configure production redirect URIs")
        
        print("\n📖 **Documentation:**")
        print("   • OAUTH_SETUP_GUIDE.md - Detailed setup instructions")
        print("   • Check browser console for OAuth debugging")
        
        print("\n🎯 **Users can now connect their calendars for AI-powered scheduling!**")
    
    def run(self):
        """Run the OAuth setup process."""
        self.welcome()
        
        # Setup Google OAuth
        setup_google = input("Set up Google Calendar OAuth? (Y/n): ").strip().lower()
        if setup_google not in ['n', 'no']:
            if not self.setup_google_oauth():
                print("❌ Google OAuth setup failed")
                return False
        
        # Setup Microsoft OAuth
        setup_microsoft = input("Set up Microsoft Outlook OAuth? (Y/n): ").strip().lower()
        if setup_microsoft not in ['n', 'no']:
            if not self.setup_microsoft_oauth():
                print("❌ Microsoft OAuth setup failed")
                return False
        
        if not self.credentials["google"] and not self.credentials["microsoft"]:
            print("❌ No OAuth credentials configured")
            return False
        
        # Update configuration files
        self.update_env_file()
        
        # Store in AWS (optional)
        self.store_in_aws_secrets()
        
        # Show redirect URIs
        self.show_redirect_uris()
        
        # Test configuration
        self.test_oauth_setup()
        
        # Show summary
        self.show_summary()
        
        return True

def main():
    """Main function."""
    setup = OAuthSetup()
    
    try:
        success = setup.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())