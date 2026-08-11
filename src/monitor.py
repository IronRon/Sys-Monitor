import time
import psutil

from collectors.cpu import get_cpu_usage
from collectors.memory import get_memory_usage
from collectors.disk import get_disk_usage
from collectors.network import get_network_usage
from collectors.processes import get_processes


SAMPLE_INTERVAL = 1


def bytes_to_mb(value):
    return value / (1024 ** 2)


def bytes_to_gb(value):
    return value / (1024 ** 3)


def main():
    print("Starting PC Performance Monitor...\n")

    # Prime CPU measurement.
    # The first non-blocking cpu_percent() reading is meaningless.
    # "Priming" means: Make an initial call so psutil has a baseline to compare the next call against.
    psutil.cpu_percent(interval=None)
    psutil.cpu_percent(interval=None, percpu=True)

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

        previous_disk = disk
        previous_network = network


if __name__ == "__main__":
    main()