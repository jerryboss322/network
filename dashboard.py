"""
dashboard.py — Real-time Streamlit Dashboard
"""

import sys
from pathlib import Path

# Make sure Python can find local modules (important for Streamlit Cloud)
sys.path.insert(0, str(Path(__file__).parent))

import time
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from config import DB_PATH, MAX_CHART_POINTS, DASHBOARD_REFRESH_SECS, HOSTS

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Hybrid Network Monitor",
    page_icon="📡",
    layout="wide",
)

# ── Helper: load data from SQLite ─────────────────────────────────────────────
def load_table(query):
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def get_snmp():
    return load_table(f"""
        SELECT * FROM snmp_metrics
        ORDER BY timestamp DESC
        LIMIT {MAX_CHART_POINTS * len(HOSTS)}
    """)


def get_icmp():
    return load_table(f"""
        SELECT * FROM icmp_metrics
        ORDER BY timestamp DESC
        LIMIT {MAX_CHART_POINTS * len(HOSTS)}
    """)


def get_alerts():
    return load_table("""
        SELECT * FROM alerts
        ORDER BY timestamp DESC
        LIMIT 100
    """)


def severity_colour(sev):
    return {"CRITICAL": "🔴", "WARNING": "🟡"}.get(sev, "🟢")


def status_badge(status):
    return {"Up": "🟢 Up", "Degraded": "🟡 Degraded", "Down": "🔴 Down"}.get(
        status, "⚪ Unknown"
    )


# ═════════════════════════════════════════════════════════════════════════════
st.title("📡 Hybrid Network Monitoring Agent")
st.caption(f"Real-time monitoring using SNMP + ICMP  |  Auto-refreshes every {DASHBOARD_REFRESH_SECS} seconds")

placeholder = st.empty()

while True:
    snmp_df  = get_snmp()
    icmp_df  = get_icmp()
    alert_df = get_alerts()

    if not snmp_df.empty:
        snmp_df = snmp_df.iloc[::-1].reset_index(drop=True)
    if not icmp_df.empty:
        icmp_df = icmp_df.iloc[::-1].reset_index(drop=True)

    with placeholder.container():
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 Overview", "📊 SNMP Metrics", "🌐 ICMP Metrics", "🚨 Alerts"])

        with tab1:
            st.subheader("Host Status Summary")
            cols = st.columns(len(HOSTS))
            for idx, host in enumerate(HOSTS):
                ip = host["ip"]
                label = host["label"]

                if not icmp_df.empty:
                    row = icmp_df[icmp_df["host_ip"] == ip].tail(1)
                    if not row.empty:
                        status = row["status"].values[0]
                        rtt = row["avg_rtt_ms"].values[0]
                        loss = row["packet_loss_pct"].values[0]
                    else:
                        status, rtt, loss = "Unknown", None, None
                else:
                    status, rtt, loss = "Waiting…", None, None

                if not snmp_df.empty and host["snmp"]:
                    srow = snmp_df[snmp_df["host_ip"] == ip].tail(1)
                    cpu = srow["cpu_pct"].values[0] if not srow.empty else None
                    mem = srow["mem_pct"].values[0] if not srow.empty else None
                else:
                    cpu, mem = None, None

                with cols[idx]:
                    st.markdown(f"### {label}")
                    st.markdown(f"**Status:** {status_badge(status)}")
                    st.metric("RTT (ms)", f"{rtt:.1f}" if rtt is not None else "—")
                    st.metric("Packet Loss", f"{loss:.0f}%" if loss is not None else "—")
                    if cpu is not None:
                        st.metric("CPU", f"{cpu:.1f}%")
                    if mem is not None:
                        st.metric("Memory", f"{mem:.1f}%")

            st.divider()
            if not alert_df.empty:
                active = alert_df[alert_df["resolved"] == 0]
                if not active[active["severity"] == "CRITICAL"].empty:
                    st.error("🔴 Critical alerts active — check Alerts tab")
                elif not active.empty:
                    st.warning("🟡 Warnings active — check Alerts tab")
                else:
                    st.success("✅ All systems normal")
            else:
                st.info("Monitoring is starting up...")

        # (Rest of your tabs remain the same - abbreviated for brevity)
        with tab2:
            st.info("SNMP Charts will appear here once data is collected.")
        with tab3:
            st.info("ICMP Charts will appear here once data is collected.")
        with tab4:
            st.info("Alerts will appear here.")

    time.sleep(DASHBOARD_REFRESH_SECS)
