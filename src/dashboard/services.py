import atexit
import copy
import threading
import time

from monitoring.history import MonitorHistory
from monitoring.sampler import SystemSampler
from monitoring.process_worker import (
    ProcessSnapshotWorker,
)

from collectors.hardware import (
    get_hardware_info,
)

from hardware.normalizer import (
    normalize_hardware,
)

from hardware.explanations import (
    explain_cpu,
    explain_memory,
    explain_disk,
)

import socket

from concurrent.futures import (
    ThreadPoolExecutor,
)

import logging

from telemetry.writer import (
    TelemetryWriter,
)

logger = logging.getLogger(
    __name__
)

class HostnameResolver:

    def __init__(self):
        self._cache = {}

        self._pending = set()

        self._lock = (
            threading.Lock()
        )

        self._executor = (
            ThreadPoolExecutor(
                max_workers=4,
                thread_name_prefix=(
                    "dns-resolver"
                ),
            )
        )


    def get(self, ip):
        if not ip:
            return None


        with self._lock:

            if ip in self._cache:
                return self._cache[ip]


            if ip not in self._pending:

                self._pending.add(ip)

                self._executor.submit(
                    self._resolve,
                    ip,
                )


        return None


    def _resolve(self, ip):

        try:

            hostname = (
                socket.gethostbyaddr(
                    ip
                )[0]
            )

        except (
            socket.herror,
            socket.gaierror,
            OSError,
        ):
            hostname = None


        with self._lock:

            self._cache[ip] = (
                hostname
            )

            self._pending.discard(
                ip
            )


    def stop(self):

        self._executor.shutdown(
            wait=False,
            cancel_futures=True,
        )


class HardwareService:

    def __init__(self):
        self._hardware = None


    def refresh(self):
        raw = get_hardware_info()

        hardware = normalize_hardware(raw)


        explanations = {

            "cpu":
                explain_cpu(
                    hardware["cpu"]
                ),

            "memory":
                explain_memory(
                    hardware["memory"]
                ),

            "disks": [
                {
                    "disk_index": index,
                    "name": disk["name"],
                    "items": explain_disk(disk),
                }

                for index, disk
                in enumerate(hardware["disks"])
            ],
        }


        self._hardware = {
            "hardware":
                hardware,

            "explanations":
                explanations,
        }


        return self._hardware


    def get_hardware_data(self):

        if self._hardware is None:

            return self.refresh()


        return self._hardware


hardware_service = HardwareService()


