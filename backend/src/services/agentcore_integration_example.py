"""
Example integration of AgentCore Tool Invocation with existing services.
Demonstrates how to use the tool invocation primitive with the router and orchestrator.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .agentcore_tool_invocation import (
    AgentCoreToolInvocation, ToolSchema, ValidationLevel, ToolResult
)
from .agentcore_router import AgentCoreRouter, TaskType, ExecutionStep
from .agentcore_orchestrator import AgentCoreOrchestrator

logger = logging.getLogger(__name__)


class AgentCoreIntegratedExecution:
    """
    Integrated AgentCore execution that combines tool invocation with routing and orchestration.
    """
    
    def __init__(self):
        """Initialize integrated execution system."""
        self.tool_invocation = AgentCoreToolInvocation()
        self.router = AgentCoreRouter()
        self.orchestrator = AgentCoreOrchestrator()
        
        # Register actual tool implementations
        self._register_tool_implementations()
    
    def execute_scheduling_workflow(
        self,
        task_type: TaskType,
        request_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Execute a complete scheduling workflow using integrated tool invocation.
        
        Args:
            task_type: Type of scheduling task
            request_data: Request data
            user_id: User identifier
            
        Returns:
            Complete execution result with tool invocation details
        """
        try:
            # Step 1: Plan execution using router
            context_id, execution_steps = self.router.plan_execution(
                task_type=task_type,
                request_data=request_data,
                user_id=user_id
            )
            
            # Step 2: Execute steps using tool invocation system
            tool_results = []
            
            for step in execution_steps:
                # Convert execution step to tool invocation
                tool_result = self._execute_step_with_tool_invocation(step)
                tool_results.append(tool_result)
                
                # Update router context with result
                self.router.update_context(
                    context_id=context_id,
                    step_result=tool_result.data if tool_result.success else {"error": tool_result.error},
                    next_step_index=len(tool_results)
                )
            
            # Step 3: Aggregate results
            aggregated_results = self.tool_invocation.aggregate_results(
                tool_results, 
                aggregation_strategy="collect"
            )
            
            return {
                "context_id": context_id,
                "execution_successful": all(r.success for r in tool_results),
                "steps_executed": len(tool_results),
                "tool_results": aggregated_results,
                "audit_trail": self.tool_invocation.get_audit_trail(),
                "system_stats": self.tool_invocation.get_system_stats()
            }
            
        except Exception as e:
            logger.error(f"Integrated execution failed: {e}")
            return {
                "error": str(e),
                "execution_successful": False
            }
    
    def _execute_step_with_tool_invocation(self, step: ExecutionStep) -> ToolResult:
        """Execute an execution step using the tool invocation system."""
        return self.tool_invocation.invoke_tool(
            tool_name=step.tool_type.value,
            inputs=step.inputs,
            invocation_id=f"{step.step_id}_{int(datetime.utcnow().timestamp())}"
        )
    
    def _register_tool_implementations(self) -> None:
        """Register actual tool implementations with the invocation system."""
        
        # Mock OAuth Manager implementation
        def oauth_manager_impl(inputs: Dict[str, Any]) -> Dict[str, Any]:
            """Mock OAuth manager implementation."""
            attendees = inputs.get("attendees", [])
            action = inputs.get("action", "validate_tokens")
            
            # Simulate token validation
            valid_tokens = [f"{attendee}_token" for attendee in attendees[:3]]
            invalid_tokens = attendees[3:] if len(attendees) > 3 else []
            
            return {
                "valid_tokens": valid_tokens,
                "invalid_tokens": invalid_tokens,
                "action_performed": action,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Register OAuth Manager
        oauth_schema = self.tool_invocation.tool_schemas["oauth_manager"]
        self.tool_invocation.register_tool("oauth_manager", oauth_manager_impl, oauth_schema)
        
        logger.info("Tool implementations registered successfully")


# Example usage function
def example_usage():
    """Example of how to use the integrated system."""
    
    # Initialize integrated system
    integrated_system = AgentCoreIntegratedExecution()
    
    # Example scheduling request
    request_data = {
        "attendees": ["user1@example.com", "user2@example.com"],
        "duration_minutes": 60,
        "time_range": {
            "start": "2024-01-15T09:00:00Z",
            "end": "2024-01-15T17:00:00Z"
        }
    }
    
    # Execute workflow
    result = integrated_system.execute_scheduling_workflow(
        task_type=TaskType.SCHEDULE_MEETING,
        request_data=request_data,
        user_id="example_user"
    )
    
    print("Execution Result:")
    print(f"Success: {result.get('execution_successful')}")
    print(f"Steps Executed: {result.get('steps_executed')}")
    
    return result


if __name__ == "__main__":
    example_usage()