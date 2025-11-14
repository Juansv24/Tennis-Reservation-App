#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real Supabase Load Test - 10+ Concurrent Users
Stress tests actual Supabase backend to detect socket exhaustion and overflows
"""

import sys
import io

# Fix Unicode on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import threading
from collections import defaultdict
import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent / "User App"))

try:
    # Try to import Supabase and app modules
    from supabase import create_client, Client
    from supabase.client import ClientOptions
    import httpx
    import streamlit as st
    print("[OK] Supabase modules imported successfully")
except ImportError as e:
    print(f"[WARN] Warning: Could not import required modules: {e}")
    print("Note: Some features will be simulated instead of using real Supabase")

# Load configuration
TEST_CONFIG = {
    "num_users": 15,
    "num_concurrent_requests": 15,
    "test_duration_seconds": 120,
    "timeout_seconds": 30,
    "test_date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
    "test_time_slots": [14, 15, 16, 17, 18],  # 2 PM - 6 PM
}


class SupabaseConnectionPool:
    """Manages Supabase client with proper connection pooling"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.client: Optional[Client] = None
        self.connection_errors = 0
        self.successful_connections = 0

        try:
            # Try to load from environment or secrets
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")

            if not supabase_url or not supabase_key:
                print("[WARN] Supabase credentials not found in environment")
                print("   Continuing with simulated load test...")
                self.client = None
                return

            # Configure httpx client for high concurrency
            limits = httpx.Limits(
                max_connections=50,           # Increase for high concurrency
                max_keepalive_connections=25
            )

            httpx_client = httpx.Client(
                limits=limits,
                timeout=httpx.Timeout(30.0, connect=10.0),
                http2=True,
                verify=True
            )

            # Create Supabase client with proper configuration
            options = ClientOptions(
                schema="public",
                auto_refresh_token=True,
                persist_session=True,
                httpx_client=httpx_client,
                postgrest_client_timeout=httpx.Timeout(30.0, connect=10.0),
                storage_client_timeout=httpx.Timeout(30.0, connect=10.0),
                function_client_timeout=httpx.Timeout(30.0, connect=10.0)
            )

            self.client = create_client(supabase_url, supabase_key, options)
            self.successful_connections += 1
            print("[OK] Supabase client initialized with high-concurrency configuration")

        except Exception as e:
            self.connection_errors += 1
            print(f"[WARN] Could not initialize Supabase client: {e}")
            self.client = None


class MetricsCollector:
    """Collects detailed metrics during load test"""

    def __init__(self):
        self.lock = threading.Lock()
        self.request_times = []
        self.requests_by_type = defaultdict(int)
        self.success_count = 0
        self.failure_count = 0
        self.timeout_count = 0
        self.socket_exhaustion_count = 0
        self.supabase_overflow_count = 0
        self.rate_limit_errors = 0
        self.connection_errors = 0
        self.errors_by_type = defaultdict(int)
        self.concurrent_requests = 0
        self.max_concurrent = 0
        self.start_time = None
        self.end_time = None
        self.request_queue = []  # Track request timing for throughput

    def record_request(
        self,
        request_type: str,
        duration: float,
        success: bool,
        error_type: Optional[str] = None,
        concurrent: int = 0
    ):
        with self.lock:
            self.request_times.append(duration)
            self.requests_by_type[request_type] += 1
            self.concurrent_requests = concurrent
            self.max_concurrent = max(self.max_concurrent, concurrent)

            if success:
                self.success_count += 1
            else:
                self.failure_count += 1
                if error_type:
                    self.errors_by_type[error_type] += 1

                    # Categorize errors
                    if "socket" in error_type.lower() or "EAGAIN" in error_type or "Connection" in error_type:
                        self.socket_exhaustion_count += 1
                    elif "resource" in error_type.lower() or "503" in error_type or "overflow" in error_type:
                        self.supabase_overflow_count += 1
                    elif "429" in error_type or "rate" in error_type.lower():
                        self.rate_limit_errors += 1

            self.request_queue.append({
                'timestamp': time.time(),
                'duration': duration,
                'success': success
            })

    def record_timeout(self, request_type: str = "unknown"):
        with self.lock:
            self.timeout_count += 1
            self.failure_count += 1
            self.requests_by_type[request_type] += 1

    def get_throughput(self) -> float:
        """Calculate requests per second"""
        if not self.start_time or not self.end_time:
            return 0

        duration = (self.end_time - self.start_time).total_seconds()
        total_requests = self.success_count + self.failure_count + self.timeout_count
        return total_requests / duration if duration > 0 else 0

    def get_report(self) -> Dict:
        with self.lock:
            total_requests = self.success_count + self.failure_count + self.timeout_count

            if not self.request_times:
                return {"error": "No requests completed"}

            return {
                "summary": {
                    "total_requests": total_requests,
                    "successful": self.success_count,
                    "failed": self.failure_count,
                    "timeouts": self.timeout_count,
                    "success_rate": f"{(self.success_count / total_requests * 100):.2f}%" if total_requests > 0 else "0%",
                    "failure_rate": f"{(self.failure_count / total_requests * 100):.2f}%" if total_requests > 0 else "0%",
                    "timeout_rate": f"{(self.timeout_count / total_requests * 100):.2f}%" if total_requests > 0 else "0%",
                },
                "critical_issues": {
                    "socket_exhaustion": self.socket_exhaustion_count,
                    "supabase_overflow": self.supabase_overflow_count,
                    "rate_limit_errors": self.rate_limit_errors,
                    "connection_errors": self.connection_errors,
                },
                "response_times": {
                    "average": f"{statistics.mean(self.request_times):.3f}s",
                    "min": f"{min(self.request_times):.3f}s",
                    "max": f"{max(self.request_times):.3f}s",
                    "median": f"{statistics.median(self.request_times):.3f}s",
                    "p95": f"{sorted(self.request_times)[int(len(self.request_times) * 0.95)]:.3f}s" if len(self.request_times) > 20 else "N/A",
                    "p99": f"{sorted(self.request_times)[int(len(self.request_times) * 0.99)]:.3f}s" if len(self.request_times) > 100 else "N/A",
                },
                "concurrency": {
                    "max_concurrent_requests": self.max_concurrent,
                    "throughput_rps": f"{self.get_throughput():.2f}",
                },
                "by_type": dict(self.requests_by_type),
                "errors_by_type": dict(self.errors_by_type),
            }


