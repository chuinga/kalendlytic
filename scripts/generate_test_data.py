#!/usr/bin/env python3
"""
Test Data Generation Script for AWS Meeting Scheduling Agent

This script generates realistic test data for demonstration and testing purposes,
including users, calendar events, preferences, and various scheduling scenarios.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import boto3
from botocore.exceptions import ClientError
import uuid
import argparse

class TestDataGenerator:
    """Generates comprehensive test data for the meeting scheduling agent"""
    
    def __init__(self, region: str = "eu-west-1"):
        self.region = region
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        
        # Sample data pools
        self.sample_names = [
            "Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson",
            "Emma Brown", "Frank Miller", "Grace Lee", "Henry Taylor",
            "Ivy Chen", "Jack Anderson", "Kate Martinez", "Liam Garcia"
        ]
        
        self.sample_companies = [
            "TechCorp", "InnovateLabs", "DataSystems", "CloudFirst",
            "AgileWorks", "FutureScale", "SmartSolutions", "NextGen"
        ]
        
        self.meeting_types = [
            {"name": "standup", "duration": 15, "priority": 0.6},
            {"name": "one-on-one", "duration": 30, "priority": 0.7},
            {"name": "team-meeting", "duration": 60, "priority": 0.7},
            {"name": "client-call", "duration": 45, "priority": 0.9},
            {"name": "interview", "duration": 60, "priority": 0.8},
            {"name": "presentation", "duration": 90, "priority": 0.8},
            {"name": "workshop", "duration": 120, "priority": 0.6},
            {"name": "executive-review", "duration": 30, "priority": 0.95}
        ]
        
        self.meeting_subjects = [
            "Weekly Team Standup", "Project Planning Session", "Client Requirements Review",
            "Technical Architecture Discussion", "Sprint Retrospective", "Product Demo",
            "Budget Planning Meeting", "Performance Review", "Training Session",
            "Strategy Planning", "Code Review", "System Design Discussion"
        ]
        
    def generate_demo_users(self, count: int = 5) -> List[Dict]:
        """Generate demo user accounts with realistic profiles"""
        users = []
        
        for i in range(count):
            name = self.sample_names[i % len(self.sample_names)]
            company = random.choice(self.sample_companies)
            
            user = {
                "pk": f"user#{uuid.uuid4()}",
                "email": f"{name.lower().replace(' ', '.')}@{company.lower()}.com",
                "timezone": random.choice([
                    "America/New_York", "America/Los_Angeles", "Europe/London",
                    "Europe/Berlin", "Asia/Tokyo", "Australia/Sydney"
                ]),
                "created_at": datetime.now().isoformat(),
                "profile": {
                    "name": name,
                    "company": company,
                    "role": random.choice([
                        "Software Engineer", "Product Manager", "Designer",
                        "Data Scientist", "Engineering Manager", "CEO"
                    ]),
                    "default_meeting_duration": random.choice([30, 45, 60]),
                    "auto_book_enabled": random.choice([True, False])
                }
            }
            users.append(user)
            
        return users
        
    def generate_user_preferences(self, user_id: str) -> Dict:
        """Generate realistic user preferences and scheduling rules"""
        
        # Generate working hours (with some variation)
        start_hour = random.choice([8, 9, 10])
        end_hour = random.choice([17, 18, 19])
        
        working_hours = {}
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            working_hours[day] = {
                "start": f"{start_hour:02d}:00",
                "end": f"{end_hour:02d}:00"
            }
            
        # Some users work weekends
        if random.random() < 0.3:
            working_hours["saturday"] = {
                "start": f"{start_hour + 1:02d}:00",
                "end": f"{end_hour - 2:02d}:00"
            }
            
        # Generate focus blocks
        focus_blocks = []
        if random.random() < 0.7:  # 70% of users have focus blocks
            focus_blocks.append({
                "day": random.choice(["monday", "tuesday", "wednesday"]),
                "start": "09:00",
                "end": "11:00",
                "title": "Deep Work Block"
            })
            
        # Generate VIP contacts
        vip_contacts = []
        for _ in range(random.randint(2, 5)):
            name = random.choice(self.sample_names)
            company = random.choice(self.sample_companies)
            vip_contacts.append(f"{name.lower().replace(' ', '.')}@{company.lower()}.com")
            
        preferences = {
            "pk": user_id,
            "working_hours": working_hours,
            "buffer_minutes": random.choice([5, 10, 15, 30]),
            "focus_blocks": focus_blocks,
            "vip_contacts": vip_contacts,
            "meeting_types": {
                mt["name"]: {
                    "duration": mt["duration"],
                    "priority": mt["priority"] + random.uniform(-0.1, 0.1)
                }
                for mt in self.meeting_types
            },
            "auto_decline_conflicts": random.choice([True, False]),
            "require_confirmation": random.choice([True, False])
        }
        
        return preferences
        
    def generate_calendar_events(self, user_id: str, days_ahead: int = 14, events_per_day: int = 3) -> List[Dict]:
        """Generate realistic calendar events for testing"""
        events = []
        
        for day_offset in range(days_ahead):
            date = datetime.now() + timedelta(days=day_offset)
            
            # Skip weekends for most events
            if date.weekday() >= 5 and random.random() > 0.2:
                continue
                
            # Generate events for this day
            num_events = random.randint(1, events_per_day)
            used_times = set()
            
            for _ in range(num_events):
                # Pick a random time during working hours
                hour = random.randint(9, 17)
                minute = random.choice([0, 15, 30, 45])
                
                start_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Avoid overlapping events
                if start_time.hour in used_times:
                    continue
                used_times.add(start_time.hour)
                
                # Pick meeting type and duration
                meeting_type = random.choice(self.meeting_types)
                duration = meeting_type["duration"]
                end_time = start_time + timedelta(minutes=duration)
                
                # Generate attendees
                attendees = []
                for _ in range(random.randint(1, 4)):
                    name = random.choice(self.sample_names)
                    company = random.choice(self.sample_companies)
                    attendees.append(f"{name.lower().replace(' ', '.')}@{company.lower()}.com")
                
                event = {
                    "pk": user_id,
                    "sk": f"meeting#{uuid.uuid4()}",
                    "provider_event_id": f"google_cal_{uuid.uuid4()}",
                    "provider": random.choice(["google", "microsoft"]),
                    "title": random.choice(self.meeting_subjects),
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "attendees": attendees,
                    "status": random.choice(["confirmed", "tentative", "cancelled"]),
                    "priority_score": meeting_type["priority"] + random.uniform(-0.1, 0.1),
                    "created_by_agent": random.choice([True, False]),
                    "last_modified": datetime.now().isoformat(),
                    "location": random.choice([
                        "Conference Room A", "Conference Room B", "Zoom Meeting",
                        "Teams Meeting", "Office 123", "Client Site"
                    ]) if random.random() > 0.3 else None
                }
                
                events.append(event)
                
        return events
        
    def generate_oauth_connections(self, user_id: str) -> List[Dict]:
        """Generate OAuth connection records for testing"""
        connections = []
        
        # Google connection
        if random.random() > 0.2:  # 80% have Google
            google_connection = {
                "pk": f"{user_id}#google",
                "provider": "google",
                "access_token_encrypted": "encrypted_google_token_" + str(uuid.uuid4()),
                "refresh_token_encrypted": "encrypted_google_refresh_" + str(uuid.uuid4()),
                "scopes": ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/gmail.send"],
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "last_refresh": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
                "status": "active"
            }
            connections.append(google_connection)
            
        # Microsoft connection
        if random.random() > 0.4:  # 60% have Microsoft
            microsoft_connection = {
                "pk": f"{user_id}#microsoft",
                "provider": "microsoft",
                "access_token_encrypted": "encrypted_ms_token_" + str(uuid.uuid4()),
                "refresh_token_encrypted": "encrypted_ms_refresh_" + str(uuid.uuid4()),
                "scopes": ["https://graph.microsoft.com/Calendars.ReadWrite", "https://graph.microsoft.com/Mail.Send"],
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "last_refresh": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
                "status": "active"
            }
            connections.append(microsoft_connection)
            
        return connections
        
    def generate_agent_runs(self, user_id: str, count: int = 10) -> List[Dict]:
        """Generate sample agent execution logs"""
        runs = []
        
        for i in range(count):
            run_time = datetime.now() - timedelta(hours=random.randint(1, 72))
            
            run = {
                "pk": f"run#{uuid.uuid4()}",
                "user_id": user_id,
                "request_type": random.choice([
                    "schedule_meeting", "resolve_conflict", "find_availability",
                    "reschedule_meeting", "cancel_meeting", "update_preferences"
                ]),
                "inputs": {
                    "attendees": [f"user{random.randint(1,5)}@example.com"],
                    "duration": random.choice([30, 45, 60]),
                    "subject": random.choice(self.meeting_subjects)
                },
                "tools_used": random.sample([
                    "get_availability", "create_event", "send_email",
                    "prioritize_meeting", "reschedule_event", "extract_preferences"
                ], random.randint(2, 4)),
                "outputs": {
                    "success": random.choice([True, False]),
                    "event_created": random.choice([True, False]),
                    "emails_sent": random.randint(0, 3),
                    "conflicts_resolved": random.randint(0, 2)
                },
                "cost_estimate": {
                    "bedrock_tokens": random.randint(500, 3000),
                    "estimated_cost_usd": round(random.uniform(0.01, 0.15), 4)
                },
                "execution_time_ms": random.randint(800, 5000),
                "created_at": run_time.isoformat()
            }
            
            runs.append(run)
            
        return runs
        
    def generate_audit_logs(self, user_id: str, run_ids: List[str]) -> List[Dict]:
        """Generate detailed audit logs for agent decisions"""
        logs = []
        
        for run_id in run_ids:
            # Generate 2-5 audit log entries per run
            for step in range(random.randint(2, 5)):
                log_time = datetime.now() - timedelta(hours=random.randint(1, 72))
                
                log_entry = {
                    "pk": user_id,
                    "sk": f"{log_time.isoformat()}#step{step}",
                    "run_id": run_id,
                    "step": random.choice([
                        "conflict_detection", "priority_analysis", "availability_check",
                        "alternative_generation", "email_composition", "decision_making"
                    ]),
                    "action": random.choice([
                        "Detected scheduling conflict between meetings",
                        "Analyzed meeting priority based on attendees",
                        "Found optimal time slot for rescheduling",
                        "Generated alternative meeting times",
                        "Composed confirmation email",
                        "Applied user preferences to scheduling decision"
                    ]),
                    "rationale": random.choice([
                        "Meeting with VIP contact takes priority over team standup",
                        "Proposed time slot respects user's focus block preferences",
                        "Alternative times optimize for all attendees' availability",
                        "Email template customized based on meeting type and urgency",
                        "Decision follows user's auto-booking preferences"
                    ]),
                    "tool_calls": random.sample([
                        "get_availability", "prioritize_meeting", "send_email"
                    ], random.randint(1, 2)),
                    "decision": random.choice([
                        "schedule_meeting", "propose_reschedule", "request_approval",
                        "send_notification", "update_preferences"
                    ]),
                    "alternatives_proposed": random.randint(0, 3),
                    "user_action_required": random.choice([True, False])
                }
                
                logs.append(log_entry)
                
        return logs
        
    def write_to_dynamodb(self, table_name: str, items: List[Dict]):
        """Write generated data to DynamoDB table"""
        try:
            table = self.dynamodb.Table(table_name)
            
            # Batch write items
            with table.batch_writer() as batch:
                for item in items:
                    batch.put_item(Item=item)
                    
            print(f"✓ Wrote {len(items)} items to {table_name}")
            
        except ClientError as e:
            print(f"✗ Error writing to {table_name}: {e}")
            
    def export_to_json(self, data: Dict[str, List], filename: str):
        """Export generated data to JSON file for backup/review"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"✓ Exported test data to {filename}")
        except Exception as e:
            print(f"✗ Error exporting to {filename}: {e}")
            
    def generate_complete_dataset(self, num_users: int = 5, write_to_db: bool = False) -> Dict[str, List]:
        """Generate a complete test dataset"""
        print(f"Generating test data for {num_users} users...")
        
        # Generate all data
        users = self.generate_demo_users(num_users)
        all_preferences = []
        all_connections = []
        all_meetings = []
        all_runs = []
        all_audit_logs = []
        
        for user in users:
            user_id = user["pk"]
            
            # Generate data for this user
            preferences = self.generate_user_preferences(user_id)
            connections = self.generate_oauth_connections(user_id)
            meetings = self.generate_calendar_events(user_id)
            runs = self.generate_agent_runs(user_id)
            audit_logs = self.generate_audit_logs(user_id, [run["pk"] for run in runs])
            
            all_preferences.append(preferences)
            all_connections.extend(connections)
            all_meetings.extend(meetings)
            all_runs.extend(runs)
            all_audit_logs.extend(audit_logs)
            
        dataset = {
            "users": users,
            "preferences": all_preferences,
            "connections": all_connections,
            "meetings": all_meetings,
            "agent_runs": all_runs,
            "audit_logs": all_audit_logs
        }
        
        # Write to DynamoDB if requested
        if write_to_db:
            print("Writing to DynamoDB tables...")
            self.write_to_dynamodb("Users", users)
            self.write_to_dynamodb("Preferences", all_preferences)
            self.write_to_dynamodb("Connections", all_connections)
            self.write_to_dynamodb("Meetings", all_meetings)
            self.write_to_dynamodb("AgentRuns", all_runs)
            self.write_to_dynamodb("AuditLogs", all_audit_logs)
            
        return dataset

