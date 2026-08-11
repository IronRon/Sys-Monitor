import psutil


def bytes_to_gb(value):
    return value / (1024 ** 3)


print("=== PC PERFORMANCE MONITOR ===")

# CPU
print("\n--- CPU ---")

cpu_usage = psutil.cpu_percent(interval=1)

print(f"CPU Usage: {cpu_usage}%")
print(f"Physical Cores: {psutil.cpu_count(logical=False)}")
print(f"Logical Processors: {psutil.cpu_count(logical=True)}")


# RAM
print("\n--- MEMORY ---")

memory = psutil.virtual_memory()

print(f"RAM Usage: {memory.percent}%")
print(f"Total RAM: {bytes_to_gb(memory.total):.2f} GB")
print(f"Available RAM: {bytes_to_gb(memory.available):.2f} GB")


# DISK
print("\n--- DISK ---")

disk = psutil.disk_usage("C:\\")

print(f"Disk Usage: {disk.percent}%")
print(f"Total Disk: {bytes_to_gb(disk.total):.2f} GB")
print(f"Free Disk: {bytes_to_gb(disk.free):.2f} GB")


# NETWORK
print("\n--- NETWORK ---")

network = psutil.net_io_counters()

print(f"Bytes Sent: {network.bytes_sent:,}")
print(f"Bytes Received: {network.bytes_recv:,}")


# PROCESSES
print("\n--- RUNNING PROCESSES ---")

processes = list(psutil.process_iter(["pid", "name"]))

print(f"Running Processes: {len(processes)}")

for process in processes[:10]:
    print(
        f"PID: {process.info['pid']:<8} "
        f"Name: {process.info['name']}"
    )