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

# Force restart monitoring
if "monitoring_started" not in st.session_state:
    database.init_db()
    snmp_monitor.start()
    icmp_monitor.start()
    st.session_state.monitoring_started = True
    st.success("Monitoring threads started!")

st.set_page_config(page_title="Hybrid Network Monitor", page_icon="📡", layout="wide")
st.title("📡 Hybrid Network Monitoring Agent")
st.caption(f"Real-time Monitor • Refreshing every {DASHBOARD_REFRESH_SECS}s")

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
    icmp_df = load_table("SELECT * FROM icmp_metrics ORDER BY timestamp DESC LIMIT 100")
    snmp_df = load_table("SELECT * FROM snmp_metrics ORDER BY timestamp DESC LIMIT 100")

    with placeholder.container():
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 Overview", "📊 SNMP Metrics", "🌐 ICMP Metrics", "🚨 Alerts"])

        with tab1:
            st.subheader("Host Status Summary")
            cols = st.columns(len(HOSTS))
            for idx, host in enumerate(HOSTS):
                ip = host["ip"]
                label = host["label"]
                with cols[idx]:
                    st.markdown(f"**{label}**")
                    row = icmp_df[icmp_df["host_ip"] == ip].head(1) if not icmp_df.empty else pd.DataFrame()
                    if not row.empty:
                        status = row["status"].values[0]
                        rtt = row["avg_rtt_ms"].values[0]
                        loss = row["packet_loss_pct"].values[0]
                        icon = "🟢" if status == "Up" else "🟡" if status == "Degraded" else "🔴"
                        st.markdown(f"**Status:** {icon} {status}")
                        st.metric("RTT", f"{rtt:.1f} ms" if rtt is not None else "—")
                        st.metric("Packet Loss", f"{loss:.1f}%")
                    else:
                        st.warning("No ICMP data yet...")

        with tab2:
            st.success("✅ SNMP Working")
            if not snmp_df.empty:
                st.dataframe(snmp_df[["host_ip","cpu_pct","mem_pct"]].tail(8), use_container_width=True)

        with tab3:
            st.subheader("Recent ICMP Data")
            if not icmp_df.empty:
                st.dataframe(icmp_df[["timestamp","host_ip","avg_rtt_ms","packet_loss_pct","status"]].head(15), use_container_width=True)
            else:
                st.info("Waiting for ICMP data...")

        with tab4:
            st.info("Alerts will show here when thresholds are crossed.")

    time.sleep(DASHBOARD_REFRESH_SECS)
