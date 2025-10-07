"""
AgentCore Planner for complex scheduling scenario planning and optimization.
Works with the AgentCore Router to provide intelligent planning capabilities.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Import TaskType and other classes from router when available
try:
    from .agentcore_router import TaskType, Priority, ExecutionStep, ExecutionContext
except ImportError:
    # Define locally if import fails (for standalone testing)
    class TaskType:
        SCHEDULE_MEETING = "schedule_meeting"
        RESOLVE_CONFLICT = "resolve_conflict"
        FIND_AVAILABILITY = "find_availability"
        RESCHEDULE_MEETING = "reschedule_meeting"
        CANCEL_MEETING = "cancel_meeting"
        UPDATE_PREFERENCES = "update_preferences"
        GENERATE_COMMUNICATION = "generate_communication"
    
    class Priority:
        LOW = 1
        MEDIUM = 2
        HIGH = 3
        CRITICAL = 4
    
    @dataclass
    class ExecutionStep:
        step_id: str
        tool_type: str
        action: str
        inputs: Dict[str, Any]
        dependencies: List[str]
        priority: int
        estimated_duration_ms: int
        retry_count: int = 0
        max_retries: int = 3

logger = logging.getLogger(__name__)


class PlanningStrategy(Enum):
    """Planning strategies for different scenarios."""
    GREEDY = "greedy"  # Quick, first-available solution
    OPTIMAL = "optimal"  # Best possible solution considering all factors
    BALANCED = "balanced"  # Balance between speed and quality
    CONSERVATIVE = "conservative"  # Minimize risk and conflicts


class ConstraintType(Enum):
    """Types of scheduling constraints."""
    TIME_WINDOW = "time_window"
    ATTENDEE_AVAILABILITY = "attendee_availability"
    RESOURCE_AVAILABILITY = "resource_availability"
    BUSINESS_HOURS = "business_hours"
    TIMEZONE = "timezone"
    DURATION = "duration"
    PRIORITY = "priority"


@dataclass
class PlanningConstraint:
    """Individual planning constraint."""
    constraint_type: ConstraintType
    value: Any
    weight: float  # 0.0 to 1.0, higher means more important
    is_hard: bool  # True = must satisfy, False = prefer to satisfy


@dataclass
class PlanningScenario:
    """Complex scheduling scenario definition."""
    scenario_id: str
    primary_task: TaskType
    constraints: List[PlanningConstraint]
    attendees: List[str]
    time_preferences: Dict[str, Any]
    resource_requirements: List[str]
    conflict_tolerance: float  # 0.0 to 1.0
    optimization_goals: List[str]
    fallback_options: List[Dict[str, Any]]


@dataclass
class PlanningResult:
    """Result of planning operation."""
    scenario_id: str
    recommended_plan: List[ExecutionStep]
    alternative_plans: List[List[ExecutionStep]]
    confidence_score: float
    estimated_success_rate: float
    risk_factors: List[str]
    optimization_metrics: Dict[str, float]
    execution_time_estimate_ms: int


class AgentCorePlannerError(Exception):
    """Custom exception for AgentCore planner errors."""
    pass


class AgentCorePlanner:
    """
    AgentCore Planner for complex scheduling scenarios.
    Provides intelligent planning and optimization for multi-step operations.
    """
    
    def __init__(self):
        """Initialize the AgentCore planner."""
        self.planning_cache: Dict[str, PlanningResult] = {}
        self.scenario_templates: Dict[str, PlanningScenario] = {}
        self.optimization_weights = {
            'time_efficiency': 0.3,
            'attendee_satisfaction': 0.25,
            'conflict_minimization': 0.2,
            'resource_optimization': 0.15,
            'cost_efficiency': 0.1
        }
    
    def create_planning_scenario(
        self,
        task_type: TaskType,
        request_data: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> PlanningScenario:
        """
        Create a planning scenario from request data.
        
        Args:
            task_type: Type of scheduling task
            request_data: Request details
            user_preferences: User scheduling preferences
            
        Returns:
            PlanningScenario object
        """
        try:
            scenario_id = f"{task_type}_{int(datetime.utcnow().timestamp())}"
            
            # Extract constraints from request
            constraints = self._extract_constraints(request_data, user_preferences)
            
            # Determine optimization goals
            optimization_goals = self._determine_optimization_goals(task_type, request_data)
            
            # Create fallback options
            fallback_options = self._generate_fallback_options(task_type, request_data)
            
            scenario = PlanningScenario(
                scenario_id=scenario_id,
                primary_task=task_type,
                constraints=constraints,
                attendees=request_data.get('attendees', []),
                time_preferences=request_data.get('time_preferences', {}),
                resource_requirements=request_data.get('resources', []),
                conflict_tolerance=user_preferences.get('conflict_tolerance', 0.3),
                optimization_goals=optimization_goals,
                fallback_options=fallback_options
            )
            
            logger.info(f"Planning scenario created: {scenario_id} with {len(constraints)} constraints")
            return scenario
            
        except Exception as e:
            logger.error(f"Failed to create planning scenario: {e}")
            raise AgentCorePlannerError(f"Scenario creation failed: {e}")
    
    def plan_complex_scenario(
        self,
        scenario: PlanningScenario,
        strategy: PlanningStrategy = PlanningStrategy.BALANCED
    ) -> PlanningResult:
        """
        Plan execution for a complex scheduling scenario.
        
        Args:
            scenario: Planning scenario to solve
            strategy: Planning strategy to use
            
        Returns:
            PlanningResult with recommended execution plan
        """
        try:
            # Check cache first
            cache_key = f"{scenario.scenario_id}_{strategy.value}"
            if cache_key in self.planning_cache:
                logger.info(f"Using cached planning result for {scenario.scenario_id}")
                return self.planning_cache[cache_key]
            
            # Generate multiple plan options
            plan_options = self._generate_plan_options(scenario, strategy)
            
            # Evaluate and rank plans
            evaluated_plans = self._evaluate_plans(plan_options, scenario)
            
            # Select best plan
            best_plan = evaluated_plans[0] if evaluated_plans else []
            alternative_plans = evaluated_plans[1:3] if len(evaluated_plans) > 1 else []
            
            # Calculate metrics
            confidence_score = self._calculate_confidence_score(best_plan, scenario)
            success_rate = self._estimate_success_rate(best_plan, scenario)
            risk_factors = self._identify_risk_factors(best_plan, scenario)
            optimization_metrics = self._calculate_optimization_metrics(best_plan, scenario)
            execution_time = sum(step.estimated_duration_ms for step in best_plan)
            
            result = PlanningResult(
                scenario_id=scenario.scenario_id,
                recommended_plan=best_plan,
                alternative_plans=alternative_plans,
                confidence_score=confidence_score,
                estimated_success_rate=success_rate,
                risk_factors=risk_factors,
                optimization_metrics=optimization_metrics,
                execution_time_estimate_ms=execution_time
            )
            
            # Cache result
            self.planning_cache[cache_key] = result
            
            logger.info(f"Complex scenario planned: {len(best_plan)} steps, {confidence_score:.2f} confidence")
            return result
            
        except Exception as e:
            logger.error(f"Failed to plan complex scenario: {e}")
            raise AgentCorePlannerError(f"Complex planning failed: {e}")
    
    def optimize_execution_order(
        self,
        steps: List[ExecutionStep],
        constraints: List[PlanningConstraint]
    ) -> List[ExecutionStep]:
        """
        Optimize the execution order of steps based on constraints.
        
        Args:
            steps: List of execution steps to optimize
            constraints: Planning constraints to consider
            
        Returns:
            Optimized list of execution steps
        """
        try:
            # Create dependency graph
            dependency_graph = self._build_dependency_graph(steps)
            
            # Apply constraint-based optimization
            optimized_order = self._optimize_with_constraints(dependency_graph, constraints)
            
            # Reorder steps based on optimization
            optimized_steps = [steps[i] for i in optimized_order]
            
            logger.info(f"Execution order optimized: {len(steps)} steps reordered")
            return optimized_steps
            
        except Exception as e:
            logger.error(f"Failed to optimize execution order: {e}")
            raise AgentCorePlannerError(f"Execution optimization failed: {e}")
    
    def handle_planning_conflicts(
        self,
        scenario: PlanningScenario,
        detected_conflicts: List[Dict[str, Any]]
    ) -> List[ExecutionStep]:
        """
        Handle conflicts detected during planning.
        
        Args:
            scenario: Original planning scenario
            detected_conflicts: List of detected conflicts
            
        Returns:
            Updated execution steps to resolve conflicts
        """
        try:
            # Analyze conflict impact
            conflict_impact = self._analyze_conflict_impact(detected_conflicts, scenario)
            
            # Determine resolution approach
            resolution_approach = self._select_resolution_approach(conflict_impact, scenario)
            
            # Generate resolution steps
            resolution_steps = self._generate_resolution_steps(
                resolution_approach, detected_conflicts, scenario
            )
            
            logger.info(f"Planning conflicts handled: {len(detected_conflicts)} conflicts, {len(resolution_steps)} resolution steps")
            return resolution_steps
            
        except Exception as e:
            logger.error(f"Failed to handle planning conflicts: {e}")
            raise AgentCorePlannerError(f"Conflict handling failed: {e}")
    
    def _extract_constraints(
        self,
        request_data: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> List[PlanningConstraint]:
        """Extract planning constraints from request and preferences."""
        constraints = []
        
        # Time window constraints
        if 'time_range' in request_data:
            constraints.append(PlanningConstraint(
                constraint_type=ConstraintType.TIME_WINDOW,
                value=request_data['time_range'],
                weight=0.9,
                is_hard=True
            ))
        
        # Business hours constraint
        if user_preferences.get('respect_business_hours', True):
            constraints.append(PlanningConstraint(
                constraint_type=ConstraintType.BUSINESS_HOURS,
                value=user_preferences.get('business_hours', {'start': '09:00', 'end': '17:00'}),
                weight=0.7,
                is_hard=False
            ))
        
        # Duration constraint
        if 'duration_minutes' in request_data:
            constraints.append(PlanningConstraint(
                constraint_type=ConstraintType.DURATION,
                value=request_data['duration_minutes'],
                weight=0.8,
                is_hard=True
            ))
        
        # Priority constraint
        if 'priority' in request_data:
            constraints.append(PlanningConstraint(
                constraint_type=ConstraintType.PRIORITY,
                value=request_data['priority'],
                weight=0.6,
                is_hard=False
            ))
        
        return constraints
    
    def _determine_optimization_goals(
        self,
        task_type: TaskType,
        request_data: Dict[str, Any]
    ) -> List[str]:
        """Determine optimization goals based on task type and request."""
        goals = ['minimize_conflicts', 'maximize_attendee_satisfaction']
        
        if task_type == TaskType.SCHEDULE_MEETING:
            goals.extend(['optimize_time_slots', 'minimize_travel_time'])
        elif task_type == TaskType.RESOLVE_CONFLICT:
            goals.extend(['minimize_disruption', 'preserve_priorities'])
        elif task_type == TaskType.RESCHEDULE_MEETING:
            goals.extend(['minimize_notice_time', 'preserve_attendee_availability'])
        
        # Add request-specific goals
        if request_data.get('optimize_for_cost'):
            goals.append('minimize_cost')
        if request_data.get('optimize_for_speed'):
            goals.append('minimize_execution_time')
        
        return goals
    
    def _generate_fallback_options(
        self,
        task_type: TaskType,
        request_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate fallback options for the scenario."""
        fallbacks = []
        
        # Common fallbacks
        fallbacks.append({
            'type': 'reduce_attendees',
            'description': 'Schedule with core attendees only',
            'impact': 'medium'
        })
        
        fallbacks.append({
            'type': 'extend_time_window',
            'description': 'Expand available time slots',
            'impact': 'low'
        })
        
        # Task-specific fallbacks
        if task_type == TaskType.SCHEDULE_MEETING:
            fallbacks.append({
                'type': 'split_meeting',
                'description': 'Split into multiple smaller meetings',
                'impact': 'high'
            })
        
        return fallbacks    

    def _generate_plan_options(
        self,
        scenario: PlanningScenario,
        strategy: PlanningStrategy
    ) -> List[List[ExecutionStep]]:
        """Generate multiple plan options based on strategy."""
        plan_options = []
        
        if strategy == PlanningStrategy.GREEDY:
            # Quick, first-available solution
            plan_options.append(self._generate_greedy_plan(scenario))
        
        elif strategy == PlanningStrategy.OPTIMAL:
            # Generate multiple optimal plans
            plan_options.extend(self._generate_optimal_plans(scenario))
        
        elif strategy == PlanningStrategy.BALANCED:
            # Balance between speed and quality
            plan_options.append(self._generate_greedy_plan(scenario))
            plan_options.extend(self._generate_optimal_plans(scenario)[:2])
        
        elif strategy == PlanningStrategy.CONSERVATIVE:
            # Minimize risk
            plan_options.append(self._generate_conservative_plan(scenario))
        
        return plan_options
    
    def _generate_greedy_plan(self, scenario: PlanningScenario) -> List[ExecutionStep]:
        """Generate a greedy (fast) execution plan."""
        steps = []
        
        # Basic validation step
        steps.append(ExecutionStep(
            step_id="quick_validation",
            tool_type="oauth_manager",
            action="quick_validate",
            inputs={"attendees": scenario.attendees[:3]},  # Limit for speed
            dependencies=[],
            priority=Priority.HIGH,
            estimated_duration_ms=300
        ))
        
        # Fast availability check
        steps.append(ExecutionStep(
            step_id="fast_availability",
            tool_type="availability_aggregator",
            action="get_basic_availability",
            inputs={
                "attendees": scenario.attendees,
                "time_range": scenario.time_preferences.get('preferred_range')
            },
            dependencies=["quick_validation"],
            priority=Priority.HIGH,
            estimated_duration_ms=800
        ))
        
        # Quick scheduling
        steps.append(ExecutionStep(
            step_id="quick_schedule",
            tool_type="calendar_service",
            action="schedule_first_available",
            inputs={"availability": "{{fast_availability.result}}"},
            dependencies=["fast_availability"],
            priority=Priority.HIGH,
            estimated_duration_ms=500
        ))
        
        return steps
    
    def _generate_optimal_plans(self, scenario: PlanningScenario) -> List[List[ExecutionStep]]:
        """Generate optimal execution plans."""
        plans = []
        
        # Plan 1: AI-optimized approach
        ai_plan = []
        ai_plan.append(ExecutionStep(
            step_id="comprehensive_validation",
            tool_type="oauth_manager",
            action="validate_all_tokens",
            inputs={"attendees": scenario.attendees},
            dependencies=[],
            priority=Priority.HIGH,
            estimated_duration_ms=1000
        ))
        
        ai_plan.append(ExecutionStep(
            step_id="detailed_availability",
            tool_type="availability_aggregator",
            action="get_comprehensive_availability",
            inputs={
                "attendees": scenario.attendees,
                "constraints": [c.__dict__ for c in scenario.constraints]
            },
            dependencies=["comprehensive_validation"],
            priority=Priority.HIGH,
            estimated_duration_ms=2500
        ))
        
        ai_plan.append(ExecutionStep(
            step_id="ai_optimization",
            tool_type="scheduling_agent",
            action="find_optimal_time",
            inputs={
                "availability": "{{detailed_availability.result}}",
                "preferences": scenario.time_preferences,
                "optimization_goals": scenario.optimization_goals
            },
            dependencies=["detailed_availability"],
            priority=Priority.MEDIUM,
            estimated_duration_ms=3500
        ))
        
        ai_plan.append(ExecutionStep(
            step_id="optimal_schedule",
            tool_type="calendar_service",
            action="create_optimized_meeting",
            inputs={"optimization_result": "{{ai_optimization.result}}"},
            dependencies=["ai_optimization"],
            priority=Priority.HIGH,
            estimated_duration_ms=1500
        ))
        
        plans.append(ai_plan)
        
        # Plan 2: Constraint-focused approach
        constraint_plan = []
        constraint_plan.append(ExecutionStep(
            step_id="constraint_analysis",
            tool_type="scheduling_agent",
            action="analyze_constraints",
            inputs={"constraints": [c.__dict__ for c in scenario.constraints]},
            dependencies=[],
            priority=Priority.MEDIUM,
            estimated_duration_ms=1200
        ))
        
        constraint_plan.append(ExecutionStep(
            step_id="constraint_based_scheduling",
            tool_type="calendar_service",
            action="schedule_with_constraints",
            inputs={"constraint_analysis": "{{constraint_analysis.result}}"},
            dependencies=["constraint_analysis"],
            priority=Priority.HIGH,
            estimated_duration_ms=2000
        ))
        
        plans.append(constraint_plan)
        
        return plans
    
    def _generate_conservative_plan(self, scenario: PlanningScenario) -> List[ExecutionStep]:
        """Generate a conservative (low-risk) execution plan."""
        steps = []
        
        # Extensive validation
        steps.append(ExecutionStep(
            step_id="extensive_validation",
            tool_type="oauth_manager",
            action="validate_with_backup",
            inputs={"attendees": scenario.attendees},
            dependencies=[],
            priority=Priority.HIGH,
            estimated_duration_ms=1500
        ))
        
        # Risk assessment
        steps.append(ExecutionStep(
            step_id="risk_assessment",
            tool_type="scheduling_agent",
            action="assess_scheduling_risks",
            inputs={
                "scenario": scenario.__dict__,
                "fallback_options": scenario.fallback_options
            },
            dependencies=["extensive_validation"],
            priority=Priority.MEDIUM,
            estimated_duration_ms=2000
        ))
        
        # Conservative scheduling with fallbacks
        steps.append(ExecutionStep(
            step_id="conservative_schedule",
            tool_type="calendar_service",
            action="schedule_with_fallbacks",
            inputs={
                "risk_assessment": "{{risk_assessment.result}}",
                "fallback_options": scenario.fallback_options
            },
            dependencies=["risk_assessment"],
            priority=Priority.HIGH,
            estimated_duration_ms=2500
        ))
        
        return steps
    
    def _evaluate_plans(
        self,
        plan_options: List[List[ExecutionStep]],
        scenario: PlanningScenario
    ) -> List[List[ExecutionStep]]:
        """Evaluate and rank plan options."""
        scored_plans = []
        
        for plan in plan_options:
            score = self._calculate_plan_score(plan, scenario)
            scored_plans.append((score, plan))
        
        # Sort by score (descending)
        scored_plans.sort(key=lambda x: x[0], reverse=True)
        
        return [plan for score, plan in scored_plans]
    
    def _calculate_plan_score(
        self,
        plan: List[ExecutionStep],
        scenario: PlanningScenario
    ) -> float:
        """Calculate a score for a plan based on multiple factors."""
        score = 0.0
        
        # Time efficiency (lower execution time = higher score)
        total_time = sum(step.estimated_duration_ms for step in plan)
        time_score = max(0, 1.0 - (total_time / 10000))  # Normalize to 10 seconds max
        score += time_score * self.optimization_weights['time_efficiency']
        
        # Step count (fewer steps = higher score for simplicity)
        step_score = max(0, 1.0 - (len(plan) / 10))  # Normalize to 10 steps max
        score += step_score * 0.2
        
        # Priority alignment (higher priority steps = higher score)
        priority_score = sum(step.priority for step in plan) / (len(plan) * 4)
        score += priority_score * 0.3
        
        # Constraint satisfaction (placeholder - would need actual constraint checking)
        constraint_score = 0.8  # Assume good constraint satisfaction
        score += constraint_score * 0.3
        
        return min(1.0, score)  # Cap at 1.0
    
    def _calculate_confidence_score(
        self,
        plan: List[ExecutionStep],
        scenario: PlanningScenario
    ) -> float:
        """Calculate confidence score for a plan."""
        # Base confidence on plan complexity and constraint satisfaction
        base_confidence = 0.8
        
        # Reduce confidence for complex scenarios
        if len(scenario.constraints) > 5:
            base_confidence -= 0.1
        if len(scenario.attendees) > 10:
            base_confidence -= 0.1
        if scenario.conflict_tolerance < 0.3:
            base_confidence -= 0.1
        
        # Increase confidence for well-structured plans
        if len(plan) <= 5:
            base_confidence += 0.1
        if all(step.priority >= 2 for step in plan):
            base_confidence += 0.05
        
        return max(0.0, min(1.0, base_confidence))
    
    def _estimate_success_rate(
        self,
        plan: List[ExecutionStep],
        scenario: PlanningScenario
    ) -> float:
        """Estimate success rate for a plan."""
        # Base success rate
        success_rate = 0.85
        
        # Adjust based on plan characteristics
        for step in plan:
            if step.max_retries > 0:
                success_rate += 0.02  # Retries increase success rate
            if step.priority == Priority.CRITICAL:
                success_rate -= 0.05  # Critical steps are riskier
        
        # Adjust based on scenario complexity
        complexity_factor = len(scenario.constraints) * 0.01
        success_rate -= complexity_factor
        
        return max(0.0, min(1.0, success_rate))
    
    def _identify_risk_factors(
        self,
        plan: List[ExecutionStep],
        scenario: PlanningScenario
    ) -> List[str]:
        """Identify potential risk factors in the plan."""
        risks = []
        
        # Check for high-risk steps
        critical_steps = [s for s in plan if s.priority == Priority.CRITICAL]
        if critical_steps:
            risks.append(f"Contains {len(critical_steps)} critical steps")
        
        # Check for long execution times
        long_steps = [s for s in plan if s.estimated_duration_ms > 3000]
        if long_steps:
            risks.append(f"Contains {len(long_steps)} time-intensive steps")
        
        # Check for complex dependencies
        complex_deps = [s for s in plan if len(s.dependencies) > 2]
        if complex_deps:
            risks.append(f"Contains {len(complex_deps)} steps with complex dependencies")
        
        # Check scenario-specific risks
        if len(scenario.attendees) > 15:
            risks.append("Large number of attendees increases coordination complexity")
        
        if scenario.conflict_tolerance < 0.2:
            risks.append("Low conflict tolerance limits flexibility")
        
        return risks
    
    def _calculate_optimization_metrics(
        self,
        plan: List[ExecutionStep],
        scenario: PlanningScenario
    ) -> Dict[str, float]:
        """Calculate optimization metrics for the plan."""
        metrics = {}
        
        # Execution efficiency
        total_time = sum(step.estimated_duration_ms for step in plan)
        metrics['execution_time_ms'] = total_time
        metrics['steps_count'] = len(plan)
        metrics['avg_step_time_ms'] = total_time / len(plan) if plan else 0
        
        # Priority distribution
        priority_sum = sum(step.priority for step in plan)
        metrics['avg_priority'] = priority_sum / len(plan) if plan else 0
        
        # Dependency complexity
        total_deps = sum(len(step.dependencies) for step in plan)
        metrics['avg_dependencies'] = total_deps / len(plan) if plan else 0
        
        # Constraint satisfaction (placeholder)
        metrics['constraint_satisfaction'] = 0.85
        
        return metrics
    
    def _build_dependency_graph(self, steps: List[ExecutionStep]) -> Dict[str, List[str]]:
        """Build dependency graph for steps."""
        graph = {}
        for step in steps:
            graph[step.step_id] = step.dependencies
        return graph
    
    def _optimize_with_constraints(
        self,
        dependency_graph: Dict[str, List[str]],
        constraints: List[PlanningConstraint]
    ) -> List[int]:
        """Optimize execution order with constraints (simplified topological sort)."""
        # This is a simplified implementation
        # In practice, this would use more sophisticated optimization algorithms
        
        step_ids = list(dependency_graph.keys())
        ordered_indices = []
        remaining_steps = set(range(len(step_ids)))
        
        while remaining_steps:
            # Find steps with no unresolved dependencies
            ready_steps = []
            for i in remaining_steps:
                step_id = step_ids[i]
                deps = dependency_graph[step_id]
                if all(dep_id in [step_ids[j] for j in ordered_indices] for dep_id in deps):
                    ready_steps.append(i)
            
            if not ready_steps:
                # Handle circular dependencies by picking the first remaining step
                ready_steps = [next(iter(remaining_steps))]
            
            # Select the best step based on constraints (simplified)
            selected_step = ready_steps[0]  # Simple selection
            ordered_indices.append(selected_step)
            remaining_steps.remove(selected_step)
        
        return ordered_indices
    
    def _analyze_conflict_impact(
        self,
        conflicts: List[Dict[str, Any]],
        scenario: PlanningScenario
    ) -> Dict[str, Any]:
        """Analyze the impact of conflicts on the scenario."""
        impact = {
            'severity': 'low',
            'affected_attendees': set(),
            'time_impact_minutes': 0,
            'resolution_complexity': 'simple'
        }
        
        for conflict in conflicts:
            # Update severity
            conflict_severity = conflict.get('severity', 'low')
            if conflict_severity == 'high' or impact['severity'] == 'low':
                impact['severity'] = conflict_severity
            
            # Track affected attendees
            if 'attendees' in conflict:
                impact['affected_attendees'].update(conflict['attendees'])
            
            # Sum time impact
            impact['time_impact_minutes'] += conflict.get('time_impact', 0)
        
        # Determine resolution complexity
        if len(conflicts) > 3 or impact['severity'] == 'high':
            impact['resolution_complexity'] = 'complex'
        elif len(conflicts) > 1 or impact['severity'] == 'medium':
            impact['resolution_complexity'] = 'moderate'
        
        return impact
    
    def _select_resolution_approach(
        self,
        conflict_impact: Dict[str, Any],
        scenario: PlanningScenario
    ) -> str:
        """Select the best approach for resolving conflicts."""
        if conflict_impact['severity'] == 'high':
            return 'escalate'
        elif conflict_impact['resolution_complexity'] == 'complex':
            return 'multi_step_resolution'
        elif len(conflict_impact['affected_attendees']) > 5:
            return 'batch_resolution'
        else:
            return 'simple_resolution'
    
    def _generate_resolution_steps(
        self,
        approach: str,
        conflicts: List[Dict[str, Any]],
        scenario: PlanningScenario
    ) -> List[ExecutionStep]:
        """Generate resolution steps based on approach."""
        steps = []
        
        if approach == 'simple_resolution':
            steps.append(ExecutionStep(
                step_id="simple_conflict_resolution",
                tool_type="scheduling_agent",
                action="resolve_simple_conflicts",
                inputs={"conflicts": conflicts},
                dependencies=[],
                priority=Priority.HIGH,
                estimated_duration_ms=1500
            ))
        
        elif approach == 'multi_step_resolution':
            steps.extend([
                ExecutionStep(
                    step_id="analyze_complex_conflicts",
                    tool_type="scheduling_agent",
                    action="analyze_conflicts",
                    inputs={"conflicts": conflicts, "scenario": scenario.__dict__},
                    dependencies=[],
                    priority=Priority.HIGH,
                    estimated_duration_ms=2000
                ),
                ExecutionStep(
                    step_id="generate_resolution_options",
                    tool_type="scheduling_agent",
                    action="generate_options",
                    inputs={"analysis": "{{analyze_complex_conflicts.result}}"},
                    dependencies=["analyze_complex_conflicts"],
                    priority=Priority.MEDIUM,
                    estimated_duration_ms=1800
                ),
                ExecutionStep(
                    step_id="apply_resolution",
                    tool_type="calendar_service",
                    action="apply_resolution",
                    inputs={"options": "{{generate_resolution_options.result}}"},
                    dependencies=["generate_resolution_options"],
                    priority=Priority.HIGH,
                    estimated_duration_ms=1200
                )
            ])
        
        elif approach == 'batch_resolution':
            steps.append(ExecutionStep(
                step_id="batch_conflict_resolution",
                tool_type="scheduling_agent",
                action="batch_resolve_conflicts",
                inputs={"conflicts": conflicts, "batch_size": 5},
                dependencies=[],
                priority=Priority.HIGH,
                estimated_duration_ms=3000
            ))
        
        elif approach == 'escalate':
            steps.append(ExecutionStep(
                step_id="escalate_conflicts",
                tool_type="communication_generator",
                action="generate_escalation",
                inputs={"conflicts": conflicts, "scenario": scenario.__dict__},
                dependencies=[],
                priority=Priority.CRITICAL,
                estimated_duration_ms=1000
            ))
        
        return steps