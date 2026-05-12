"""
icmp_monitor.py — ICMP Probe Module
Hybrid Network Monitoring Agent (SNMP + ICMP)

Uses the system ping command (cross-platform: Windows & Linux/macOS).
Measures RTT (avg/min/max), packet loss, jitter, and host status.
"""

import re
import time
import platform
import statistics
import subprocess
import threading

import database
from config import HOSTS, ICMP_INTERVAL, ICMP_COUNT, ICMP_TIMEOUT, THRESHOLDS


# ── Probe a single host ───────────────────────────────────────────────────────
def probe_host(ip, count=ICMP_COUNT, timeout=ICMP_TIMEOUT):
    """
    Send `count` ICMP Echo Requests to `ip`.
    Returns a dict with keys:
        host, avg_rtt, min_rtt, max_rtt, packet_loss, jitter, status
    """
    system = platform.system().lower()

    # Build OS-appropriate ping command
    if system == "windows":
        cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), ip]
    else:
        # Linux / macOS
        cmd = ["ping", "-c", str(count), "-W", str(timeout), ip]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=count * timeout + 5,
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return _down_result(ip)
    except FileNotFoundError:
        print("[ICMP] ping command not found on this system.")
        return _down_result(ip)

    # ── Parse RTT values ──────────────────────────────────────────────────────
    # Windows:  "time=12ms"  or  "time<1ms"
    # Linux:    "time=12.3 ms"
    rtt_matches = re.findall(
        r"time[=<](\d+\.?\d*)\s*ms", output, re.IGNORECASE
    )
    rtts = [float(r) for r in rtt_matches]

    # ── Parse packet loss ─────────────────────────────────────────────────────
    loss_match = re.search(r"(\d+)%\s*(packet\s*)?loss", output, re.IGNORECASE)
    packet_loss = float(loss_match.group(1)) if loss_match else 100.0

    # ── Compute statistics ────────────────────────────────────────────────────
    if rtts:
        avg_rtt = round(statistics.mean(rtts), 2)
        min_rtt = round(min(rtts), 2)
        max_rtt = round(max(rtts), 2)
        jitter  = round(statistics.stdev(rtts), 2) if len(rtts) > 1 else 0.0
    else:
        avg_rtt = min_rtt = max_rtt = jitter = None

    # ── Determine host status ─────────────────────────────────────────────────
    if packet_loss >= 100:
        status = "Down"
    elif packet_loss >= THRESHOLDS["loss_warning"]:
        status = "Degraded"
    else:
        status = "Up"

    return {
        "host":        ip,
        "avg_rtt":     avg_rtt,
        "min_rtt":     min_rtt,
        "max_rtt":     max_rtt,
        "packet_loss": packet_loss,
        "jitter":      jitter,
        "status":      status,
    }


def _down_result(ip):
    return {
        "host": ip, "avg_rtt": None, "min_rtt": None,
        "max_rtt": None, "packet_loss": 100.0,
        "jitter": None, "status": "Down",
    }


# ── Alert evaluation ──────────────────────────────────────────────────────────
def _check_alerts(result):
    ip   = result["host"]
    loss = result["packet_loss"]
    rtt  = result["avg_rtt"]

    if loss >= THRESHOLDS["loss_critical"]:
        database.write_alert(ip, "Host Unavailable", "CRITICAL", loss,
                             THRESHOLDS["loss_critical"],
                             f"Packet loss {loss:.0f}% — host is DOWN")
    elif loss >= THRESHOLDS["loss_warning"]:
        database.write_alert(ip, "High Packet Loss", "WARNING", loss,
                             THRESHOLDS["loss_warning"],
                             f"Packet loss {loss:.0f}% exceeds warning threshold")

    if rtt is not None:
        if rtt >= THRESHOLDS["rtt_critical"]:
            database.write_alert(ip, "High Latency", "CRITICAL", rtt,
                                 THRESHOLDS["rtt_critical"],
                                 f"RTT {rtt}ms exceeds critical threshold")
        elif rtt >= THRESHOLDS["rtt_warning"]:
            database.write_alert(ip, "High Latency", "WARNING", rtt,
                                 THRESHOLDS["rtt_warning"],
                                 f"RTT {rtt}ms exceeds warning threshold")


# ── Main probe loop ───────────────────────────────────────────────────────────
def _probe_loop():
    while True:
        for host in HOSTS:
            ip    = host["ip"]
            label = host.get("label", ip)
            result = probe_host(ip)

            database.write_icmp(
                ip,
                result["avg_rtt"],
                result["min_rtt"],
                result["max_rtt"],
                result["packet_loss"],
                result["jitter"],
                result["status"],
            )
            _check_alerts(result)

            status_icon = "✓" if result["status"] == "Up" else (
                          "⚠" if result["status"] == "Degraded" else "✗")
            print(f"[ICMP] {status_icon} {label} ({ip}) — "
                  f"RTT:{result['avg_rtt']}ms  "
                  f"Loss:{result['packet_loss']}%  "
                  f"Status:{result['status']}")

        time.sleep(ICMP_INTERVAL)


def start():
    """Start the ICMP probe loop in a background daemon thread."""
    t = threading.Thread(target=_probe_loop, name="icmp-prober", daemon=True)
    t.start()
    print("[ICMP] Probe thread started.")
    return t
