import os
import time

import psutil


class SelfMonitorCollector:
    """
    Monitor the Python process running Sys Monitor.

    This collector has state because:
    - process CPU % needs a previous observation
    - process I/O throughput needs previous counters
    """

    def __init__(self):
        self.process = psutil.Process(
            os.getpid()
        )

        self.logical_processors = (
            psutil.cpu_count(
                logical=True
            )
            or 1
        )

        self.total_memory = (
            psutil.virtual_memory().total
        )

        self.previous_io = None


    def prime(self):
        """
        Establish baselines for CPU and I/O.
        """

        # Prime process CPU measurement.
        self.process.cpu_percent(
            interval=None
        )

        self.previous_io = (
            self._get_io_counters()
        )


    def collect(
        self,
        elapsed_seconds,
    ):
        """
        Collect the current overhead of the
        Sys Monitor Python process.
        """

        raw_cpu_percent = (
            self.process.cpu_percent(
                interval=None
            )
        )

        # psutil process CPU can exceed 100%
        # on multi-core systems.
        #
        # Divide by logical processors to get
        # an approximate whole-machine share,
        # similar to the normalised process CPU
        # values used elsewhere in Sys Monitor.
        cpu_percent = (
            raw_cpu_percent
            /
            self.logical_processors
        )


        memory_info = (
            self.process.memory_info()
        )

        memory_bytes = (
            memory_info.rss
        )

        memory_percent = (
            (
                memory_bytes
                /
                self.total_memory
            )
            * 100
        )


        current_io = (
            self._get_io_counters()
        )


        read_bytes_per_second = 0.0

        write_bytes_per_second = 0.0


        if (
            self.previous_io is not None
            and
            current_io is not None
            and
            elapsed_seconds > 0
        ):

            read_delta = max(
                current_io.read_bytes
                -
                self.previous_io.read_bytes,
                0,
            )

            write_delta = max(
                current_io.write_bytes
                -
                self.previous_io.write_bytes,
                0,
            )


            read_bytes_per_second = (
                read_delta
                /
                elapsed_seconds
            )

            write_bytes_per_second = (
                write_delta
                /
                elapsed_seconds
            )


        self.previous_io = (
            current_io
        )


        try:
            handle_count = (
                self.process.num_handles()
            )

        except (
            psutil.Error,
            AttributeError,
        ):
            handle_count = None


        try:
            thread_count = (
                self.process.num_threads()
            )

        except psutil.Error:
            thread_count = None


        try:
            child_count = len(
                self.process.children(
                    recursive=True
                )
            )

        except psutil.Error:
            child_count = 0


        uptime_seconds = max(
            time.time()
            -
            self.process.create_time(),
            0,
        )


        return {
            "pid":
                self.process.pid,

            "cpu_percent":
                cpu_percent,

            "raw_cpu_percent":
                raw_cpu_percent,

            "memory_bytes":
                memory_bytes,

            "memory_percent":
                memory_percent,

            "read_bytes_per_second":
                read_bytes_per_second,

            "write_bytes_per_second":
                write_bytes_per_second,

            "thread_count":
                thread_count,

            "handle_count":
                handle_count,

            "child_process_count":
                child_count,

            "uptime_seconds":
                uptime_seconds,
        }


    def _get_io_counters(self):
        try:
            return (
                self.process.io_counters()
            )

        except (
            psutil.Error,
            AttributeError,
        ):
            return None