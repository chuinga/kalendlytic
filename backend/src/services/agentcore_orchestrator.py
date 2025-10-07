"""
AgentCore Orchestrator that integrates Router and Planner for complete agent execution.
Provides the main interface for complex scheduling operations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

try:
    from .agentcore_router import (
        AgentCoreRouter, TaskType, Priority, ExecutionStep, ExecutionContext,
        AgentCoreRouterError
    )
    from .agentcore_planner import (
        AgentCorePlanner, PlanningStrategy, PlanningScenario, PlanningResult,
        AgentCorePlannerError
    )
except ImportError:
    # For standalone testing, import from current directory
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    
    from agentcore_router import (
        AgentCoreRouter, TaskType, Priority, ExecutionStep, ExecutionContext,
        AgentCoreRouterError
    )
    from agentcore_planner import (
        AgentCorePlanner, PlanningStrategy, PlanningScenario, PlanningResult,
        AgentCorePlannerError
    )

logger = logging.getLogger(__name__)


class AgentCoreOrchestratorError(Exception):
    """Custom exception for AgentCore orchestrator errors."""
    pass


class AgentCoreOrchestrator:
    """
    AgentCore Orchestrator that combines Router and Planner capabilities.
    Provides intelligent agent execution with decision trees and context management.
    """
    
    def __init__(self):
        """Initialize the AgentCore orchestrator."""
        self.router = AgentCoreRouter()
        self.planner = AgentCorePlanner()
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        
    def execute_intelligent_scheduling(
        self,
        task_type: TaskType,
        request_data: Dict[str, Any],
        user_id: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        planning_strategy: PlanningStrategy = PlanningStrategy.BALANCED
    ) -> Dict[str, Any]:
        """
        Execute intelligent scheduling with full router/planner integration.
        
        Args:
            task_type: Type of scheduling task
            request_data: Request details
            user_id: User identifier
            user_preferences: Optional user preferences
            planning_strategy: Planning strategy to use
            
        Returns:
            Execution result with recommendations and metadata
        """
        try:
            execution_id = f"exec_{user_id}_{int(datetime.utcnow().timestamp())}"
            logger.info(f"Starting intelligent scheduling execution: {execution_id}")
            
            # Step 1: Create planning scenario
            scenario = self.planner.create_planning_scenario(
                task_type=task_type,
                request_data=request_data,
                user_preferences=user_preferences or {}
            )
            
            # Step 2: Plan complex scenario
            planning_result = self.planner.plan_complex_scenario(
                scenario=scenario,
                strategy=planning_strategy
            )
            
            # Step 3: Create router execution plan
            context_id, router_steps = self.router.plan_execution(
                task_type=task_type,
                request_data=request_data,
                user_id=user_id
            )
            
            # Step 4: Integrate and optimize execution steps
            integrated_steps = self._integrate_execution_plans(
                planning_result.recommended_plan,
                router_steps,
                scenario
            )
            
            # Step 5: Execute with monitoring
            execution_result = self._execute_with_monitoring(
                execution_id=execution_id,
                context_id=context_id,
                steps=integrated_steps,
                scenario=scenario
            )
            
            # Step 6: Compile comprehensive result
            result = {
                'execution_id': execution_id,
                'context_id': context_id,
                'task_type': task_type.value,
                'planning_metadata': {
                    'scenario_id': scenario.scenario_id,
                    'confidence_score': planning_result.confidence_score,
                    'estimated_success_rate': planning_result.estimated_success_rate,
                    'risk_factors': planning_result.risk_factors,
                    'optimization_metrics': planning_result.optimization_metrics,
                    'alternative_plans_count': len(planning_result.alternative_plans)
                },
                'execution_result': execution_result,
                'recommendations': self._generate_recommendations(
                    planning_result, execution_result, scenario
                ),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Intelligent scheduling completed: {execution_id}")
            return result
            
        except (AgentCoreRouterError, AgentCorePlannerError) as e:
            logger.error(f"AgentCore error in intelligent scheduling: {e}")
            raise AgentCoreOrchestratorError(f"Intelligent scheduling failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in intelligent scheduling: {e}")
            raise AgentCoreOrchestratorError(f"Execution failed: {e}")
    
    def handle_complex_conflicts(
        self,
        context_id: str,
        conflicts: List[Dict[str, Any]],
        available_alternatives: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Handle complex scheduling conflicts using both router and planner.
        
        Args:
            context_id: Execution context identifier
            conflicts: List of detected conflicts
            available_alternatives: Alternative options available
            
        Returns:
            Conflict resolution result
        """
        try:
            logger.info(f"Handling complex conflicts for context: {context_id}")
            
            # Get execution context
            context = self.router.get_context(context_id)
            if not context:
                raise AgentCoreOrchestratorError(f"Context not found: {context_id}")
            
            # Create scenario from context
            scenario = self._context_to_scenario(context)
            
            # Use planner for conflict analysis and resolution planning
            planner_resolution_steps = self.planner.handle_planning_conflicts(
                scenario=scenario,
                detected_conflicts=conflicts
            )
            
            # Use router for execution-level conflict handling
            router_resolution_steps = self.router.handle_conflicts(
                context_id=context_id,
                conflicts=conflicts,
                available_alternatives=available_alternatives
            )
            
            # Integrate resolution approaches
            integrated_resolution = self._integrate_conflict_resolution(
                planner_steps=planner_resolution_steps,
                router_steps=router_resolution_steps,
                conflicts=conflicts
            )
            
            # Execute resolution
            resolution_result = self._execute_conflict_resolution(
                context_id=context_id,
                resolution_steps=integrated_resolution,
                conflicts=conflicts
            )
            
            result = {
                'context_id': context_id,
                'conflicts_resolved': len(conflicts),
                'resolution_approach': 'integrated_router_planner',
                'resolution_steps_executed': len(integrated_resolution),
                'resolution_result': resolution_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Complex conflicts resolved for context: {context_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to handle complex conflicts: {e}")
            raise AgentCoreOrchestratorError(f"Conflict resolution failed: {e}")
    
    def optimize_multi_step_operation(
        self,
        operations: List[Dict[str, Any]],
        user_id: str,
        optimization_goals: List[str]
    ) -> Dict[str, Any]:
        """
        Optimize a multi-step scheduling operation across multiple tasks.
        
        Args:
            operations: List of scheduling operations to optimize
            user_id: User identifier
            optimization_goals: Goals for optimization
            
        Returns:
            Optimized execution plan
        """
        try:
            logger.info(f"Optimizing multi-step operation for user: {user_id}")
            
            # Create integrated scenario for all operations
            integrated_scenario = self._create_integrated_scenario(
                operations=operations,
                user_id=user_id,
                optimization_goals=optimization_goals
            )
            
            # Plan with optimal strategy
            planning_result = self.planner.plan_complex_scenario(
                scenario=integrated_scenario,
                strategy=PlanningStrategy.OPTIMAL
            )
            
            # Create execution contexts for each operation
            execution_contexts = []
            for i, operation in enumerate(operations):
                task_type = TaskType(operation['task_type'])
                context_id, steps = self.router.plan_execution(
                    task_type=task_type,
                    request_data=operation['request_data'],
                    user_id=user_id,
                    session_id=f"multi_step_{i}"
                )
                execution_contexts.append({
                    'context_id': context_id,
                    'steps': steps,
                    'operation': operation
                })
            
            # Optimize execution order across all operations
            optimized_plan = self._optimize_cross_operation_execution(
                planning_result=planning_result,
                execution_contexts=execution_contexts,
                optimization_goals=optimization_goals
            )
            
            result = {
                'optimization_id': f"multi_{user_id}_{int(datetime.utcnow().timestamp())}",
                'operations_count': len(operations),
                'integrated_scenario_id': integrated_scenario.scenario_id,
                'optimized_plan': optimized_plan,
                'execution_contexts': [ctx['context_id'] for ctx in execution_contexts],
                'optimization_metrics': planning_result.optimization_metrics,
                'estimated_total_time_ms': sum(
                    step['estimated_duration_ms'] for step in optimized_plan
                ),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Multi-step operation optimized: {len(operations)} operations")
            return result
            
        except Exception as e:
            logger.error(f"Failed to optimize multi-step operation: {e}")
            raise AgentCoreOrchestratorError(f"Multi-step optimization failed: {e}")
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of an active execution."""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        else:
            return {'status': 'not_found', 'execution_id': execution_id}
    
    def _integrate_execution_plans(
        self,
        planner_steps: List[ExecutionStep],
        router_steps: List[ExecutionStep],
        scenario: PlanningScenario
    ) -> List[ExecutionStep]:
        """Integrate execution plans from planner and router."""
        # Combine and deduplicate steps
        all_steps = planner_steps + router_steps
        
        # Remove duplicates based on step_id and action
        seen_combinations = set()
        integrated_steps = []
        
        for step in all_steps:
            step_key = (step.step_id, step.action)
            if step_key not in seen_combinations:
                seen_combinations.add(step_key)
                integrated_steps.append(step)
        
        # Optimize execution order using planner
        optimized_steps = self.planner.optimize_execution_order(
            steps=integrated_steps,
            constraints=scenario.constraints
        )
        
        return optimized_steps
    
    def _execute_with_monitoring(
        self,
        execution_id: str,
        context_id: str,
        steps: List[ExecutionStep],
        scenario: PlanningScenario
    ) -> Dict[str, Any]:
        """Execute steps with monitoring and error handling."""
        # Track execution
        self.active_executions[execution_id] = {
            'status': 'running',
            'context_id': context_id,
            'total_steps': len(steps),
            'completed_steps': 0,
            'current_step': None,
            'start_time': datetime.utcnow().isoformat(),
            'errors': []
        }
        
        execution_results = []
        
        try:
            for i, step in enumerate(steps):
                # Update monitoring
                self.active_executions[execution_id]['current_step'] = step.step_id
                self.active_executions[execution_id]['completed_steps'] = i
                
                # Simulate step execution (in real implementation, this would call actual services)
                step_result = self._simulate_step_execution(step)
                execution_results.append({
                    'step_id': step.step_id,
                    'result': step_result,
                    'execution_time_ms': step.estimated_duration_ms,
                    'success': step_result.get('success', True)
                })
                
                # Update router context
                self.router.update_context(
                    context_id=context_id,
                    step_result=step_result,
                    next_step_index=i + 1
                )
            
            # Mark as completed
            self.active_executions[execution_id]['status'] = 'completed'
            self.active_executions[execution_id]['completed_steps'] = len(steps)
            self.active_executions[execution_id]['end_time'] = datetime.utcnow().isoformat()
            
            return {
                'status': 'success',
                'steps_executed': len(steps),
                'execution_results': execution_results,
                'total_time_ms': sum(r['execution_time_ms'] for r in execution_results)
            }
            
        except Exception as e:
            # Mark as failed
            self.active_executions[execution_id]['status'] = 'failed'
            self.active_executions[execution_id]['errors'].append(str(e))
            
            logger.error(f"Execution failed for {execution_id}: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'steps_completed': len(execution_results),
                'execution_results': execution_results
            }
    
    def _simulate_step_execution(self, step: ExecutionStep) -> Dict[str, Any]:
        """Simulate step execution (placeholder for actual implementation)."""
        # In real implementation, this would call the actual services
        return {
            'success': True,
            'step_id': step.step_id,
            'tool_type': step.tool_type,
            'action': step.action,
            'result_data': f"Simulated result for {step.action}",
            'execution_time_ms': step.estimated_duration_ms
        }
    
    def _generate_recommendations(
        self,
        planning_result: PlanningResult,
        execution_result: Dict[str, Any],
        scenario: PlanningScenario
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on planning and execution results."""
        recommendations = []
        
        # Performance recommendations
        if planning_result.confidence_score < 0.7:
            recommendations.append({
                'type': 'performance',
                'priority': 'medium',
                'message': 'Consider simplifying constraints to improve scheduling confidence',
                'action': 'review_constraints'
            })
        
        # Risk mitigation recommendations
        if planning_result.risk_factors:
            recommendations.append({
                'type': 'risk_mitigation',
                'priority': 'high',
                'message': f"Identified {len(planning_result.risk_factors)} risk factors",
                'details': planning_result.risk_factors,
                'action': 'review_risks'
            })
        
        # Alternative plan recommendations
        if len(planning_result.alternative_plans) > 0:
            recommendations.append({
                'type': 'alternatives',
                'priority': 'low',
                'message': f"{len(planning_result.alternative_plans)} alternative plans available",
                'action': 'review_alternatives'
            })
        
        # Execution optimization recommendations
        if execution_result.get('status') == 'success':
            total_time = execution_result.get('total_time_ms', 0)
            if total_time > 10000:  # More than 10 seconds
                recommendations.append({
                    'type': 'optimization',
                    'priority': 'medium',
                    'message': 'Execution time could be optimized',
                    'action': 'optimize_execution'
                })
        
        return recommendations   
 
    def _context_to_scenario(self, context: ExecutionContext) -> PlanningScenario:
        """Convert execution context to planning scenario."""
        from .agentcore_planner import PlanningConstraint, ConstraintType
        
        # Create basic constraints from context
        constraints = [
            PlanningConstraint(
                constraint_type=ConstraintType.TIME_WINDOW,
                value=context.original_request.get('time_range'),
                weight=0.8,
                is_hard=True
            )
        ]
        
        scenario = PlanningScenario(
            scenario_id=f"context_{context.session_id}",
            primary_task=context.task_type,
            constraints=constraints,
            attendees=context.original_request.get('attendees', []),
            time_preferences=context.original_request.get('time_preferences', {}),
            resource_requirements=context.original_request.get('resources', []),
            conflict_tolerance=0.5,
            optimization_goals=['minimize_conflicts'],
            fallback_options=[]
        )
        
        return scenario
    
    def _integrate_conflict_resolution(
        self,
        planner_steps: List[ExecutionStep],
        router_steps: List[ExecutionStep],
        conflicts: List[Dict[str, Any]]
    ) -> List[ExecutionStep]:
        """Integrate conflict resolution steps from planner and router."""
        # Prioritize planner steps for complex analysis, router steps for execution
        integrated_steps = []
        
        # Add planner analysis steps first
        analysis_steps = [s for s in planner_steps if 'analyze' in s.action.lower()]
        integrated_steps.extend(analysis_steps)
        
        # Add router execution steps
        execution_steps = [s for s in router_steps if 'execute' in s.action.lower() or 'update' in s.action.lower()]
        integrated_steps.extend(execution_steps)
        
        # Add remaining steps
        remaining_planner = [s for s in planner_steps if s not in analysis_steps]
        remaining_router = [s for s in router_steps if s not in execution_steps]
        integrated_steps.extend(remaining_planner)
        integrated_steps.extend(remaining_router)
        
        return integrated_steps
    
    def _execute_conflict_resolution(
        self,
        context_id: str,
        resolution_steps: List[ExecutionStep],
        conflicts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute conflict resolution steps."""
        resolution_results = []
        
        for step in resolution_steps:
            # Simulate resolution step execution
            step_result = {
                'step_id': step.step_id,
                'action': step.action,
                'success': True,
                'conflicts_addressed': len(conflicts) if 'resolve' in step.action.lower() else 0,
                'execution_time_ms': step.estimated_duration_ms
            }
            resolution_results.append(step_result)
        
        return {
            'status': 'resolved',
            'resolution_steps': len(resolution_steps),
            'conflicts_resolved': len(conflicts),
            'total_time_ms': sum(r['execution_time_ms'] for r in resolution_results),
            'step_results': resolution_results
        }
    
    def _create_integrated_scenario(
        self,
        operations: List[Dict[str, Any]],
        user_id: str,
        optimization_goals: List[str]
    ) -> PlanningScenario:
        """Create an integrated scenario for multiple operations."""
        from .agentcore_planner import PlanningConstraint, ConstraintType
        
        # Aggregate all attendees
        all_attendees = set()
        all_constraints = []
        all_resources = set()
        
        for operation in operations:
            request_data = operation['request_data']
            all_attendees.update(request_data.get('attendees', []))
            all_resources.update(request_data.get('resources', []))
            
            # Add operation-specific constraints
            if 'time_range' in request_data:
                all_constraints.append(PlanningConstraint(
                    constraint_type=ConstraintType.TIME_WINDOW,
                    value=request_data['time_range'],
                    weight=0.7,
                    is_hard=True
                ))
        
        scenario = PlanningScenario(
            scenario_id=f"integrated_{user_id}_{int(datetime.utcnow().timestamp())}",
            primary_task=TaskType.SCHEDULE_MEETING,  # Default for multi-operation
            constraints=all_constraints,
            attendees=list(all_attendees),
            time_preferences={},
            resource_requirements=list(all_resources),
            conflict_tolerance=0.4,  # Lower tolerance for multi-operation
            optimization_goals=optimization_goals,
            fallback_options=[]
        )
        
        return scenario
    
    def _optimize_cross_operation_execution(
        self,
        planning_result: PlanningResult,
        execution_contexts: List[Dict[str, Any]],
        optimization_goals: List[str]
    ) -> List[Dict[str, Any]]:
        """Optimize execution order across multiple operations."""
        optimized_plan = []
        
        # Create a unified execution plan
        for i, context in enumerate(execution_contexts):
            for step in context['steps']:
                optimized_plan.append({
                    'operation_index': i,
                    'context_id': context['context_id'],
                    'step_id': step.step_id,
                    'tool_type': step.tool_type,
                    'action': step.action,
                    'priority': step.priority.value,
                    'estimated_duration_ms': step.estimated_duration_ms,
                    'dependencies': step.dependencies
                })
        
        # Sort by priority and dependencies (simplified optimization)
        optimized_plan.sort(key=lambda x: (-x['priority'], x['estimated_duration_ms']))
        
        return optimized_plan
    
    def cleanup_execution(self, execution_id: str) -> None:
        """Clean up completed execution."""
        if execution_id in self.active_executions:
            execution_data = self.active_executions.pop(execution_id)
            
            # Clean up associated router context
            context_id = execution_data.get('context_id')
            if context_id:
                self.router.cleanup_context(context_id)
            
            logger.info(f"Execution cleaned up: {execution_id}")
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            'active_executions': len(self.active_executions),
            'router_stats': {
                'active_contexts': len(self.router.active_contexts),
                'execution_history_count': len(self.router.execution_history)
            },
            'planner_stats': {
                'cached_plans': len(self.planner.planning_cache),
                'scenario_templates': len(self.planner.scenario_templates)
            },
            'timestamp': datetime.utcnow().isoformat()
        }