import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import time
import streamlit as st
import pandas as pd

from config import DB_PATH, MAX_CHART_POINTS, DASHBOARD_REFRESH_SECS, HOSTS
import database
import snmp_monitor
import icmp_monitor

# Start monitoring once
if "monitoring_started" not in st.session_state:
    database.init_db()
    snmp_monitor.start()
    icmp_monitor.start()
    st.session_state.monitoring_started = True

st.set_page_config(page_title="Hybrid Network Monitor", page_icon="📡", layout="wide")

st.title("📡 Hybrid Network Monitoring Agent")
st.caption(f"Real-time Monitor • Refresh: {DASHBOARD_REFRESH_SECS}s")

def load_table(query):
    try:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

placeholder = st.empty()

while True:
    icmp_df = load_table(f"SELECT * FROM icmp_metrics ORDER BY timestamp DESC LIMIT {MAX_CHART_POINTS * len(HOSTS)}")
    snmp_df = load_table(f"SELECT * FROM snmp_metrics ORDER BY timestamp DESC LIMIT {MAX_CHART_POINTS * len(HOSTS)}")

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
                    if not icmp_df.empty:
                        row = icmp_df[icmp_df["host_ip"] == ip].tail(1)
                        if not row.empty:
                            status = row["status"].values[0]
                            rtt = row["avg_rtt_ms"].values[0]
                            loss = row["packet_loss_pct"].values[0]
                            icon = "🟢" if status == "Up" else "🟡" if status == "Degraded" else "🔴"
                            st.markdown(f"**Status:** {icon} {status}")
                            st.metric("RTT", f"{rtt:.1f} ms" if rtt else "—")
                            st.metric("Packet Loss", f"{loss:.1f}%")
                        else:
                            st.info("Waiting for data...")
                    else:
                        st.info("Starting up...")

        with tab2:
            st.success("✅ SNMP Simulation Running (Localhost)")
            if not snmp_df.empty:
                st.dataframe(snmp_df[["timestamp","host_ip","cpu_pct","mem_pct"]].tail(10), use_container_width=True)
            else:
                st.info("SNMP data will appear shortly...")

        with tab3:
            if not icmp_df.empty:
                st.dataframe(icmp_df[["timestamp","host_ip","avg_rtt_ms","packet_loss_pct","status"]].tail(15), use_container_width=True)
            else:
                st.info("ICMP data coming...")

        with tab4:
            st.info("Alerts will appear here when thresholds are crossed.")

    time.sleep(DASHBOARD_REFRESH_SECS)
