import threading
import time

from monitoring.history import MonitorHistory
from monitoring.sampler import SystemSampler


class MonitoringService:
    def __init__(self):
        self.sampler = SystemSampler()
        self.history = MonitorHistory(max_samples=60)

        self.is_primed = False
        self.previous_time = None

        self.lock = threading.Lock()

    def _prime(self):
        self.sampler.prime()

        self.previous_time = time.perf_counter()
        self.is_primed = True

    def get_system_data(self):
        with self.lock:
            if not self.is_primed:
                self._prime()

                # Give CPU/process counters time to accumulate
                # before taking the first displayed reading.
                time.sleep(1)

            current_time = time.perf_counter()

            elapsed_seconds = (
                current_time - self.previous_time
            )

            sample = self.sampler.sample(
                elapsed_seconds=elapsed_seconds
            )

            self.previous_time = current_time

            self.history.add(sample)

            return self._serialize(
                sample,
                self.history.get_all(),
            )

    def _serialize(self, sample, history):
        return {
            "timestamp": sample["timestamp"].isoformat(),

            "cpu": sample["cpu"],

            "memory": sample["memory"],

            "disk": sample["disk"],

            "network": sample["network"],

            "processes": sample["processes"],

            "history": [
                {
                    "timestamp": item["timestamp"].isoformat(),
                    "cpu_percent": item["cpu"]["percent"],
                }
                for item in history
            ],
        }


monitoring_service = MonitoringService()