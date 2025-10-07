#!/usr/bin/env python3
"""
Test script for AgentCore Router/Planner integration.
Verifies the implementation works correctly.
"""

import sys
import os

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Import directly from the modules
from services.agentcore_router import AgentCoreRouter, TaskType, Priority, ExecutionStep
from services.agentcore_planner import AgentCorePlanner, PlanningStrategy


def test_agentcore_integration():
    """Test AgentCore router/planner integration."""
    print("Testing AgentCore Router/Planner Integration...")
    
    # Test basic router functionality
    print("\n1. Testing AgentCore Router...")
    try:
        router = AgentCoreRouter()
        
        request_data = {
            'attendees': ['user1@example.com', 'user2@example.com'],
            'duration_minutes': 60,
            'time_range': {
                'start': '2024-01-15T09:00:00Z',
                'end': '2024-01-15T17:00:00Z'
            }
        }
        
        context_id, steps = router.plan_execution(
            task_type=TaskType.SCHEDULE_MEETING,
            request_data=request_data,
            user_id='test_user_123'
        )
        
        print(f"✓ Router execution planning completed:")
        print(f"  - Context ID: {context_id}")
        print(f"  - Steps generated: {len(steps)}")
        print(f"  - First step: {steps[0].step_id if steps else 'None'}")
        
        # Test conflict handling
        conflicts = [
            {
                'type': 'time_overlap',
                'severity': 'medium',
                'attendees': ['user1@example.com'],
                'overlap_minutes': 30
            }
        ]
        
        alternatives = [
            {
                'time': '2024-01-15T14:00:00Z',
                'availability_score': 0.8
            }
        ]
        
        conflict_steps = router.handle_conflicts(
            context_id=context_id,
            conflicts=conflicts,
            available_alternatives=alternatives
        )
        
        print(f"  - Conflict resolution steps: {len(conflict_steps)}")
        
    except Exception as e:
        print(f"✗ Router test failed: {e}")
        return False
    
    # Test planner functionality
    print("\n2. Testing AgentCore Planner...")
    try:
        planner = AgentCorePlanner()
        
        scenario = planner.create_planning_scenario(
            task_type=TaskType.SCHEDULE_MEETING,
            request_data=request_data,
            user_preferences={'conflict_tolerance': 0.3}
        )
        
        print(f"✓ Planning scenario created:")
        print(f"  - Scenario ID: {scenario.scenario_id}")
        print(f"  - Constraints: {len(scenario.constraints)}")
        print(f"  - Attendees: {len(scenario.attendees)}")
        
        planning_result = planner.plan_complex_scenario(
            scenario=scenario,
            strategy=PlanningStrategy.BALANCED
        )
        
        print(f"✓ Complex scenario planning completed:")
        print(f"  - Recommended plan steps: {len(planning_result.recommended_plan)}")
        print(f"  - Confidence score: {planning_result.confidence_score:.2f}")
        print(f"  - Success rate: {planning_result.estimated_success_rate:.2f}")
        print(f"  - Risk factors: {len(planning_result.risk_factors)}")
        print(f"  - Alternative plans: {len(planning_result.alternative_plans)}")
        
    except Exception as e:
        print(f"✗ Planner test failed: {e}")
        return False
    
    print("\n✓ All AgentCore integration tests passed!")
    return True


def test_decision_tree_logic():
    """Test decision tree and prioritization logic."""
    print("\nTesting decision tree and prioritization logic...")
    
    try:
        router = AgentCoreRouter()
        
        # Test different complexity scenarios
        simple_request = {
            'attendees': ['user1@example.com'],
            'duration_minutes': 30
        }
        
        complex_request = {
            'attendees': ['user1@example.com', 'user2@example.com', 'user3@example.com', 'user4@example.com'],
            'duration_minutes': 120,
            'constraints': {'business_hours_only': True},
            'preferences': {'preferred_time': 'morning'},
            'external_calendars': ['calendar1', 'calendar2']
        }
        
        # Test simple scenario
        context_id_simple, steps_simple = router.plan_execution(
            task_type=TaskType.SCHEDULE_MEETING,
            request_data=simple_request,
            user_id='test_user'
        )
        
        # Test complex scenario
        context_id_complex, steps_complex = router.plan_execution(
            task_type=TaskType.SCHEDULE_MEETING,
            request_data=complex_request,
            user_id='test_user'
        )
        
        print(f"✓ Decision tree logic working:")
        print(f"  - Simple scenario steps: {len(steps_simple)}")
        print(f"  - Complex scenario steps: {len(steps_complex)}")
        print(f"  - Complex scenario has more steps: {len(steps_complex) > len(steps_simple)}")
        
        # Test different task types
        conflict_context, conflict_steps = router.plan_execution(
            task_type=TaskType.RESOLVE_CONFLICT,
            request_data={'conflicts': [{'type': 'overlap'}], 'alternatives': []},
            user_id='test_user'
        )
        
        reschedule_context, reschedule_steps = router.plan_execution(
            task_type=TaskType.RESCHEDULE_MEETING,
            request_data={'meeting_id': 'test123', 'new_time': '2024-01-15T14:00:00Z'},
            user_id='test_user'
        )
        
        print(f"  - Conflict resolution steps: {len(conflict_steps)}")
        print(f"  - Reschedule steps: {len(reschedule_steps)}")
        
    except Exception as e:
        print(f"✗ Decision tree test failed: {e}")
        return False
    
    print("✓ Decision tree and prioritization tests passed!")
    return True


if __name__ == "__main__":
    print("AgentCore Router/Planner Integration Test")
    print("=" * 50)
    
    # Test decision tree logic
    if not test_decision_tree_logic():
        print("\n✗ Decision tree tests failed!")
        sys.exit(1)
    
    # Test full integration
    if not test_agentcore_integration():
        print("\n✗ Integration tests failed!")
        sys.exit(1)
    
    print("\n🎉 All tests passed! AgentCore Router/Planner implementation is working correctly.")