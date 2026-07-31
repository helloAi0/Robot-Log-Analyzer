import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union
from src.models.log_entry import LogEntry, LogLevel
from src.parser.log_parser import LogParser


class FileReader:
    """Universal File Ingestion Engine for Text, CSV, and JSON Robot Logs."""

    def __init__(self, parser: Optional[LogParser] = None):
        self.parser = parser or LogParser()

    def read_file(self, file_path: Union[str, Path]) -> List[LogEntry]:
        """Dispatches file reading based on file extension."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Log file not found: '{path.resolve()}'")

        extension = path.suffix.lower()

        if extension in [".log", ".txt"]:
            return self.read_text_file(path)
        elif extension == ".csv":
            return self.read_csv_file(path)
        elif extension == ".json":
            return self.read_json_file(path)
        else:
            raise ValueError(
                f"Unsupported file extension '{extension}'. "
                f"Supported formats are: .log, .txt, .csv, .json"
            )

    def read_text_file(self, path: Path) -> List[LogEntry]:
        """Reads plain text log files and parses lines using LogParser."""
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        return self.parser.parse_text(content)

    def read_csv_file(self, path: Path) -> List[LogEntry]:
        """Reads CSV files containing tabular robot log data."""
        entries: List[LogEntry] = []
        with open(path, "r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                entry = self._csv_row_to_entry(row)
                if entry:
                    entries.append(entry)
        return entries

    def read_json_file(self, path: Path) -> List[LogEntry]:
        """Reads JSON files containing structured log arrays."""
        entries: List[LogEntry] = []
        with open(path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Corrupt or invalid JSON file '{path}': {e}")

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    entry = self._dict_to_entry(item)
                    if entry:
                        entries.append(entry)
        return entries

    def _csv_row_to_entry(self, row: dict) -> Optional[LogEntry]:
        """Converts a dictionary row from CSV into a LogEntry object."""
        try:
            timestamp = datetime.fromisoformat(row["timestamp"])
            level = LogLevel[row["level"].upper()]
            return LogEntry(
                timestamp=timestamp,
                level=level,
                robot_id=row.get("robot_id", "UNKNOWN"),
                subsystem=row.get("subsystem", "UNKNOWN"),
                message=row.get("message", ""),
                battery_level=float(row["battery_level"]) if row.get("battery_level") else None,
                cpu_usage=float(row["cpu_usage"]) if row.get("cpu_usage") else None,
                memory_usage=float(row["memory_usage"]) if row.get("memory_usage") else None,
                temperature=float(row["temperature"]) if row.get("temperature") else None,
                raw_text=str(row)
            )
        except (KeyError, ValueError):
            return None

    def _dict_to_entry(self, item: dict) -> Optional[LogEntry]:
        """Converts a JSON record dictionary into a LogEntry object."""
        try:
            timestamp = datetime.fromisoformat(item["timestamp"])
            level = LogLevel[item["level"].upper()]
            return LogEntry(
                timestamp=timestamp,
                level=level,
                robot_id=item.get("robot_id", "UNKNOWN"),
                subsystem=item.get("subsystem", "UNKNOWN"),
                message=item.get("message", ""),
                battery_level=float(item["battery_level"]) if item.get("battery_level") is not None else None,
                cpu_usage=float(item["cpu_usage"]) if item.get("cpu_usage") is not None else None,
                memory_usage=float(item["memory_usage"]) if item.get("memory_usage") is not None else None,
                temperature=float(item["temperature"]) if item.get("temperature") is not None else None,
                raw_text=json.dumps(item)
            )
        except (KeyError, ValueError):
            return None


if __name__ == "__main__":
    import tempfile

    reader = FileReader()

    sample_json_data = [
        {
            "timestamp": "2026-07-31T11:00:00",
            "level": "INFO",
            "robot_id": "AMR-003",
            "subsystem": "BATTERY",
            "message": "Charging initiated",
            "battery_level": 15.0,
            "cpu_usage": 5.2,
            "memory_usage": 22.1,
            "temperature": 29.8
        },
        {
            "timestamp": "2026-07-31T11:05:00",
            "level": "CRITICAL",
            "robot_id": "AMR-003",
            "subsystem": "BATTERY",
            "message": "Overheating during rapid charge",
            "battery_level": 32.0,
            "cpu_usage": 8.0,
            "memory_usage": 23.0,
            "temperature": 72.5
        }
    ]

    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as temp_file:
        json.dump(sample_json_data, temp_file)
        temp_path = temp_file.name

    print(f"Created temporary JSON log at: {temp_path}")
    parsed_entries = reader.read_file(temp_path)

    print(f"Successfully loaded {len(parsed_entries)} entries from JSON:")
    for entry in parsed_entries:
        print(f"[{entry.level.value}] {entry.timestamp} | Robot: {entry.robot_id} -> {entry.message} (Temp: {entry.temperature}°C)")

    Path(temp_path).unlink()