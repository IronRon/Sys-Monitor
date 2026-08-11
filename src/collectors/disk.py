import psutil
# Those last two are cumulative counters.
# psutil documents read_bytes and write_bytes as the total bytes read/written by the system counters.
# Suppose we see:
# 12:00:00
# read_bytes = 1,000,000,000
# 12:00:01
# read_bytes = 1,025,000,000

# Then:
# 1,025,000,000
# -
# 1,000,000,000
# =
# 25,000,000 bytes
# were read during that sample period.
# That's how we'll calculate disk read speed.

def get_disk_usage():
    usage = psutil.disk_usage("C:\\")
    io = psutil.disk_io_counters()

    return {
        "percent": usage.percent,
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
        "read_bytes": io.read_bytes,
        "write_bytes": io.write_bytes,
    }