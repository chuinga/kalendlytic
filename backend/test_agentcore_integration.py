#!/usr/bin/env python3
"""
Test script to verify AgentCore integration implementation.
Tests Bedrock client, Router, Planner, and Tool Invocation primitives.
"""

import sys
import os

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

try:
    from services.bedrock_client import BedrockClient, BedrockClientError
    from services.agentcore_router import AgentCoreRouter, TaskType, Priority
    from services.agentcore_planner import AgentCorePlanner, PlanningStrategy
    from services.agentcore_tool_invocation import AgentCoreToolInvocation, ValidationLevel
    from services.agentcore_orchestrator import AgentCoreOrchestrator
    from services.scheduling_prompts import SchedulingPrompts
except ImportError as e:
    print(f"Import error: {e}")
    print("Running simplified tests without full service dependencies...")
    
    # Create minimal test implementations
    class MockBedrockClient:
        def __init__(self, region_name="us-east-1"):
            self.region_name = region_name
    
    class MockTaskType:
        SCHEDULE_MEETING = "schedule_meeting"
    
    BedrockClient = MockBedrockClient
    TaskType = MockTaskType


def test_bedrock_client():
    """Test Bedrock client initialization and prompt generation."""
    print("Testing Bedrock Client...")
    
    try:
        # Test client initialization (will fail without AWS credentials, but should not crash)
        client = BedrockClient(region_name="us-east-1")
        print("✓ Bedrock client initialized successfully")
        
        # Test prompt generation
        prompts = SchedulingPrompts()
        conflict_prompt = prompts.conflict_resolution_prompt(
            meeting_request={
                "title": "Team Meeting",
                "duration_minutes": 60,
                "attendees": ["user1@example.com", "user2@example.com"]
            },
            conflicts=[{
                "title": "Existing Meeting",
                "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T11:00:00Z"
            }],
            available_slots=[{
                "start_time": "2024-01-15T14:00:00Z",
                "end_time": "2024-01-15T15:00:00Z"
            }]
        )
        
        assert "MEETING REQUEST:" in conflict_prompt
        assert "CONFLICTS DETECTED:" in conflict_prompt
        print("✓ Prompt generation working correctly")
        
    except Exception as e:
        print(f"✗ Bedrock client test failed: {e}")
        return False
    
    return True


def test_agentcore_router():
    """Test AgentCore Router functionality."""
    print("Testing AgentCore Router...")
    
    try:
        router = AgentCoreRouter()
        
        # Test execution planning
        context_id, steps = router.plan_execution(
            task_type=TaskType.SCHEDULE_MEETING,
            request_data={
                "attendees": ["user1@example.com", "user2@example.com"],
                "duration_minutes": 60,
                "time_range": {"start": "2024-01-15T09:00:00Z", "end": "2024-01-15T17:00:00Z"}
            },
            user_id="test_user"
        )
        
        assert context_id is not None
        assert len(steps) > 0
        assert all(hasattr(step, 'step_id') for step in steps)
        print(f"✓ Router planned {len(steps)} execution steps")
        
        # Test context management
        context = router.get_context(context_id)
        assert context is not None
        assert context.user_id == "test_user"
        print("✓ Context management working correctly")
        
        # Test conflict handling
        conflicts = [{"type": "time_overlap", "severity": "medium"}]
        alternatives = [{"start_time": "2024-01-15T14:00:00Z"}]
        
        conflict_steps = router.handle_conflicts(context_id, conflicts, alternatives)
        assert len(conflict_steps) > 0
        print("✓ Conflict handling working correctly")
        
    except Exception as e:
        print(f"✗ Router test failed: {e}")
        return False
    
    return True


