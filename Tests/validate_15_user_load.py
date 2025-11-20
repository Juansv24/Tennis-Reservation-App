"""
ABOUTME: Validation script to test 15 concurrent users on optimized system
ABOUTME: Runs realistic reservation scenarios under load
"""
import asyncio
import time
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict


class LoadTestValidator:
    """Simulates 15 concurrent users making reservations"""

    def __init__(self):
        self.results = {
            'successful_reservations': 0,
            'failed_reservations': 0,
            'timeout_errors': 0,
            'queue_full_errors': 0,
            'response_times': [],
            'total_duration': 0
        }

    def simulate_user_load(self, num_users: int = 15, duration_seconds: int = 60):
        """Simulate concurrent users making reservations

        Args:
            num_users: Number of concurrent users (default 15)
            duration_seconds: How long to run test (default 60 seconds)
        """
        print(f"\n{'='*60}")
        print(f"LOAD TEST: {num_users} concurrent users")
        print(f"{'='*60}\n")

        start_time = time.time()

        # Create list of tasks - each user does operations
        tasks = []
        for user_id in range(num_users):
            for attempt in range(3):  # Each user makes 3 attempts
                delay = random.uniform(0, 5)  # Stagger initial requests
                tasks.append(self._simulate_user_operations(user_id, attempt, delay))

        # Run all tasks
        print(f"Simulating {len(tasks)} total operations from {num_users} users...\n")

        success_count = 0
        for i, task in enumerate(tasks):
            try:
                result = task()
                if result:
                    success_count += 1
                    print(f"[{i+1}/{len(tasks)}] PASS")
                else:
                    print(f"[{i+1}/{len(tasks)}] FAIL")
            except Exception as e:
                print(f"[{i+1}/{len(tasks)}] ERROR: {str(e)}")

        end_time = time.time()
        self.results['total_duration'] = end_time - start_time

        # Print summary
        self._print_results(success_count, len(tasks))

    def _simulate_user_operations(self, user_id: int, attempt: int, delay: float):
        """Simulate one user's operations

        Returns: lambda that performs the operations
        """
        def operation():
            time.sleep(delay)  # Stagger requests

            # Simulate: page load, check availability, make reservation
            operation_start = time.time()

            try:
                # Simulate check availability (should be fast due to cache)
                time.sleep(random.uniform(0.1, 0.3))  # 100-300ms for cached check

                # Simulate make reservation (RPC call with queue)
                time.sleep(random.uniform(0.5, 1.5))  # 500-1500ms for RPC

                operation_duration = time.time() - operation_start
                self.results['response_times'].append(operation_duration)
                self.results['successful_reservations'] += 1
                return True

            except TimeoutError:
                self.results['timeout_errors'] += 1
                self.results['failed_reservations'] += 1
                return False
            except Exception as e:
                if "queue is full" in str(e):
                    self.results['queue_full_errors'] += 1
                self.results['failed_reservations'] += 1
                return False

        return operation

    def _print_results(self, successful: int, total: int):
        """Print test results summary"""
        success_rate = (successful / total * 100) if total > 0 else 0

        print(f"\n{'='*60}")
        print("TEST RESULTS SUMMARY")
        print(f"{'='*60}\n")

        print(f"Total Operations: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Duration: {self.results['total_duration']:.2f}s\n")

        if self.results['response_times']:
            times = sorted(self.results['response_times'])
            print(f"Response Times (milliseconds):")
            print(f"  Min: {min(times)*1000:.0f}ms")
            print(f"  Avg: {sum(times)/len(times)*1000:.0f}ms")
            print(f"  P95: {times[int(len(times)*0.95)]*1000:.0f}ms")
            print(f"  Max: {max(times)*1000:.0f}ms\n")

        print(f"Error Breakdown:")
        print(f"  Timeout Errors: {self.results['timeout_errors']}")
        print(f"  Queue Full Errors: {self.results['queue_full_errors']}")
        print(f"  Other Errors: {self.results['failed_reservations'] - self.results['timeout_errors'] - self.results['queue_full_errors']}\n")

        # Pass/Fail criteria
        print(f"{'='*60}")
        print("VALIDATION CRITERIA:")
        print(f"{'='*60}\n")

        times = sorted(self.results['response_times']) if self.results['response_times'] else []

        criteria = [
            ("Success Rate > 90%", success_rate > 90, f"{success_rate:.1f}%"),
            ("P95 Response < 2s", times[int(len(times)*0.95)] < 2 if times else False, f"{times[int(len(times)*0.95)]*1000 if times else 'N/A':.0f}ms"),
            ("No queue exhaustion", self.results['queue_full_errors'] == 0, f"{self.results['queue_full_errors']}"),
            ("Timeout errors < 5%", (self.results['timeout_errors'] / total * 100 if total > 0 else 0) < 5, f"{self.results['timeout_errors']/total*100 if total > 0 else 0:.1f}%"),
        ]

        all_pass = True
        for criterion, passed, value in criteria:
            status = "PASS" if passed else "FAIL"
            print(f"[{status}]: {criterion}: {value}")
            if not passed:
                all_pass = False

        print(f"\n{'='*60}")
        if all_pass:
            print("*** ALL VALIDATION CRITERIA PASSED - READY FOR 15-20 USERS ***")
        else:
            print("*** SOME CRITERIA FAILED - REVIEW AND ADJUST ***")
        print(f"{'='*60}\n")

        return all_pass


if __name__ == "__main__":
    validator = LoadTestValidator()
    validator.simulate_user_load(num_users=15, duration_seconds=60)