def main():
    parser = argparse.ArgumentParser(description="Generate test data for AWS Meeting Scheduling Agent")
    parser.add_argument("--users", type=int, default=5, help="Number of demo users to generate")
    parser.add_argument("--region", default="eu-west-1", help="AWS region")
    parser.add_argument("--write-db", action="store_true", help="Write data to DynamoDB tables")
    parser.add_argument("--export-json", default="test_data.json", help="Export data to JSON file")
    
    args = parser.parse_args()
    
    print("AWS Meeting Scheduling Agent - Test Data Generator")
    print("=" * 50)
    
    generator = TestDataGenerator(region=args.region)
    dataset = generator.generate_complete_dataset(
        num_users=args.users,
        write_to_db=args.write_db
    )
    
    # Export to JSON
    if args.export_json:
        generator.export_to_json(dataset, args.export_json)
        
    print("\n✅ Test data generation completed!")
    print(f"Generated data for {len(dataset['users'])} users:")
    print(f"  - {len(dataset['preferences'])} preference profiles")
    print(f"  - {len(dataset['connections'])} OAuth connections")
    print(f"  - {len(dataset['meetings'])} calendar events")
    print(f"  - {len(dataset['agent_runs'])} agent execution logs")
    print(f"  - {len(dataset['audit_logs'])} audit log entries")

if __name__ == "__main__":
    main()