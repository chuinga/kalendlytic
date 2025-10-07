"""
Tool Registry Service for registering and managing agent tools.
Integrates with AgentCore tool invocation system.
"""

import logging
from typing import Dict, List, Any, Optional

from .agentcore_tool_invocation import AgentCoreToolInvocation
from ..tools.availability_tool import AvailabilityTool, AvailabilityRequest
from ..models.connection import Connection
from ..models.preferences import Preferences
from ..utils.logging import setup_logger

logger = setup_logger(__name__)


class ToolRegistry:
    """
    Registry for managing and registering agent tools with AgentCore.
    """
    
    def __init__(self, tool_invocation_service: AgentCoreToolInvocation):
        """
        Initialize the tool registry.
        
        Args:
            tool_invocation_service: AgentCore tool invocation service
        """
        self.tool_invocation = tool_invocation_service
        self.availability_tool = AvailabilityTool()
        
        # Register all tools
        self._register_all_tools()
    
    def _register_all_tools(self) -> None:
        """Register all available tools with the AgentCore system."""
        try:
            # Register availability tool
            self._register_availability_tool()
            
            logger.info("All tools registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register tools: {str(e)}")
            raise
    
    def _register_availability_tool(self) -> None:
        """Register the availability tool with AgentCore."""
        try:
            # Get the tool schema from the availability tool
            tool_schema = self.availability_tool.get_tool_schema()
            
            # Create wrapper function for AgentCore integration
            def availability_tool_wrapper(inputs: Dict[str, Any]) -> Dict[str, Any]:
                """Wrapper function for availability tool execution."""
                try:
                    # Get connections and preferences from context
                    # In a real implementation, these would be retrieved from the database
                    # For now, we'll use empty lists/None as defaults
                    connections = inputs.get('connections', [])
                    preferences = inputs.get('preferences')
                    
                    # Execute the tool
                    result = self.availability_tool.execute_tool(
                        parameters=inputs,
                        connections=connections,
                        preferences=preferences
                    )
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Availability tool execution failed: {str(e)}")
                    return {
                        "success": False,
                        "error": str(e),
                        "available_slots": [],
                        "total_slots_found": 0
                    }
            
            # Get the existing schema from AgentCore
            existing_schema = self.tool_invocation.tool_schemas.get("get_availability")
            
            if existing_schema:
                # Register the tool function with the existing schema
                self.tool_invocation.register_tool(
                    tool_name="get_availability",
                    tool_function=availability_tool_wrapper,
                    schema=existing_schema
                )
                
                logger.info("Availability tool registered successfully")
            else:
                logger.error("No schema found for get_availability tool")
                
        except Exception as e:
            logger.error(f"Failed to register availability tool: {str(e)}")
            raise
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return list(self.tool_invocation.registered_tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        if tool_name in self.tool_invocation.tool_schemas:
            schema = self.tool_invocation.tool_schemas[tool_name]
            return {
                "tool_name": tool_name,
                "registered": tool_name in self.tool_invocation.registered_tools,
                "required_inputs": schema.required_inputs,
                "optional_inputs": schema.optional_inputs,
                "timeout_ms": schema.timeout_ms,
                "max_retries": schema.max_retries,
                "validation_level": schema.validation_level.value
            }
        return None
    
    def execute_availability_tool(self, 
                                user_id: str,
                                start_date: str,
                                end_date: str,
                                connections: List[Connection],
                                preferences: Optional[Preferences] = None,
                                **kwargs) -> Dict[str, Any]:
        """
        Execute the availability tool with proper context.
        
        Args:
            user_id: User identifier
            start_date: Start date in ISO format
            end_date: End date in ISO format
            connections: Active calendar connections
            preferences: User preferences
            **kwargs: Additional parameters
            
        Returns:
            Tool execution result
        """
        try:
            # Prepare parameters
            parameters = {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
                "connections": connections,
                "preferences": preferences,
                **kwargs
            }
            
            # Execute through AgentCore
            result = self.tool_invocation.invoke_tool(
                tool_name="get_availability",
                inputs=parameters
            )
            
            return {
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms,
                "retry_count": result.retry_count
            }
            
        except Exception as e:
            logger.error(f"Failed to execute availability tool: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools_registered": len(self.tool_invocation.registered_tools),
            "total_schemas_available": len(self.tool_invocation.tool_schemas),
            "available_tools": self.get_available_tools(),
            "tool_invocation_stats": self.tool_invocation.get_system_stats()
        }


# Global tool registry instance
_tool_registry_instance: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _tool_registry_instance
    
    if _tool_registry_instance is None:
        # Create AgentCore tool invocation service
        tool_invocation_service = AgentCoreToolInvocation()
        
        # Create and initialize tool registry
        _tool_registry_instance = ToolRegistry(tool_invocation_service)
    
    return _tool_registry_instance


def initialize_tool_registry() -> ToolRegistry:
    """Initialize the global tool registry."""
    global _tool_registry_instance
    
    # Force re-initialization
    _tool_registry_instance = None
    return get_tool_registry()