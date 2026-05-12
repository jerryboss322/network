import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import time
import threading
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import your modules
from config import DB_PATH, MAX_CHART_POINTS, DASHBOARD_REFRESH_SECS, HOSTS
import database
import snmp_monitor
import icmp_monitor

# Initialize database and start monitoring threads (only once)
if "monitoring_started" not in st.session_state:
    database.init_db()
    snmp_monitor.start()
    icmp_monitor.start()
    st.session_state.monitoring_started = True
    print("✅ Monitoring threads started!")

# ── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hybrid Network Monitor", page_icon="📡", layout="wide")

st.title("📡 Hybrid Network Monitoring Agent")
st.caption(f"Real-time SNMP + ICMP Monitor • Auto-refreshes every {DASHBOARD_REFRESH_SECS}s")

# Data loading functions
def load_table(query):
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

def get_snmp():
    return load_table(f"SELECT * FROM snmp_metrics ORDER BY timestamp DESC LIMIT {MAX_CHART_POINTS * len(HOSTS)}")

def get_icmp():
    return load_table(f"SELECT * FROM icmp_metrics ORDER BY timestamp DESC LIMIT {MAX_CHART_POINTS * len(HOSTS)}")

def get_alerts():
    return load_table("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 100")

placeholder = st.empty()

while True:
    snmp_df = get_snmp()
    icmp_df = get_icmp()
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
                with cols[idx]:
                    st.markdown(f"### {label}")

                    # ICMP Status
                    if not icmp_df.empty:
                        row = icmp_df[icmp_df["host_ip"] == ip].tail(1)
                        if not row.empty:
                            status = row["status"].values[0]
                            rtt = row["avg_rtt_ms"].values[0]
                            loss = row["packet_loss_pct"].values[0]
                            st.markdown(f"**Status:** { {'Up':'🟢 Up', 'Degraded':'🟡 Degraded', 'Down':'🔴 Down'}.get(status, status) }")
                            st.metric("RTT", f"{rtt:.1f} ms" if rtt else "—")
                            st.metric("Loss", f"{loss:.1f}%" if loss is not None else "—")
                        else:
                            st.write("Waiting for data...")
                    else:
                        st.write("Waiting for first ICMP probe...")

        with tab2:
            st.info("SNMP charts will appear here after data is collected (60s interval)")
        with tab3:
            st.info("ICMP charts will appear here after data is collected (30s interval)")
        with tab4:
            st.info("Alerts will appear here")

    time.sleep(DASHBOARD_REFRESH_SECS)
