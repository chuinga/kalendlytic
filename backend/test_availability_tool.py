#!/usr/bin/env python3
"""
Simple test script for the availability tool implementation.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Test basic imports and structure
def test_imports():
    """Test that all modules can be imported."""
    try:
        # Test tool structure
        from tools import AvailabilityTool
        print("✅ AvailabilityTool imported successfully")
        
        # Test tool creation
        tool = AvailabilityTool()
        print("✅ AvailabilityTool instance created")
        
        # Test schema generation
        schema = tool.get_tool_schema()
        print(f"✅ Tool schema generated: {schema['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return False


def test_tool_structure():
    """Test the tool structure and basic functionality."""
    print("Testing tool structure...")
    
    try:
        from tools import AvailabilityTool
        
        # Create tool instance
        tool = AvailabilityTool()
        
        # Test schema
        schema = tool.get_tool_schema()
        print(f"✅ Schema name: {schema['name']}")
        print(f"✅ Required params: {schema['parameters']['required']}")
        
        # Test basic execution with minimal parameters
        parameters = {
            "user_id": "test_user_123",
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=1)).isoformat()
        }
        
        result = tool.execute_tool(parameters, [], None)
        print(f"✅ Tool execution completed: success={result.get('success', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool structure test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running Availability Tool Tests...")
    
    # Test imports
    import_success = test_imports()
    
    # Test tool structure if imports work
    if import_success:
        structure_success = test_tool_structure()
        success = import_success and structure_success
    else:
        success = False
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    sys.exit(0 if success else 1)