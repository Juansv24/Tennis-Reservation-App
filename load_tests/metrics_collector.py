"""
Metrics collector for load testing
Tracks performance metrics, errors, and timing for all test operations
"""
import time
import csv
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from threading import Lock
from dataclasses import dataclass, asdict
from enum import Enum


class OperationType(Enum):
    """Types of operations tracked"""
    LOGIN = "login"
    PAGE_LOAD = "page_load"
    VIEW_DASHBOARD = "view_dashboard"
    VIEW_RESERVATIONS = "view_reservations"
    VIEW_ACCOUNT_INFO = "view_account_info"
    BROWSE_SLOTS = "browse_slots"
    MAKE_RESERVATION = "make_reservation"
    CHECK_CREDITS = "check_credits"
    LOGOUT = "logout"
    ERROR = "error"


class OperationStatus(Enum):
    """Status of operation"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class Metric:
    """Single metric record"""
    timestamp: str
    user_id: str
    user_profile: str
    operation: str
    status: str
    duration_ms: float
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class MetricsCollector:
    """Thread-safe metrics collection for concurrent load testing"""

    def __init__(self, results_dir: str = "load_tests/results"):
        """Initialize metrics collector

        Args:
            results_dir: Directory to store metrics files
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.metrics: List[Metric] = []
        self.lock = Lock()  # Thread-safe access
        self.start_time = time.time()
        self.end_time: Optional[float] = None

    def record_operation(
        self,
        user_id: str,
        user_profile: str,
        operation: OperationType,
        status: OperationStatus,
        duration_ms: float,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Record an operation's metrics

        Args:
            user_id: Unique user identifier
            user_profile: User's profile (A, B, C, D)
            operation: Type of operation (login, reservation, etc.)
            status: Success/failed/timeout/error
            duration_ms: Duration in milliseconds
            error_message: Error message if operation failed
            error_type: Type of error (Errno 11, timeout, etc.)
            additional_data: Extra data to store (reservation hour, etc.)
        """
        metric = Metric(
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            user_profile=user_profile,
            operation=operation.value,
            status=status.value,
            duration_ms=duration_ms,
            error_message=error_message,
            error_type=error_type,
            additional_data=additional_data
        )

        with self.lock:
            self.metrics.append(metric)

    def record_timed_operation(
        self,
        user_id: str,
        user_profile: str,
        operation: OperationType,
        status: OperationStatus,
        start_time: float,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Record operation with automatic duration calculation

        Args:
            user_id: User identifier
            user_profile: User's profile
            operation: Operation type
            status: Operation status
            start_time: Start time from time.time()
            error_message: Error message if failed
            error_type: Error type
            additional_data: Extra data
        """
        duration_ms = (time.time() - start_time) * 1000
        self.record_operation(
            user_id=user_id,
            user_profile=user_profile,
            operation=operation,
            status=status,
            duration_ms=duration_ms,
            error_message=error_message,
            error_type=error_type,
            additional_data=additional_data
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics

        Returns:
            Dict with statistics: total ops, success rate, avg time, etc.
        """
        with self.lock:
            if not self.metrics:
                return {}

            total_ops = len(self.metrics)
            successful = sum(1 for m in self.metrics if m.status == OperationStatus.SUCCESS.value)
            failed = sum(1 for m in self.metrics if m.status != OperationStatus.SUCCESS.value)

            durations = [m.duration_ms for m in self.metrics if m.status == OperationStatus.SUCCESS.value]
            avg_duration = sum(durations) / len(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            max_duration = max(durations) if durations else 0

            # Count errors by type
            error_counts = {}
            for m in self.metrics:
                if m.error_type:
                    error_counts[m.error_type] = error_counts.get(m.error_type, 0) + 1

            # Count operations by type
            op_counts = {}
            for m in self.metrics:
                op_counts[m.operation] = op_counts.get(m.operation, 0) + 1

            elapsed_time = (self.end_time or time.time()) - self.start_time

            return {
                "total_operations": total_ops,
                "successful_operations": successful,
                "failed_operations": failed,
                "success_rate_percent": (successful / total_ops * 100) if total_ops > 0 else 0,
                "avg_duration_ms": avg_duration,
                "min_duration_ms": min_duration,
                "max_duration_ms": max_duration,
                "total_duration_seconds": elapsed_time,
                "operations_per_second": total_ops / elapsed_time if elapsed_time > 0 else 0,
                "error_counts": error_counts,
                "operation_counts": op_counts,
            }

    def save_to_csv(self, filename: Optional[str] = None) -> str:
        """Save metrics to CSV file

        Args:
            filename: Output filename (default: metrics.csv)

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = "metrics.csv"

        filepath = self.results_dir / filename

        with self.lock:
            if not self.metrics:
                print(f"No metrics to save")
                return str(filepath)

            # Write CSV header and rows
            with open(filepath, 'w', newline='') as f:
                fieldnames = [
                    'timestamp', 'user_id', 'user_profile', 'operation',
                    'status', 'duration_ms', 'error_message', 'error_type',
                    'additional_data'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for metric in self.metrics:
                    row = metric.to_dict()
                    row['additional_data'] = json.dumps(row['additional_data']) if row['additional_data'] else ""
                    writer.writerow(row)

        print(f"✅ Metrics saved to {filepath}")
        return str(filepath)

    def save_summary(self, filename: Optional[str] = None) -> str:
        """Save summary statistics to JSON

        Args:
            filename: Output filename (default: summary.json)

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = "summary.json"

        filepath = self.results_dir / filename
        summary = self.get_summary()

        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"✅ Summary saved to {filepath}")
        return str(filepath)

    def print_summary(self):
        """Print summary statistics to console"""
        summary = self.get_summary()

        print("\n" + "=" * 80)
        print("LOAD TEST SUMMARY")
        print("=" * 80)
        print(f"Total Operations: {summary.get('total_operations', 0)}")
        print(f"Successful: {summary.get('successful_operations', 0)}")
        print(f"Failed: {summary.get('failed_operations', 0)}")
        print(f"Success Rate: {summary.get('success_rate_percent', 0):.2f}%")
        print(f"\nTiming (successful operations):")
        print(f"  Average: {summary.get('avg_duration_ms', 0):.2f}ms")
        print(f"  Min: {summary.get('min_duration_ms', 0):.2f}ms")
        print(f"  Max: {summary.get('max_duration_ms', 0):.2f}ms")
        print(f"\nTest Duration: {summary.get('total_duration_seconds', 0):.2f}s")
        print(f"Operations/Second: {summary.get('operations_per_second', 0):.2f}")

        if summary.get('error_counts'):
            print(f"\nErrors:")
            for error_type, count in summary['error_counts'].items():
                print(f"  {error_type}: {count}")

        if summary.get('operation_counts'):
            print(f"\nOperations by Type:")
            for op_type, count in summary['operation_counts'].items():
                print(f"  {op_type}: {count}")

        print("=" * 80 + "\n")

    def finalize(self):
        """Mark test as complete"""
        self.end_time = time.time()
