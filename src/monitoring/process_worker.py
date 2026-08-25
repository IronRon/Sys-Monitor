import copy
import threading
import time

from collectors.processes import (
    get_processes,
    get_top_cpu_processes,
    get_top_memory_processes,
    prime_process_cpu,
)


class ProcessSnapshotWorker:
    """
    Collect process information independently from
    the main SystemSampler.

    Process enumeration is relatively expensive on
    Windows, so running it in a separate worker keeps
    the one-second system sampler responsive.
    """

    def __init__(
        self,
        refresh_interval=2.0,
    ):

        self.refresh_interval = (
            refresh_interval
        )


        self._lock = (
            threading.RLock()
        )

        self._stop_event = (
            threading.Event()
        )

        self._ready_event = (
            threading.Event()
        )

        self._thread = None

        self._started = False


        self._processes = []

        self._top_cpu = []

        self._top_memory = []

        self._collection_duration_ms = (
            None
        )

        self._timestamp = None

        self._error = None


    def start(self):

        with self._lock:

            if self._started:
                return


            prime_process_cpu()


            self._stop_event.clear()

            self._ready_event.clear()

            self._started = True


            self._thread = (
                threading.Thread(
                    target=self._run,
                    name=(
                        "process-snapshot-worker"
                    ),
                    daemon=True,
                )
            )


            self._thread.start()


    def stop(self):

        with self._lock:

            if not self._started:
                return


            thread = self._thread

            self._stop_event.set()


        if (
            thread is not None
            and
            thread
            is not threading.current_thread()
        ):

            thread.join(
                timeout=3
            )


        with self._lock:

            self._started = False

            self._thread = None


    def _run(self):

        # Give the initial cpu_percent()
        # baseline time to become meaningful.
        if self._stop_event.wait(
            self.refresh_interval
        ):
            return


        while not self._stop_event.is_set():

            cycle_started = (
                time.monotonic()
            )


            try:

                collection_started = (
                    time.perf_counter()
                )


                processes = (
                    get_processes()
                )


                duration_ms = (
                    (
                        time.perf_counter()
                        -
                        collection_started
                    )
                    * 1000
                )


                top_cpu = (
                    get_top_cpu_processes(
                        processes
                    )
                )


                top_memory = (
                    get_top_memory_processes(
                        processes
                    )
                )


                with self._lock:

                    self._processes = (
                        processes
                    )

                    self._top_cpu = (
                        top_cpu
                    )

                    self._top_memory = (
                        top_memory
                    )

                    self._collection_duration_ms = (
                        duration_ms
                    )

                    self._timestamp = (
                        time.time()
                    )

                    self._error = None

                    self._ready_event.set()


            except Exception as error:

                with self._lock:

                    self._error = error


            elapsed = (
                time.monotonic()
                -
                cycle_started
            )


            remaining = max(
                self.refresh_interval
                -
                elapsed,
                0,
            )


            if self._stop_event.wait(
                remaining
            ):
                break


    def get_snapshot(self):

        with self._lock:

            return {
                "processes":
                    copy.deepcopy(
                        self._processes
                    ),

                "top_cpu":
                    copy.deepcopy(
                        self._top_cpu
                    ),

                "top_memory":
                    copy.deepcopy(
                        self._top_memory
                    ),

                "collection_duration_ms":
                    self._collection_duration_ms,

                "ready":
                    self._ready_event.is_set(),

                "error":
                    self._error,
            }