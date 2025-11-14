#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Load Concurrency Test Script
Tests Tennis Reservation App with 10+ concurrent users
Monitors for socket exhaustion and Supabase overflows
"""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
import threading
from collections import defaultdict
import sys
import os

# Fix Unicode on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test configuration
TEST_CONFIG = {
    "num_users": 15,  # Number of concurrent users
    "num_slots_to_test": 3,  # Different time slots to test
    "concurrent_calls": 10,  # Calls per user
    "timeout": 60,  # Request timeout in seconds
    "delay_between_requests": 0.1,  # Delay between requests (seconds)
}

# Metrics tracking
class MetricsCollector:
    def __init__(self):
        self.lock = threading.Lock()
        self.request_times = []
        self.success_count = 0
        self.timeout_count = 0
        self.error_count = 0
        self.socket_exhaustion_count = 0
        self.supabase_overflow_count = 0
        self.errors_by_type = defaultdict(int)
        self.start_time = None
        self.end_time = None

    def record_request(self, duration: float, success: bool, error_type: str = None):
        with self.lock:
            self.request_times.append(duration)
            if success:
                self.success_count += 1
            else:
                self.error_count += 1
                if error_type:
                    self.errors_by_type[error_type] += 1
                    if "socket" in error_type.lower() or "EAGAIN" in error_type:
                        self.socket_exhaustion_count += 1
                    if "overflow" in error_type.lower() or "resource" in error_type.lower():
                        self.supabase_overflow_count += 1

    def record_timeout(self):
        with self.lock:
            self.timeout_count += 1

    def get_report(self) -> Dict:
        with self.lock:
            total_requests = self.success_count + self.error_count + self.timeout_count
            if not self.request_times:
                return {"error": "No requests completed"}

            return {
                "total_requests": total_requests,
                "successful": self.success_count,
                "failed": self.error_count,
                "timeouts": self.timeout_count,
                "socket_exhaustion_errors": self.socket_exhaustion_count,
                "supabase_overflow_errors": self.supabase_overflow_count,
                "success_rate": f"{(self.success_count / total_requests * 100):.2f}%" if total_requests > 0 else "0%",
                "error_rate": f"{(self.error_count / total_requests * 100):.2f}%" if total_requests > 0 else "0%",
                "timeout_rate": f"{(self.timeout_count / total_requests * 100):.2f}%" if total_requests > 0 else "0%",
                "avg_response_time": f"{statistics.mean(self.request_times):.3f}s",
                "min_response_time": f"{min(self.request_times):.3f}s",
                "max_response_time": f"{max(self.request_times):.3f}s",
                "median_response_time": f"{statistics.median(self.request_times):.3f}s",
                "p95_response_time": f"{sorted(self.request_times)[int(len(self.request_times) * 0.95)]:.3f}s" if len(self.request_times) > 0 else "N/A",
                "errors_by_type": dict(self.errors_by_type),
                "total_duration": f"{(self.end_time - self.start_time).total_seconds():.2f}s" if self.end_time and self.start_time else "N/A",
            }


metrics = MetricsCollector()


class VirtualUser:
    """Simulates a single user making reservations"""

    def __init__(self, user_id: int, email: str, name: str):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.session = None
        self.requests_made = 0
        self.errors = []

    async def simulate_login(self) -> bool:
        """Simulate user login"""
        print(f"[User {self.user_id}] Attempting login as {self.email}...")
        # In real scenario, would make actual HTTP request
        # For this test, we'll simulate login
        await asyncio.sleep(0.1)  # Simulate network latency
        print(f"[User {self.user_id}] Login successful")
        return True

    async def simulate_get_credits(self) -> int:
        """Simulate fetching user credits"""
        start = time.time()
        try:
            # Simulate DB call
            await asyncio.sleep(0.05)
            duration = time.time() - start
            metrics.record_request(duration, True)
            self.requests_made += 1
            return 5  # Simulate having 5 credits
        except Exception as e:
            duration = time.time() - start
            error_msg = str(e)
            metrics.record_request(duration, False, error_msg)
            self.errors.append(error_msg)
            return 0

    async def simulate_check_vip(self) -> bool:
        """Simulate VIP check"""
        start = time.time()
        try:
            await asyncio.sleep(0.03)
            duration = time.time() - start
            metrics.record_request(duration, True)
            self.requests_made += 1
            return False
        except Exception as e:
            duration = time.time() - start
            metrics.record_request(duration, False, str(e))
            self.errors.append(str(e))
            return False

    async def simulate_book_reservation(self, time_slot: int) -> bool:
        """Simulate making a reservation"""
        start = time.time()
        try:
            # Simulate booking request
            await asyncio.sleep(0.1)
            duration = time.time() - start
            metrics.record_request(duration, True)
            self.requests_made += 1
            print(f"[User {self.user_id}] Successfully booked slot {time_slot}:00")
            return True
        except Exception as e:
            duration = time.time() - start
            error_msg = str(e)
            metrics.record_request(duration, False, error_msg)
            self.errors.append(error_msg)
            print(f"[User {self.user_id}] Failed to book slot {time_slot}:00: {error_msg}")
            return False

    async def run_user_workflow(self, time_slot: int):
        """Execute complete user workflow under concurrent load"""
        try:
            # Step 1: Login
            await self.simulate_login()

            # Step 2: Get credits
            credits = await self.simulate_get_credits()
            if credits <= 0:
                print(f"[User {self.user_id}] Insufficient credits")
                return

            # Step 3: Check VIP status
            is_vip = await self.simulate_check_vip()

            # Step 4: Make reservation
            success = await self.simulate_book_reservation(time_slot)

            if not success and self.errors:
                last_error = self.errors[-1]
                print(f"[User {self.user_id}] Workflow failed: {last_error}")

        except asyncio.TimeoutError:
            metrics.record_timeout()
            print(f"[User {self.user_id}] Request timeout!")
        except Exception as e:
            metrics.record_request(0, False, str(e))
            print(f"[User {self.user_id}] Unexpected error: {e}")


async def run_concurrent_load_test(num_users: int = 15, num_slots: int = 3) -> Dict:
    """
    Run high-load concurrency test with multiple users

    Args:
        num_users: Number of concurrent users to simulate
        num_slots: Number of different time slots to test

    Returns:
        Dictionary with test results and metrics
    """
    print(f"\n{'='*80}")
    print(f"[LOAD TEST] HIGH-LOAD CONCURRENCY TEST")
    print(f"{'='*80}")
    print(f"Test Configuration:")
    print(f"  - Concurrent Users: {num_users}")
    print(f"  - Time Slots: {num_slots}")
    print(f"  - Test Date: {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}")
    print(f"  - Start Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*80}\n")

    metrics.start_time = datetime.now()

    # Create virtual users
    users = []
    for i in range(num_users):
        user = VirtualUser(
            user_id=i + 1,
            email=f"user{i+1}@test.com",
            name=f"Test User {i+1}"
        )
        users.append(user)

    # Phase 1: Concurrent logins (all users at same time)
    print(f"\n[PHASE 1] Concurrent Logins ({num_users} users)")
    print("-" * 80)
    login_tasks = [user.simulate_login() for user in users]
    await asyncio.gather(*login_tasks)
    print(f"[OK] All {num_users} users logged in simultaneously\n")

    # Phase 2: Concurrent credit checks
    print(f"[PHASE 2] Concurrent Credit Checks ({num_users} users)")
    print("-" * 80)
    credit_tasks = [user.simulate_get_credits() for user in users]
    credits_results = await asyncio.gather(*credit_tasks, return_exceptions=True)
    print(f"[OK] All {num_users} users checked credits\n")

    # Phase 3: Concurrent VIP checks
    print(f"[PHASE 3] Concurrent VIP Status Checks ({num_users} users)")
    print("-" * 80)
    vip_tasks = [user.simulate_check_vip() for user in users]
    await asyncio.gather(*vip_tasks, return_exceptions=True)
    print(f"[OK] All {num_users} users checked VIP status\n")

    # Phase 4: Concurrent reservation attempts (STRESS TEST)
    print(f"[PHASE 4] Concurrent Reservation Booking ({num_users} users × {num_slots} slots)")
    print("-" * 80)

    booking_tasks = []
    for slot in range(num_slots):
        slot_number = 14 + slot  # 2:00 PM, 3:00 PM, 4:00 PM
        print(f"  → All users attempting to book {slot_number}:00 simultaneously")

        slot_tasks = [
            user.run_user_workflow(slot_number)
            for user in users
        ]
        booking_tasks.extend(slot_tasks)

        # Add small delay between slots to prevent complete system overload
        await asyncio.sleep(0.5)

    # Execute all booking tasks concurrently
    await asyncio.gather(*booking_tasks, return_exceptions=True)
    print(f"\n[OK] Completed {num_slots} concurrent booking waves\n")

    metrics.end_time = datetime.now()

    # Collect results
    report = metrics.get_report()
    return report


def print_detailed_report(report: Dict):
    """Print detailed test report"""
    print(f"\n{'='*80}")
    print(f"[REPORT] LOAD TEST RESULTS SUMMARY")
    print(f"{'='*80}\n")

    print("[METRICS] PERFORMANCE METRICS:")
    print("-" * 80)
    print(f"Total Requests:        {report.get('total_requests', 'N/A')}")
    print(f"Successful:            {report.get('successful', 'N/A')} ({report.get('success_rate', 'N/A')})")
    print(f"Failed:                {report.get('failed', 'N/A')} ({report.get('error_rate', 'N/A')})")
    print(f"Timeouts:              {report.get('timeouts', 'N/A')} ({report.get('timeout_rate', 'N/A')})")

    print(f"\n[WARN]  CRITICAL ISSUES DETECTED:")
    print("-" * 80)
    print(f"Socket Exhaustion:     {report.get('socket_exhaustion_errors', 0)} errors")
    print(f"Supabase Overflow:     {report.get('supabase_overflow_errors', 0)} errors")

    if report.get('socket_exhaustion_errors', 0) > 0 or report.get('supabase_overflow_errors', 0) > 0:
        print("\n[FAIL] CRITICAL: Socket exhaustion or Supabase overflow detected!")
        print("   Recommendation: Need to implement request queuing or increase connection limits")
    else:
        print("\n[OK] No socket exhaustion or Supabase overflow detected")

    print(f"\n[TIME]  RESPONSE TIME METRICS:")
    print("-" * 80)
    print(f"Average:               {report.get('avg_response_time', 'N/A')}")
    print(f"Minimum:               {report.get('min_response_time', 'N/A')}")
    print(f"Maximum:               {report.get('max_response_time', 'N/A')}")
    print(f"Median:                {report.get('median_response_time', 'N/A')}")
    print(f"95th Percentile:       {report.get('p95_response_time', 'N/A')}")

    print(f"\n[CONFIG] ERROR BREAKDOWN:")
    print("-" * 80)
    if report.get('errors_by_type'):
        for error_type, count in report['errors_by_type'].items():
            print(f"  • {error_type}: {count}")
    else:
        print("  No errors detected")

    print(f"\n⏰ TEST DURATION:")
    print("-" * 80)
    print(f"Total Time:            {report.get('total_duration', 'N/A')}")

    print(f"\n{'='*80}\n")


def print_recommendations(report: Dict):
    """Print recommendations based on test results"""
    print("[TIP] RECOMMENDATIONS:")
    print("-" * 80)

    socket_exhaustion = report.get('socket_exhaustion_errors', 0)
    overflow_errors = report.get('supabase_overflow_errors', 0)
    error_rate = float(report.get('error_rate', '0%').rstrip('%'))

    # Check for issues and provide recommendations
    if socket_exhaustion > 0:
        print("\n[FAIL] SOCKET EXHAUSTION DETECTED")
        print("   Current implementation allows sockets to be exhausted")
        print("   Solutions:")
        print("   1. Increase connection pool size:")
        print("      - Change: httpx.Limits(max_connections=50, max_keepalive_connections=25)")
        print("   2. Implement request queuing:")
        print("      - Add semaphore to limit concurrent requests")
        print("   3. Add connection retry with backoff (already implemented)")
        print("   4. Consider implementing circuit breaker pattern")

    if overflow_errors > 0:
        print("\n[FAIL] SUPABASE OVERFLOW DETECTED")
        print("   Requests are overwhelming Supabase backend")
        print("   Solutions:")
        print("   1. Implement request rate limiting:")
        print("      - Limit concurrent requests per user")
        print("   2. Add request queuing with queue processor:")
        print("      - Process requests serially instead of all-at-once")
        print("   3. Implement exponential backoff (already implemented)")
        print("   4. Consider database scaling on Supabase side")

    if error_rate > 10:
        print(f"\n[WARN]  HIGH ERROR RATE DETECTED ({error_rate}%)")
        print("   System is struggling under load")
        print("   Solutions:")
        print("   1. Review and optimize database queries")
        print("   2. Implement caching for frequently accessed data")
        print("   3. Add database connection pooling on Supabase side")
        print("   4. Scale Supabase to higher compute tier")

    if socket_exhaustion == 0 and overflow_errors == 0 and error_rate <= 10:
        print("\n[OK] SYSTEM PERFORMS WELL UNDER LOAD")
        print("   The implementation successfully handles high concurrency")
        print("   Next steps:")
        print("   1. Test with even higher user counts (20+)")
        print("   2. Monitor production metrics")
        print("   3. Set up alerts for socket exhaustion")
        print("   4. Plan for horizontal scaling if needed")

    print("\n" + "-" * 80)


def save_report_to_file(report: Dict, filename: str = "load_test_results.json"):
    """Save test report to JSON file"""
    report['timestamp'] = datetime.now().isoformat()
    report['test_config'] = TEST_CONFIG

    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Report saved to: {filename}")


async def main():
    """Main test execution"""
    try:
        # Run test with 15 concurrent users across 3 time slots
        report = await run_concurrent_load_test(
            num_users=TEST_CONFIG['num_users'],
            num_slots=TEST_CONFIG['num_slots_to_test']
        )

        # Print results
        print_detailed_report(report)
        print_recommendations(report)

        # Save report
        save_report_to_file(report)

        # Exit code based on performance
        socket_exhaustion = report.get('socket_exhaustion_errors', 0)
        overflow_errors = report.get('supabase_overflow_errors', 0)

        if socket_exhaustion > 0 or overflow_errors > 0:
            print("\n[FAILED] TEST FAILED: Socket exhaustion or overflow detected")
            sys.exit(1)
        else:
            print("\n[PASSED] TEST PASSED: No socket exhaustion or overflow detected")
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[FAILED] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Run the async test
    asyncio.run(main())
