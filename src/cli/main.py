import argparse
import sys
from pathlib import Path

from src.parser.file_reader import FileReader
from src.analysis.telemetry_analyzer import TelemetryAnalyzer
from src.analysis.uptime_analyzer import UptimeAnalyzer
from src.analysis.error_analyzer import ErrorAnalyzer
from src.exporters.report_exporter import ReportExporter
from src.visualization.chart_generator import ChartGenerator


def build_argument_parser() -> argparse.ArgumentParser:
    """Constructs command line argument options for the analyzer CLI."""
    parser = argparse.ArgumentParser(
        description="Enterprise Autonomous Robot Fleet Log & Health Analyzer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("-i", "--input", type=str, required=True, help="Path to target log file or directory")
    parser.add_argument("-o", "--output", type=str, default="reports", help="Directory path to save reports/charts")
    parser.add_argument("--low-battery", type=float, default=20.0, help="Low battery threshold")
    parser.add_argument("--high-temp", type=float, default=65.0, help="Overheating threshold")
    parser.add_argument("--gap-threshold", type=float, default=300.0, help="Heartbeat loss gap duration (seconds)")
    parser.add_argument("--no-charts", action="store_true", help="Disable Matplotlib graphical chart rendering")

    return parser


def run_pipeline(args: argparse.Namespace) -> int:
    """Orchestrates the pipeline from ingestion to plotting."""
    input_path = Path(args.input)
    output_dir = Path(args.output)

    print("==========================================================")
    print("   AUTONOMOUS ROBOT FLEET LOG & TELEMETRY HEALTH ENGINE   ")
    print("==========================================================")

    # 1. File Reading & Parsing
    print(f"\n[1/4] Ingesting and parsing logs from: {input_path}")
    file_reader = FileReader()
    entries = []

    try:
        if input_path.is_file():
            entries = file_reader.read_file(input_path)
        elif input_path.is_dir():
            # Dynamically scan directory for supported log files
            for file_path in input_path.glob("*.*"):
                if file_path.suffix.lower() in [".log", ".txt", ".csv", ".json"]:
                    entries.extend(file_reader.read_file(file_path))
        else:
            print(f"Error: Input path '{input_path}' does not exist.", file=sys.stderr)
            return 1
    except Exception as exc:
        print(f"Error reading log files: {exc}", file=sys.stderr)
        return 1

    if not entries:
        print("Warning: No valid log entries found to process. Exiting.", file=sys.stderr)
        return 0

    print(f"      Successfully parsed {len(entries)} valid LogEntry objects.")

    # 2. Analytical Computations
    print("[2/4] Running statistical analysis engines...")
    telemetry_analyzer = TelemetryAnalyzer(
        low_battery_threshold=args.low_battery,
        high_temp_threshold=args.high_temp
    )
    uptime_analyzer = UptimeAnalyzer(gap_threshold_seconds=args.gap_threshold)
    error_analyzer = ErrorAnalyzer()

    telemetry_summary = telemetry_analyzer.compute_summary(entries)
    anomalies = telemetry_analyzer.detect_anomalies(entries)
    uptime_reports = uptime_analyzer.analyze_fleet(entries)
    error_summary = error_analyzer.analyze(entries)
    health_scores = error_analyzer.calculate_subsystem_health_scores(entries)

    # 3. Report Serialization
    print(f"[3/4] Exporting reports to directory: {output_dir}")
    exporter = ReportExporter(output_dir=output_dir)

    combined_report_data = {
        "analysis_metadata": {
            "total_logs": len(entries),
            "input_source": str(input_path)
        },
        "telemetry_summary": telemetry_summary,
        "error_summary": error_summary.to_dict(),
        "subsystem_health_scores": health_scores,
        "fleet_uptime": {
            robot_id: report.to_dict() for robot_id, report in uptime_reports.items()
        }
    }

    json_path = exporter.export_json(combined_report_data, "fleet_health_summary.json")
    anomalies_csv = exporter.export_anomalies_csv(anomalies, "hardware_anomalies.csv")
    downtime_csv = exporter.export_downtime_events_csv(uptime_reports, "downtime_events.csv")

    print(f"      - Written JSON Summary: {json_path}")
    print(f"      - Written Anomalies CSV: {anomalies_csv}")
    print(f"      - Written Downtime CSV: {downtime_csv}")

    # 4. Visual Rendering
    if not args.no_charts:
        print("[4/4] Rendering Matplotlib chart visualizations...")
        chart_gen = ChartGenerator(output_dir=output_dir / "charts")
        trend_chart = chart_gen.plot_telemetry_trends(entries)
        subsystem_chart = chart_gen.plot_subsystem_errors(error_summary.subsystem_distribution)
        uptime_chart = chart_gen.plot_uptime_summary(uptime_reports)
        print(f"      - Saved Telemetry Chart: {trend_chart}")
        print(f"      - Saved Subsystem Chart: {subsystem_chart}")
        print(f"      - Saved Uptime Chart: {uptime_chart}")
    else:
        print("[4/4] Chart generation skipped via --no-charts flag.")

    # Terminal Summary Output
    print("\n----------------------------------------------------------")
    print("                EXECUTION SUMMARY HIGHLIGHTS              ")
    print("----------------------------------------------------------")
    print(f" Total Logs Processed : {len(entries)}")
    print(f" Errors / Criticals   : {error_summary.error_count} Errors | {error_summary.critical_count} Criticals")
    print(f" Low Battery Anomalies: {len(anomalies.get('low_battery', []))}")
    print(f" Overheating Events   : {len(anomalies.get('overheating', []))}")
    print(" Fleet Robots Tracked : " + ", ".join(uptime_reports.keys()))
    print("----------------------------------------------------------")
    print("SUCCESS: Log analysis pipeline completed successfully.\n")

    return 0


def main():
    """CLI Main Entrypoint."""
    arg_parser = build_argument_parser()
    args = arg_parser.parse_args()
    status_code = run_pipeline(args)
    sys.exit(status_code)


if __name__ == "__main__":
    main()