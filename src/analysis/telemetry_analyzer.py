from dataclasses import dataclass
from statistics import mean
from typing import List, Dict, Any, Optional
from src.models.log_entry import LogEntry


@dataclass(frozen=True)
class MetricSummary:
    """Statistical summary for a specific numeric telemetry metric."""
    min_val: float
    max_val: float
    avg_val: float
    sample_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Converts summary data into a clean dictionary."""
        return {
            "min": round(self.min_val, 2),
            "max": round(self.max_val, 2),
            "avg": round(self.avg_val, 2),
            "sample_count": self.sample_count
        }


class TelemetryAnalyzer:
    """Telemetry Health & Anomaly Detection Engine for Autonomous Robots."""

    DEFAULT_LOW_BATTERY_THRESHOLD: float = 20.0  # Percentage (%)
    DEFAULT_HIGH_CPU_THRESHOLD: float = 85.0     # Percentage (%)
    DEFAULT_HIGH_MEM_THRESHOLD: float = 90.0     # Percentage (%)
    DEFAULT_HIGH_TEMP_THRESHOLD: float = 65.0    # Celsius (°C)

    def __init__(
        self,
        low_battery_threshold: float = DEFAULT_LOW_BATTERY_THRESHOLD,
        high_cpu_threshold: float = DEFAULT_HIGH_CPU_THRESHOLD,
        high_mem_threshold: float = DEFAULT_HIGH_MEM_THRESHOLD,
        high_temp_threshold: float = DEFAULT_HIGH_TEMP_THRESHOLD
    ):
        self.low_battery_threshold = low_battery_threshold
        self.high_cpu_threshold = high_cpu_threshold
        self.high_mem_threshold = high_mem_threshold
        self.high_temp_threshold = high_temp_threshold

    def compute_summary(self, entries: List[LogEntry]) -> Dict[str, Any]:
        """Generates statistical metrics for all hardware telemetry indicators."""
        battery_vals = [e.battery_level for e in entries if e.battery_level is not None]
        cpu_vals = [e.cpu_usage for e in entries if e.cpu_usage is not None]
        mem_vals = [e.memory_usage for e in entries if e.memory_usage is not None]
        temp_vals = [e.temperature for e in entries if e.temperature is not None]

        return {
            "battery": self._calculate_metric_summary(battery_vals),
            "cpu": self._calculate_metric_summary(cpu_vals),
            "memory": self._calculate_metric_summary(mem_vals),
            "temperature": self._calculate_metric_summary(temp_vals),
        }

    def detect_anomalies(self, entries: List[LogEntry]) -> Dict[str, List[LogEntry]]:
        """Filters log entries that breach safety thresholds."""
        low_battery = [
            e for e in entries if e.battery_level is not None and e.battery_level < self.low_battery_threshold
        ]
        high_cpu = [
            e for e in entries if e.cpu_usage is not None and e.cpu_usage > self.high_cpu_threshold
        ]
        high_mem = [
            e for e in entries if e.memory_usage is not None and e.memory_usage > self.high_mem_threshold
        ]
        overheating = [
            e for e in entries if e.temperature is not None and e.temperature > self.high_temp_threshold
        ]

        return {
            "low_battery": low_battery,
            "high_cpu": high_cpu,
            "high_memory": high_mem,
            "overheating": overheating
        }

    def _calculate_metric_summary(self, values: List[float]) -> Optional[MetricSummary]:
        """Calculates min, max, and average for a list of floats."""
        if not values:
            return None
        return MetricSummary(
            min_val=min(values),
            max_val=max(values),
            avg_val=mean(values),
            sample_count=len(values)
        )


if __name__ == "__main__":
    from datetime import datetime
    from src.models.log_entry import LogLevel

    sample_entries = [
        LogEntry(
            timestamp=datetime.now(), level=LogLevel.INFO, robot_id="AMR-001",
            subsystem="DRIVE", message="Moving", battery_level=90.0, cpu_usage=25.0,
            memory_usage=40.0, temperature=35.0
        ),
        LogEntry(
            timestamp=datetime.now(), level=LogLevel.WARNING, robot_id="AMR-001",
            subsystem="DRIVE", message="High load hill climb", battery_level=18.5, cpu_usage=88.0,
            memory_usage=55.0, temperature=68.2
        ),
        LogEntry(
            timestamp=datetime.now(), level=LogLevel.CRITICAL, robot_id="AMR-002",
            subsystem="ARM", message="Motor thermal limit hit", battery_level=50.0, cpu_usage=92.5,
            memory_usage=94.1, temperature=78.0
        ),
    ]

    analyzer = TelemetryAnalyzer()
    stats = analyzer.compute_summary(sample_entries)
    anomalies = analyzer.detect_anomalies(sample_entries)

    print("--- TELEMETRY STATISTICAL SUMMARY ---")
    for metric_name, summary in stats.items():
        if summary:
            print(f"{metric_name.upper()}: {summary.to_dict()}")
        else:
            print(f"{metric_name.upper()}: No data available")

    print("\n--- DETECTED HARDWARE ANOMALIES ---")
    print(f"Low Battery Logs (<20%): {len(anomalies['low_battery'])}")
    print(f"CPU Spike Logs (>85%): {len(anomalies['high_cpu'])}")
    print(f"Memory Pressure Logs (>90%): {len(anomalies['high_memory'])}")
    print(f"Overheating Logs (>65°C): {len(anomalies['overheating'])}")