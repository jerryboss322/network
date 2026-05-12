"""
icmp_monitor.py — Cloud-friendly simulation mode
"""

import time
import threading
import random
from config import HOSTS, ICMP_INTERVAL, THRESHOLDS
import database

def probe_host(ip):
    """Fully simulated probe - works reliably on Streamlit Cloud"""
    if ip == "127.0.0.1":
        # Localhost - should be very good
        loss = random.uniform(0, 3)
        rtt = random.uniform(0.5, 12)
    elif ip == "8.8.8.8":
        loss = random.uniform(0, 8)
        rtt = random.uniform(18, 75)
    elif ip == "1.1.1.1":
        loss = random.uniform(0, 6)
        rtt = random.uniform(12, 55)
    else:
        loss = random.uniform(0, 15)
        rtt = random.uniform(20, 120)

    jitter = round(random.uniform(0.2, rtt/4), 2)
    min_rtt = round(rtt * random.uniform(0.6, 0.9), 2)
    max_rtt = round(rtt * random.uniform(1.1, 1.6), 2)

    if loss > 80:
        status = "Down"
    elif loss >= THRESHOLDS["loss_warning"]:
        status = "Degraded"
    else:
        status = "Up"

    return {
        "host": ip,
        "avg_rtt": round(rtt, 2),
        "min_rtt": min_rtt,
        "max_rtt": max_rtt,
        "packet_loss": round(loss, 1),
        "jitter": jitter,
        "status": status,
    }


def _probe_loop():
    print("[ICMP] Simulation mode started (Cloud compatible)")
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
    return t
