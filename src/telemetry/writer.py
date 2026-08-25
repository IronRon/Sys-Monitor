import logging
import socket
import time

from django.db import (
    DatabaseError,
    close_old_connections,
    transaction,
)

from .models import (
    Device,
    MonitorOverheadSample,
    SystemMetricSample,
)


logger = logging.getLogger(__name__)


class TelemetryWriter:
    """
    Persist selected monitoring samples to PostgreSQL.

    SystemSampler can continue running every second,
    while this writer stores a sample less frequently.
    """

    def __init__(
        self,
        write_interval_seconds=5.0,
        device_key="desktop-pc",
        device_name="Desktop PC",
    ):
        self.write_interval_seconds = (
            write_interval_seconds
        )

        self.device_key = device_key
        self.device_name = device_name

        self._last_write_time = None
        self._device = None


    def write_if_due(self, sample):
        """
        Write the sample when the configured interval
        has elapsed.

        The first supplied sample is written immediately.
        Later samples are written about every 5 seconds.
        """

        now = time.monotonic()


        if (
            self._last_write_time is not None
            and
            (
                now
                -
                self._last_write_time
            )
            < self.write_interval_seconds
        ):
            return False


        try:
            self._write_sample(
                sample
            )

        except DatabaseError:

            logger.exception(
                "Unable to write telemetry "
                "sample to PostgreSQL."
            )

            return False


        self._last_write_time = now

        return True


    def _write_sample(
        self,
        sample,
    ):
        """
        Convert one SystemSampler sample into:

        - SystemMetricSample
        - MonitorOverheadSample
        """

        close_old_connections()


        try:

            device = (
                self._get_device()
            )


            processes = (
                sample.get(
                    "processes"
                )
                or {}
            )


            top_cpu = (
                self._first_item(
                    processes.get(
                        "top_cpu"
                    )
                )
            )


            top_memory = (
                self._first_item(
                    processes.get(
                        "top_memory"
                    )
                )
            )


            memory = (
                sample.get(
                    "memory"
                )
                or {}
            )


            pagefile = (
                memory.get(
                    "pagefile"
                )
                or {}
            )


            disk = (
                sample.get(
                    "disk"
                )
                or {}
            )


            network = (
                sample.get(
                    "network"
                )
                or {}
            )


            self_monitor = (
                sample.get(
                    "self_monitor"
                )
                or {}
            )


            with transaction.atomic():

                SystemMetricSample.objects.create(

                    device=
                        device,

                    timestamp=
                        sample["timestamp"],


                    # CPU

                    cpu_percent=
                        sample["cpu"][
                            "percent"
                        ],


                    # Memory

                    memory_percent=
                        memory[
                            "percent"
                        ],

                    memory_in_use_bytes=
                        memory[
                            "in_use_bytes"
                        ],

                    memory_available_bytes=
                        memory[
                            "available_bytes"
                        ],

                    pagefile_percent=
                        pagefile.get(
                            "percent"
                        ),


                    # Disk

                    disk_percent=
                        disk.get(
                            "percent"
                        ),

                    disk_used_bytes=
                        disk.get(
                            "used_bytes"
                        ),

                    disk_free_bytes=
                        disk.get(
                            "free_bytes"
                        ),

                    disk_read_bytes_per_second=
                        disk.get(
                            "read_bytes_per_second"
                        ),

                    disk_write_bytes_per_second=
                        disk.get(
                            "write_bytes_per_second"
                        ),


                    # Network

                    network_download_bytes_per_second=
                        network.get(
                            "download_bytes_per_second"
                        ),

                    network_upload_bytes_per_second=
                        network.get(
                            "upload_bytes_per_second"
                        ),


                    # Processes

                    process_count=
                        processes.get(
                            "count"
                        ),


                    top_cpu_process_pid=
                        (
                            top_cpu.get(
                                "pid"
                            )
                            if top_cpu
                            else None
                        ),

                    top_cpu_process_name=
                        (
                            top_cpu.get(
                                "name"
                            )
                            if top_cpu
                            else ""
                        ),

                    top_cpu_process_percent=
                        (
                            top_cpu.get(
                                "cpu_percent"
                            )
                            if top_cpu
                            else None
                        ),


                    top_memory_process_pid=
                        (
                            top_memory.get(
                                "pid"
                            )
                            if top_memory
                            else None
                        ),

                    top_memory_process_name=
                        (
                            top_memory.get(
                                "name"
                            )
                            if top_memory
                            else ""
                        ),

                    top_memory_process_bytes=
                        (
                            top_memory.get(
                                "memory_bytes"
                            )
                            if top_memory
                            else None
                        ),
                )


                MonitorOverheadSample.objects.create(

                    host_device=
                        device,

                    timestamp=
                        sample["timestamp"],

                    backend_pid=
                        self_monitor.get(
                            "pid"
                        ),

                    cpu_percent=
                        self_monitor.get(
                            "cpu_percent",
                            0.0,
                        ),

                    memory_bytes=
                        self_monitor.get(
                            "memory_bytes",
                            0,
                        ),

                    memory_percent=
                        self_monitor.get(
                            "memory_percent",
                            0.0,
                        ),

                    read_bytes_per_second=
                        self_monitor.get(
                            "read_bytes_per_second"
                        ),

                    write_bytes_per_second=
                        self_monitor.get(
                            "write_bytes_per_second"
                        ),

                    sample_duration_ms=
                        self_monitor.get(
                            "sample_duration_ms",
                            0.0,
                        ),

                    thread_count=
                        self_monitor.get(
                            "thread_count"
                        ),

                    handle_count=
                        self_monitor.get(
                            "handle_count"
                        ),

                    network_socket_count=
                        self_monitor.get(
                            "network_socket_count"
                        ),
                )


                # This tells us the last time this
                # device successfully produced stored
                # telemetry.
                Device.objects.filter(
                    pk=device.pk
                ).update(
                    last_seen_at=
                        sample["timestamp"]
                )


        finally:

            close_old_connections()


    def _get_device(self):
        """
        Resolve the monitored PC once and cache
        the Django model instance.
        """

        if self._device is not None:
            return self._device


        device, _ = (
            Device.objects.get_or_create(

                key=
                    self.device_key,

                defaults={
                    "name":
                        self.device_name,

                    "device_type":
                        Device.DeviceType.WINDOWS,

                    "hostname":
                        socket.gethostname(),
                },
            )
        )


        self._device = device

        return device


    @staticmethod
    def _first_item(items):

        if not items:
            return None

        return items[0]