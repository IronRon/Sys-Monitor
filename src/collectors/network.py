import psutil
# Again, these are cumulative counters, not speeds.
# psutil exposes sent/received bytes and packet counters,
# and can also report them per network interface later using pernic=True

def get_network_usage():
    network = psutil.net_io_counters()

    return {
        "bytes_sent": network.bytes_sent,
        "bytes_received": network.bytes_recv,
        "packets_sent": network.packets_sent,
        "packets_received": network.packets_recv,
    }