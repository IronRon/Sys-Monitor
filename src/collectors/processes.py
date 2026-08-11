import psutil
# process_iter() is the recommended way to enumerate processes because it safely deals
# with processes appearing/disappearing while you're iterating.
# psutil also caches Process objects between calls when their PID remains alive,
# which will be useful shortly for CPU sampling.


def prime_process_cpu():
    """
    Establish an initial CPU measurement for every process
    that currently exists.
    """
    for process in psutil.process_iter():
        try:
            process.cpu_percent(interval=None)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def get_processes():
    """
    Return information about every process currently running.
    """

    processes = []

    logical_cpus = psutil.cpu_count(logical=True) or 1

    for process in psutil.process_iter(
        ["pid", "ppid", "name", "memory_info"],
        ad_value=None,
    ):
        try:
            raw_cpu_percent = process.cpu_percent(interval=None)

            # psutil's process CPU percentage is based on
            # one logical CPU = 100%.
            #
            # Windows Task Manager instead normalises against
            # the total number of logical CPUs.
            task_manager_cpu_percent = (
                raw_cpu_percent / logical_cpus
            )

            memory_info = process.info["memory_info"]

            memory_bytes = (
                memory_info.rss # Resident Set Size (RSS) is the non-swapped physical memory a process has used.
                if memory_info is not None
                else 0
            )

            processes.append({
                "pid": process.info["pid"],
                "ppid": process.info["ppid"],
                "name": process.info["name"] or "<unknown>",
                "cpu_percent_raw": raw_cpu_percent,
                "cpu_percent": task_manager_cpu_percent,
                "memory_bytes": memory_bytes,
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return processes


def get_top_cpu_processes(processes, limit=5):
    return sorted(
        processes,
        key=lambda process: process["cpu_percent"],
        reverse=True,
    )[:limit]


def get_top_memory_processes(processes, limit=5):
    return sorted(
        processes,
        key=lambda process: process["memory_bytes"],
        reverse=True,
    )[:limit]