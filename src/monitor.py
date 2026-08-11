import time
import psutil

from collections import deque
from datetime import datetime

from collectors.cpu import get_cpu_usage
from collectors.memory import get_memory_usage
from collectors.disk import get_disk_usage
from collectors.network import get_network_usage
from collectors.processes import (
    prime_process_cpu,
    get_processes,
    get_top_cpu_processes,
    get_top_memory_processes,
)

HISTORY_SIZE = 60
history = deque(maxlen=HISTORY_SIZE)

SAMPLE_INTERVAL = 1


def bytes_to_mb(value):
    return value / (1024 ** 2)


def bytes_to_gb(value):
    return value / (1024 ** 3)


def main():
    print("Starting PC Performance Monitor...\n")

    # Prime system CPU measurement.
    # The first non-blocking cpu_percent() reading is meaningless.
    # "Priming" means: Make an initial call so psutil has a baseline to compare the next call against.
    psutil.cpu_percent(interval=None)
    psutil.cpu_percent(interval=None, percpu=True)

    # Prime process CPU measurements.
    prime_process_cpu()

    previous_disk = get_disk_usage()
    previous_network = get_network_usage()

    while True:
        time.sleep(SAMPLE_INTERVAL)

        cpu = get_cpu_usage()
        memory = get_memory_usage()
        disk = get_disk_usage()
        network = get_network_usage()

        disk_read_speed = (
            disk["read_bytes"] - previous_disk["read_bytes"]
        ) / SAMPLE_INTERVAL

        disk_write_speed = (
            disk["write_bytes"] - previous_disk["write_bytes"]
        ) / SAMPLE_INTERVAL

        download_speed = (
            network["bytes_received"]
            - previous_network["bytes_received"]
        ) / SAMPLE_INTERVAL

        upload_speed = (
            network["bytes_sent"]
            - previous_network["bytes_sent"]
        ) / SAMPLE_INTERVAL

        processes = get_processes()

        top_cpu_processes = get_top_cpu_processes(
            processes,
            limit=5,
        )

        top_memory_processes = get_top_memory_processes(
            processes,
            limit=5,
        )

        print("=" * 60)

        print(
            f"CPU: {cpu['total_percent']:.1f}%"
        )

        print(
            f"RAM: {memory['percent']:.1f}% "
            f"({bytes_to_gb(memory['used']):.2f} GB used)"
        )

        print(
            f"Disk: {disk['percent']:.1f}% full"
        )

        print(
            f"Disk Read:  {bytes_to_mb(disk_read_speed):.2f} MB/s"
        )

        print(
            f"Disk Write: {bytes_to_mb(disk_write_speed):.2f} MB/s"
        )

        print(
            f"Download: {bytes_to_mb(download_speed):.2f} MB/s"
        )

        print(
            f"Upload:   {bytes_to_mb(upload_speed):.2f} MB/s"
        )

        print(
            f"Processes: {len(processes)}"
        )

        print("\nTOP CPU PROCESSES")

        for process in top_cpu_processes:
            print(
                f"{process['name']:<30} "
                f"PID {process['pid']:<8} "
                f"{process['cpu_percent']:>6.2f}%"
            )

        print("\nTOP MEMORY PROCESSES")

        for process in top_memory_processes:
            print(
                f"{process['name']:<30} "
                f"PID {process['pid']:<8} "
                f"{bytes_to_mb(process['memory_bytes']):>8.2f} MB"
            )

        sample = {
            "timestamp": datetime.now(),
            "cpu_percent": cpu["total_percent"],
            "per_cpu_percent": cpu["per_cpu_percent"],
            "memory_percent": memory["percent"],
            "disk_read_mb_s": bytes_to_mb(disk_read_speed),
            "disk_write_mb_s": bytes_to_mb(disk_write_speed),
            "download_mb_s": bytes_to_mb(download_speed),
            "upload_mb_s": bytes_to_mb(upload_speed),
        }

        history.append(sample)

        print(
            f"\nHistory samples: "
            f"{len(history)}/{HISTORY_SIZE}"
        )

        previous_disk = disk
        previous_network = network


if __name__ == "__main__":
    main()