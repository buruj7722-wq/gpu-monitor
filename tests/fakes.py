"""Synthetic test-only pipeline. Never included in the installed service."""

import time

from monitor.history import HistoryStore
from monitor.models import GPU, GPUProcess, GPUReading, Snapshot, Source, SystemReading


class FakePipeline:
    def __init__(self, path):
        self.history = HistoryStore(path)
        self.calls = 0
        self.closed = False

    def sample(self):
        self.calls += 1
        snapshot = Snapshot(
            timestamp=time.time(),
            collector=Source(status="ok"),
            system=SystemReading(source=Source(status="ok")),
            gpu=GPUReading(
                source=Source(status="ok"),
                devices=[
                    GPU(
                        index=0,
                        uuid="GPU-0",
                        name="A40",
                        memory_used_bytes=1024**3,
                        memory_total_bytes=2 * 1024**3,
                    )
                ],
                processes=[
                    GPUProcess(
                        pid=1,
                        gpu_uuid="GPU-0",
                        process_type="compute",
                        gpu_memory_bytes=1024**2,
                        name="<script>unsafe</script>",
                    )
                ],
            ),
        )
        self.history.record(snapshot)
        return snapshot

    def close(self):
        self.closed = True
        self.history.close()
