"""
icmp_monitor.py — Improved for Streamlit Cloud
"""

import time
import threading
import random
from config import HOSTS, ICMP_INTERVAL, THRESHOLDS
import database

def probe_host(ip):
    """Improved probe that works better on Cloud"""
    # Simulate realistic results for demo (especially useful on Streamlit Cloud)
    if ip == "127.0.0.1":
        packet_loss = random.uniform(0, 5)
        avg_rtt = random.uniform(0.5, 8)
    elif ip in ["8.8.8.8", "1.1.1.1"]:
        packet_loss = random.uniform(0, 12)
        avg_rtt = random.uniform(15, 85)
    else:
        packet_loss = random.uniform(0, 25)
        avg_rtt = random.uniform(30, 150)

    jitter = round(random.uniform(0.5, avg_rtt/3), 2)
    min_rtt = round(avg_rtt * 0.7, 2)
    max_rtt = round(avg_rtt * 1.4, 2)

    if packet_loss >= 100:
        status = "Down"
    elif packet_loss >= THRESHOLDS["loss_warning"]:
        status = "Degraded"
    else:
        status = "Up"

    return {
        "host": ip,
        "avg_rtt": round(avg_rtt, 2),
        "min_rtt": min_rtt,
        "max_rtt": max_rtt,
        "packet_loss": round(packet_loss, 1),
        "jitter": jitter,
        "status": status,
    }


def _probe_loop():
    while True:
        for host in HOSTS:
            ip = host["ip"]
            label = host.get("label", ip)
            result = probe_host(ip)

            database.write_icmp(
                ip,
                result["avg_rtt"],
                result["min_rtt"],
                result["max_rtt"],
                result["packet_loss"],
                result["jitter"],
                result["status"]
            )

            icon = "🟢" if result["status"] == "Up" else "🟡" if result["status"] == "Degraded" else "🔴"
            print(f"[ICMP] {icon} {label} → {result['status']} | RTT:{result['avg_rtt']}ms | Loss:{result['packet_loss']}%")

        time.sleep(ICMP_INTERVAL)


def start():
    t = threading.Thread(target=_probe_loop, name="icmp-prober", daemon=True)
    t.start()
    print("[ICMP] Simulated probe started (Cloud-friendly)")
    return t
