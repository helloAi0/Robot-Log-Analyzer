from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from src.models.log_entry import LogEntry, LogLevel


@dataclass(frozen=True)
class ErrorSummary:
    """Aggregated error statistics and subsystem health summary."""
    total_logs: int
    error_count: int
    critical_count: int
    level_distribution: Dict[str, int]
    subsystem_distribution: Dict[str, int]
    top_error_messages: List[Tuple[str, int]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts ErrorSummary into a serializable dictionary."""
        return {
            "total_logs": self.total_logs,
            "error_count": self.error_count,
            "critical_count": self.critical_count,
            "level_distribution": self.level_distribution,
            "subsystem_distribution": self.subsystem_distribution,
            "top_error_messages": [
                {"message": msg, "count": count} for msg, count in self.top_error_messages
            ]
        }


class ErrorAnalyzer:
    """Statistical error analysis and subsystem risk profiling engine."""

    def analyze(self, entries: List[LogEntry], top_n_errors: int = 5) -> ErrorSummary:
        """Computes severity distributions, subsystem error counts, and top recurring errors."""
        if not entries:
            return ErrorSummary(
                total_logs=0,
                error_count=0,
                critical_count=0,
                level_distribution={},
                subsystem_distribution={},
                top_error_messages=[]
            )

        level_counts: Counter = Counter()
        subsystem_counts: Counter = Counter()
        error_message_counter: Counter = Counter()

        error_count = 0
        critical_count = 0

        for entry in entries:
            # Count by log level
            level_name = entry.level.name if isinstance(entry.level, LogLevel) else str(entry.level)
            level_counts[level_name] += 1

            # Count errors per subsystem
            subsystem_counts[entry.subsystem] += 1

            # Track ERROR and CRITICAL specifics
            if entry.level in (LogLevel.ERROR, LogLevel.CRITICAL):
                if entry.level == LogLevel.ERROR:
                    error_count += 1
                else:
                    critical_count += 1

                error_message_counter[entry.message] += 1

        return ErrorSummary(
            total_logs=len(entries),
            error_count=error_count,
            critical_count=critical_count,
            level_distribution=dict(level_counts),
            subsystem_distribution=dict(subsystem_counts),
            top_error_messages=error_message_counter.most_common(top_n_errors)
        )

    def calculate_subsystem_health_scores(self, entries: List[LogEntry]) -> Dict[str, float]:
        """Calculates error-rate percentage per subsystem. Lower percentage = healthier subsystem."""
        if not entries:
            return {}

        total_per_subsystem = Counter()
        errors_per_subsystem = Counter()

        for entry in entries:
            subsystem = entry.subsystem
            total_per_subsystem[subsystem] += 1

            if entry.level in (LogLevel.ERROR, LogLevel.CRITICAL):
                errors_per_subsystem[subsystem] += 1

        health_scores = {}
        for sub, total in total_per_subsystem.items():
            errs = errors_per_subsystem[sub]
            error_rate = (errs / total) * 100.0
            health_scores[sub] = round(error_rate, 2)

        return health_scores


if __name__ == "__main__":
    from datetime import datetime

    sample_logs = [
        LogEntry(datetime.now(), LogLevel.INFO, "AMR-001", "DRIVE", "Motor power nominal"),
        LogEntry(datetime.now(), LogLevel.WARNING, "AMR-001", "DRIVE", "Motor thermal rising"),
        LogEntry(datetime.now(), LogLevel.ERROR, "AMR-001", "DRIVE", "Wheel slip detected"),
        LogEntry(datetime.now(), LogLevel.ERROR, "AMR-001", "DRIVE", "Wheel slip detected"),
        LogEntry(datetime.now(), LogLevel.CRITICAL, "AMR-002", "POWER", "LiDAR sensor voltage loss"),
        LogEntry(datetime.now(), LogLevel.ERROR, "AMR-002", "NAV", "Costmap expansion failed"),
        LogEntry(datetime.now(), LogLevel.INFO, "AMR-002", "NAV", "Path replanned"),
    ]

    analyzer = ErrorAnalyzer()
    summary = analyzer.analyze(sample_logs)
    health_scores = analyzer.calculate_subsystem_health_scores(sample_logs)

    print("--- ERROR ANALYSIS SUMMARY ---")
    print(f"Total Logs Analyzed: {summary.total_logs}")
    print(f"Error Count: {summary.error_count} | Critical Count: {summary.critical_count}")
    print("\nLog Level Distribution:", summary.level_distribution)
    print("Subsystem Distribution:", summary.subsystem_distribution)
    
    print("\nTop Error Messages:")
    for msg, count in summary.top_error_messages:
        print(f"  - [{count}x] {msg}")

    print("\nSubsystem Failure Rates (% Error/Critical):")
    for sub, err_rate in health_scores.items():
        print(f"  - {sub}: {err_rate}% error rate")