def test_agentcore_planner():
    """Test AgentCore Planner functionality."""
    print("Testing AgentCore Planner...")
    
    try:
        planner = AgentCorePlanner()
        
        # Test scenario creation
        scenario = planner.create_planning_scenario(
            task_type=TaskType.SCHEDULE_MEETING,
            request_data={
                "attendees": ["user1@example.com", "user2@example.com"],
                "duration_minutes": 60,
                "time_preferences": {"preferred_start": "09:00", "preferred_end": "17:00"}
            },
            user_preferences={"business_hours": {"start": "09:00", "end": "17:00"}}
        )
        
        assert scenario.scenario_id is not None
        assert len(scenario.constraints) > 0
        assert scenario.primary_task == TaskType.SCHEDULE_MEETING
        print("✓ Planning scenario created successfully")
        
        # Test complex scenario planning
        planning_result = planner.plan_complex_scenario(
            scenario=scenario,
            strategy=PlanningStrategy.BALANCED
        )
        
        assert planning_result.scenario_id == scenario.scenario_id
        assert len(planning_result.recommended_plan) > 0
        assert 0 <= planning_result.confidence_score <= 1
        print(f"✓ Complex planning completed with {planning_result.confidence_score:.2f} confidence")
        
    except Exception as e:
        print(f"✗ Planner test failed: {e}")
        return False
    
    return True


def test_tool_invocation():
    """Test AgentCore Tool Invocation functionality."""
    print("Testing AgentCore Tool Invocation...")
    
    try:
        tool_invocation = AgentCoreToolInvocation()
        
        # Test built-in schemas registration
        registered_tools = tool_invocation.get_registered_tools()
        assert "oauth_manager" in registered_tools
        assert "availability_aggregator" in registered_tools
        assert "calendar_service" in registered_tools
        assert "scheduling_agent" in registered_tools
        print("✓ Built-in tool schemas registered")
        
        # Test mock tool registration and invocation
        def mock_tool(inputs):
            return {"result": "success", "processed_inputs": inputs}
        
        from services.agentcore_tool_invocation import ToolSchema
        mock_schema = ToolSchema(
            tool_name="mock_tool",
            input_schema={"test_input": {"type": "str"}},
            output_schema={"result": {"type": "str"}},
            required_inputs=["test_input"]
        )
        
        tool_invocation.register_tool("mock_tool", mock_tool, mock_schema)
        
        # Test tool invocation
        result = tool_invocation.invoke_tool(
            tool_name="mock_tool",
            inputs={"test_input": "test_value"}
        )
        
        assert result.success is True
        assert result.data["result"] == "success"
        print("✓ Tool invocation working correctly")
        
        # Test system stats
        stats = tool_invocation.get_system_stats()
        assert "registered_tools" in stats
        assert stats["total_invocations"] >= 1
        print("✓ System statistics working correctly")
        
    except Exception as e:
        print(f"✗ Tool invocation test failed: {e}")
        return False
    
    return True


def test_orchestrator():
    """Test AgentCore Orchestrator functionality."""
    print("Testing AgentCore Orchestrator...")
    
    try:
        orchestrator = AgentCoreOrchestrator()
        
        # Test orchestrator stats
        stats = orchestrator.get_orchestrator_stats()
        assert "active_executions" in stats
        assert "router_stats" in stats
        assert "planner_stats" in stats
        print("✓ Orchestrator initialized and stats available")
        
        # Test intelligent scheduling (will use mock implementations)
        result = orchestrator.execute_intelligent_scheduling(
            task_type=TaskType.SCHEDULE_MEETING,
            request_data={
                "attendees": ["user1@example.com"],
                "duration_minutes": 30,
                "time_range": {"start": "2024-01-15T09:00:00Z", "end": "2024-01-15T17:00:00Z"}
            },
            user_id="test_user"
        )
        
        assert "execution_id" in result
        assert "planning_metadata" in result
        assert "execution_result" in result
        print("✓ Intelligent scheduling execution completed")
        
    except Exception as e:
        print(f"✗ Orchestrator test failed: {e}")
        return False
    
    return True


def main():
    """Run all tests."""
    print("=== AgentCore Integration Test Suite ===\n")
    
    tests = [
        test_bedrock_client,
        test_agentcore_router,
        test_agentcore_planner,
        test_tool_invocation,
        test_orchestrator
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
        print("\n🎉 All tests passed! AgentCore integration is working correctly.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())