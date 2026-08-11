import psutil
# In a real monitor, we want the main loop to control the sampling interval instead.
# With interval=None, psutil compares CPU time against its previous call and returns immediately.
# The first non-blocking call is meaningless, so we'll prime it before starting our loop.

def get_cpu_usage():
    return {
        "total_percent": psutil.cpu_percent(interval=None),
        "per_cpu_percent": psutil.cpu_percent(interval=None, percpu=True),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_processors": psutil.cpu_count(logical=True),
    }