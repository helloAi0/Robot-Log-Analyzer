from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class LogLevel(Enum):
    """Enumeration representing valid robot logging severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class LogEntry:
    """Strongly-typed data model representing a single robot log entry."""
    timestamp: datetime
    level: LogLevel
    robot_id: str
    subsystem: str
    message: str
    battery_level: Optional[float] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    temperature: Optional[float] = None
    raw_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the LogEntry instance into a JSON-serializable dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["level"] = self.level.value
        return data


if __name__ == "__main__":
    sample_entry = LogEntry(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        robot_id="AMR-001",
        subsystem="NAV_MOTOR",
        message="Navigating to waypoint B2",
        battery_level=88.5,
        cpu_usage=14.2,
        memory_usage=42.0,
        temperature=36.5,
        raw_text="2026-07-30 18:55:00 [INFO] [AMR-001] [NAV_MOTOR]: Navigating to waypoint B2"
    )

    print("Successfully instantiated sample LogEntry:")
    print(sample_entry)
    print("\nSerialized Dictionary Output:")
    print(sample_entry.to_dict())