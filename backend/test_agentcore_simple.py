#!/usr/bin/env python3
"""
Simple test for AgentCore Router/Planner implementation.
Tests the core functionality without complex imports.
"""

import sys
import os

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

# Test the core classes directly
def test_agentcore_classes():
    """Test AgentCore classes directly."""
    print("Testing AgentCore Router/Planner Classes")
    print("=" * 50)
    
    # Test 1: Import and instantiate classes
    print("\n1. Testing imports and instantiation...")
    try:
        # Import the classes directly from their files
        exec(open('src/services/agentcore_router.py').read(), globals())
        exec(open('src/services/agentcore_planner.py').read(), globals())
        
        # Create instances
        router = AgentCoreRouter()
        planner = AgentCorePlanner()
        
        print("✓ Successfully imported and instantiated AgentCore classes")
        
    except Exception as e:
        print(f"✗ Import/instantiation failed: {e}")
        return False
    
    # Test 2: Test router planning
    print("\n2. Testing router execution planning...")
    try:
        request_data = {
            'attendees': ['user1@example.com', 'user2@example.com'],
            'duration_minutes': 60,
            'time_range': {
                'start': '2024-01-15T09:00:00Z',
                'end': '2024-01-15T17:00:00Z'
            }
        }
        
        context_id, steps = router.plan_execution(
            task_type="schedule_meeting",
            request_data=request_data,
            user_id='test_user_123'
        )
        
        print(f"✓ Router planning successful:")
        print(f"  - Context ID: {context_id}")
        print(f"  - Steps generated: {len(steps)}")
        
        if steps:
            print(f"  - First step ID: {steps[0].step_id}")
            print(f"  - First step tool: {steps[0].tool_type}")
            print(f"  - First step priority: {steps[0].priority}")
        
    except Exception as e:
        print(f"✗ Router planning failed: {e}")
        return False
    
    # Test 3: Test planner scenario creation
    print("\n3. Testing planner scenario creation...")
    try:
        scenario = planner.create_planning_scenario(
            task_type="schedule_meeting",
            request_data=request_data,
            user_preferences={'conflict_tolerance': 0.3}
        )
        
        print(f"✓ Planner scenario creation successful:")
        print(f"  - Scenario ID: {scenario.scenario_id}")
        print(f"  - Task type: {scenario.primary_task}")
        print(f"  - Constraints: {len(scenario.constraints)}")
        print(f"  - Attendees: {len(scenario.attendees)}")
        print(f"  - Optimization goals: {len(scenario.optimization_goals)}")
        
    except Exception as e:
        print(f"✗ Planner scenario creation failed: {e}")
        return False
    
    # Test 4: Test complex scenario planning
    print("\n4. Testing complex scenario planning...")
    try:
        planning_result = planner.plan_complex_scenario(
            scenario=scenario,
            strategy=PlanningStrategy.BALANCED
        )
        
        print(f"✓ Complex scenario planning successful:")
        print(f"  - Recommended plan steps: {len(planning_result.recommended_plan)}")
        print(f"  - Alternative plans: {len(planning_result.alternative_plans)}")
        print(f"  - Confidence score: {planning_result.confidence_score:.2f}")
        print(f"  - Success rate: {planning_result.estimated_success_rate:.2f}")
        print(f"  - Risk factors: {len(planning_result.risk_factors)}")
        
        if planning_result.risk_factors:
            print(f"  - Risk factors: {planning_result.risk_factors}")
        
    except Exception as e:
        print(f"✗ Complex scenario planning failed: {e}")
        return False
    
    # Test 5: Test conflict handling
    print("\n5. Testing conflict handling...")
    try:
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
        
        # Test router conflict handling
        conflict_steps = router.handle_conflicts(
            context_id=context_id,
            conflicts=conflicts,
            available_alternatives=alternatives
        )
        
        print(f"✓ Router conflict handling successful:")
        print(f"  - Conflict resolution steps: {len(conflict_steps)}")
        
        # Test planner conflict handling
        planner_conflict_steps = planner.handle_planning_conflicts(
            scenario=scenario,
            detected_conflicts=conflicts
        )
        
        print(f"✓ Planner conflict handling successful:")
        print(f"  - Planning conflict steps: {len(planner_conflict_steps)}")
        
    except Exception as e:
        print(f"✗ Conflict handling failed: {e}")
        return False
    
    # Test 6: Test different task types
    print("\n6. Testing different task types...")
    try:
        task_types_to_test = [
            "resolve_conflict",
            "reschedule_meeting", 
            "find_availability",
            "cancel_meeting"
        ]
        
        for task_type in task_types_to_test:
            test_request = {
                'attendees': ['user1@example.com'],
                'duration_minutes': 30
            }
            
            if task_type == "reschedule_meeting":
                test_request['meeting_id'] = 'test123'
                test_request['new_time'] = '2024-01-15T14:00:00Z'
            elif task_type == "resolve_conflict":
                test_request['conflicts'] = conflicts
                test_request['alternatives'] = alternatives
            elif task_type == "cancel_meeting":
                test_request['meeting_id'] = 'test123'
                test_request['reason'] = 'Schedule conflict'
            
            ctx_id, task_steps = router.plan_execution(
                task_type=task_type,
                request_data=test_request,
                user_id='test_user'
            )
            
            print(f"  - {task_type}: {len(task_steps)} steps")
        
        print("✓ All task types tested successfully")
        
    except Exception as e:
        print(f"✗ Task type testing failed: {e}")
        return False
    
    print("\n🎉 All AgentCore tests passed! Implementation is working correctly.")
    return True


if __name__ == "__main__":
    success = test_agentcore_classes()
    sys.exit(0 if success else 1)