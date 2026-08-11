from datetime import datetime

import psutil

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


class SystemSampler:
    def __init__(self):
        self.previous_disk = None
        self.previous_network = None

    def prime(self):
        """
        Establish initial measurements needed for
        calculating CPU percentages and I/O rates.
        """

        # Prime system CPU.
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)

        # Prime individual process CPU measurements.
        prime_process_cpu()

        # Establish baseline cumulative counters.
        self.previous_disk = get_disk_usage()
        self.previous_network = get_network_usage()

    def sample(self, elapsed_seconds):
        """
        Take one complete system sample.
        """

        cpu = get_cpu_usage()
        memory = get_memory_usage()
        disk = get_disk_usage()
        network = get_network_usage()

        processes = get_processes()

        top_cpu_processes = get_top_cpu_processes(
            processes,
            limit=5,
        )

        top_memory_processes = get_top_memory_processes(
            processes,
            limit=5,
        )

        disk_read_speed = (
            disk["read_bytes"]
            - self.previous_disk["read_bytes"]
        ) / elapsed_seconds

        disk_write_speed = (
            disk["write_bytes"]
            - self.previous_disk["write_bytes"]
        ) / elapsed_seconds

        download_speed = (
            network["bytes_received"]
            - self.previous_network["bytes_received"]
        ) / elapsed_seconds

        upload_speed = (
            network["bytes_sent"]
            - self.previous_network["bytes_sent"]
        ) / elapsed_seconds

        sample = {
            "timestamp": datetime.now(),

            "cpu": {
                "percent": cpu["total_percent"],
                "per_cpu_percent": cpu["per_cpu_percent"],
            },

            "memory": {
                "percent": memory["percent"],
                "total_bytes": memory["total"],
                "used_bytes": memory["used"],
                "available_bytes": memory["available"],
            },

            "disk": {
                "percent": disk["percent"],
                "total_bytes": disk["total"],
                "used_bytes": disk["used"],
                "free_bytes": disk["free"],
                "read_bytes_per_second": disk_read_speed,
                "write_bytes_per_second": disk_write_speed,
            },

            "network": {
                "download_bytes_per_second": download_speed,
                "upload_bytes_per_second": upload_speed,
            },

            "processes": {
                "count": len(processes),
                "top_cpu": top_cpu_processes,
                "top_memory": top_memory_processes,
            },
        }

        self.previous_disk = disk
        self.previous_network = network

        return sample