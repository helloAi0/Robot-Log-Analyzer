import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Union
from src.models.log_entry import LogEntry
from src.analysis.uptime_analyzer import DowntimeEvent, UptimeReport


class ReportExporter:
    """Export engine for serializing fleet analysis into structured JSON and CSV files."""

    def __init__(self, output_dir: Union[str, Path] = "reports"):
        self.output_dir = Path(output_dir)
        self._ensure_output_directory()

    def _ensure_output_directory(self) -> None:
        """Creates the output directory path if it does not already exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_json(self, data: Dict[str, Any], filename: str) -> Path:
        """Exports a dictionary structure into a formatted JSON report file."""
        filepath = self.output_dir / filename
        with open(filepath, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, default=str)
        return filepath

    def export_anomalies_csv(self, anomalies: Dict[str, List[LogEntry]], filename: str = "hardware_anomalies.csv") -> Path:
        """Flattens and exports detected hardware anomalies across all categories into a CSV table."""
        filepath = self.output_dir / filename
        fieldnames = [
            "anomaly_category",
            "timestamp",
            "robot_id",
            "level",
            "subsystem",
            "message",
            "battery_level",
            "cpu_usage",
            "memory_usage",
            "temperature"
        ]

        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for category, entries in anomalies.items():
                for entry in entries:
                    writer.writerow({
                        "anomaly_category": category,
                        "timestamp": entry.timestamp.isoformat(),
                        "robot_id": entry.robot_id,
                        "level": entry.level.name if hasattr(entry.level, "name") else str(entry.level),
                        "subsystem": entry.subsystem,
                        "message": entry.message,
                        "battery_level": entry.battery_level,
                        "cpu_usage": entry.cpu_usage,
                        "memory_usage": entry.memory_usage,
                        "temperature": entry.temperature
                    })

        return filepath

    def export_downtime_events_csv(self, reports: Dict[str, UptimeReport], filename: str = "downtime_events.csv") -> Path:
        """Extracts and writes all fleet downtime events into a CSV ledger."""
        filepath = self.output_dir / filename
        fieldnames = ["robot_id", "start_time", "end_time", "duration_seconds", "reason"]

        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for robot_id, report in reports.items():
                for event in report.downtime_events:
                    writer.writerow({
                        "robot_id": event.robot_id,
                        "start_time": event.start_time.isoformat(),
                        "end_time": event.end_time.isoformat(),
                        "duration_seconds": round(event.duration_seconds, 2),
                        "reason": event.reason
                    })

        return filepath


if __name__ == "__main__":
    from datetime import datetime, timedelta
    from src.models.log_entry import LogLevel

    base_time = datetime(2026, 7, 31, 12, 0, 0)

    # 1. Sample Telemetry Anomalies
    sample_anomaly_logs = {
        "overheating": [
            LogEntry(
                timestamp=base_time, level=LogLevel.CRITICAL, robot_id="AMR-001",
                subsystem="DRIVE", message="Motor overtemp limit", temperature=72.5, battery_level=45.0
            )
        ],
        "low_battery": [
            LogEntry(
                timestamp=base_time + timedelta(minutes=5), level=LogLevel.WARNING, robot_id="AMR-002",
                subsystem="POWER", message="Battery critically low", battery_level=12.0
            )
        ]
    }

    # 2. Sample Uptime Reports
    sample_downtime = DowntimeEvent(
        robot_id="AMR-001",
        start_time=base_time,
        end_time=base_time + timedelta(minutes=10),
        duration_seconds=600.0,
        reason="Heartbeat lost for > 300s"
    )
    sample_uptime_reports = {
        "AMR-001": UptimeReport(
            robot_id="AMR-001",
            total_active_seconds=3600.0,
            total_downtime_seconds=600.0,
            uptime_percentage=85.71,
            downtime_events=[sample_downtime]
        )
    }

    exporter = ReportExporter(output_dir="reports_test")

    # Perform Test Exports
    json_path = exporter.export_json(
        data={"status": "SUCCESS", "fleet_summary": {"total_robots": 2, "avg_uptime": 85.71}},
        filename="fleet_summary.json"
    )
    anomalies_csv_path = exporter.export_anomalies_csv(sample_anomaly_logs)
    downtime_csv_path = exporter.export_downtime_events_csv(sample_uptime_reports)

    print("--- REPORT EXPORTER TEST COMPLETE ---")
    print(f"Exported JSON: {json_path}")
    print(f"Exported Anomalies CSV: {anomalies_csv_path}")
    print(f"Exported Downtime CSV: {downtime_csv_path}")