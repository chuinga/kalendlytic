#!/usr/bin/env python3
"""
AWS Meeting Scheduling Agent - End-to-End Demo Script

This script demonstrates the key functionality of the meeting scheduling agent
by simulating real-world scenarios and showcasing the AI-powered features.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import boto3
from botocore.exceptions import ClientError
import requests
import time

class DemoRunner:
    """Orchestrates the demo scenarios for the meeting scheduling agent"""
    
    def __init__(self, api_base_url: str, demo_user_email: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.demo_user_email = demo_user_email
        self.auth_token = None
        self.user_id = None
        self.session = requests.Session()
        
    def log(self, message: str, level: str = "INFO"):
        """Log demo progress with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    async def setup_demo_environment(self):
        """Initialize demo environment and authenticate"""
        self.log("Setting up demo environment...")
        
        # Authenticate demo user
        auth_response = self.session.post(f"{self.api_base_url}/auth/login", json={
            "email": self.demo_user_email,
            "password": os.getenv("DEMO_USER_PASSWORD", "DemoPass123!")
        })
        
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            self.auth_token = auth_data["access_token"]
            self.user_id = auth_data["user_id"]
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            self.log(f"✓ Authenticated as {self.demo_user_email}")
        else:
            self.log(f"✗ Authentication failed: {auth_response.text}", "ERROR")
            return False
            
        return True
        
    async def demo_oauth_connections(self):
        """Demonstrate OAuth connection setup (simulated)"""
        self.log("=== Demo: OAuth Calendar Connections ===")
        
        # Simulate Google Calendar connection
        self.log("Connecting to Google Calendar...")
        google_response = self.session.post(f"{self.api_base_url}/connections/google/simulate", json={
            "demo_mode": True,
            "calendar_count": 2,
            "event_count": 15
        })
        
        if google_response.status_code == 200:
            self.log("✓ Google Calendar connected (simulated)")
            self.log("  - Personal Calendar: 8 events")
            self.log("  - Work Calendar: 7 events")
        else:
            self.log("✗ Google Calendar connection failed", "ERROR")
            
        # Simulate Microsoft Outlook connection
        self.log("Connecting to Microsoft Outlook...")
        outlook_response = self.session.post(f"{self.api_base_url}/connections/microsoft/simulate", json={
            "demo_mode": True,
            "calendar_count": 1,
            "event_count": 12
        })
        
        if outlook_response.status_code == 200:
            self.log("✓ Microsoft Outlook connected (simulated)")
            self.log("  - Business Calendar: 12 events")
        else:
            self.log("✗ Microsoft Outlook connection failed", "ERROR")
            
        await asyncio.sleep(2)  # Pause for demo effect
        
    async def demo_availability_aggregation(self):
        """Demonstrate unified availability across platforms"""
        self.log("=== Demo: Unified Availability Aggregation ===")
        
        # Get availability for next week
        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        availability_response = self.session.get(
            f"{self.api_base_url}/calendar/availability",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "duration": 60  # 1 hour meetings
            }
        )
        
        if availability_response.status_code == 200:
            availability = availability_response.json()
            self.log("✓ Availability aggregated across all calendars")
            self.log(f"  - Total free slots found: {len(availability.get('free_slots', []))}")
            self.log(f"  - Conflicts detected: {len(availability.get('conflicts', []))}")
            
            # Show sample free slots
            for i, slot in enumerate(availability.get('free_slots', [])[:3]):
                self.log(f"  - Free slot {i+1}: {slot['start']} - {slot['end']}")
        else:
            self.log("✗ Availability aggregation failed", "ERROR")
            
        await asyncio.sleep(2)
        
    async def demo_conflict_detection(self):
        """Demonstrate intelligent conflict detection and resolution"""
        self.log("=== Demo: Conflict Detection & AI Resolution ===")
        
        # Create a meeting that conflicts with existing events
        conflict_meeting = {
            "title": "Important Client Meeting",
            "start": (datetime.now() + timedelta(days=2, hours=10)).isoformat(),
            "end": (datetime.now() + timedelta(days=2, hours=11)).isoformat(),
            "attendees": ["client@important.com", "colleague@company.com"],
            "priority": "high"
        }
        
        self.log("Attempting to schedule meeting with potential conflicts...")
        self.log(f"  Meeting: {conflict_meeting['title']}")
        self.log(f"  Time: {conflict_meeting['start']}")
        
        schedule_response = self.session.post(
            f"{self.api_base_url}/agent/schedule",
            json=conflict_meeting
        )
        
        if schedule_response.status_code == 200:
            result = schedule_response.json()
            
            if result.get('conflicts_detected'):
                self.log("⚠ Conflicts detected by AI agent")
                for conflict in result.get('conflicts', []):
                    self.log(f"  - Conflict: {conflict['title']} ({conflict['priority']})")
                
                self.log("🤖 AI Agent proposing solutions...")
                for i, alternative in enumerate(result.get('alternatives', [])[:3]):
                    self.log(f"  Option {i+1}: {alternative['start']} (fit score: {alternative['fit_score']})")
                    self.log(f"    Rationale: {alternative['rationale']}")
            else:
                self.log("✓ No conflicts - meeting scheduled successfully")
                self.log(f"  Event ID: {result.get('event_id')}")
        else:
            self.log("✗ Conflict detection failed", "ERROR")
            
        await asyncio.sleep(3)
        
    async def demo_priority_based_scheduling(self):
        """Demonstrate AI-powered meeting prioritization"""
        self.log("=== Demo: AI-Powered Meeting Prioritization ===")
        
        # Test different meeting types with various priorities
        test_meetings = [
            {
                "title": "Daily Standup",
                "attendees": ["team@company.com"],
                "type": "standup",
                "expected_priority": "medium"
            },
            {
                "title": "CEO Strategy Session", 
                "attendees": ["ceo@company.com"],
                "type": "executive",
                "expected_priority": "high"
            },
            {
                "title": "Coffee Chat",
                "attendees": ["friend@personal.com"],
                "type": "social",
                "expected_priority": "low"
            }
        ]
        
        for meeting in test_meetings:
            self.log(f"Analyzing priority for: {meeting['title']}")
            
            priority_response = self.session.post(
                f"{self.api_base_url}/agent/analyze-priority",
                json=meeting
            )
            
            if priority_response.status_code == 200:
                result = priority_response.json()
                priority_score = result.get('priority_score', 0)
                rationale = result.get('rationale', 'No rationale provided')
                
                self.log(f"  ✓ Priority Score: {priority_score:.2f}")
                self.log(f"  🤖 AI Rationale: {rationale}")
            else:
                self.log(f"  ✗ Priority analysis failed", "ERROR")
                
            await asyncio.sleep(1)
            
    async def demo_automated_communication(self):
        """Demonstrate automated email communication"""
        self.log("=== Demo: Automated Email Communication ===")
        
        # Simulate meeting confirmation email
        email_data = {
            "type": "meeting_confirmation",
            "meeting": {
                "title": "Project Kickoff Meeting",
                "start": (datetime.now() + timedelta(days=3, hours=14)).isoformat(),
                "end": (datetime.now() + timedelta(days=3, hours=15)).isoformat(),
                "attendees": ["stakeholder@company.com", "developer@company.com"],
                "location": "Conference Room A"
            }
        }
        
        self.log("Generating meeting confirmation email...")
        
        email_response = self.session.post(
            f"{self.api_base_url}/agent/compose-email",
            json=email_data
        )
        
        if email_response.status_code == 200:
            result = email_response.json()
            self.log("✓ Email composed by AI agent")
            self.log(f"  Subject: {result.get('subject')}")
            self.log(f"  Recipients: {', '.join(result.get('recipients', []))}")
            self.log("  Preview:")
            preview = result.get('body', '')[:150] + "..." if len(result.get('body', '')) > 150 else result.get('body', '')
            self.log(f"    {preview}")
        else:
            self.log("✗ Email composition failed", "ERROR")
            
        await asyncio.sleep(2)
        
    async def demo_agent_decision_audit(self):
        """Demonstrate agent decision audit trail"""
        self.log("=== Demo: Agent Decision Audit Trail ===")
        
        # Get recent agent decisions
        audit_response = self.session.get(
            f"{self.api_base_url}/agent/audit-logs",
            params={"limit": 5}
        )
        
        if audit_response.status_code == 200:
            logs = audit_response.json().get('logs', [])
            self.log(f"✓ Retrieved {len(logs)} recent agent decisions")
            
            for i, log_entry in enumerate(logs[:3]):
                self.log(f"  Decision {i+1}:")
                self.log(f"    Action: {log_entry.get('action')}")
                self.log(f"    Rationale: {log_entry.get('rationale')}")
                self.log(f"    Tools Used: {', '.join(log_entry.get('tools_used', []))}")
                self.log(f"    Timestamp: {log_entry.get('timestamp')}")
        else:
            self.log("✗ Audit log retrieval failed", "ERROR")
            
        await asyncio.sleep(2)
        
    async def demo_performance_metrics(self):
        """Display performance metrics and system health"""
        self.log("=== Demo: System Performance Metrics ===")
        
        # Get system metrics
        metrics_response = self.session.get(f"{self.api_base_url}/system/metrics")
        
        if metrics_response.status_code == 200:
            metrics = metrics_response.json()
            self.log("✓ System performance metrics:")
            self.log(f"  - Average response time: {metrics.get('avg_response_time_ms', 0)}ms")
            self.log(f"  - Bedrock token usage (24h): {metrics.get('bedrock_tokens_24h', 0)}")
            self.log(f"  - Estimated cost (24h): ${metrics.get('estimated_cost_24h', 0):.4f}")
            self.log(f"  - Active connections: {metrics.get('active_connections', 0)}")
            self.log(f"  - Success rate: {metrics.get('success_rate', 0):.1f}%")
        else:
            self.log("✗ Metrics retrieval failed", "ERROR")
            
    async def run_complete_demo(self):
        """Run the complete demo sequence"""
        self.log("🚀 Starting AWS Meeting Scheduling Agent Demo")
        self.log("=" * 50)
        
        # Setup
        if not await self.setup_demo_environment():
            return False
            
        try:
            # Run demo scenarios
            await self.demo_oauth_connections()
            await self.demo_availability_aggregation()
            await self.demo_conflict_detection()
            await self.demo_priority_based_scheduling()
            await self.demo_automated_communication()
            await self.demo_agent_decision_audit()
            await self.demo_performance_metrics()
            
            self.log("=" * 50)
            self.log("✅ Demo completed successfully!")
            self.log("Key features demonstrated:")
            self.log("  ✓ Multi-platform calendar integration")
            self.log("  ✓ AI-powered conflict detection")
            self.log("  ✓ Intelligent meeting prioritization")
            self.log("  ✓ Automated email communication")
            self.log("  ✓ Comprehensive audit trails")
            self.log("  ✓ Real-time performance monitoring")
            
            return True
            
        except Exception as e:
            self.log(f"Demo failed with error: {str(e)}", "ERROR")
            return False

def main():
    """Main demo execution function"""
    # Get configuration from environment
    api_url = os.getenv("DEMO_API_URL", "https://your-api-gateway-url.execute-api.eu-west-1.amazonaws.com")
    demo_email = os.getenv("DEMO_USER_EMAIL", "demo@example.com")
    
    if not api_url or api_url == "https://your-api-gateway-url.execute-api.eu-west-1.amazonaws.com":
        print("❌ Please set DEMO_API_URL environment variable to your deployed API Gateway URL")
        sys.exit(1)
        
    print("AWS Meeting Scheduling Agent - Interactive Demo")
    print("=" * 50)
    print(f"API URL: {api_url}")
    print(f"Demo User: {demo_email}")
    print("=" * 50)
    
    # Run the demo
    demo_runner = DemoRunner(api_url, demo_email)
    success = asyncio.run(demo_runner.run_complete_demo())
    
    if success:
        print("\n🎉 Demo completed successfully!")
        print("Visit the web interface to explore more features interactively.")
    else:
        print("\n❌ Demo encountered errors. Check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()