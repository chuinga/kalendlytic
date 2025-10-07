"""
Tests for AgentCore Tool Invocation primitive.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import time

from backend.src.services.agentcore_tool_invocation import (
    AgentCoreToolInvocation,
    ToolSchema,
    ToolInvocation,
    ToolResult,
    ToolStatus,
    ValidationLevel,
    ToolInvocationError
)


class TestAgentCoreToolInvocation:
    """Test suite for AgentCore Tool Invocation."""
    
    def setup_method(self):
        """Setup test environment."""
        self.tool_invocation = AgentCoreToolInvocation()
        
        # Create a simple test tool
        def mock_tool_function(inputs):
            """Mock tool function for testing."""
            if inputs.get("should_fail"):
                raise Exception("Mock tool failure")
            
            # Add small delay to ensure measurable execution time
            time.sleep(0.001)
            
            return {
                "result": f"Processed {inputs.get('data', 'default')}",
                "timestamp": datetime.utcnow().isoformat(),
                "input_count": len(inputs)
            }
        
        # Register the mock tool
        test_schema = ToolSchema(
            tool_name="test_tool",
            input_schema={
                "data": {"type": "str", "constraints": {"min_length": 1}},
                "should_fail": {"type": "bool"}
            },
            output_schema={
                "result": {"type": "str"},
                "timestamp": {"type": "str"},
                "input_count": {"type": "int"}
            },
            required_inputs=["data"],
            optional_inputs=["should_fail"],
            timeout_ms=5000,
            max_retries=2
        )
        
        self.tool_invocation.register_tool("test_tool", mock_tool_function, test_schema)
    
    def test_tool_registration(self):
        """Test tool registration functionality."""
        # Check that tool was registered
        assert "test_tool" in self.tool_invocation.registered_tools
        assert "test_tool" in self.tool_invocation.tool_schemas
        
        # Check registered tools info
        tools_info = self.tool_invocation.get_registered_tools()
        assert "test_tool" in tools_info
        assert tools_info["test_tool"]["registered"] is True
        assert "data" in tools_info["test_tool"]["required_inputs"]
    
    def test_successful_tool_invocation(self):
        """Test successful tool invocation."""
        inputs = {"data": "test_input"}
        
        result = self.tool_invocation.invoke_tool("test_tool", inputs)
        
        assert result.success is True
        assert result.tool_name == "test_tool"
        assert result.data is not None
        assert "result" in result.data
        assert result.data["result"] == "Processed test_input"
        assert result.execution_time_ms >= 0  # Allow 0 for very fast execution
        assert result.validation_passed is True
    
    def test_tool_invocation_with_validation_error(self):
        """Test tool invocation with input validation errors."""
        # Missing required input
        inputs = {"should_fail": False}
        
        result = self.tool_invocation.invoke_tool("test_tool", inputs)
        
        assert result.success is False
        assert result.validation_passed is False
        assert "Missing required input: data" in result.error
    
    def test_tool_invocation_with_execution_error(self):
        """Test tool invocation with execution errors."""
        inputs = {"data": "test", "should_fail": True}
        
        result = self.tool_invocation.invoke_tool("test_tool", inputs)
        
        assert result.success is False
        assert "Mock tool failure" in result.error
        assert result.retry_count > 0  # Should have retried
    
    def test_tool_invocation_with_custom_validation_level(self):
        """Test tool invocation with different validation levels."""
        inputs = {"data": "test"}
        
        # Test with strict validation
        result = self.tool_invocation.invoke_tool(
            "test_tool", 
            inputs, 
            validation_level=ValidationLevel.STRICT
        )
        
        assert result.success is True
        
        # Test with lenient validation
        result = self.tool_invocation.invoke_tool(
            "test_tool", 
            inputs, 
            validation_level=ValidationLevel.LENIENT
        )
        
        assert result.success is True
    
    def test_batch_tool_invocation(self):
        """Test batch tool invocation."""
        tool_invocations = [
            {
                "tool_name": "test_tool",
                "inputs": {"data": "batch_1"}
            },
            {
                "tool_name": "test_tool",
                "inputs": {"data": "batch_2"}
            },
            {
                "tool_name": "test_tool",
                "inputs": {"data": "batch_3"}
            }
        ]
        
        results = self.tool_invocation.invoke_tools_batch(tool_invocations)
        
        assert len(results) == 3
        assert all(result.success for result in results)
        assert results[0].data["result"] == "Processed batch_1"
        assert results[1].data["result"] == "Processed batch_2"
        assert results[2].data["result"] == "Processed batch_3"
    
    def test_batch_tool_invocation_with_fail_fast(self):
        """Test batch tool invocation with fail_fast option."""
        tool_invocations = [
            {
                "tool_name": "test_tool",
                "inputs": {"data": "batch_1"}
            },
            {
                "tool_name": "test_tool",
                "inputs": {"data": "batch_2", "should_fail": True}
            },
            {
                "tool_name": "test_tool",
                "inputs": {"data": "batch_3"}
            }
        ]
        
        results = self.tool_invocation.invoke_tools_batch(
            tool_invocations, 
            fail_fast=True
        )
        
        # Should stop at the second tool due to failure
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
    
    def test_result_aggregation_merge(self):
        """Test result aggregation with merge strategy."""
        # Create some test results
        results = [
            ToolResult(
                invocation_id="1",
                tool_name="tool1",
                success=True,
                data={"key1": "value1", "shared": "from_tool1"},
                execution_time_ms=100
            ),
            ToolResult(
                invocation_id="2",
                tool_name="tool2",
                success=True,
                data={"key2": "value2", "shared": "from_tool2"},
                execution_time_ms=200
            )
        ]
        
        aggregated = self.tool_invocation.aggregate_results(results, "merge")
        
        assert "aggregated_data" in aggregated
        assert "tool1_key1" in aggregated["aggregated_data"]
        assert "tool2_key2" in aggregated["aggregated_data"]
        assert aggregated["metadata"]["successful_tools"] == 2
        assert aggregated["metadata"]["total_execution_time_ms"] == 300
    
    def test_result_aggregation_collect(self):
        """Test result aggregation with collect strategy."""
        results = [
            ToolResult(
                invocation_id="1",
                tool_name="tool1",
                success=True,
                data={"result": "success1"},
                execution_time_ms=100
            ),
            ToolResult(
                invocation_id="2",
                tool_name="tool2",
                success=False,
                error="Tool failed",
                execution_time_ms=50
            )
        ]
        
        aggregated = self.tool_invocation.aggregate_results(results, "collect")
        
        assert "collected_results" in aggregated
        assert len(aggregated["collected_results"]) == 2
        assert aggregated["collected_results"][0]["success"] is True
        assert aggregated["collected_results"][1]["success"] is False
        assert aggregated["metadata"]["successful_tools"] == 1
        assert aggregated["metadata"]["failed_tools"] == 1
    
    def test_result_aggregation_reduce(self):
        """Test result aggregation with reduce strategy."""
        results = [
            ToolResult(
                invocation_id="1",
                tool_name="fast_tool",
                success=True,
                data={"result": "success1"},
                execution_time_ms=50
            ),
            ToolResult(
                invocation_id="2",
                tool_name="slow_tool",
                success=True,
                data={"result": "success2"},
                execution_time_ms=200
            ),
            ToolResult(
                invocation_id="3",
                tool_name="failed_tool",
                success=False,
                error="Tool failed",
                execution_time_ms=100
            )
        ]
        
        aggregated = self.tool_invocation.aggregate_results(results, "reduce")
        
        assert "reduced_data" in aggregated
        reduced = aggregated["reduced_data"]
        
        assert reduced["summary"]["total_tools"] == 3
        assert reduced["summary"]["successful"] == 2
        assert reduced["summary"]["failed"] == 1
        assert reduced["summary"]["success_rate"] == 2/3
        
        assert reduced["performance"]["fastest_tool"] == "fast_tool"
        assert reduced["performance"]["slowest_tool"] == "slow_tool"
        assert len(reduced["errors"]) == 1
    
    def test_invocation_status_tracking(self):
        """Test invocation status tracking."""
        inputs = {"data": "status_test"}
        
        result = self.tool_invocation.invoke_tool("test_tool", inputs, invocation_id="status_test_1")
        
        # Check status after completion
        status = self.tool_invocation.get_invocation_status("status_test_1")
        
        assert status is not None
        assert status["invocation_id"] == "status_test_1"
        assert status["tool_name"] == "test_tool"
        assert status["status"] == ToolStatus.SUCCESS.value
        assert status["execution_time_ms"] > 0
    
    def test_audit_trail(self):
        """Test audit trail functionality."""
        inputs = {"data": "audit_test"}
        
        result = self.tool_invocation.invoke_tool("test_tool", inputs)
        
        # Get audit trail
        audit_trail = self.tool_invocation.get_audit_trail(tool_name="test_tool")
        
        assert len(audit_trail) > 0
        
        # Check for expected audit entries
        actions = [entry["action"] for entry in audit_trail]
        assert "execution_attempt" in actions
        assert "execution_success" in actions
        assert "invocation_complete" in actions
    
    def test_system_stats(self):
        """Test system statistics."""
        # Perform some invocations
        for i in range(3):
            inputs = {"data": f"stats_test_{i}"}
            self.tool_invocation.invoke_tool("test_tool", inputs)
        
        # Perform one failed invocation
        inputs = {"data": "fail_test", "should_fail": True}
        self.tool_invocation.invoke_tool("test_tool", inputs)
        
        stats = self.tool_invocation.get_system_stats()
        
        assert stats["registered_tools"] >= 1
        assert stats["total_invocations"] == 4
        assert stats["success_rate"] == 0.75  # 3 out of 4 successful
        assert stats["average_execution_time_ms"] > 0
        assert len(stats["most_used_tools"]) > 0
        assert stats["most_used_tools"][0]["tool_name"] == "test_tool"
    
    def test_unregistered_tool_error(self):
        """Test error handling for unregistered tools."""
        inputs = {"data": "test"}
        
        result = self.tool_invocation.invoke_tool("nonexistent_tool", inputs)
        
        assert result.success is False
        assert "Tool not registered" in result.error
    
    def test_builtin_schemas_registration(self):
        """Test that built-in schemas are properly registered."""
        tools_info = self.tool_invocation.get_registered_tools()
        
        # Check that built-in schemas exist
        builtin_tools = ["oauth_manager", "availability_aggregator", "calendar_service", "scheduling_agent"]
        
        for tool_name in builtin_tools:
            assert tool_name in tools_info
            # These should have schemas but not be registered (no actual functions)
            assert tools_info[tool_name]["registered"] is False
    
    def test_field_validation_constraints(self):
        """Test field validation with various constraints."""
        # Create a tool with strict constraints
        def constrained_tool(inputs):
            return {"result": "success"}
        
        constrained_schema = ToolSchema(
            tool_name="constrained_tool",
            input_schema={
                "short_text": {
                    "type": "str", 
                    "constraints": {"min_length": 5, "max_length": 10}
                },
                "number": {
                    "type": "int",
                    "constraints": {"min_value": 1, "max_value": 100}
                }
            },
            output_schema={
                "result": {"type": "str"}
            },
            required_inputs=["short_text", "number"],
            validation_level=ValidationLevel.STRICT
        )
        
        self.tool_invocation.register_tool("constrained_tool", constrained_tool, constrained_schema)
        
        # Test valid inputs
        valid_inputs = {"short_text": "hello", "number": 50}
        result = self.tool_invocation.invoke_tool("constrained_tool", valid_inputs)
        assert result.success is True
        
        # Test invalid inputs - text too short
        invalid_inputs = {"short_text": "hi", "number": 50}
        result = self.tool_invocation.invoke_tool("constrained_tool", invalid_inputs)
        assert result.success is False
        assert "length below minimum" in result.error
        
        # Test invalid inputs - text too long
        invalid_inputs = {"short_text": "this_is_too_long", "number": 50}
        result = self.tool_invocation.invoke_tool("constrained_tool", invalid_inputs)
        assert result.success is False
        assert "length above maximum" in result.error


if __name__ == "__main__":
    pytest.main([__file__])