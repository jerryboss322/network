import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

import time
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from config import DB_PATH, MAX_CHART_POINTS, DASHBOARD_REFRESH_SECS, HOSTS

st.set_page_config(page_title="Hybrid Network Monitor", page_icon="📡", layout="wide")

def load_table(query):
    try:
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

def status_badge(s):
    return {"Up": "🟢 Up", "Degraded": "🟡 Degraded", "Down": "🔴 Down"}.get(s, "⚪ Unknown")

st.title("📡 Hybrid Network Monitoring Agent")
st.caption(f"Auto-refreshes every {DASHBOARD_REFRESH_SECS} seconds")

placeholder = st.empty()

while True:
    snmp_df = get_snmp()
    icmp_df = get_icmp()
    alert_df = get_alerts()

    if not snmp_df.empty: snmp_df = snmp_df.iloc[::-1].reset_index(drop=True)
    if not icmp_df.empty: icmp_df = icmp_df.iloc[::-1].reset_index(drop=True)

    with placeholder.container():
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 Overview", "📊 SNMP Metrics", "🌐 ICMP Metrics", "🚨 Alerts"])

        with tab1:
            st.subheader("Host Status")
            cols = st.columns(len(HOSTS))
            for i, host in enumerate(HOSTS):
                ip = host["ip"]
                label = host["label"]
                with cols[i]:
                    st.markdown(f"**{label}**")
                    # Add more metrics here later
                    st.write("Status will appear after main.py runs")

        with tab2: st.info("SNMP charts coming soon...")
        with tab3: st.info("ICMP charts coming soon...")
        with tab4: st.info("Alerts coming soon...")

    time.sleep(DASHBOARD_REFRESH_SECS)
