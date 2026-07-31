import matplotlib
matplotlib.use("Agg")  # Non-GUI backend for headless server/script rendering
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Union
from src.models.log_entry import LogEntry
from src.analysis.uptime_analyzer import UptimeReport


class ChartGenerator:
    """Visualization engine for generating graphical charts from robot log analytics."""

    def __init__(self, output_dir: Union[str, Path] = "reports/charts"):
        self.output_dir = Path(output_dir)
        self._ensure_output_directory()

    def _ensure_output_directory(self) -> None:
        """Creates the output chart directory if it does not exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_telemetry_trends(
        self, entries: List[LogEntry], filename: str = "telemetry_trends.png"
    ) -> Path:
        """Generates a 4-panel time-series line chart tracking CPU, Memory, Battery, and Temperature."""
        sorted_entries = sorted(entries, key=lambda e: e.timestamp)
        timestamps = [e.timestamp for e in sorted_entries]
        cpu_vals = [e.cpu_usage if e.cpu_usage is not None else float("nan") for e in sorted_entries]
        mem_vals = [e.memory_usage if e.memory_usage is not None else float("nan") for e in sorted_entries]
        bat_vals = [e.battery_level if e.battery_level is not None else float("nan") for e in sorted_entries]
        temp_vals = [e.temperature if e.temperature is not None else float("nan") for e in sorted_entries]

        fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
        fig.suptitle("Fleet Telemetry Trends Over Time", fontsize=14, fontweight="bold")

        # 1. CPU Subplot
        axes[0, 0].plot(timestamps, cpu_vals, color="tab:red", marker="o", linewidth=1.5)
        axes[0, 0].set_title("CPU Usage (%)")
        axes[0, 0].set_ylabel("%")
        axes[0, 0].grid(True, linestyle="--", alpha=0.6)

        # 2. Memory Subplot
        axes[0, 1].plot(timestamps, mem_vals, color="tab:purple", marker="o", linewidth=1.5)
        axes[0, 1].set_title("Memory Usage (%)")
        axes[0, 1].set_ylabel("%")
        axes[0, 1].grid(True, linestyle="--", alpha=0.6)

        # 3. Battery Subplot
        axes[1, 0].plot(timestamps, bat_vals, color="tab:green", marker="o", linewidth=1.5)
        axes[1, 0].set_title("Battery Level (%)")
        axes[1, 0].set_ylabel("%")
        axes[1, 0].grid(True, linestyle="--", alpha=0.6)

        # 4. Temperature Subplot
        axes[1, 1].plot(timestamps, temp_vals, color="tab:orange", marker="o", linewidth=1.5)
        axes[1, 1].set_title("Temperature (°C)")
        axes[1, 1].set_ylabel("°C")
        axes[1, 1].grid(True, linestyle="--", alpha=0.6)

        fig.autofmt_xdate()
        plt.tight_layout()

        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        return filepath

    def plot_subsystem_errors(
        self, subsystem_counts: Dict[str, int], filename: str = "subsystem_errors.png"
    ) -> Path:
        """Generates a bar chart visualizing error counts per subsystem."""
        subsystems = list(subsystem_counts.keys())
        counts = list(subsystem_counts.values())

        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(subsystems, counts, color="tab:blue", edgecolor="black")

        ax.set_title("Log Frequency by Subsystem", fontsize=14, fontweight="bold")
        ax.set_xlabel("Subsystem")
        ax.set_ylabel("Log Count")
        ax.grid(axis="y", linestyle="--", alpha=0.6)

        for bar in bars:
            yval = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                yval + 0.1,
                str(int(yval)),
                ha="center",
                va="bottom",
                fontweight="bold"
            )

        plt.tight_layout()

        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        return filepath

    def plot_uptime_summary(
        self, uptime_reports: Dict[str, UptimeReport], filename: str = "uptime_summary.png"
    ) -> Path:
        """Generates a bar chart comparing operational uptime percentage per robot."""
        robot_ids = list(uptime_reports.keys())
        percentages = [report.uptime_percentage for report in uptime_reports.values()]

        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(robot_ids, percentages, color="tab:green", edgecolor="black")

        ax.set_title("Robot Operational Uptime (%)", fontsize=14, fontweight="bold")
        ax.set_xlabel("Robot ID")
        ax.set_ylabel("Uptime (%)")
        ax.set_ylim(0, 105)
        ax.grid(axis="y", linestyle="--", alpha=0.6)

        for bar in bars:
            yval = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                yval + 1.0,
                f"{yval:.1f}%",
                ha="center",
                va="bottom",
                fontweight="bold"
            )

        plt.tight_layout()

        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=300)
        plt.close(fig)
        return filepath


if __name__ == "__main__":
    from datetime import datetime, timedelta
    from src.models.log_entry import LogLevel

    base_time = datetime(2026, 7, 31, 12, 0, 0)

    sample_logs = [
        LogEntry(
            timestamp=base_time, level=LogLevel.INFO, robot_id="AMR-001",
            subsystem="DRIVE", message="Nominal speed", battery_level=95.0,
            cpu_usage=20.0, memory_usage=35.0, temperature=32.0
        ),
        LogEntry(
            timestamp=base_time + timedelta(minutes=5), level=LogLevel.WARNING, robot_id="AMR-001",
            subsystem="DRIVE", message="High motor load", battery_level=80.0,
            cpu_usage=75.0, memory_usage=50.0, temperature=55.0
        ),
        LogEntry(
            timestamp=base_time + timedelta(minutes=10), level=LogLevel.CRITICAL, robot_id="AMR-001",
            subsystem="POWER", message="Thermal shutdown warning", battery_level=60.0,
            cpu_usage=95.0, memory_usage=85.0, temperature=72.0
        ),
    ]

    sample_subsystems = {"DRIVE": 15, "NAV": 8, "POWER": 4, "ARM": 2}

    sample_uptime = {
        "AMR-001": UptimeReport("AMR-001", 3600.0, 300.0, 92.3, []),
        "AMR-002": UptimeReport("AMR-002", 3400.0, 600.0, 85.0, []),
    }

    generator = ChartGenerator(output_dir="reports_test/charts")

    trend_chart = generator.plot_telemetry_trends(sample_logs)
    subsystem_chart = generator.plot_subsystem_errors(sample_subsystems)
    uptime_chart = generator.plot_uptime_summary(sample_uptime)

    print("--- CHART GENERATOR TEST COMPLETE ---")
    print(f"Generated Telemetry Chart: {trend_chart}")
    print(f"Generated Subsystem Chart: {subsystem_chart}")
    print(f"Generated Uptime Chart: {uptime_chart}")