import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Import your existing modules
from src.parser.log_parser import LogParser
from src.analysis.error_analyzer import ErrorAnalyzer
from src.analysis.telemetry_analyzer import TelemetryAnalyzer
from src.analysis.uptime_analyzer import UptimeAnalyzer
from src.models.log_entry import LogLevel

# Page Configuration
st.set_page_config(
    page_title="AMR Fleet Telemetry & Log Analyzer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title & Header
st.title("🤖 Autonomous Mobile Robot (AMR) Fleet Telemetry Analyzer")
st.markdown("Real-time log parsing, telemetry anomaly detection, and fleet health monitoring dashboard.")

# Sidebar - Data Source & Filters
st.sidebar.header("🔌 Connectivity & Ingestion")
data_source = st.sidebar.radio("Data Source", ["Upload Log File (USB/Local)", "Load Built-in Demo Fleet Data"])

logs_raw = []
parser = LogParser()

if data_source == "Upload Log File (USB/Local)":
    uploaded_file = st.sidebar.file_uploader("Choose a robot .log file", type=["log", "txt"])
    if uploaded_file is not None:
        lines = uploaded_file.getvalue().decode("utf-8").splitlines()
        logs_raw = [parser.parse_line(line) for line in lines if parser.parse_line(line) is not None]
    else:
        st.info("👈 Please upload a log file from your USB drive or select 'Load Built-in Demo Fleet Data' to test.")
        st.stop()
else:
    # Sample Demo Data
    sample_lines = [
        "2026-07-31 12:00:00 [INFO] [AMR-001] [NAV]: Mission initialized | BAT:95.0% CPU:22.0% MEM:30.0% TEMP:35.0C",
        "2026-07-31 12:01:00 [INFO] [AMR-001] [NAV]: Waypoint A reached | BAT:92.0% CPU:25.0% MEM:32.0% TEMP:38.0C",
        "2026-07-31 12:02:00 [WARNING] [AMR-001] [DRIVE]: High motor load detected | BAT:88.0% CPU:78.0% MEM:45.0% TEMP:62.0C",
        "2026-07-31 12:03:00 [ERROR] [AMR-001] [POWER]: Thermal throttling activated | BAT:82.0% CPU:90.0% MEM:60.0% TEMP:78.0C",
        "2026-07-31 12:00:00 [INFO] [AMR-002] [NAV]: Docking sequence start | BAT:18.0% CPU:15.0% MEM:20.0% TEMP:32.0C",
        "2026-07-31 12:01:30 [WARNING] [AMR-002] [POWER]: Low battery warning | BAT:14.0% CPU:18.0% MEM:22.0% TEMP:34.0C",
        "2026-07-31 12:05:00 [CRITICAL] [AMR-002] [POWER]: Battery depleted - emergency stop | BAT:4.0% CPU:95.0% MEM:80.0% TEMP:75.0C",
    ]
    logs_raw = [parser.parse_line(line) for line in sample_lines if parser.parse_line(line) is not None]

# Filter by Robot ID
robot_ids = sorted(list(set(entry.robot_id for entry in logs_raw)))
selected_robot = st.sidebar.selectbox("Filter by Robot ID", ["All Fleet"] + robot_ids)

# Apply Filter
if selected_robot != "All Fleet":
    filtered_logs = [e for e in logs_raw if e.robot_id == selected_robot]
else:
    filtered_logs = logs_raw

# Convert to Pandas DataFrame for visualization
df_data = []
for entry in filtered_logs:
    df_data.append({
        "Timestamp": entry.timestamp,
        "Level": entry.level.value if hasattr(entry.level, 'value') else str(entry.level),
        "Robot ID": entry.robot_id,
        "Subsystem": entry.subsystem,
        "Message": entry.message,
        "Battery (%)": entry.battery_level,
        "CPU (%)": entry.cpu_usage,
        "Memory (%)": entry.memory_usage,
        "Temperature (°C)": entry.temperature
    })
df = pd.DataFrame(df_data)

# --- KEY METRICS CARDS ---
st.subheader("📊 Executive Fleet Overview")
col1, col2, col3, col4, col5 = st.columns(5)

error_analyzer = ErrorAnalyzer()
error_summary = error_analyzer.analyze(filtered_logs)

telemetry_analyzer = TelemetryAnalyzer(low_battery_threshold=20.0, high_temp_threshold=65.0)
anomalies = telemetry_analyzer.detect_anomalies(filtered_logs)

col1.metric("Total Logs Analyzed", len(filtered_logs))
col2.metric("Critical Errors", error_summary.critical_count)
col3.metric("Errors Detected", error_summary.error_count)
col4.metric("Low Battery Alerts", len(anomalies.get("low_battery", [])))
col5.metric("Overheating Alerts", len(anomalies.get("overheating", [])))

st.markdown("---")

# --- CHARTS SECTION ---
tab1, tab2, tab3 = st.tabs(["📈 Telemetry Charts", "🧩 Subsystem Breakdown", "🔍 Raw Log Inspector"])

with tab1:
    st.subheader("Robot Telemetry Trends Over Time")
    if not df.empty:
        # Temperature & Battery Line Charts
        fig_temp = px.line(
            df, x="Timestamp", y="Temperature (°C)", color="Robot ID",
            title="Thermal Profile (°C) over Time", markers=True,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        # Add horizontal threshold line
        fig_temp.add_hline(y=65.0, line_dash="dash", line_color="red", annotation_text="Overheat Limit (65°C)")
        st.plotly_chart(fig_temp, use_container_width=True)

        fig_bat = px.line(
            df, x="Timestamp", y="Battery (%)", color="Robot ID",
            title="Battery State of Charge (%)", markers=True,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_bat.add_hline(y=20.0, line_dash="dash", line_color="orange", annotation_text="Low Battery Limit (20%)")
        st.plotly_chart(fig_bat, use_container_width=True)

with tab2:
    st.subheader("Error & Warning Distribution by Subsystem")
    if not df.empty:
        col_left, col_right = st.columns(2)
        
        with col_left:
            subsystem_counts = df["Subsystem"].value_counts().reset_index()
            subsystem_counts.columns = ["Subsystem", "Count"]
            fig_sub = px.pie(
                subsystem_counts, values="Count", names="Subsystem",
                title="Log Volume by Subsystem (NAV, DRIVE, POWER)",
                hole=0.4
            )
            st.plotly_chart(fig_sub, use_container_width=True)

        with col_right:
            level_counts = df["Level"].value_counts().reset_index()
            level_counts.columns = ["Log Level", "Count"]
            fig_lvl = px.bar(
                level_counts, x="Log Level", y="Count", color="Log Level",
                title="Severity Distribution",
                color_discrete_map={"INFO": "green", "WARNING": "orange", "ERROR": "red", "CRITICAL": "darkred"}
            )
            st.plotly_chart(fig_lvl, use_container_width=True)

with tab3:
    st.subheader("Filter & Search Parsed Logs")
    
    # Severity Filter
    selected_levels = st.multiselect("Filter by Severity Level", options=["INFO", "WARNING", "ERROR", "CRITICAL"], default=["INFO", "WARNING", "ERROR", "CRITICAL"])
    
    filtered_df = df[df["Level"].isin(selected_levels)]
    
    # Search box
    search_query = st.text_input("Search message content...", "")
    if search_query:
        filtered_df = filtered_df[filtered_df["Message"].str.contains(search_query, case=False, na=False)]
        
    st.dataframe(filtered_df, use_container_width=True, height=400)

st.markdown("---")
st.caption("Robot Log & Telemetry Health Analyzer | Built with Python, Streamlit & Plotly")