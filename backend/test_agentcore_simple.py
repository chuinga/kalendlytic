#!/usr/bin/env python3
"""
Simple test script to verify AgentCore integration components work independently.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)


def test_bedrock_client():
    """Test Bedrock client can be imported and initialized."""
    print("Testing Bedrock Client...")
    
    try:
        from services.bedrock_client import BedrockClient, BedrockClientError, TokenUsage, BedrockResponse
        
        # Test class definitions exist
        assert BedrockClient is not None
        assert BedrockClientError is not None
        assert TokenUsage is not None
        assert BedrockResponse is not None
        
        # Test client can be initialized (will fail AWS connection but class should work)
        try:
            client = BedrockClient(region_name="us-east-1")
            print("✓ Bedrock client class initialized")
        except Exception as e:
            # Expected to fail without AWS credentials, but class should exist
            if "BedrockClientError" in str(type(e)) or "Failed to initialize" in str(e):
                print("✓ Bedrock client class exists (AWS connection expected to fail)")
            else:
                raise e
        
        # Test cost calculation method
        client = BedrockClient.__new__(BedrockClient)  # Create without __init__
        cost = client._BedrockClient__calculate_cost(1000, 500)  # Access private method
        assert isinstance(cost, float)
        assert cost > 0
        print("✓ Cost calculation method working")
        
        return True
        
    except Exception as e:
        print(f"✗ Bedrock client test failed: {e}")
        return False


def test_scheduling_prompts():
    """Test scheduling prompts generation."""
    print("Testing Scheduling Prompts...")
    
    try:
        from services.scheduling_prompts import SchedulingPrompts
        
        prompts = SchedulingPrompts()
        
        # Test conflict resolution prompt
        conflict_prompt = prompts.conflict_resolution_prompt(
            meeting_request={
                "title": "Team Meeting",
                "duration_minutes": 60,
                "attendees": ["user1@example.com", "user2@example.com"],
                "priority": "high"
            },
            conflicts=[{
                "title": "Existing Meeting",
                "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T11:00:00Z",
                "attendees": ["user1@example.com"],
                "priority": "medium"
            }],
            available_slots=[{
                "start_time": "2024-01-15T14:00:00Z",
                "end_time": "2024-01-15T15:00:00Z"
            }]
        )
        
        assert "MEETING REQUEST:" in conflict_prompt
        assert "CONFLICTS DETECTED:" in conflict_prompt
        assert "AVAILABLE ALTERNATIVE SLOTS:" in conflict_prompt
        assert "Team Meeting" in conflict_prompt
        assert "60 minutes" in conflict_prompt
        print("✓ Conflict resolution prompt generated correctly")
        
        # Test optimal scheduling prompt
        optimal_prompt = prompts.optimal_scheduling_prompt(
            meeting_request={
                "title": "Project Review",
                "duration_minutes": 90,
                "attendees": ["manager@example.com", "dev@example.com"]
            },
            attendee_availability={
                "manager@example.com": [
                    {"start": "09:00", "end": "12:00", "status": "free"},
                    {"start": "14:00", "end": "17:00", "status": "free"}
                ],
                "dev@example.com": [
                    {"start": "10:00", "end": "16:00", "status": "free"}
                ]
            },
            preferences={
                "business_hours": "9:00 AM - 5:00 PM",
                "timezone": "UTC",
                "buffer_minutes": 15
            }
        )
        
        assert "MEETING REQUEST:" in optimal_prompt
        assert "ATTENDEE AVAILABILITY:" in optimal_prompt
        assert "SCHEDULING PREFERENCES:" in optimal_prompt
        assert "Project Review" in optimal_prompt
        print("✓ Optimal scheduling prompt generated correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Scheduling prompts test failed: {e}")
        return False


def test_agentcore_router_classes():
    """Test AgentCore Router classes and enums."""
    print("Testing AgentCore Router Classes...")
    
    try:
        from services.agentcore_router import (
            TaskType, Priority, ToolType, ExecutionStep, ExecutionContext,
            AgentCoreRouter, AgentCoreRouterError
        )
        
        # Test enums
        assert TaskType.SCHEDULE_MEETING == "schedule_meeting"
        assert TaskType.RESOLVE_CONFLICT == "resolve_conflict"
        assert Priority.HIGH == 3
        assert ToolType.CALENDAR_SERVICE == "calendar_service"
        print("✓ Enums defined correctly")
        
        # Test ExecutionStep creation
        step = ExecutionStep(
            step_id="test_step",
            tool_type=ToolType.CALENDAR_SERVICE,
            action="create_meeting",
            inputs={"test": "data"},
            dependencies=[],
            priority=Priority.HIGH,
            estimated_duration_ms=1000
        )
        
        assert step.step_id == "test_step"
        assert step.tool_type == ToolType.CALENDAR_SERVICE
        assert step.priority == Priority.HIGH
        print("✓ ExecutionStep class working correctly")
        
        # Test ExecutionContext creation
        context = ExecutionContext(
            session_id="test_session",
            user_id="test_user",
            task_type=TaskType.SCHEDULE_MEETING,
            original_request={"test": "request"},
            current_step=0,
            total_steps=5,
            accumulated_data={},
            conflict_resolution_history=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        assert context.session_id == "test_session"
        assert context.user_id == "test_user"
        assert context.task_type == TaskType.SCHEDULE_MEETING
        print("✓ ExecutionContext class working correctly")
        
        # Test router initialization
        router = AgentCoreRouter()
        assert len(router.active_contexts) == 0
        assert len(router.execution_history) == 0
        assert len(router.task_workflows) > 0
        print("✓ AgentCoreRouter initialized correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ AgentCore Router classes test failed: {e}")
        return False


def test_agentcore_tool_invocation_classes():
    """Test AgentCore Tool Invocation classes."""
    print("Testing AgentCore Tool Invocation Classes...")
    
    try:
        from services.agentcore_tool_invocation import (
            ToolStatus, ValidationLevel, ToolSchema, ToolInvocation, ToolResult,
            AgentCoreToolInvocation, ToolInvocationError
        )
        
        # Test enums
        assert ToolStatus.SUCCESS == "success"
        assert ToolStatus.FAILED == "failed"
        assert ValidationLevel.STRICT == "strict"
        print("✓ Tool invocation enums defined correctly")
        
        # Test ToolSchema creation
        schema = ToolSchema(
            tool_name="test_tool",
            input_schema={"param1": {"type": "str"}},
            output_schema={"result": {"type": "str"}},
            required_inputs=["param1"],
            optional_inputs=[],
            validation_level=ValidationLevel.MODERATE,
            timeout_ms=5000,
            max_retries=2
        )
        
        assert schema.tool_name == "test_tool"
        assert schema.validation_level == ValidationLevel.MODERATE
        assert schema.timeout_ms == 5000
        print("✓ ToolSchema class working correctly")
        
        # Test ToolInvocation creation
        invocation = ToolInvocation(
            invocation_id="test_invocation",
            tool_name="test_tool",
            inputs={"param1": "value1"},
            status=ToolStatus.PENDING
        )
        
        assert invocation.invocation_id == "test_invocation"
        assert invocation.tool_name == "test_tool"
        assert invocation.status == ToolStatus.PENDING
        print("✓ ToolInvocation class working correctly")
        
        # Test ToolResult creation
        result = ToolResult(
            invocation_id="test_invocation",
            tool_name="test_tool",
            success=True,
            data={"result": "success"},
            execution_time_ms=1500
        )
        
        assert result.success is True
        assert result.data["result"] == "success"
        assert result.execution_time_ms == 1500
        print("✓ ToolResult class working correctly")
        
        # Test AgentCoreToolInvocation initialization
        tool_invocation = AgentCoreToolInvocation()
        assert len(tool_invocation.registered_tools) == 0
        assert len(tool_invocation.tool_schemas) >= 4  # Built-in schemas
        assert len(tool_invocation.active_invocations) == 0
        print("✓ AgentCoreToolInvocation initialized with built-in schemas")
        
        # Test built-in schemas
        registered_tools = tool_invocation.get_registered_tools()
        assert "oauth_manager" in registered_tools
        assert "availability_aggregator" in registered_tools
        assert "calendar_service" in registered_tools
        assert "scheduling_agent" in registered_tools
        print("✓ Built-in tool schemas registered correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ AgentCore Tool Invocation classes test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=== AgentCore Simple Integration Test ===\n")
    
    tests = [
        test_bedrock_client,
        test_scheduling_prompts,
        test_agentcore_router_classes,
        test_agentcore_tool_invocation_classes
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✓ PASSED\n")
            else:
                failed += 1
                print("✗ FAILED\n")
        except Exception as e:
            failed += 1
            print(f"✗ FAILED with exception: {e}\n")
    
    print("=== Test Results ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! AgentCore integration components are working correctly.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())