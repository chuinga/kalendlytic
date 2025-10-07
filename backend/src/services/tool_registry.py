"""
Tool Registry Service for registering and managing agent tools.
Integrates with AgentCore tool invocation system.
"""

import logging
from typing import Dict, List, Any, Optional

from .agentcore_tool_invocation import AgentCoreToolInvocation
from ..tools.availability_tool import AvailabilityTool, AvailabilityRequest
from ..tools.event_management_tool import EventManagementTool, EventRequest, RescheduleRequest
from ..tools.email_communication_tool import EmailCommunicationTool, EmailRequest, EmailType
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
        self.event_management_tool = EventManagementTool()
        self.email_communication_tool = EmailCommunicationTool()
        
        # Register all tools
        self._register_all_tools()
    
    def _register_all_tools(self) -> None:
        """Register all available tools with the AgentCore system."""
        try:
            # Register availability tool
            self._register_availability_tool()
            
            # Register event management tool
            self._register_event_management_tool()
            
            # Register email communication tool
            self._register_email_communication_tool()
            
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
    
    def _register_event_management_tool(self) -> None:
        """Register the event management tool with AgentCore."""
        try:
            # Get the tool schema from the event management tool
            tool_schema = self.event_management_tool.get_tool_schema()
            
            # Create wrapper function for AgentCore integration
            def event_management_tool_wrapper(inputs: Dict[str, Any]) -> Dict[str, Any]:
                """Wrapper function for event management tool execution."""
                try:
                    action = inputs.get('action')
                    user_id = inputs.get('user_id')
                    connections = inputs.get('connections', [])
                    preferences = inputs.get('preferences')
                    
                    if action == "create":
                        event_data = inputs.get('event_data', {})
                        request = EventRequest(
                            user_id=user_id,
                            title=event_data.get('title', ''),
                            start=event_data.get('start'),
                            end=event_data.get('end'),
                            attendees=event_data.get('attendees'),
                            description=event_data.get('description', ''),
                            location=event_data.get('location', ''),
                            conference_provider=event_data.get('conference_provider', 'none'),
                            timezone=event_data.get('timezone', 'UTC'),
                            send_notifications=event_data.get('send_notifications', True)
                        )
                        result = self.event_management_tool.create_event(request, connections, preferences)
                        
                    elif action == "reschedule":
                        event_id = inputs.get('event_id')
                        new_start = inputs.get('new_start')
                        new_end = inputs.get('new_end')
                        conflict_resolution = inputs.get('conflict_resolution', 'find_alternative')
                        
                        request = RescheduleRequest(
                            user_id=user_id,
                            event_id=event_id,
                            new_start=new_start,
                            new_end=new_end,
                            conflict_resolution=conflict_resolution
                        )
                        result = self.event_management_tool.reschedule_event(request, connections, preferences)
                        
                    elif action == "modify":
                        event_id = inputs.get('event_id')
                        modifications = inputs.get('modifications', {})
                        result = self.event_management_tool.modify_event(
                            user_id, event_id, modifications, connections, preferences
                        )
                        
                    elif action == "cancel":
                        event_id = inputs.get('event_id')
                        send_notifications = inputs.get('send_notifications', True)
                        cancellation_reason = inputs.get('cancellation_reason', '')
                        result = self.event_management_tool.cancel_event(
                            user_id, event_id, connections, send_notifications, cancellation_reason
                        )
                        
                    else:
                        return {
                            "success": False,
                            "error": f"Unknown action: {action}"
                        }
                    
                    return {
                        "success": result.success,
                        "event_id": result.event_id,
                        "event_data": result.event_data,
                        "conflicts": result.conflicts,
                        "alternatives": result.alternatives,
                        "conference_url": result.conference_url,
                        "html_link": result.html_link,
                        "error_message": result.error_message,
                        "execution_time_ms": result.execution_time_ms
                    }
                    
                except Exception as e:
                    logger.error(f"Event management tool execution failed: {str(e)}")
                    return {
                        "success": False,
                        "error": str(e)
                    }
            
            # Register the tool function with a default schema
            self.tool_invocation.register_tool(
                tool_name="manage_events",
                tool_function=event_management_tool_wrapper,
                schema=tool_schema
            )
            
            logger.info("Event management tool registered successfully")
                
        except Exception as e:
            logger.error(f"Failed to register event management tool: {str(e)}")
            raise
    
    def _register_email_communication_tool(self) -> None:
        """Register the email communication tool with AgentCore."""
        try:
            # Get the tool schema from the email communication tool
            tool_schema = self.email_communication_tool.get_tool_schema()
            
            # Create wrapper function for AgentCore integration
            def email_communication_tool_wrapper(inputs: Dict[str, Any]) -> Dict[str, Any]:
                """Wrapper function for email communication tool execution."""
                try:
                    user_id = inputs.get('user_id')
                    email_type = inputs.get('email_type')
                    recipients = inputs.get('recipients', [])
                    connections = inputs.get('connections', [])
                    preferences = inputs.get('preferences')
                    
                    # Create email request
                    request = EmailRequest(
                        user_id=user_id,
                        email_type=EmailType(email_type),
                        recipients=recipients,
                        subject=inputs.get('subject', ''),
                        body=inputs.get('body', ''),
                        meeting_data=inputs.get('meeting_data'),
                        thread_id=inputs.get('thread_id'),
                        provider=inputs.get('provider', 'auto'),
                        auto_send=inputs.get('auto_send', True),
                        template_data=inputs.get('template_data'),
                        priority=inputs.get('priority', 'normal')
                    )
                    
                    # Execute the tool
                    result = self.email_communication_tool.send_email(request, connections, preferences)
                    
                    return {
                        "success": result.success,
                        "email_id": result.email_id,
                        "thread_id": result.thread_id,
                        "provider_used": result.provider_used,
                        "is_draft": result.is_draft,
                        "recipients_sent": result.recipients_sent,
                        "error_message": result.error_message,
                        "execution_time_ms": result.execution_time_ms
                    }
                    
                except Exception as e:
                    logger.error(f"Email communication tool execution failed: {str(e)}")
                    return {
                        "success": False,
                        "error": str(e)
                    }
            
            # Register the tool function
            self.tool_invocation.register_tool(
                tool_name="send_email",
                tool_function=email_communication_tool_wrapper,
                schema=tool_schema
            )
            
            logger.info("Email communication tool registered successfully")
                
        except Exception as e:
            logger.error(f"Failed to register email communication tool: {str(e)}")
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
    
    def execute_event_management_tool(self, 
                                    action: str,
                                    user_id: str,
                                    connections: List[Connection],
                                    preferences: Optional[Preferences] = None,
                                    **kwargs) -> Dict[str, Any]:
        """
        Execute the event management tool with proper context.
        
        Args:
            action: Event management action (create, reschedule, modify, cancel)
            user_id: User identifier
            connections: Active calendar connections
            preferences: User preferences
            **kwargs: Additional parameters specific to the action
            
        Returns:
            Tool execution result
        """
        try:
            # Prepare parameters
            parameters = {
                "action": action,
                "user_id": user_id,
                "connections": connections,
                "preferences": preferences,
                **kwargs
            }
            
            # Execute through AgentCore
            result = self.tool_invocation.invoke_tool(
                tool_name="manage_events",
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
            logger.error(f"Failed to execute event management tool: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    def execute_email_communication_tool(self, 
                                       email_type: str,
                                       user_id: str,
                                       recipients: List[str],
                                       connections: List[Connection],
                                       preferences: Optional[Preferences] = None,
                                       **kwargs) -> Dict[str, Any]:
        """
        Execute the email communication tool with proper context.
        
        Args:
            email_type: Type of email (confirmation, reschedule, cancellation, etc.)
            user_id: User identifier
            recipients: List of recipient email addresses
            connections: Active email connections
            preferences: User preferences
            **kwargs: Additional parameters
            
        Returns:
            Tool execution result
        """
        try:
            # Prepare parameters
            parameters = {
                "email_type": email_type,
                "user_id": user_id,
                "recipients": recipients,
                "connections": connections,
                "preferences": preferences,
                **kwargs
            }
            
            # Execute through AgentCore
            result = self.tool_invocation.invoke_tool(
                tool_name="send_email",
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
            logger.error(f"Failed to execute email communication tool: {str(e)}")
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