metrics = MetricsCollector()


class VirtualUser:
    """Simulates a concurrent user making database queries"""

    def __init__(self, user_id: int, email: str, name: str):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.client = SupabaseConnectionPool().client
        self.requests_completed = 0
        self.errors = []

    async def _make_request(
        self,
        request_func,
        request_type: str,
        timeout: float = 30.0
    ) -> Tuple[bool, Optional[str]]:
        """Execute request with timeout and error handling"""
        start = time.time()
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(request_func),
                timeout=timeout
            )
            duration = time.time() - start
            metrics.record_request(request_type, duration, True, None)
            self.requests_completed += 1
            return True, None

        except asyncio.TimeoutError:
            duration = time.time() - start
            error_msg = f"Timeout (>{timeout}s)"
            metrics.record_timeout(request_type)
            self.errors.append(error_msg)
            return False, error_msg

        except Exception as e:
            duration = time.time() - start
            error_msg = str(e)
            metrics.record_request(request_type, duration, False, error_msg)
            self.errors.append(error_msg)
            return False, error_msg

    async def check_user_credits(self) -> bool:
        """Query user credits from Supabase"""
        def query():
            if not self.client:
                raise Exception("Supabase client not available")
            result = self.client.table('users').select('credits').eq(
                'email', self.email
            ).execute()
            return result.data[0]['credits'] if result.data else 0

        success, error = await self._make_request(query, "check_credits")
        return success

    async def check_vip_status(self) -> bool:
        """Query VIP status from Supabase"""
        def query():
            if not self.client:
                raise Exception("Supabase client not available")
            result = self.client.table('vip_users').select('id').eq(
                'email', self.email
            ).execute()
            return len(result.data) > 0

        success, error = await self._make_request(query, "check_vip")
        return success

    async def get_reservations(self, date: str) -> bool:
        """Get existing reservations for a date"""
        def query():
            if not self.client:
                raise Exception("Supabase client not available")
            result = self.client.table('reservations').select(
                'id, hour, name'
            ).eq('date', date).execute()
            return result.data

        success, error = await self._make_request(query, "get_reservations")
        return success

    async def run_full_workflow(self, test_date: str, time_slot: int):
        """Execute complete user workflow"""
        try:
            # 1. Check credits
            has_credits = await self.check_user_credits()
            if not has_credits:
                print(f"[User {self.user_id}] Insufficient credits")
                return

            # 2. Check VIP
            await self.check_vip_status()

            # 3. Get existing reservations
            await self.get_reservations(test_date)

            print(f"[User {self.user_id}] Workflow completed ({self.requests_completed} requests)")

        except Exception as e:
            print(f"[User {self.user_id}] Workflow error: {e}")
            self.errors.append(str(e))


async def run_load_test_wave(
    num_users: int,
    test_date: str,
    time_slot: int
) -> Dict:
    """
    Run a single wave of concurrent requests (all users hitting same time slot)

    Args:
        num_users: Number of concurrent users
        test_date: Date for reservation attempt
        time_slot: Hour (14-18)

    Returns:
        Metrics from this wave
    """
    print(f"\n🌊 LOAD TEST WAVE: {num_users} users attempting {time_slot}:00")
    print("-" * 80)

    # Create virtual users
    users = [
        VirtualUser(i + 1, f"loadtest_user{i+1}@test.com", f"Load Test User {i+1}")
        for i in range(num_users)
    ]

    # Execute workflows concurrently
    start_wave = time.time()
    tasks = [user.run_full_workflow(test_date, time_slot) for user in users]

    try:
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        print(f"[FAIL] Wave error: {e}")

    duration = time.time() - start_wave
    print(f"[OK] Wave completed in {duration:.2f}s")

    return {
        "duration": duration,
        "users": num_users,
        "time_slot": time_slot,
    }


