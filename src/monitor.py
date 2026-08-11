import time

from monitoring.history import MonitorHistory
from monitoring.sampler import SystemSampler


SAMPLE_INTERVAL = 1
HISTORY_SIZE = 60


def bytes_to_mb(value):
    return value / (1024 ** 2)


def bytes_to_gb(value):
    return value / (1024 ** 3)


def print_sample(sample, history):
    print("=" * 60)

    print(
        f"CPU: {sample['cpu']['percent']:.1f}%"
    )

    print(
        f"RAM: {sample['memory']['percent']:.1f}% "
        f"("
        f"{bytes_to_gb(sample['memory']['used_bytes']):.2f} GB used"
        f")"
    )

    print(
        f"Disk: {sample['disk']['percent']:.1f}% full"
    )

    print(
        "Disk Read:  "
        f"{bytes_to_mb(sample['disk']['read_bytes_per_second']):.2f} MB/s"
    )

    print(
        "Disk Write: "
        f"{bytes_to_mb(sample['disk']['write_bytes_per_second']):.2f} MB/s"
    )

    print(
        "Download: "
        f"{bytes_to_mb(sample['network']['download_bytes_per_second']):.2f} MB/s"
    )

    print(
        "Upload:   "
        f"{bytes_to_mb(sample['network']['upload_bytes_per_second']):.2f} MB/s"
    )

    print(
        f"Processes: {sample['processes']['count']}"
    )

    print("\nTOP CPU PROCESSES")

    for process in sample["processes"]["top_cpu"]:
        print(
            f"{process['name']:<30} "
            f"PID {process['pid']:<8} "
            f"{process['cpu_percent']:>6.2f}%"
        )

    print("\nTOP MEMORY PROCESSES")

    for process in sample["processes"]["top_memory"]:
        print(
            f"{process['name']:<30} "
            f"PID {process['pid']:<8} "
            f"{bytes_to_mb(process['memory_bytes']):>8.2f} MB"
        )

    print(
        f"\nHistory: {len(history)}/{HISTORY_SIZE} samples"
    )


def main():
    print("Starting PC Performance Monitor...")
    print("Press Ctrl+C to stop.\n")

    sampler = SystemSampler()
    history = MonitorHistory(
        max_samples=HISTORY_SIZE
    )

    sampler.prime()

    previous_time = time.perf_counter()

    try:
        while True:
            time.sleep(SAMPLE_INTERVAL)

            current_time = time.perf_counter()

            elapsed_seconds = (
                current_time - previous_time
            )

            sample = sampler.sample(
                elapsed_seconds=elapsed_seconds
            )

            history.add(sample)

            print_sample(
                sample,
                history,
            )

            previous_time = current_time

    except KeyboardInterrupt:
        print("\nStopping PC Performance Monitor...")

    finally:
        print("Monitor stopped cleanly.")


if __name__ == "__main__":
    main()