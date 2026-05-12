import time
import threading
import random
from config import HOSTS, ICMP_INTERVAL, THRESHOLDS
import database

def probe_host(ip):
    if ip == "127.0.0.1":
        loss = random.uniform(0, 4)
        rtt = random.uniform(1, 10)
    elif ip == "8.8.8.8":
        loss = random.uniform(0, 7)
        rtt = random.uniform(20, 70)
    else:  # 1.1.1.1
        loss = random.uniform(0, 5)
        rtt = random.uniform(15, 60)

    status = "Down" if loss >= 90 else "Degraded" if loss >= THRESHOLDS["loss_warning"] else "Up"

    return {
        "host": ip,
        "avg_rtt": round(rtt, 2),
        "min_rtt": round(rtt*0.8, 2),
        "max_rtt": round(rtt*1.3, 2),
        "packet_loss": round(loss, 1),
        "jitter": round(random.uniform(0.5, 5), 2),
        "status": status,
    }

def _probe_loop():
    print("[ICMP] Cloud simulation started - writing data every 30s")
    while True:
        for host in HOSTS:
            result = probe_host(host["ip"])
            database.write_icmp(
                host["ip"],
                result["avg_rtt"],
                result["min_rtt"],
                result["max_rtt"],
                result["packet_loss"],
                result["jitter"],
                result["status"]
            )
            icon = "🟢" if result["status"] == "Up" else "🔴"
            print(f"[ICMP] {icon} {host['label']} → {result['status']} | RTT {result['avg_rtt']}ms | Loss {result['packet_loss']}%")
        time.sleep(ICMP_INTERVAL)

def start():
    if "icmp_thread" not in globals():
        t = threading.Thread(target=_probe_loop, daemon=True)
        t.start()
        print("[ICMP] Thread started successfully")
    return t
