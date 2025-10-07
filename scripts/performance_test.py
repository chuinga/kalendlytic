#!/usr/bin/env python3
"""
Performance and Load Testing Script for AWS Meeting Scheduling Agent

This script performs comprehensive performance testing including load testing,
stress testing, and performance monitoring for the meeting scheduling system.
"""

import asyncio
import aiohttp
import time
import statistics
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import concurrent.futures
import boto3
from dataclasses import dataclass
import random

@dataclass
class TestResult:
    """Container for individual test results"""
    endpoint: str
    response_time: float
    status_code: int
    success: bool
    error_message: str = None
    timestamp: datetime = None

@dataclass
class LoadTestConfig:
    """Configuration for load testing scenarios"""
    concurrent_users: int
    requests_per_user: int
    ramp_up_time: int  # seconds
    test_duration: int  # seconds
    endpoint: str
    payload: Dict = None

class PerformanceTester:
    """Comprehensive performance testing suite"""
    
    def __init__(self, api_base_url: str, auth_token: str = None):
        self.api_base_url = api_base_url.rstrip('/')
        self.auth_token = auth_token
        self.results: List[TestResult] = []
        self.session = None
        
    async def setup_session(self):
        """Initialize aiohttp session with proper headers"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'PerformanceTester/1.0'
        }
        
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
            
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            connector=connector,
            timeout=timeout
        )
        
    async def cleanup_session(self):
        """Clean up aiohttp session"""
        if self.session:
            await self.session.close()
            
    async def make_request(self, method: str, endpoint: str, payload: Dict = None) -> TestResult:
        """Make a single HTTP request and measure performance"""
        start_time = time.time()
        url = f"{self.api_base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url, params=payload) as response:
                    await response.text()  # Consume response
                    response_time = time.time() - start_time
                    
                    return TestResult(
                        endpoint=endpoint,
                        response_time=response_time,
                        status_code=response.status,
                        success=200 <= response.status < 300,
                        timestamp=datetime.now()
                    )
            else:
                async with self.session.post(url, json=payload) as response:
                    await response.text()  # Consume response
                    response_time = time.time() - start_time
                    
                    return TestResult(
                        endpoint=endpoint,
                        response_time=response_time,
                        status_code=response.status,
                        success=200 <= response.status < 300,
                        timestamp=datetime.now()
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                endpoint=endpoint,
                response_time=response_time,
                status_code=0,
                success=False,
                error_message=str(e),
                timestamp=datetime.now()
            )
            
    async def run_single_user_scenario(self, scenario: Dict) -> List[TestResult]:
        """Run a complete user scenario (multiple requests)"""
        results = []
        
        for request in scenario['requests']:
            result = await self.make_request(
                method=request.get('method', 'GET'),
                endpoint=request['endpoint'],
                payload=request.get('payload')
            )
            results.append(result)
            
            # Add delay between requests if specified
            if 'delay' in request:
                await asyncio.sleep(request['delay'])
                
        return results
        
    async def run_load_test(self, config: LoadTestConfig) -> List[TestResult]:
        """Run load test with specified configuration"""
        print(f"Starting load test: {config.concurrent_users} users, {config.requests_per_user} requests each")
        
        # Create user scenarios
        scenarios = []
        for user_id in range(config.concurrent_users):
            scenario = self.create_user_scenario(user_id, config)
            scenarios.append(scenario)
            
        # Ramp up users gradually
        tasks = []
        ramp_delay = config.ramp_up_time / config.concurrent_users if config.concurrent_users > 0 else 0
        
        for i, scenario in enumerate(scenarios):
            # Delay user start for ramp-up
            if ramp_delay > 0:
                await asyncio.sleep(ramp_delay)
                
            task = asyncio.create_task(self.run_single_user_scenario(scenario))
            tasks.append(task)
            
        # Wait for all users to complete
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        all_results = []
        for results_list in results_lists:
            if isinstance(results_list, list):
                all_results.extend(results_list)
                
        return all_results
        
    def create_user_scenario(self, user_id: int, config: LoadTestConfig) -> Dict:
        """Create a realistic user scenario for testing"""
        
        # Define different user behavior patterns
        scenarios = {
            'dashboard_user': {
                'requests': [
                    {'endpoint': '/auth/me', 'method': 'GET'},
                    {'endpoint': '/calendar/availability', 'method': 'GET', 'delay': 1},
                    {'endpoint': '/agent/audit-logs', 'method': 'GET', 'delay': 2},
                    {'endpoint': '/system/metrics', 'method': 'GET', 'delay': 1}
                ]
            },
            'scheduling_user': {
                'requests': [
                    {'endpoint': '/auth/me', 'method': 'GET'},
                    {'endpoint': '/calendar/availability', 'method': 'GET', 'delay': 1},
                    {
                        'endpoint': '/agent/schedule',
                        'method': 'POST',
                        'payload': {
                            'title': f'Test Meeting {user_id}',
                            'start': (datetime.now() + timedelta(days=1)).isoformat(),
                            'end': (datetime.now() + timedelta(days=1, hours=1)).isoformat(),
                            'attendees': [f'user{user_id}@test.com']
                        },
                        'delay': 2
                    },
                    {'endpoint': '/agent/audit-logs', 'method': 'GET', 'delay': 1}
                ]
            },
            'heavy_user': {
                'requests': [
                    {'endpoint': '/auth/me', 'method': 'GET'},
                    {'endpoint': '/calendar/availability', 'method': 'GET'},
                    {'endpoint': '/preferences', 'method': 'GET', 'delay': 0.5},
                    {
                        'endpoint': '/agent/analyze-priority',
                        'method': 'POST',
                        'payload': {
                            'title': 'Important Meeting',
                            'attendees': ['vip@company.com'],
                            'type': 'executive'
                        },
                        'delay': 1
                    },
                    {'endpoint': '/connections', 'method': 'GET', 'delay': 0.5},
                    {'endpoint': '/system/metrics', 'method': 'GET', 'delay': 1}
                ]
            }
        }
        
        # Randomly assign scenario type
        scenario_type = random.choice(list(scenarios.keys()))
        return scenarios[scenario_type]
        
    def analyze_results(self, results: List[TestResult]) -> Dict[str, Any]:
        """Analyze performance test results and generate statistics"""
        
        if not results:
            return {"error": "No results to analyze"}
            
        # Basic statistics
        response_times = [r.response_time for r in results]
        success_count = sum(1 for r in results if r.success)
        total_requests = len(results)
        
        # Response time statistics
        stats = {
            "total_requests": total_requests,
            "successful_requests": success_count,
            "failed_requests": total_requests - success_count,
            "success_rate": (success_count / total_requests) * 100 if total_requests > 0 else 0,
            "response_times": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "mean": statistics.mean(response_times) if response_times else 0,
                "median": statistics.median(response_times) if response_times else 0,
                "p95": self.percentile(response_times, 95) if response_times else 0,
                "p99": self.percentile(response_times, 99) if response_times else 0
            }
        }
        
        # Endpoint-specific statistics
        endpoint_stats = {}
        endpoints = set(r.endpoint for r in results)
        
        for endpoint in endpoints:
            endpoint_results = [r for r in results if r.endpoint == endpoint]
            endpoint_times = [r.response_time for r in endpoint_results]
            endpoint_success = sum(1 for r in endpoint_results if r.success)
            
            endpoint_stats[endpoint] = {
                "requests": len(endpoint_results),
                "success_rate": (endpoint_success / len(endpoint_results)) * 100,
                "avg_response_time": statistics.mean(endpoint_times) if endpoint_times else 0,
                "p95_response_time": self.percentile(endpoint_times, 95) if endpoint_times else 0
            }
            
        stats["endpoint_breakdown"] = endpoint_stats
        
        # Error analysis
        errors = [r for r in results if not r.success]
        error_breakdown = {}
        
        for error in errors:
            key = f"{error.status_code}: {error.error_message or 'HTTP Error'}"
            error_breakdown[key] = error_breakdown.get(key, 0) + 1
            
        stats["errors"] = error_breakdown
        
        return stats
        
    def percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a dataset"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
            
    async def run_stress_test(self, max_users: int = 100, step_size: int = 10, step_duration: int = 30):
        """Run stress test by gradually increasing load"""
        print(f"Starting stress test: 0 to {max_users} users in steps of {step_size}")
        
        stress_results = {}
        
        for user_count in range(step_size, max_users + 1, step_size):
            print(f"Testing with {user_count} concurrent users...")
            
            config = LoadTestConfig(
                concurrent_users=user_count,
                requests_per_user=5,
                ramp_up_time=5,
                test_duration=step_duration,
                endpoint="/calendar/availability"
            )
            
            step_results = await self.run_load_test(config)
            step_stats = self.analyze_results(step_results)
            
            stress_results[user_count] = step_stats
            
            # Check if system is degrading
            if step_stats["success_rate"] < 95 or step_stats["response_times"]["p95"] > 5.0:
                print(f"⚠ System degradation detected at {user_count} users")
                break
                
            await asyncio.sleep(2)  # Brief pause between steps
            
        return stress_results
        
    async def run_endurance_test(self, duration_minutes: int = 30, users: int = 20):
        """Run endurance test to check for memory leaks and performance degradation"""
        print(f"Starting endurance test: {users} users for {duration_minutes} minutes")
        
        end_time = time.time() + (duration_minutes * 60)
        interval_results = []
        
        while time.time() < end_time:
            config = LoadTestConfig(
                concurrent_users=users,
                requests_per_user=3,
                ramp_up_time=2,
                test_duration=60,  # 1 minute intervals
                endpoint="/calendar/availability"
            )
            
            interval_result = await self.run_load_test(config)
            interval_stats = self.analyze_results(interval_result)
            interval_stats["timestamp"] = datetime.now().isoformat()
            
            interval_results.append(interval_stats)
            
            print(f"Interval complete - Success rate: {interval_stats['success_rate']:.1f}%, "
                  f"Avg response: {interval_stats['response_times']['mean']:.3f}s")
                  
        return interval_results
        
    def generate_report(self, results: Dict[str, Any], test_type: str) -> str:
        """Generate a formatted performance test report"""
        
        report = f"""