class BackgroundMonitoringService:

    def __init__(
        self,
        sample_interval=1.0,
        history_size=60,
        process_refresh_interval=3.0,
    ):
        self.sample_interval = sample_interval

        # Fast system metrics:
        # CPU, RAM, disk/network counters, interfaces,
        # cached sockets and Sys Monitor self-overhead.
        self.sampler = SystemSampler()

        # Process enumeration is relatively expensive on
        # Windows, so it runs independently from the main
        # one-second sampler.
        self.process_worker = (
            ProcessSnapshotWorker(
                refresh_interval=
                    process_refresh_interval
            )
        )

        self.history = MonitorHistory(
            max_samples=history_size
        )

        self.telemetry_writer = (
            TelemetryWriter(
                write_interval_seconds=5.0
            )
        )

        self.latest_sample = None
        self.latest_error = None

        self._started = False

        self._thread = None

        self._stop_event = threading.Event()

        self._ready_event = threading.Event()

        self._lock = threading.RLock()


    def start(self):
        """
        Start background monitoring.

        Calling this more than once is safe.

        The process worker owns process CPU priming and
        process enumeration. SystemSampler owns the fast
        system-level baselines.
        """

        with self._lock:

            if self._started:
                return

            self._stop_event.clear()

            self._ready_event.clear()

            self.latest_error = None


            try:

                # Start process monitoring separately so its
                # expensive enumeration does not block the
                # one-second system sampler.
                self.process_worker.start()

                # Establish CPU, disk, network and self-monitor
                # baselines for the fast sampler.
                self.sampler.prime()

            except Exception:

                # If startup fails after the worker starts,
                # make sure we do not leave an orphan worker
                # thread running.
                self.process_worker.stop()

                raise


            self._started = True


            self._thread = threading.Thread(
                target=self._run,
                name="sys-monitor-sampler",
                daemon=True,
            )

            self._thread.start()


    def stop(self):
        """
        Ask both monitoring workers to stop cleanly.
        """

        with self._lock:

            if not self._started:
                return

            thread = self._thread

            self._stop_event.set()


        if (
            thread is not None
            and
            thread is not threading.current_thread()
        ):
            thread.join(timeout=3)


        # Process monitoring has its own worker thread.
        self.process_worker.stop()


        with self._lock:

            self._started = False

            self._thread = None


    def _run(self):
        """
        Main fast sampling loop.

        The target is approximately one sample start per
        sample_interval. Work time is subtracted from the
        next wait rather than added on top of the interval.

        Process information is read from the independent
        ProcessSnapshotWorker cache.
        """

        previous_time = time.perf_counter()


        # Give the primed cumulative counters a real time
        # window before taking the first rate-based sample.
        if self._stop_event.wait(
            self.sample_interval
        ):
            return


        while not self._stop_event.is_set():

            cycle_started = time.perf_counter()

            elapsed_seconds = (
                cycle_started
                -
                previous_time
            )

            previous_time = cycle_started

            sample = None


            try:

                process_snapshot = (
                    self.process_worker
                    .get_snapshot()
                )


                sample = self.sampler.sample(
                    elapsed_seconds=
                        elapsed_seconds,

                    processes=
                        process_snapshot[
                            "processes"
                        ],
                )


                # Keep the public/internal sample contract the
                # same as before even though the data now comes
                # from a separate worker.
                sample["processes"] = {
                    "count":
                        len(
                            process_snapshot[
                                "processes"
                            ]
                        ),

                    "top_cpu":
                        process_snapshot[
                            "top_cpu"
                        ],

                    "top_memory":
                        process_snapshot[
                            "top_memory"
                        ],

                    "items":
                        process_snapshot[
                            "processes"
                        ],

                    "collection_duration_ms":
                        process_snapshot[
                            "collection_duration_ms"
                        ],

                    "ready":
                        process_snapshot[
                            "ready"
                        ],
                }


                # Expose the slow worker timing separately from
                # SystemSampler.sample_duration_ms.
                sample["self_monitor"][
                    "process_collection_duration_ms"
                ] = (
                    process_snapshot[
                        "collection_duration_ms"
                    ]
                )

                sample["self_monitor"][
                    "process_snapshot_ready"
                ] = (
                    process_snapshot[
                        "ready"
                    ]
                )


                history_sample = (
                    self._create_history_sample(
                        sample
                    )
                )


                with self._lock:

                    self.latest_sample = sample

                    self.history.add(
                        history_sample
                    )

                    self.latest_error = None

                    self._ready_event.set()


            except Exception as error:

                with self._lock:

                    self.latest_error = error

                logger.exception(
                    "Background monitoring "
                    "sample failed."
                )


            # Persistence is intentionally isolated from live
            # monitoring. A PostgreSQL problem must not stop
            # the dashboard from receiving new live samples.
            if sample is not None:

                try:

                    self.telemetry_writer.write_if_due(
                        sample
                    )

                except Exception:

                    logger.exception(
                        "Telemetry persistence failed. "
                        "Live monitoring will continue."
                    )


            # Fixed-rate-ish scheduling:
            #
            # target interval = 1.0 s
            # sample work     = 0.05 s
            # remaining wait  = 0.95 s
            #
            # This avoids the old behaviour where a 1 second
            # wait was added after the collection duration.
            work_seconds = (
                time.perf_counter()
                -
                cycle_started
            )

            remaining_seconds = max(
                self.sample_interval
                -
                work_seconds,
                0.0,
            )


            if self._stop_event.wait(
                remaining_seconds
            ):
                break


    def _create_history_sample(
        self,
        sample,
    ):
        """
        Create a smaller sample for the rolling
        history.

        We deliberately do not keep the complete
        process list or socket list in every history entry.
        """

        return {
            "timestamp": sample["timestamp"],

            "cpu": copy.deepcopy(
                sample["cpu"]
            ),

            "memory": copy.deepcopy(
                sample["memory"]
            ),

            "disk": copy.deepcopy(
                sample["disk"]
            ),

            "network": {
                "download_bytes_per_second":
                    sample["network"][
                        "download_bytes_per_second"
                    ],

                "upload_bytes_per_second":
                    sample["network"][
                        "upload_bytes_per_second"
                    ],
            },

            "processes": {
                "count":
                    sample["processes"][
                        "count"
                    ],

                "ready":
                    sample["processes"].get(
                        "ready",
                        False,
                    ),
            },

            "self_monitor": {
                "cpu_percent":
                    sample[
                        "self_monitor"
                    ]["cpu_percent"],

                "memory_bytes":
                    sample[
                        "self_monitor"
                    ]["memory_bytes"],

                "read_bytes_per_second":
                    sample[
                        "self_monitor"
                    ][
                        "read_bytes_per_second"
                    ],

                "write_bytes_per_second":
                    sample[
                        "self_monitor"
                    ][
                        "write_bytes_per_second"
                    ],

                "sample_duration_ms":
                    sample[
                        "self_monitor"
                    ]["sample_duration_ms"],

                "process_collection_duration_ms":
                    sample[
                        "self_monitor"
                    ].get(
                        "process_collection_duration_ms"
                    ),
            },
        }


    def _get_snapshot(self):
        """
        Return copies of the latest sample and
        history.

        If monitoring has not started yet,
        start it.

        The fast system sampler does not wait for the
        slower process worker to produce its first snapshot.
        """

        self.start()


        if not self._ready_event.wait(
            timeout=10.0
        ):

            with self._lock:

                error = self.latest_error


            if error is not None:

                raise RuntimeError(
                    "Background monitoring "
                    "failed to produce a sample."
                ) from error


            raise RuntimeError(
                "Background monitoring has not "
                "produced its first sample yet."
            )


        with self._lock:

            sample = copy.deepcopy(
                self.latest_sample
            )

            history = copy.deepcopy(
                self.history.get_all()
            )


        return sample, history


    def get_system_data(self):
        """
        Data used by /api/system/.
        """

        sample, history = (
            self._get_snapshot()
        )


        return {
            "timestamp":
                sample["timestamp"].isoformat(),

            "cpu":
                sample["cpu"],

            "memory":
                sample["memory"],

            "disk":
                sample["disk"],

            "network":
                sample["network"],

            "processes": {
                "count":
                    sample["processes"][
                        "count"
                    ],

                "top_cpu":
                    sample["processes"][
                        "top_cpu"
                    ],

                "top_memory":
                    sample["processes"][
                        "top_memory"
                    ],

                "ready":
                    sample["processes"].get(
                        "ready",
                        False,
                    ),
            },

            "history": [
                {
                    "timestamp":
                        item[
                            "timestamp"
                        ].isoformat(),

                    "cpu_percent":
                        item[
                            "cpu"
                        ]["percent"],
                }

                for item in history
            ],
        }


    def get_process_data(self):
        """
        Data used by /api/processes/.

        The process list is a cached snapshot produced by
        ProcessSnapshotWorker, not a new process enumeration
        triggered by this API request.
        """

        sample, _ = (
            self._get_snapshot()
        )


        return {
            "timestamp":
                sample["timestamp"]
                .isoformat(),

            "count":
                sample["processes"][
                    "count"
                ],

            "ready":
                sample["processes"].get(
                    "ready",
                    False,
                ),

            "collection_duration_ms":
                sample["processes"].get(
                    "collection_duration_ms"
                ),

            "processes":
                sample["processes"][
                    "items"
                ],
        }


    def get_memory_data(self):
        """
        Data used by /api/memory/.

        No new system or process collection happens here.
        We only read the latest background snapshots.
        """

        sample, history = (
            self._get_snapshot()
        )


        processes = (
            sample["processes"][
                "items"
            ]
        )


        top_memory = sorted(
            processes,
            key=lambda process:
                process.get(
                    "memory_bytes"
                ) or 0,
            reverse=True,
        )[:10]


        return {
            "timestamp":
                sample["timestamp"]
                .isoformat(),

            "memory":
                sample["memory"],

            "top_processes":
                top_memory,

            "processes_ready":
                sample["processes"].get(
                    "ready",
                    False,
                ),

            "history": [
                {
                    "timestamp":
                        item["timestamp"]
                        .isoformat(),

                    "percent":
                        item["memory"][
                            "percent"
                        ],

                    "in_use_bytes":
                        item["memory"][
                            "in_use_bytes"
                        ],

                    "available_bytes":
                        item["memory"][
                            "available_bytes"
                        ],

                    "pagefile_percent":
                        item["memory"][
                            "pagefile"
                        ]["percent"],
                }

                for item in history
            ],
        }


    def get_disk_data(self):
        """
        Data used by /api/disk/.

        This does not collect new disk information.
        It reads the latest background sample.
        """

        sample, history = (
            self._get_snapshot()
        )


        return {
            "timestamp":
                sample["timestamp"]
                .isoformat(),

            "disk":
                sample["disk"],

            "history": [
                {
                    "timestamp":
                        item["timestamp"]
                        .isoformat(),

                    "percent":
                        item["disk"][
                            "percent"
                        ],

                    "used_bytes":
                        item["disk"][
                            "used_bytes"
                        ],

                    "free_bytes":
                        item["disk"][
                            "free_bytes"
                        ],

                    "read_bytes_per_second":
                        item["disk"][
                            "read_bytes_per_second"
                        ],

                    "write_bytes_per_second":
                        item["disk"][
                            "write_bytes_per_second"
                        ],
                }

                for item in history
            ],
        }


    def get_network_data(self):

        sample, history = (
            self._get_snapshot()
        )


        connections = (
            copy.deepcopy(
                sample["network"][
                    "connections"
                ]
            )
        )


        established = 0
        listening = 0
        remote_count = 0


        for connection in connections:

            remote = (
                connection[
                    "remote"
                ]
            )


            if remote:

                remote_count += 1

                connection["hostname"] = (
                    hostname_resolver.get(
                        remote["ip"]
                    )
                )

            else:

                connection["hostname"] = (
                    None
                )


            if (
                connection["status"]
                == "ESTABLISHED"
            ):
                established += 1


            if (
                connection["status"]
                == "LISTEN"
            ):
                listening += 1


        interfaces = (
            sample["network"][
                "interfaces"
            ]
        )


        return {
            "timestamp":
                sample["timestamp"]
                .isoformat(),


            "network": {
                "download_bytes_per_second":
                    sample["network"][
                        "download_bytes_per_second"
                    ],

                "upload_bytes_per_second":
                    sample["network"][
                        "upload_bytes_per_second"
                    ],

                "interfaces":
                    interfaces,

                "connections":
                    connections,

                "summary": {
                    "total_sockets":
                        len(connections),

                    "remote_connections":
                        remote_count,

                    "established":
                        established,

                    "listening":
                        listening,

                    "interfaces_up":
                        sum(
                            1

                            for interface
                            in interfaces

                            if interface[
                                "is_up"
                            ]
                        ),
                },
            },


            "history": [
                {
                    "timestamp":
                        item["timestamp"]
                        .isoformat(),

                    "download_bytes_per_second":
                        item["network"][
                            "download_bytes_per_second"
                        ],

                    "upload_bytes_per_second":
                        item["network"][
                            "upload_bytes_per_second"
                        ],
                }

                for item in history
            ],
        }


    def get_self_data(self):
        """
        Return the overhead of the Sys Monitor
        backend itself.

        No new psutil collection happens here.
        """

        sample, history = (
            self._get_snapshot()
        )


        return {
            "timestamp":
                sample["timestamp"]
                .isoformat(),

            "overhead":
                sample[
                    "self_monitor"
                ],

            "system": {
                "cpu_percent":
                    sample["cpu"][
                        "percent"
                    ],

                "total_memory_bytes":
                    sample["memory"][
                        "total_bytes"
                    ],
            },

            "history": [
                {
                    "timestamp":
                        item[
                            "timestamp"
                        ].isoformat(),

                    "cpu_percent":
                        item[
                            "self_monitor"
                        ][
                            "cpu_percent"
                        ],

                    "memory_bytes":
                        item[
                            "self_monitor"
                        ][
                            "memory_bytes"
                        ],

                    "sample_duration_ms":
                        item[
                            "self_monitor"
                        ][
                            "sample_duration_ms"
                        ],

                    "process_collection_duration_ms":
                        item[
                            "self_monitor"
                        ].get(
                            "process_collection_duration_ms"
                        ),
                }

                for item in history

                if (
                    "self_monitor"
                    in item
                )
            ],
        }


hostname_resolver = (
    HostnameResolver()
)

monitoring_service = BackgroundMonitoringService(
    sample_interval=1.0,
    history_size=60,
)


# Try to stop cleanly when Python exits.
atexit.register(
    monitoring_service.stop
)

atexit.register(
    hostname_resolver.stop
)