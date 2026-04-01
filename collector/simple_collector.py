import requests
import psutil
from datetime import datetime
import time

API_URL = "http://localhost:8080"

def collect_and_send():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    net = psutil.net_io_counters()
    
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "cpu_usage": cpu,
        "cpu_temp": 45.0,
        "ram_usage": ram.percent,
        "ram_total": round(ram.total / (1024**3), 2),
        "ram_used": round(ram.used / (1024**3), 2),
        "disk_read": 0,
        "disk_write": 0,
        "network_sent": net.bytes_sent,
        "network_recv": net.bytes_recv,
        "gpu_usage": 0,
        "gpu_temp": 0,
    }
    
    try:
        r = requests.post(f"{API_URL}/api/metrics/ingest", json=payload, timeout=5)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] CPU: {cpu:.1f}% RAM: {ram.percent:.1f}% Status: {r.status_code}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    print("Collector iniciado...")
    while True:
        collect_and_send()
        time.sleep(5)
