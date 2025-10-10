#!/usr/bin/env python3
"""
Setup script for deployment prerequisites
"""

import subprocess
import sys
import os
import json

def check_and_setup_aws():
    """Check AWS CLI and guide setup."""
    print("🔍 Checking AWS CLI Configuration...")
    
    try:
        # Check AWS CLI
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ AWS CLI installed: {result.stdout.strip()}")
        else:
            print("❌ AWS CLI not found")
            return False
        
        # Check AWS credentials
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            identity = json.loads(result.stdout)
            print(f"✅ AWS configured for account: {identity.get('Account')}")
            print(f"✅ User/Role: {identity.get('Arn', 'Unknown')}")
            return True
        else:
            print("❌ AWS credentials not configured")
            print("\n💡 To configure AWS:")
            print("   aws configure")
            print("   # Enter your AWS Access Key ID")
            print("   # Enter your AWS Secret Access Key")
            print("   # Default region: eu-west-1")
            print("   # Default output format: json")
            return False
            
    except Exception as e:
        print(f"❌ Error checking AWS: {e}")
        return False

def check_and_install_cdk():
    """Check CDK and install if needed."""
    print("\n🔍 Checking AWS CDK...")
    
    try:
        # Check if CDK is installed
        result = subprocess.run(['cdk', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ AWS CDK installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ AWS CDK not found")
    except:
        print("❌ AWS CDK not found")
    
    # Try to install CDK
    print("📦 Installing AWS CDK...")
    try:
        result = subprocess.run(['npm', 'install', '-g', 'aws-cdk'], 
                              capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print("✅ CDK installed successfully")
            return True
        else:
            print(f"❌ CDK installation failed: {result.stderr}")
            print("\n💡 Manual installation:")
            print("   npm install -g aws-cdk")
            return False
    except Exception as e:
        print(f"❌ Error installing CDK: {e}")
        print("\n💡 Manual installation:")
        print("   npm install -g aws-cdk")
        return False

def prepare_infrastructure():
    """Prepare infrastructure for deployment."""
    print("\n🏗️ Preparing Infrastructure...")
    
    if not os.path.exists("infrastructure"):
        print("❌ Infrastructure directory not found")
        return False
    
    try:
        # Install CDK dependencies
        print("📦 Installing CDK dependencies...")
        result = subprocess.run(['npm', 'install'], 
                              cwd='infrastructure',
                              capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print("✅ CDK dependencies installed")
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
        
        # List CDK stacks
        print("📋 Checking CDK stacks...")
        result = subprocess.run(['cdk', 'list'], 
                              cwd='infrastructure',
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ CDK stacks available:")
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"   • {line.strip()}")
        else:
            print(f"⚠️ Could not list CDK stacks: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error preparing infrastructure: {e}")
        return False

def prepare_frontend():
    """Prepare frontend for deployment."""
    print("\n🌐 Preparing Frontend...")
    
    if not os.path.exists("frontend"):
        print("❌ Frontend directory not found")
        return False
    
    try:
        # Check if dependencies are installed
        node_modules = os.path.join("frontend", "node_modules")
        if os.path.exists(node_modules):
            print("✅ Frontend dependencies already installed")
            return True
        
        # Install frontend dependencies
        print("📦 Installing frontend dependencies...")
        result = subprocess.run(['npm', 'install'], 
                              cwd='frontend',
                              capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print("✅ Frontend dependencies installed")
            return True
        else:
            print(f"❌ Failed to install frontend dependencies: {result.stderr}")
            return False
        
    except Exception as e:
        print(f"❌ Error preparing frontend: {e}")
        return False

def show_deployment_commands():
    """Show the deployment commands."""
    print("\n" + "="*60)
    print("🚀 **READY FOR DEPLOYMENT**")
    print("="*60)
    
    print("\n📋 **Deployment Commands:**")
    
    print("\n1. **Bootstrap CDK (first time only):**")
    print("   cd infrastructure")
    print("   cdk bootstrap")
    
    print("\n2. **Deploy Backend Infrastructure:**")
    print("   cdk deploy --all")
    print("   # This will take 15-25 minutes")
    
    print("\n3. **Update Configuration:**")
    print("   # Update .env with deployed API Gateway URL")
    print("   # Get outputs from CloudFormation console")
    
    print("\n4. **Deploy Frontend:**")
    print("   cd ../frontend")
    print("   npm run build")
    print("   # Frontend will be deployed via CDK")
    
    print("\n5. **Test Deployment:**")
    print("   curl https://your-api-id.execute-api.eu-west-1.amazonaws.com/health")
    
    print("\n📖 **For detailed instructions, see: DEPLOYMENT_GUIDE.md**")

def main():
    """Main setup function."""
    print("AWS Meeting Scheduling Agent - Deployment Setup")
    print("="*60)
    
    print("This script will prepare your environment for full-stack deployment.")
    print()
    
    # Check prerequisites
    aws_ready = check_and_setup_aws()
    cdk_ready = check_and_install_cdk()
    
    if not aws_ready:
        print("\n❌ AWS configuration required before proceeding")
        print("Run 'aws configure' and then run this script again")
        return 1
    
    if not cdk_ready:
        print("\n❌ CDK installation required before proceeding")
        return 1
    
    # Prepare components
    infra_ready = prepare_infrastructure()
    frontend_ready = prepare_frontend()
    
    if infra_ready and frontend_ready:
        show_deployment_commands()
        print("\n🎉 Setup complete! Ready for deployment.")
        return 0
    else:
        print("\n❌ Setup incomplete. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())