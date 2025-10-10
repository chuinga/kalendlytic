#!/usr/bin/env python3
"""
Fix Chrome DevTools MCP configuration
"""

import json
import os
import subprocess
import sys

def create_fixed_mcp_config():
    """Create a working MCP configuration for Chrome DevTools."""
    
    # Path to user MCP config
    mcp_config_path = os.path.expanduser("~/.kiro/settings/mcp.json")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(mcp_config_path), exist_ok=True)
    
    # Fixed configuration
    config = {
        "mcpServers": {
            "chrome-devtools": {
                "command": "chrome-devtools-mcp",
                "args": [
                    "--headless",
                    "--isolated",
                    "--viewport", "1280x720"
                ],
                "env": {
                    "DEBUG": "chrome-devtools-mcp:*"
                },
                "disabled": False,
                "autoApprove": [
                    "new_page",
                    "navigate", 
                    "screenshot",
                    "get_page_content"
                ],
                "disabledTools": []
            }
        }
    }
    
    # Write the configuration
    with open(mcp_config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Updated MCP configuration: {mcp_config_path}")
    print("📋 Configuration:")
    print(json.dumps(config, indent=2))

def test_chrome_devtools_direct():
    """Test Chrome DevTools MCP directly."""
    print("\n🧪 Testing Chrome DevTools MCP Server...")
    
    try:
        # Try to run with timeout using Python
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Command timed out")
        
        # Set timeout for 10 seconds
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)
        
        try:
            # Test if chrome-devtools-mcp can start
            result = subprocess.run([
                'chrome-devtools-mcp', 
                '--headless', 
                '--isolated',
                '--viewport', '1280x720'
            ], capture_output=True, text=True, timeout=5)
            
            print(f"✅ Command executed")
            print(f"📤 Return code: {result.returncode}")
            if result.stdout:
                print(f"📄 Stdout: {result.stdout[:200]}...")
            if result.stderr:
                print(f"📄 Stderr: {result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            print("⏰ Command timed out (expected for MCP server)")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            signal.alarm(0)  # Cancel the alarm
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

def check_chrome_processes():
    """Check running Chrome processes."""
    print("\n🔍 Checking Chrome Processes...")
    
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq chrome.exe'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            chrome_processes = [line for line in lines if 'chrome.exe' in line.lower()]
            print(f"📊 Found {len(chrome_processes)} Chrome processes")
            for proc in chrome_processes[:3]:  # Show first 3
                print(f"   {proc}")
        else:
            print("❌ Could not check Chrome processes")
    except Exception as e:
        print(f"❌ Error checking processes: {e}")

def show_troubleshooting_steps():
    """Show troubleshooting steps."""
    print("\n" + "="*60)
    print("🔧 **Chrome DevTools MCP Troubleshooting**")
    print("="*60)
    
    print("\n🎯 **Likely Issues:**")
    print("1. Chrome is already running with debugging disabled")
    print("2. Port 9222 (Chrome DevTools) is in use")
    print("3. Chrome security settings blocking remote debugging")
    print("4. MCP server can't launch isolated Chrome instance")
    
    print("\n🚀 **Solutions to Try:**")
    
    print("\n**Option 1: Close all Chrome instances and restart Kiro**")
    print("1. Close all Chrome windows")
    print("2. End Chrome processes in Task Manager")
    print("3. Restart Kiro")
    
    print("\n**Option 2: Use existing Chrome with debugging**")
    print("1. Close all Chrome instances")
    print("2. Start Chrome with: chrome.exe --remote-debugging-port=9222")
    print("3. Update MCP config to use --browserUrl http://127.0.0.1:9222")
    
    print("\n**Option 3: Alternative MCP Configuration**")
    print("Try this configuration in ~/.kiro/settings/mcp.json:")
    print("""
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "chrome-devtools-mcp",
      "args": ["--browserUrl", "http://127.0.0.1:9222"],
      "disabled": false,
      "autoApprove": ["new_page", "navigate", "screenshot"]
    }
  }
}""")
    
    print("\n**Option 4: Disable Chrome DevTools MCP temporarily**")
    print("Set 'disabled': true in the MCP configuration")
    
    print("\n💡 **Testing Commands:**")
    print("• Test MCP server: chrome-devtools-mcp --help")
    print("• Check Chrome processes: tasklist | findstr chrome")
    print("• Start Chrome with debugging: chrome --remote-debugging-port=9222")

def main():
    """Main function."""
    print("Chrome DevTools MCP - Diagnostic and Fix Tool")
    print("="*60)
    
    # Create fixed configuration
    create_fixed_mcp_config()
    
    # Test Chrome processes
    check_chrome_processes()
    
    # Test MCP server
    test_chrome_devtools_direct()
    
    # Show troubleshooting
    show_troubleshooting_steps()
    
    print(f"\n🎯 **Next Steps:**")
    print("1. Try restarting Kiro with the updated configuration")
    print("2. If still failing, close all Chrome instances first")
    print("3. Consider using --browserUrl option instead of --isolated")

if __name__ == "__main__":
    main()