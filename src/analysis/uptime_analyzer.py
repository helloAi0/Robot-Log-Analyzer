from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.models.log_entry import LogEntry


@dataclass(frozen=True)
class DowntimeEvent:
    """Represents a specific interval where a robot went offline or stopped logging."""
    robot_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        """Converts DowntimeEvent to a serializable dictionary."""
        return {
            "robot_id": self.robot_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": round(self.duration_seconds, 2),
            "reason": self.reason
        }


@dataclass(frozen=True)
class UptimeReport:
    """Aggregated uptime metrics for a robot or entire fleet."""
    robot_id: str
    total_active_seconds: float
    total_downtime_seconds: float
    uptime_percentage: float
    downtime_events: List[DowntimeEvent]

    def to_dict(self) -> Dict[str, Any]:
        """Converts UptimeReport to a serializable dictionary."""
        return {
            "robot_id": self.robot_id,
            "total_active_seconds": round(self.total_active_seconds, 2),
            "total_downtime_seconds": round(self.total_downtime_seconds, 2),
            "uptime_percentage": round(self.uptime_percentage, 2),
            "downtime_count": len(self.downtime_events),
            "downtime_events": [e.to_dict() for e in self.downtime_events]
        }


class UptimeAnalyzer:
    """Time-series engine for calculating robot availability and heartbeat gap detection."""

    DEFAULT_HEARTBEAT_GAP_THRESHOLD: float = 300.0  # 5 minutes in seconds

    def __init__(self, gap_threshold_seconds: float = DEFAULT_HEARTBEAT_GAP_THRESHOLD):
        self.gap_threshold_seconds = gap_threshold_seconds

    def analyze_robot(self, robot_id: str, entries: List[LogEntry]) -> Optional[UptimeReport]:
        """Calculates operational uptime and detects downtime events for a single robot."""
        robot_logs = [e for e in entries if e.robot_id == robot_id]
        if not robot_logs:
            return None

        sorted_logs = sorted(robot_logs, key=lambda e: e.timestamp)

        if len(sorted_logs) == 1:
            return UptimeReport(
                robot_id=robot_id,
                total_active_seconds=0.0,
                total_downtime_seconds=0.0,
                uptime_percentage=100.0,
                downtime_events=[]
            )

        downtime_events: List[DowntimeEvent] = []
        total_downtime_sec = 0.0

        for i in range(len(sorted_logs) - 1):
            current_log = sorted_logs[i]
            next_log = sorted_logs[i + 1]

            delta_sec = (next_log.timestamp - current_log.timestamp).total_seconds()

            if delta_sec > self.gap_threshold_seconds:
                total_downtime_sec += delta_sec
                downtime_events.append(
                    DowntimeEvent(
                        robot_id=robot_id,
                        start_time=current_log.timestamp,
                        end_time=next_log.timestamp,
                        duration_seconds=delta_sec,
                        reason=f"Heartbeat lost for > {self.gap_threshold_seconds}s"
                    )
                )

        start_time = sorted_logs[0].timestamp
        end_time = sorted_logs[-1].timestamp
        total_timespan_sec = (end_time - start_time).total_seconds()

        if total_timespan_sec <= 0:
            uptime_pct = 100.0
            total_active_sec = 0.0
        else:
            total_active_sec = max(0.0, total_timespan_sec - total_downtime_sec)
            uptime_pct = (total_active_sec / total_timespan_sec) * 100.0

        return UptimeReport(
            robot_id=robot_id,
            total_active_seconds=total_active_sec,
            total_downtime_seconds=total_downtime_sec,
            uptime_percentage=uptime_pct,
            downtime_events=downtime_events
        )

    def analyze_fleet(self, entries: List[LogEntry]) -> Dict[str, UptimeReport]:
        """Calculates uptime reports for every robot present in the log dataset."""
        unique_robots = {e.robot_id for e in entries}
        reports: Dict[str, UptimeReport] = {}

        for r_id in unique_robots:
            report = self.analyze_robot(r_id, entries)
            if report:
                reports[r_id] = report

        return reports


if __name__ == "__main__":
    from src.models.log_entry import LogLevel

    base_time = datetime(2026, 7, 31, 12, 0, 0)

    sample_logs = [
        LogEntry(timestamp=base_time, level=LogLevel.INFO, robot_id="AMR-001", subsystem="NAV", message="Started mission"),
        LogEntry(timestamp=base_time + timedelta(minutes=2), level=LogLevel.INFO, robot_id="AMR-001", subsystem="NAV", message="En route"),
        LogEntry(timestamp=base_time + timedelta(minutes=12), level=LogLevel.INFO, robot_id="AMR-001", subsystem="NAV", message="Reconnected"),
        LogEntry(timestamp=base_time + timedelta(minutes=15), level=LogLevel.INFO, robot_id="AMR-001", subsystem="NAV", message="Mission complete"),
    ]

    analyzer = UptimeAnalyzer(gap_threshold_seconds=180.0)
    fleet_reports = analyzer.analyze_fleet(sample_logs)

    print("--- FLEET UPTIME & DOWNTIME REPORT ---")
    for robot_id, report in fleet_reports.items():
        print(f"\nRobot ID: {robot_id}")
        print(f"Uptime: {report.uptime_percentage:.2f}%")
        print(f"Active Time: {report.total_active_seconds} seconds")
        print(f"Downtime: {report.total_downtime_seconds} seconds")
        print(f"Detected Downtime Events: {len(report.downtime_events)}")
        for event in report.downtime_events:
            print(f"  -> Gap: {event.start_time.time()} to {event.end_time.time()} ({event.duration_seconds}s)")