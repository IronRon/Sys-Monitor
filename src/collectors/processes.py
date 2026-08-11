import psutil
# process_iter() is the recommended way to enumerate processes because it safely deals
# with processes appearing/disappearing while you're iterating.
# psutil also caches Process objects between calls when their PID remains alive,
# which will be useful shortly for CPU sampling.

def get_processes():
    processes = []

    for process in psutil.process_iter(
        ["pid", "name", "memory_percent"]
    ):
        try:
            processes.append({
                "pid": process.info["pid"],
                "name": process.info["name"],
                "memory_percent": process.info["memory_percent"],
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return processes