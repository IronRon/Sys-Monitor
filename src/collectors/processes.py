import psutil


def prime_process_cpu():
    """
    Establish an initial non-blocking CPU measurement
    for every currently running process.

    Later cpu_percent(interval=None) calls can then
    calculate CPU use since this baseline.
    """

    for process in psutil.process_iter():

        try:

            process.cpu_percent(
                interval=None
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue


def get_processes():
    """
    Return a snapshot of currently running processes.

    This function can be relatively expensive on Windows
    because information must be retrieved for hundreds of
    separate processes.

    It therefore should not run directly in the main
    one-second SystemSampler path.
    """

    processes = []

    logical_cpus = (
        psutil.cpu_count(
            logical=True
        )
        or 1
    )


    for process in psutil.process_iter(
        [
            "pid",
            "ppid",
            "name",
            "memory_info",
        ],
        ad_value=None,
    ):

        try:

            raw_cpu_percent = (
                process.cpu_percent(
                    interval=None
                )
            )


            task_manager_cpu_percent = (
                raw_cpu_percent
                /
                logical_cpus
            )


            memory_info = (
                process.info[
                    "memory_info"
                ]
            )


            memory_bytes = (
                memory_info.rss
                if memory_info is not None
                else 0
            )


            processes.append({
                "pid":
                    process.info["pid"],

                "ppid":
                    process.info["ppid"],

                "name":
                    (
                        process.info["name"]
                        or "<unknown>"
                    ),

                "cpu_percent_raw":
                    raw_cpu_percent,

                "cpu_percent":
                    task_manager_cpu_percent,

                "memory_bytes":
                    memory_bytes,
            })


        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            continue


    return processes


def get_top_cpu_processes(
    processes,
    limit=5,
):

    return sorted(
        processes,
        key=lambda process:
            process["cpu_percent"],
        reverse=True,
    )[:limit]


def get_top_memory_processes(
    processes,
    limit=5,
):

    return sorted(
        processes,
        key=lambda process:
            process["memory_bytes"],
        reverse=True,
    )[:limit]