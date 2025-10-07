"""
AgentCore Tool Invocation primitive for safe, validated tool execution.
Provides schema validation, error handling, result aggregation, and audit logging.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import traceback
from pydantic import BaseModel, ValidationError, Field

logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """Status of tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ValidationLevel(Enum):
    """Validation strictness levels."""
    STRICT = "strict"      # All fields required, strict types
    MODERATE = "moderate"  # Required fields only, flexible types
    LENIENT = "lenient"    # Basic validation only


@dataclass
class ToolSchema:
    """Schema definition for tool inputs and outputs."""
    tool_name: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_inputs: List[str]
    optional_inputs: List[str] = field(default_factory=list)
    validation_level: ValidationLevel = ValidationLevel.MODERATE
    timeout_ms: int = 30000
    max_retries: int = 3


@dataclass
class ToolInvocation:
    """Individual tool invocation record."""
    invocation_id: str
    tool_name: str
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]] = None
    status: ToolStatus = ToolStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    validation_errors: List[str] = field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ToolResult:
    """Result of tool execution with metadata."""
    invocation_id: str
    tool_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    retry_count: int = 0
    validation_passed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolInvocationError(Exception):
    """Custom exception for tool invocation errors."""
    pass


class AgentCoreToolInvocation:
    """
    AgentCore Tool Invocation primitive for safe, validated tool execution.
    Handles schema validation, error handling, result aggregation, and audit logging.
    """
    
    def __init__(self):
        """Initialize the tool invocation system."""
        self.registered_tools: Dict[str, Callable] = {}
        self.tool_schemas: Dict[str, ToolSchema] = {}
        self.active_invocations: Dict[str, ToolInvocation] = {}
        self.invocation_history: List[ToolInvocation] = []
        self.audit_logger = self._setup_audit_logger()
        
        # Register built-in tool schemas
        self._register_builtin_schemas()
    
    def register_tool(
        self,
        tool_name: str,
        tool_function: Callable,
        schema: ToolSchema
    ) -> None:
        """
        Register a tool with its execution function and schema.
        
        Args:
            tool_name: Name of the tool
            tool_function: Function to execute the tool
            schema: Schema definition for validation
        """
        try:
            self.registered_tools[tool_name] = tool_function
            self.tool_schemas[tool_name] = schema
            
            logger.info(f"Tool registered: {tool_name}")
            self._audit_log("tool_registration", {
                "tool_name": tool_name,
                "schema_validation_level": schema.validation_level.value,
                "timeout_ms": schema.timeout_ms
            })
            
        except Exception as e:
            logger.error(f"Failed to register tool {tool_name}: {e}")
            raise ToolInvocationError(f"Tool registration failed: {e}")
    
    def invoke_tool(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        invocation_id: Optional[str] = None,
        validation_level: Optional[ValidationLevel] = None
    ) -> ToolResult:
        """
        Invoke a tool with input validation and error handling.
        
        Args:
            tool_name: Name of the tool to invoke
            inputs: Input parameters for the tool
            invocation_id: Optional custom invocation ID
            validation_level: Override validation level for this invocation
            
        Returns:
            ToolResult with execution results and metadata
        """
        # Generate invocation ID if not provided
        if not invocation_id:
            invocation_id = f"{tool_name}_{int(datetime.utcnow().timestamp() * 1000)}"
        
        # Create invocation record
        invocation = ToolInvocation(
            invocation_id=invocation_id,
            tool_name=tool_name,
            inputs=inputs.copy(),
            start_time=datetime.utcnow()
        )
        
        self.active_invocations[invocation_id] = invocation
        
        try:
            # Validate tool exists
            if tool_name not in self.registered_tools:
                raise ToolInvocationError(f"Tool not registered: {tool_name}")
            
            schema = self.tool_schemas[tool_name]
            tool_function = self.registered_tools[tool_name]
            
            # Override validation level if specified
            effective_validation_level = validation_level or schema.validation_level
            
            # Validate inputs
            validation_result = self._validate_inputs(
                inputs, schema, effective_validation_level
            )
            
            if not validation_result["valid"]:
                invocation.validation_errors = validation_result["errors"]
                invocation.status = ToolStatus.FAILED
                
                result = ToolResult(
                    invocation_id=invocation_id,
                    tool_name=tool_name,
                    success=False,
                    error=f"Input validation failed: {validation_result['errors']}",
                    validation_passed=False
                )
                
                self._finalize_invocation(invocation, result)
                return result
            
            # Execute tool with retry logic
            result = self._execute_with_retry(
                invocation, tool_function, schema
            )
            
            # Validate outputs if successful
            if result.success and result.data:
                output_validation = self._validate_outputs(
                    result.data, schema, effective_validation_level
                )
                
                if not output_validation["valid"]:
                    logger.warning(f"Output validation failed for {tool_name}: {output_validation['errors']}")
                    result.metadata["output_validation_warnings"] = output_validation["errors"]
            
            self._finalize_invocation(invocation, result)
            return result
            
        except Exception as e:
            logger.error(f"Tool invocation failed for {tool_name}: {e}")
            
            invocation.status = ToolStatus.FAILED
            invocation.error_message = str(e)
            
            result = ToolResult(
                invocation_id=invocation_id,
                tool_name=tool_name,
                success=False,
                error=str(e)
            )
            
            self._finalize_invocation(invocation, result)
            return result
    
    def invoke_tools_batch(
        self,
        tool_invocations: List[Dict[str, Any]],
        parallel: bool = False,
        fail_fast: bool = True
    ) -> List[ToolResult]:
        """
        Invoke multiple tools in batch with optional parallel execution.
        
        Args:
            tool_invocations: List of tool invocation specifications
            parallel: Whether to execute tools in parallel
            fail_fast: Whether to stop on first failure
            
        Returns:
            List of ToolResult objects
        """
        results = []
        
        try:
            self._audit_log("batch_invocation_start", {
                "tool_count": len(tool_invocations),
                "parallel": parallel,
                "fail_fast": fail_fast
            })
            
            if parallel:
                # For now, implement sequential execution
                # In production, this would use asyncio or threading
                logger.info("Parallel execution not yet implemented, using sequential")
            
            for i, invocation_spec in enumerate(tool_invocations):
                tool_name = invocation_spec["tool_name"]
                inputs = invocation_spec["inputs"]
                invocation_id = invocation_spec.get("invocation_id")
                validation_level = invocation_spec.get("validation_level")
                
                result = self.invoke_tool(
                    tool_name=tool_name,
                    inputs=inputs,
                    invocation_id=invocation_id,
                    validation_level=ValidationLevel(validation_level) if validation_level else None
                )
                
                results.append(result)
                
                # Check fail_fast condition
                if fail_fast and not result.success:
                    logger.warning(f"Batch execution stopped at tool {i+1} due to failure")
                    break
            
            self._audit_log("batch_invocation_complete", {
                "tools_executed": len(results),
                "successful": sum(1 for r in results if r.success),
                "failed": sum(1 for r in results if not r.success)
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Batch tool invocation failed: {e}")
            raise ToolInvocationError(f"Batch invocation failed: {e}")
    
    def aggregate_results(
        self,
        results: List[ToolResult],
        aggregation_strategy: str = "merge"
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple tool invocations.
        
        Args:
            results: List of tool results to aggregate
            aggregation_strategy: Strategy for aggregation ("merge", "collect", "reduce")
            
        Returns:
            Aggregated result data
        """
        try:
            if aggregation_strategy == "merge":
                return self._merge_results(results)
            elif aggregation_strategy == "collect":
                return self._collect_results(results)
            elif aggregation_strategy == "reduce":
                return self._reduce_results(results)
            else:
                raise ToolInvocationError(f"Unknown aggregation strategy: {aggregation_strategy}")
                
        except Exception as e:
            logger.error(f"Result aggregation failed: {e}")
            raise ToolInvocationError(f"Result aggregation failed: {e}")
    
    def get_invocation_status(self, invocation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific invocation."""
        if invocation_id in self.active_invocations:
            invocation = self.active_invocations[invocation_id]
            return {
                "invocation_id": invocation_id,
                "tool_name": invocation.tool_name,
                "status": invocation.status.value,
                "start_time": invocation.start_time.isoformat() if invocation.start_time else None,
                "execution_time_ms": invocation.execution_time_ms,
                "retry_count": invocation.retry_count,
                "error_message": invocation.error_message
            }
        
        # Check history
        for invocation in self.invocation_history:
            if invocation.invocation_id == invocation_id:
                return {
                    "invocation_id": invocation_id,
                    "tool_name": invocation.tool_name,
                    "status": invocation.status.value,
                    "start_time": invocation.start_time.isoformat() if invocation.start_time else None,
                    "end_time": invocation.end_time.isoformat() if invocation.end_time else None,
                    "execution_time_ms": invocation.execution_time_ms,
                    "retry_count": invocation.retry_count,
                    "error_message": invocation.error_message
                }
        
        return None
    
    def get_audit_trail(
        self,
        tool_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit trail for tool invocations.
        
        Args:
            tool_name: Filter by specific tool name
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            List of audit trail entries
        """
        audit_entries = []
        
        # Get from active invocations
        for invocation in self.active_invocations.values():
            if self._matches_audit_filter(invocation, tool_name, start_time, end_time):
                audit_entries.extend(invocation.audit_trail)
        
        # Get from history
        for invocation in self.invocation_history:
            if self._matches_audit_filter(invocation, tool_name, start_time, end_time):
                audit_entries.extend(invocation.audit_trail)
        
        return sorted(audit_entries, key=lambda x: x.get("timestamp", ""))
    
    def _validate_inputs(
        self,
        inputs: Dict[str, Any],
        schema: ToolSchema,
        validation_level: ValidationLevel
    ) -> Dict[str, Any]:
        """Validate tool inputs against schema."""
        validation_result = {"valid": True, "errors": []}
        
        try:
            # Check required inputs
            for required_field in schema.required_inputs:
                if required_field not in inputs:
                    validation_result["errors"].append(f"Missing required input: {required_field}")
            
            # Validate input types and constraints
            for field_name, field_value in inputs.items():
                if field_name in schema.input_schema:
                    field_schema = schema.input_schema[field_name]
                    field_validation = self._validate_field(
                        field_name, field_value, field_schema, validation_level
                    )
                    
                    if not field_validation["valid"]:
                        validation_result["errors"].extend(field_validation["errors"])
            
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _validate_outputs(
        self,
        outputs: Dict[str, Any],
        schema: ToolSchema,
        validation_level: ValidationLevel
    ) -> Dict[str, Any]:
        """Validate tool outputs against schema."""
        validation_result = {"valid": True, "errors": []}
        
        try:
            # Validate output structure
            for field_name, field_value in outputs.items():
                if field_name in schema.output_schema:
                    field_schema = schema.output_schema[field_name]
                    field_validation = self._validate_field(
                        field_name, field_value, field_schema, validation_level
                    )
                    
                    if not field_validation["valid"]:
                        validation_result["errors"].extend(field_validation["errors"])
            
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Output validation error: {str(e)}")
        
        return validation_result
    
    def _validate_field(
        self,
        field_name: str,
        field_value: Any,
        field_schema: Dict[str, Any],
        validation_level: ValidationLevel
    ) -> Dict[str, Any]:
        """Validate individual field against its schema."""
        validation_result = {"valid": True, "errors": []}
        
        try:
            expected_type = field_schema.get("type")
            
            if validation_level == ValidationLevel.STRICT:
                # Strict type checking
                if expected_type and not isinstance(field_value, eval(expected_type)):
                    validation_result["errors"].append(
                        f"Field {field_name} expected {expected_type}, got {type(field_value).__name__}"
                    )
            
            elif validation_level == ValidationLevel.MODERATE:
                # Basic type compatibility
                if expected_type == "str" and not isinstance(field_value, (str, int, float)):
                    validation_result["errors"].append(
                        f"Field {field_name} cannot be converted to string"
                    )
                elif expected_type == "int" and not isinstance(field_value, (int, float)):
                    validation_result["errors"].append(
                        f"Field {field_name} cannot be converted to integer"
                    )
            
            # Check constraints
            constraints = field_schema.get("constraints", {})
            
            if "min_length" in constraints and hasattr(field_value, "__len__"):
                if len(field_value) < constraints["min_length"]:
                    validation_result["errors"].append(
                        f"Field {field_name} length below minimum: {constraints['min_length']}"
                    )
            
            if "max_length" in constraints and hasattr(field_value, "__len__"):
                if len(field_value) > constraints["max_length"]:
                    validation_result["errors"].append(
                        f"Field {field_name} length above maximum: {constraints['max_length']}"
                    )
            
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Field validation error for {field_name}: {str(e)}")
        
        return validation_result
    
    def _execute_with_retry(
        self,
        invocation: ToolInvocation,
        tool_function: Callable,
        schema: ToolSchema
    ) -> ToolResult:
        """Execute tool with retry logic and error handling."""
        invocation.status = ToolStatus.RUNNING
        
        for attempt in range(schema.max_retries + 1):
            try:
                invocation.retry_count = attempt
                
                # Add audit entry for execution attempt
                self._add_audit_entry(invocation, "execution_attempt", {
                    "attempt": attempt + 1,
                    "max_retries": schema.max_retries
                })
                
                # Execute the tool function
                start_time = datetime.utcnow()
                
                # Call the actual tool function
                output_data = tool_function(invocation.inputs)
                
                end_time = datetime.utcnow()
                execution_time = int((end_time - start_time).total_seconds() * 1000)
                
                # Success case
                invocation.status = ToolStatus.SUCCESS
                invocation.outputs = output_data
                invocation.execution_time_ms = execution_time
                
                result = ToolResult(
                    invocation_id=invocation.invocation_id,
                    tool_name=invocation.tool_name,
                    success=True,
                    data=output_data,
                    execution_time_ms=execution_time,
                    retry_count=attempt
                )
                
                self._add_audit_entry(invocation, "execution_success", {
                    "execution_time_ms": execution_time,
                    "retry_count": attempt
                })
                
                return result
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Tool execution attempt {attempt + 1} failed: {error_msg}")
                
                self._add_audit_entry(invocation, "execution_error", {
                    "attempt": attempt + 1,
                    "error": error_msg,
                    "traceback": traceback.format_exc()
                })
                
                # If this is the last attempt, fail
                if attempt >= schema.max_retries:
                    invocation.status = ToolStatus.FAILED
                    invocation.error_message = error_msg
                    
                    result = ToolResult(
                        invocation_id=invocation.invocation_id,
                        tool_name=invocation.tool_name,
                        success=False,
                        error=error_msg,
                        retry_count=attempt
                    )
                    
                    return result
        
        # Should not reach here, but handle gracefully
        invocation.status = ToolStatus.FAILED
        invocation.error_message = "Maximum retries exceeded"
        
        return ToolResult(
            invocation_id=invocation.invocation_id,
            tool_name=invocation.tool_name,
            success=False,
            error="Maximum retries exceeded",
            retry_count=schema.max_retries
        )
    
    def _finalize_invocation(self, invocation: ToolInvocation, result: ToolResult) -> None:
        """Finalize invocation and move to history."""
        invocation.end_time = datetime.utcnow()
        
        if invocation.start_time and invocation.end_time:
            total_time = int((invocation.end_time - invocation.start_time).total_seconds() * 1000)
            invocation.execution_time_ms = total_time
            result.execution_time_ms = total_time
        
        # Add final audit entry
        self._add_audit_entry(invocation, "invocation_complete", {
            "success": result.success,
            "total_execution_time_ms": invocation.execution_time_ms,
            "final_status": invocation.status.value
        })
        
        # Move to history and remove from active
        self.invocation_history.append(invocation)
        if invocation.invocation_id in self.active_invocations:
            del self.active_invocations[invocation.invocation_id]
        
        # Log audit information
        self._audit_log("tool_invocation_complete", {
            "invocation_id": invocation.invocation_id,
            "tool_name": invocation.tool_name,
            "success": result.success,
            "execution_time_ms": invocation.execution_time_ms,
            "retry_count": invocation.retry_count,
            "error": result.error
        })
    
    def _merge_results(self, results: List[ToolResult]) -> Dict[str, Any]:
        """Merge results by combining all data fields."""
        merged_data = {}
        metadata = {
            "aggregation_strategy": "merge",
            "source_tools": [],
            "total_execution_time_ms": 0,
            "successful_tools": 0,
            "failed_tools": 0
        }
        
        for result in results:
            metadata["source_tools"].append(result.tool_name)
            metadata["total_execution_time_ms"] += result.execution_time_ms
            
            if result.success:
                metadata["successful_tools"] += 1
                if result.data:
                    # Merge data with tool name prefix to avoid conflicts
                    tool_data = {f"{result.tool_name}_{key}": value for key, value in result.data.items()}
                    merged_data.update(tool_data)
            else:
                metadata["failed_tools"] += 1
        
        return {
            "aggregated_data": merged_data,
            "metadata": metadata
        }
    
    def _collect_results(self, results: List[ToolResult]) -> Dict[str, Any]:
        """Collect results as a list of individual tool outputs."""
        collected_data = []
        metadata = {
            "aggregation_strategy": "collect",
            "total_tools": len(results),
            "successful_tools": 0,
            "failed_tools": 0,
            "total_execution_time_ms": 0
        }
        
        for result in results:
            tool_result = {
                "tool_name": result.tool_name,
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "execution_time_ms": result.execution_time_ms
            }
            collected_data.append(tool_result)
            
            metadata["total_execution_time_ms"] += result.execution_time_ms
            if result.success:
                metadata["successful_tools"] += 1
            else:
                metadata["failed_tools"] += 1
        
        return {
            "collected_results": collected_data,
            "metadata": metadata
        }
    
    def _reduce_results(self, results: List[ToolResult]) -> Dict[str, Any]:
        """Reduce results to summary statistics and key metrics."""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        reduced_data = {
            "summary": {
                "total_tools": len(results),
                "successful": len(successful_results),
                "failed": len(failed_results),
                "success_rate": len(successful_results) / len(results) if results else 0
            },
            "performance": {
                "total_execution_time_ms": sum(r.execution_time_ms for r in results),
                "average_execution_time_ms": sum(r.execution_time_ms for r in results) / len(results) if results else 0,
                "fastest_tool": min(results, key=lambda r: r.execution_time_ms).tool_name if results else None,
                "slowest_tool": max(results, key=lambda r: r.execution_time_ms).tool_name if results else None
            },
            "errors": [{"tool": r.tool_name, "error": r.error} for r in failed_results]
        }
        
        # Extract key data points from successful results
        if successful_results:
            key_data = {}
            for result in successful_results:
                if result.data:
                    # Extract commonly used fields
                    for key in ["result", "output", "data", "response"]:
                        if key in result.data:
                            key_data[f"{result.tool_name}_{key}"] = result.data[key]
            
            reduced_data["key_outputs"] = key_data
        
        return {
            "reduced_data": reduced_data,
            "metadata": {
                "aggregation_strategy": "reduce",
                "reduction_timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _matches_audit_filter(
        self,
        invocation: ToolInvocation,
        tool_name: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> bool:
        """Check if invocation matches audit filter criteria."""
        if tool_name and invocation.tool_name != tool_name:
            return False
        
        if start_time and invocation.start_time and invocation.start_time < start_time:
            return False
        
        if end_time and invocation.start_time and invocation.start_time > end_time:
            return False
        
        return True
    
    def _add_audit_entry(
        self,
        invocation: ToolInvocation,
        action: str,
        details: Dict[str, Any]
    ) -> None:
        """Add an audit entry to the invocation."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details
        }
        invocation.audit_trail.append(audit_entry)
    
    def _audit_log(self, action: str, details: Dict[str, Any]) -> None:
        """Log audit information."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details
        }
        
        # In production, this would write to a proper audit log system
        logger.info(f"AUDIT: {action} - {json.dumps(details)}")
    
    def _setup_audit_logger(self) -> logging.Logger:
        """Setup dedicated audit logger."""
        audit_logger = logging.getLogger("agentcore.audit")
        audit_logger.setLevel(logging.INFO)
        
        # In production, add file handler for audit logs
        if not audit_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(message)s'
            )
            handler.setFormatter(formatter)
            audit_logger.addHandler(handler)
        
        return audit_logger
    
    def _register_builtin_schemas(self) -> None:
        """Register built-in tool schemas for common operations."""
        
        # OAuth Manager schema
        oauth_schema = ToolSchema(
            tool_name="oauth_manager",
            input_schema={
                "attendees": {"type": "list", "constraints": {"min_length": 1}},
                "action": {"type": "str", "constraints": {"allowed_values": ["validate_tokens", "refresh_tokens"]}}
            },
            output_schema={
                "valid_tokens": {"type": "list"},
                "invalid_tokens": {"type": "list"},
                "refresh_results": {"type": "dict"}
            },
            required_inputs=["attendees", "action"],
            timeout_ms=5000,
            max_retries=2
        )
        
        # Availability Aggregator schema
        availability_schema = ToolSchema(
            tool_name="availability_aggregator",
            input_schema={
                "attendees": {"type": "list", "constraints": {"min_length": 1}},
                "time_range": {"type": "dict"},
                "duration": {"type": "int", "constraints": {"min_value": 15, "max_value": 480}}
            },
            output_schema={
                "availability_slots": {"type": "list"},
                "conflicts": {"type": "list"},
                "best_slot": {"type": "dict"}
            },
            required_inputs=["attendees"],
            optional_inputs=["time_range", "duration"],
            timeout_ms=10000,
            max_retries=3
        )
        
        # Calendar Service schema
        calendar_schema = ToolSchema(
            tool_name="calendar_service",
            input_schema={
                "action": {"type": "str", "constraints": {"allowed_values": ["create_meeting", "update_meeting", "cancel_meeting"]}},
                "meeting_details": {"type": "dict"},
                "meeting_id": {"type": "str"}
            },
            output_schema={
                "meeting_id": {"type": "str"},
                "status": {"type": "str"},
                "calendar_links": {"type": "list"}
            },
            required_inputs=["action"],
            timeout_ms=8000,
            max_retries=2
        )
        
        # Scheduling Agent schema
        scheduling_schema = ToolSchema(
            tool_name="scheduling_agent",
            input_schema={
                "action": {"type": "str"},
                "meeting_request": {"type": "dict"},
                "availability_data": {"type": "dict"},
                "preferences": {"type": "dict"}
            },
            output_schema={
                "recommended_time": {"type": "dict"},
                "confidence_score": {"type": "float"},
                "alternatives": {"type": "list"},
                "reasoning": {"type": "str"}
            },
            required_inputs=["action"],
            optional_inputs=["meeting_request", "availability_data", "preferences"],
            timeout_ms=15000,
            max_retries=2
        )
        
        # Get Availability Tool schema
        get_availability_schema = ToolSchema(
            tool_name="get_availability",
            input_schema={
                "user_id": {"type": "str", "constraints": {"min_length": 1}},
                "start_date": {"type": "str", "constraints": {"format": "iso_datetime"}},
                "end_date": {"type": "str", "constraints": {"format": "iso_datetime"}},
                "attendees": {"type": "list"},
                "duration_minutes": {"type": "int", "constraints": {"min_value": 15, "max_value": 480}},
                "buffer_minutes": {"type": "int", "constraints": {"min_value": 0, "max_value": 60}},
                "max_results": {"type": "int", "constraints": {"min_value": 1, "max_value": 50}},
                "time_preferences": {"type": "dict"},
                "working_hours_only": {"type": "bool"}
            },
            output_schema={
                "success": {"type": "bool"},
                "available_slots": {"type": "list"},
                "total_slots_found": {"type": "int"},
                "date_range_start": {"type": "str"},
                "date_range_end": {"type": "str"},
                "constraints_applied": {"type": "list"},
                "ranking_factors": {"type": "dict"},
                "execution_time_ms": {"type": "int"}
            },
            required_inputs=["user_id", "start_date", "end_date"],
            optional_inputs=["attendees", "duration_minutes", "buffer_minutes", "max_results", "time_preferences", "working_hours_only"],
            timeout_ms=12000,
            max_retries=2
        )

        # Store schemas (tools will be registered when actual implementations are available)
        self.tool_schemas.update({
            "oauth_manager": oauth_schema,
            "availability_aggregator": availability_schema,
            "calendar_service": calendar_schema,
            "scheduling_agent": scheduling_schema,
            "get_availability": get_availability_schema
        })
        
        logger.info("Built-in tool schemas registered")
    
    def get_registered_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered tools."""
        tools_info = {}
        
        for tool_name, schema in self.tool_schemas.items():
            tools_info[tool_name] = {
                "registered": tool_name in self.registered_tools,
                "required_inputs": schema.required_inputs,
                "optional_inputs": schema.optional_inputs,
                "validation_level": schema.validation_level.value,
                "timeout_ms": schema.timeout_ms,
                "max_retries": schema.max_retries
            }
        
        return tools_info
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics for monitoring."""
        return {
            "registered_tools": len(self.registered_tools),
            "active_invocations": len(self.active_invocations),
            "total_invocations": len(self.invocation_history),
            "success_rate": self._calculate_success_rate(),
            "average_execution_time_ms": self._calculate_average_execution_time(),
            "most_used_tools": self._get_most_used_tools(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate."""
        if not self.invocation_history:
            return 0.0
        
        successful = sum(1 for inv in self.invocation_history if inv.status == ToolStatus.SUCCESS)
        return successful / len(self.invocation_history)
    
    def _calculate_average_execution_time(self) -> float:
        """Calculate average execution time."""
        if not self.invocation_history:
            return 0.0
        
        total_time = sum(inv.execution_time_ms or 0 for inv in self.invocation_history)
        return total_time / len(self.invocation_history)
    
    def _get_most_used_tools(self) -> List[Dict[str, Any]]:
        """Get most frequently used tools."""
        tool_usage = {}
        
        for invocation in self.invocation_history:
            tool_name = invocation.tool_name
            if tool_name not in tool_usage:
                tool_usage[tool_name] = {"count": 0, "success_count": 0}
            
            tool_usage[tool_name]["count"] += 1
            if invocation.status == ToolStatus.SUCCESS:
                tool_usage[tool_name]["success_count"] += 1
        
        # Sort by usage count and add success rate
        sorted_tools = []
        for tool_name, stats in tool_usage.items():
            success_rate = stats["success_count"] / stats["count"] if stats["count"] > 0 else 0
            sorted_tools.append({
                "tool_name": tool_name,
                "usage_count": stats["count"],
                "success_rate": success_rate
            })
        
        return sorted(sorted_tools, key=lambda x: x["usage_count"], reverse=True)[:5]