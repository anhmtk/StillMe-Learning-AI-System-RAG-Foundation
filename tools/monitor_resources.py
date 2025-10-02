import csv
import os
import time

import psutil


def monitor_resources():
    """Monitor CPU and RAM usage during K6 test"""
    out = "reports/k6_seal_test/resources.csv"
    os.makedirs(os.path.dirname(out), exist_ok=True)

    print("🔍 Starting resource monitoring...")

    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "cpu_percent", "mem_percent"])
        f.flush()

        try:
            while True:
                cpu_percent = psutil.cpu_percent(interval=1)
                mem_percent = psutil.virtual_memory().percent
                timestamp = time.time()

                w.writerow([timestamp, cpu_percent, mem_percent])
                f.flush()

                print(f"📊 CPU: {cpu_percent:.1f}%, RAM: {mem_percent:.1f}%")

        except KeyboardInterrupt:
            print("🛑 Resource monitoring stopped")
            pass

if __name__ == "__main__":
    monitor_resources()
