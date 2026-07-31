import re
from datetime import datetime
from typing import Optional, List
from src.models.log_entry import LogEntry, LogLevel


class LogParser:
    """High-performance Regular Expression log parser for robot telemetry logs."""

    LOG_PATTERN = re.compile(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+"
        r"\[(?P<level>[A-Z]+)\]\s+"
        r"\[(?P<robot_id>[^\]]+)\]\s+"
        r"\[(?P<subsystem>[^\]]+)\]:\s+"
        r"(?P<message>.*)$"
    )

    BATTERY_PATTERN = re.compile(r"BAT:(?P<battery>\d+(?:\.\d+)?)%")
    CPU_PATTERN = re.compile(r"CPU:(?P<cpu>\d+(?:\.\d+)?)%")
    MEMORY_PATTERN = re.compile(r"MEM:(?P<memory>\d+(?:\.\d+)?)%")
    TEMP_PATTERN = re.compile(r"TEMP:(?P<temp>\d+(?:\.\d+)?)C")

    TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

    def parse_line(self, raw_line: str) -> Optional[LogEntry]:
        """Parses a single raw string line into a strongly-typed LogEntry instance."""
        line = raw_line.strip()
        if not line:
            return None

        match = self.LOG_PATTERN.match(line)
        if not match:
            return None

        data = match.groupdict()

        try:
            timestamp = datetime.strptime(data["timestamp"], self.TIMESTAMP_FORMAT)
            level = LogLevel[data["level"].upper()]
        except (ValueError, KeyError):
            return None

        message = data["message"]

        battery_level = self._extract_metric(self.BATTERY_PATTERN, message)
        cpu_usage = self._extract_metric(self.CPU_PATTERN, message)
        memory_usage = self._extract_metric(self.MEMORY_PATTERN, message)
        temperature = self._extract_metric(self.TEMP_PATTERN, message)

        return LogEntry(
            timestamp=timestamp,
            level=level,
            robot_id=data["robot_id"],
            subsystem=data["subsystem"],
            message=message,
            battery_level=battery_level,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            temperature=temperature,
            raw_text=line
        )

    def _extract_metric(self, pattern: re.Pattern, text: str) -> Optional[float]:
        """Helper method to extract floating-point telemetry values using regex."""
        match = pattern.search(text)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, IndexError):
                return None
        return None

    def parse_text(self, text_content: str) -> List[LogEntry]:
        """Parses a multi-line text block into a list of valid LogEntry instances."""
        entries: List[LogEntry] = []
        for line in text_content.splitlines():
            entry = self.parse_line(line)
            if entry:
                entries.append(entry)
        return entries


if __name__ == "__main__":
    sample_logs = """
    2026-07-31 10:15:30 [INFO] [AMR-001] [NAV]: Waypoint A reached | BAT:95.5% CPU:12.4% MEM:38.1% TEMP:34.2C
    2026-07-31 10:15:35 [WARNING] [AMR-001] [LIDAR]: Obstacle detected at 0.5m | BAT:95.0% CPU:45.8% MEM:40.2% TEMP:38.0C
    2026-07-31 10:15:40 [ERROR] [AMR-002] [ARM]: Servo motor overcurrent error | TEMP:65.4C
    INVALID LOG LINE THAT SHOULD BE SKIPPED SAFELY
    """

    parser = LogParser()
    parsed_entries = parser.parse_text(sample_logs)

    print(f"Successfully parsed {len(parsed_entries)} log entries:\n")
    for entry in parsed_entries:
        print(f"[{entry.level.value}] Robot: {entry.robot_id} | Subsystem: {entry.subsystem}")
        print(f"  Message: {entry.message}")
        print(f"  Telemetry -> Battery: {entry.battery_level}%, CPU: {entry.cpu_usage}%, Temp: {entry.temperature}°C\n")