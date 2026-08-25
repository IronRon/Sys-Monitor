from datetime import (
    datetime,
    timezone,
)
import time

import psutil

from collectors.cpu import get_cpu_usage
from collectors.memory import get_memory_usage
from collectors.disk import get_disk_usage
from collectors.network import (
    get_network_counters,
    get_interface_counters,
    get_network_connections,
    get_network_interfaces,
)
from collectors.self_monitor import (
    SelfMonitorCollector,
)

class SystemSampler:
    def __init__(self):
        self.previous_disk = None
        self.previous_network = None
        self.previous_interface_counters = None
        self.self_monitor = (
            SelfMonitorCollector()
        )
        self.cached_network_connections = []
        self.last_connection_refresh = None
        self.connection_refresh_interval = 5.0

    def prime(self):
        """
        Establish initial measurements needed for
        calculating CPU percentages and I/O rates.
        """

        # Prime system CPU.
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)

        # Establish baseline cumulative counters.
        self.previous_disk = get_disk_usage()
        self.previous_network = (
            get_network_counters()
        )
        self.previous_interface_counters = (
            get_interface_counters()
        )

        # Prime Sys Monitor's own CPU/I/O.
        self.self_monitor.prime()

    def sample(
        self,
        elapsed_seconds,
        processes=None,
    ):
        """
        Take one complete system sample.

        Process data is supplied by ProcessSnapshotWorker rather
        than collected here. This keeps expensive Windows process
        enumeration off the main one-second sampling path.
        """

        if processes is None:
            processes = []

        sample_started = (
            time.perf_counter()
        )

        timings = {}

        started = time.perf_counter()
        cpu = get_cpu_usage()
        timings["cpu_ms"] = (
            time.perf_counter() - started
        ) * 1000

        started = time.perf_counter()
        memory = get_memory_usage()
        timings["memory_ms"] = (
            time.perf_counter() - started
        ) * 1000


        started = time.perf_counter()
        disk = get_disk_usage()
        timings["disk_ms"] = (
            time.perf_counter() - started
        ) * 1000


        started = time.perf_counter()
        network = get_network_counters()
        timings["network_counters_ms"] = (
            time.perf_counter() - started
        ) * 1000


        disk_read_speed = max(
            disk["read_bytes"]
            - self.previous_disk["read_bytes"],
            0,
        ) / elapsed_seconds

        disk_write_speed = max(
            disk["write_bytes"]
            - self.previous_disk["write_bytes"],
            0,
        ) / elapsed_seconds

        download_speed = max(
            network["bytes_received"]
            - self.previous_network["bytes_received"],
            0,
        ) / elapsed_seconds

        upload_speed = max(
            network["bytes_sent"]
            - self.previous_network["bytes_sent"],
            0,
        ) / elapsed_seconds

        current_interface_counters = (
            get_interface_counters()
        )

        interface_rates = (
            self._calculate_interface_rates(
                self.previous_interface_counters,
                current_interface_counters,
                elapsed_seconds,
            )
        )

        started = time.perf_counter()
        interfaces = get_network_interfaces()
        timings["interfaces_ms"] = (
            time.perf_counter() - started
        ) * 1000

        for interface in interfaces:

            rates = interface_rates.get(
                interface["name"],
                {},
            )

            interface[
                "download_bytes_per_second"
            ] = rates.get(
                "download_bytes_per_second",
                0.0,
            )

            interface[
                "upload_bytes_per_second"
            ] = rates.get(
                "upload_bytes_per_second",
                0.0,
            )

        process_name_by_pid = {
            process["pid"]:
                process["name"]

            for process in processes
        }

        connection_time = time.monotonic()

        should_refresh_connections = (
            self.last_connection_refresh is None
            or
            (
                connection_time
                -
                self.last_connection_refresh
            )
            >= self.connection_refresh_interval
        )


        if should_refresh_connections:
            started = time.perf_counter()

            self.cached_network_connections = (
                get_network_connections(
                    process_name_by_pid
                )
            )

            timings["connections_ms"] = (
                time.perf_counter() - started
            ) * 1000

            self.last_connection_refresh = (
                connection_time
            )
        else:
            timings["connections_ms"] = 0.0


        connections = (
            self.cached_network_connections
        )

        started = time.perf_counter()

        self_metrics = (
            self.self_monitor.collect(
                elapsed_seconds
            )
        )

        timings["self_monitor_ms"] = (
            time.perf_counter() - started
        ) * 1000

        self_pid = (
            self_metrics["pid"]
        )


        self_connections = [
            connection

            for connection in connections

            if connection["pid"]
            == self_pid
        ]


        self_metrics[
            "network_socket_count"
        ] = len(
            self_connections
        )


        self_metrics[
            "remote_socket_count"
        ] = sum(
            1

            for connection
            in self_connections

            if connection["remote"]
        )


        self_metrics[
            "listening_socket_count"
        ] = sum(
            1

            for connection
            in self_connections

            if connection["status"]
            == "LISTEN"
        )

        self_metrics[
            "sample_duration_ms"
        ] = (
            (
                time.perf_counter()
                -
                sample_started
            )
            * 1000
        )

        self_metrics["collector_timings"] = (
            timings
        )

        sample = {
            "timestamp": datetime.now(timezone.utc),

            "cpu": {
                "percent": cpu["total_percent"],
                "per_cpu_percent": cpu["per_cpu_percent"],
                "physical_cores": cpu["physical_cores"],
                "logical_processors": cpu["logical_processors"],
            },

            "memory": {
                "percent":
                    memory["percent"],

                "total_bytes":
                    memory["total"],

                "used_bytes":
                    memory["used"],

                "available_bytes":
                    memory["available"],

                "free_bytes":
                    memory["free"],


                # This intentionally matches the
                # percentage calculation based on
                # total - available.
                "in_use_bytes":
                    max(
                        memory["total"]
                        - memory["available"],
                        0,
                    ),


                "pagefile": {
                    "total_bytes":
                        memory["pagefile"]["total"],

                    "used_bytes":
                        memory["pagefile"]["used"],

                    "free_bytes":
                        memory["pagefile"]["free"],

                    "percent":
                        memory["pagefile"]["percent"],
                },
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
                "download_bytes_per_second":
                    download_speed,

                "upload_bytes_per_second":
                    upload_speed,

                "interfaces":
                    interfaces,

                "connections":
                    connections,
            },

            "self_monitor": self_metrics,
        }

        self.previous_disk = disk
        self.previous_network = network
        self.previous_interface_counters = (
            current_interface_counters
        )

        return sample

    def _calculate_interface_rates(
        self,
        previous,
        current,
        elapsed_seconds,
    ):
        rates = {}


        if (
            previous is None
            or elapsed_seconds <= 0
        ):
            return rates


        for name, current_values in (
            current.items()
        ):

            previous_values = (
                previous.get(name)
            )


            if previous_values is None:
                continue


            received_delta = max(
                current_values[
                    "bytes_received"
                ]
                -
                previous_values[
                    "bytes_received"
                ],
                0,
            )


            sent_delta = max(
                current_values[
                    "bytes_sent"
                ]
                -
                previous_values[
                    "bytes_sent"
                ],
                0,
            )


            rates[name] = {
                "download_bytes_per_second":
                    (
                        received_delta
                        /
                        elapsed_seconds
                    ),

                "upload_bytes_per_second":
                    (
                        sent_delta
                        /
                        elapsed_seconds
                    ),
            }


        return rates