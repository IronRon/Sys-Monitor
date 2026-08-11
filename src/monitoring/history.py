from collections import deque


class MonitorHistory:
    def __init__(self, max_samples=60):
        self.samples = deque(maxlen=max_samples)

    def add(self, sample):
        self.samples.append(sample)

    def get_all(self):
        return list(self.samples)

    def latest(self):
        if not self.samples:
            return None

        return self.samples[-1]

    def __len__(self):
        return len(self.samples)