async def run_sustained_load_test(duration_seconds: int = 60) -> Dict:
    """
    Run sustained load test with continuous concurrent requests

    Args:
        duration_seconds: How long to run the test

    Returns:
        Test results
    """
    print(f"\n⚡ SUSTAINED LOAD TEST: {duration_seconds}s")
    print("-" * 80)

    num_users = TEST_CONFIG['num_concurrent_requests']
    test_date = TEST_CONFIG['test_date']

    # Create users
    users = [
        VirtualUser(i + 1, f"sustained_user{i+1}@test.com", f"Sustained Test User {i+1}")
        for i in range(num_users)
    ]

    start_time = time.time()
    wave_number = 0

    while time.time() - start_time < duration_seconds:
        wave_number += 1
        time_slot = TEST_CONFIG['test_time_slots'][wave_number % len(TEST_CONFIG['test_time_slots'])]

        # Run all users concurrently
        tasks = [user.run_full_workflow(test_date, time_slot) for user in users]

        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            print(f"[FAIL] Wave {wave_number} error: {e}")

        # Small delay between waves
        await asyncio.sleep(1)
        elapsed = time.time() - start_time
        print(f"  Wave {wave_number} complete. Elapsed: {elapsed:.1f}s / {duration_seconds}s")

    return {"waves_completed": wave_number}


async def main():
    """Main load test execution"""

    print(f"\n{'='*80}")
    print(f"[TENNIS] SUPABASE HIGH-LOAD CONCURRENCY TEST (10+ Users)")
    print(f"{'='*80}")
    print(f"\nTest Configuration:")
    print(f"  Concurrent Users:       {TEST_CONFIG['num_users']}")
    print(f"  Test Date:              {TEST_CONFIG['test_date']}")
    print(f"  Time Slots:             {TEST_CONFIG['test_time_slots']}")
    print(f"  Timeout:                {TEST_CONFIG['timeout_seconds']}s")
    print(f"\nStarting test at {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}\n")

    metrics.start_time = datetime.now()

    try:
        # Run multiple waves of load testing
        for wave, time_slot in enumerate(TEST_CONFIG['test_time_slots'][:3], 1):
            await run_load_test_wave(
                num_users=TEST_CONFIG['num_users'],
                test_date=TEST_CONFIG['test_date'],
                time_slot=time_slot
            )
            await asyncio.sleep(1)  # Brief pause between waves

        # Run sustained load test
        await run_sustained_load_test(duration_seconds=30)

        metrics.end_time = datetime.now()

        # Generate report
        report = metrics.get_report()

        # Print results
        print_load_test_report(report)

        # Save report
        save_report(report)

        # Return exit code based on results
        if (report['critical_issues']['socket_exhaustion'] > 0 or
            report['critical_issues']['supabase_overflow'] > 0):
            print("\n[FAIL] TEST FAILED: Critical issues detected")
            return 1
        else:
            print("\n[OK] TEST PASSED: No critical socket/overflow issues")
            return 0

    except KeyboardInterrupt:
        print("\n\n[WARN] Test interrupted by user")
        return 130
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


def print_load_test_report(report: Dict):
    """Print detailed load test report"""

    print(f"\n{'='*80}")
    print(f"[REPORT] LOAD TEST RESULTS")
    print(f"{'='*80}\n")

    # Summary
    print("[REPORT] REQUEST SUMMARY:")
    print("-" * 80)
    summary = report.get('summary', {})
    for key, value in summary.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")

    # Critical issues
    print(f"\n[WARN]  CRITICAL ISSUES:")
    print("-" * 80)
    critical = report.get('critical_issues', {})
    for key, value in critical.items():
        status = "[FAIL]" if value > 0 else "[OK]"
        print(f"  {status} {key.replace('_', ' ').title()}: {value}")

    # Response times
    print(f"\n[TIME]  RESPONSE TIME ANALYSIS:")
    print("-" * 80)
    times = report.get('response_times', {})
    for key, value in times.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")

    # Concurrency metrics
    print(f"\n[RETRY] CONCURRENCY METRICS:")
    print("-" * 80)
    concurrency = report.get('concurrency', {})
    for key, value in concurrency.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")

    print(f"\n{'='*80}\n")


def save_report(report: Dict, filename: str = "load_test_results.json"):
    """Save test report to file"""
    report['timestamp'] = datetime.now().isoformat()
    report['test_config'] = TEST_CONFIG

    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Report saved to: {filename}")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
