from config import DB_PATH
import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS snmp_metrics (
        id INTEGER PRIMARY KEY, timestamp TEXT, host_ip TEXT, cpu_pct REAL, mem_pct REAL,
        if_in_mbps REAL, if_out_mbps REAL, if_errors INTEGER, sys_uptime TEXT, reachable INTEGER)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS icmp_metrics (
        id INTEGER PRIMARY KEY, timestamp TEXT, host_ip TEXT, avg_rtt_ms REAL, min_rtt_ms REAL,
        max_rtt_ms REAL, packet_loss_pct REAL, jitter_ms REAL, status TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY, timestamp TEXT, host_ip TEXT, alert_type TEXT, severity TEXT,
        metric_value REAL, threshold_value REAL, message TEXT, resolved INTEGER DEFAULT 0)""")
    conn.commit()
    conn.close()
    print("[DB] Database ready.")

def write_snmp(host_ip, cpu_pct, mem_pct, if_in_mbps, if_out_mbps, if_errors, sys_uptime, reachable=1):
    ts = datetime.datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO snmp_metrics VALUES (NULL,?,?,?,?,?,?,?,?,?)",
                 (ts, host_ip, cpu_pct, mem_pct, if_in_mbps, if_out_mbps, if_errors, sys_uptime, reachable))
    conn.commit()
    conn.close()

def write_icmp(host_ip, avg_rtt, min_rtt, max_rtt, packet_loss, jitter, status):
    ts = datetime.datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO icmp_metrics VALUES (NULL,?,?,?,?,?,?,?,?)",
                 (ts, host_ip, avg_rtt, min_rtt, max_rtt, packet_loss, jitter, status))
    conn.commit()
    conn.close()

def write_alert(host_ip, alert_type, severity, metric_value, threshold_value, message):
    ts = datetime.datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO alerts VALUES (NULL,?,?,?,?,?,?,?,0)",
                 (ts, host_ip, alert_type, severity, metric_value, threshold_value, message))
    conn.commit()
    conn.close()
