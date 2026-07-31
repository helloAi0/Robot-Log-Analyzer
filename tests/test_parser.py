import pytest
from datetime import datetime
from src.parser.log_parser import LogParser
from src.models.log_entry import LogLevel


def test_parse_valid_log_line():
    """Validates that a correctly formatted text log line parses into a valid LogEntry object."""
    parser = LogParser()
    line = "2026-07-31 12:00:00 [INFO] [AMR-001] [NAV]: Mission initialized | BAT:95.0% CPU:22.0% MEM:30.0% TEMP:35.0C"
    
    entry = parser.parse_line(line)

    assert entry is not None
    assert entry.timestamp == datetime(2026, 7, 31, 12, 0, 0)
    assert entry.level == LogLevel.INFO
    assert entry.robot_id == "AMR-001"
    assert entry.subsystem == "NAV"
    assert "Mission initialized" in entry.message
    assert entry.battery_level == 95.0
    assert entry.cpu_usage == 22.0
    assert entry.memory_usage == 30.0
    assert entry.temperature == 35.0


def test_parse_corrupt_log_line():
    """Ensures that invalid or malformed log lines return None instead of throwing an unhandled exception."""
    parser = LogParser()
    corrupt_line = "INVALID_LOG_LINE_WITHOUT_TIMESTAMP_OR_BRACKETS"

    entry = parser.parse_line(corrupt_line)
    assert entry is None


def test_parse_partial_telemetry():
    """Validates parsing when optional telemetry key-value pairs are missing."""
    parser = LogParser()
    line = "2026-07-31 12:05:00 [ERROR] [AMR-002] [DRIVE]: Motor stall detected | TEMP:72.5C"

    entry = parser.parse_line(line)

    assert entry is not None
    assert entry.level == LogLevel.ERROR
    assert entry.battery_level is None
    assert entry.cpu_usage is None
    assert entry.temperature == 72.5