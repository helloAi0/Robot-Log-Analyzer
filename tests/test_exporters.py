import pytest
from datetime import datetime
from src.models.log_entry import LogEntry, LogLevel
from src.exporters.report_exporter import ReportExporter


def test_report_exporter_json(tmp_path):
    """Verifies JSON report creation using pytest's temporary path fixture."""
    exporter = ReportExporter(output_dir=tmp_path)
    sample_data = {"status": "SUCCESS", "fleet_count": 2}
    
    output_file = exporter.export_json(sample_data, "test_report.json")

    assert output_file.exists()
    assert output_file.name == "test_report.json"
    assert output_file.stat().st_size > 0


def test_export_anomalies_csv(tmp_path):
    """Verifies hardware anomalies CSV generation with valid headers and rows."""
    exporter = ReportExporter(output_dir=tmp_path)
    anomalies = {
        "low_battery": [
            LogEntry(
                timestamp=datetime(2026, 7, 31, 12, 0, 0),
                level=LogLevel.WARNING,
                robot_id="AMR-001",
                subsystem="POWER",
                message="Low battery alert",
                battery_level=12.0
            )
        ]
    }

    output_file = exporter.export_anomalies_csv(anomalies, "anomalies_test.csv")

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "anomaly_category" in content
    assert "AMR-001" in content
    assert "low_battery" in content