# Performance Test Report - {test_type}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total Requests**: {results.get('total_requests', 0):,}
- **Success Rate**: {results.get('success_rate', 0):.2f}%
- **Failed Requests**: {results.get('failed_requests', 0):,}

## Response Time Statistics
- **Average**: {results.get('response_times', {}).get('mean', 0):.3f}s
- **Median**: {results.get('response_times', {}).get('median', 0):.3f}s
- **95th Percentile**: {results.get('response_times', {}).get('p95', 0):.3f}s
- **99th Percentile**: {results.get('response_times', {}).get('p99', 0):.3f}s
- **Min/Max**: {results.get('response_times', {}).get('min', 0):.3f}s / {results.get('response_times', {}).get('max', 0):.3f}s

## Endpoint Performance
"""
        
        for endpoint, stats in results.get('endpoint_breakdown', {}).items():
            report += f"""
### {endpoint}
- Requests: {stats['requests']:,}
- Success Rate: {stats['success_rate']:.2f}%
- Avg Response Time: {stats['avg_response_time']:.3f}s
- 95th Percentile: {stats['p95_response_time']:.3f}s
"""
        
        if results.get('errors'):
            report += "\n## Error Breakdown\n"
            for error, count in results['errors'].items():
                report += f"- {error}: {count:,} occurrences\n"
                
        return report

async def main():
    parser = argparse.ArgumentParser(description="Performance testing for AWS Meeting Scheduling Agent")
    parser.add_argument("--api-url", required=True, help="API Gateway base URL")
    parser.add_argument("--auth-token", help="Authentication token for API access")
    parser.add_argument("--test-type", choices=['load', 'stress', 'endurance', 'all'], 
                       default='load', help="Type of performance test to run")
    parser.add_argument("--users", type=int, default=50, help="Number of concurrent users for load test")
    parser.add_argument("--requests", type=int, default=10, help="Requests per user")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--output", default="performance_report.json", help="Output file for results")
    
    args = parser.parse_args()
    
    print("AWS Meeting Scheduling Agent - Performance Testing")
    print("=" * 60)
    print(f"API URL: {args.api_url}")
    print(f"Test Type: {args.test_type}")
    print("=" * 60)
    
    tester = PerformanceTester(args.api_url, args.auth_token)
    await tester.setup_session()
    
    try:
        if args.test_type == 'load' or args.test_type == 'all':
            print("\n🔄 Running Load Test...")
            config = LoadTestConfig(
                concurrent_users=args.users,
                requests_per_user=args.requests,
                ramp_up_time=10,
                test_duration=args.duration,
                endpoint="/calendar/availability"
            )
            
            load_results = await tester.run_load_test(config)
            load_stats = tester.analyze_results(load_results)
            
            print("✅ Load Test Complete")
            print(f"Success Rate: {load_stats['success_rate']:.2f}%")
            print(f"Average Response Time: {load_stats['response_times']['mean']:.3f}s")
            print(f"95th Percentile: {load_stats['response_times']['p95']:.3f}s")
            
        if args.test_type == 'stress' or args.test_type == 'all':
            print("\n🔄 Running Stress Test...")
            stress_results = await tester.run_stress_test(max_users=100, step_size=10)
            print("✅ Stress Test Complete")
            
        if args.test_type == 'endurance' or args.test_type == 'all':
            print("\n🔄 Running Endurance Test...")
            endurance_results = await tester.run_endurance_test(duration_minutes=10, users=20)
            print("✅ Endurance Test Complete")
            
        # Save results
        final_results = {
            'test_config': vars(args),
            'timestamp': datetime.now().isoformat(),
            'load_test': load_stats if 'load_stats' in locals() else None,
            'stress_test': stress_results if 'stress_results' in locals() else None,
            'endurance_test': endurance_results if 'endurance_results' in locals() else None
        }
        
        with open(args.output, 'w') as f:
            json.dump(final_results, f, indent=2, default=str)
            
        print(f"\n📊 Results saved to {args.output}")
        
    finally:
        await tester.cleanup_session()

if __name__ == "__main__":
    asyncio.run(main())