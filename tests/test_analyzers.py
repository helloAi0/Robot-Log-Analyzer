import pytest
from datetime import datetime, timedelta
from src.models.log_entry import LogEntry, LogLevel
from src.analysis.telemetry_analyzer import TelemetryAnalyzer
from src.analysis.uptime_analyzer import UptimeAnalyzer
from src.analysis.error_analyzer import ErrorAnalyzer


@pytest.fixture
def sample_entries():
    """Fixture providing standard sample LogEntry objects for analyzer testing."""
    base = datetime(2026, 7, 31, 12, 0, 0)
    return [
        LogEntry(
            timestamp=base, level=LogLevel.INFO, robot_id="AMR-001",
            subsystem="NAV", message="OK", battery_level=90.0,
            cpu_usage=20.0, memory_usage=30.0, temperature=35.0
        ),
        LogEntry(
            timestamp=base + timedelta(minutes=2), level=LogLevel.WARNING, robot_id="AMR-001",
            subsystem="DRIVE", message="High load", battery_level=15.0,
            cpu_usage=85.0, memory_usage=50.0, temperature=68.0
        ),
        LogEntry(
            timestamp=base + timedelta(minutes=10), level=LogLevel.CRITICAL, robot_id="AMR-001",
            subsystem="POWER", message="Overheat", battery_level=10.0,
            cpu_usage=95.0, memory_usage=80.0, temperature=75.0
        ),
    ]


def test_telemetry_anomaly_detection(sample_entries):
    """Tests that low battery and high temperature anomalies are flagged accurately."""
    analyzer = TelemetryAnalyzer(low_battery_threshold=20.0, high_temp_threshold=65.0)
    anomalies = analyzer.detect_anomalies(sample_entries)

    assert len(anomalies["low_battery"]) == 2
    assert len(anomalies["overheating"]) == 2


def test_uptime_gap_detection(sample_entries):
    """Verifies that time gaps exceeding threshold are flagged as downtime events."""
    # Gap between index 1 (12:02) and index 2 (12:10) is 8 minutes (480 seconds)
    analyzer = UptimeAnalyzer(gap_threshold_seconds=300.0)
    reports = analyzer.analyze_fleet(sample_entries)

    assert "AMR-001" in reports
    report = reports["AMR-001"]
    assert len(report.downtime_events) == 1
    assert report.downtime_events[0].duration_seconds == 480.0


def test_error_analyzer_distribution(sample_entries):
    """Validates log level counts and subsystem distribution metrics."""
    analyzer = ErrorAnalyzer()
    summary = analyzer.analyze(sample_entries)

    assert summary.total_logs == 3
    assert summary.error_count == 0
    assert summary.critical_count == 1
    assert summary.subsystem_distribution["DRIVE"] == 1