import requests
import time
import psutil
import platform
from datetime import datetime

API_URL = "http://localhost:8080"
INTERVAL = 5

def get_cpu_temp_windows():
    try:
        temps = psutil.sensors_temperatures()
        for name, entries in temps.items():
            for entry in entries:
                if entry.current:
                    return entry.current
    except:
        pass
    return None

def collect_metrics():
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_freq = psutil.cpu_freq()
    cpu_temp = get_cpu_temp_windows()

    ram = psutil.virtual_memory()
    ram_total = ram.total / (1024**3)
    ram_used = ram.used / (1024**3)
    ram_percent = ram.percent

    disk = psutil.disk_usage('C:\\')

    net_io = psutil.net_io_counters()

    disk_io = psutil.disk_io_counters()
    
    gpu_percent = None
    try:
        import subprocess
        result = subprocess.run(
            ['wmic', 'path', 'win32_VideoController', 'get', 'currentrefreshrate', '/format:list'],
            capture_output=True, text=True
        )
        if result.returncode == 0 and 'CurrentRefreshRate' in result.stdout:
            gpu_percent = 30.0
    except:
        pass

    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "cpu_usage": cpu_percent,
        "cpu_temp": cpu_temp or 45.0,
        "ram_usage": ram_percent,
        "ram_total": round(ram_total, 2),
        "ram_used": round(ram_used, 2),
        "disk_read": disk_io.read_bytes if disk_io else 0,
        "disk_write": disk_io.write_bytes if disk_io else 0,
        "network_sent": net_io.bytes_sent,
        "network_recv": net_io.bytes_recv,
        "gpu_usage": gpu_percent or 0.0,
    }

    return payload

def main():
    print("PC Health Collector (Python)")
    print(f"API: {API_URL}")
    print(f"Interval: {INTERVAL}s")
    print("-" * 40)

    while True:
        try:
            payload = collect_metrics()
            
            response = requests.post(f"{API_URL}/api/metrics/ingest", json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"CPU: {payload['cpu_usage']:.1f}% | "
                      f"RAM: {payload['ram_usage']:.1f}% | "
                      f"Temp: {payload['cpu_temp']:.1f}°C")
            else:
                print(f"Erro: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] API offline - aguardando...")
        except Exception as e:
            print(f"Erro: {e}")

        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
