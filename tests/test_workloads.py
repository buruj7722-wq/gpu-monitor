from types import SimpleNamespace as NS

import psutil

from monitor.collectors.gpu import GPUCollector
from monitor.collectors.workloads import ActivityAnalyzer, ProcessCollector
from monitor.config import Settings
from monitor.models import GPU, GPUReading, Source


class Proc:
    start = 10

    def create_time(self):
        return self.start

    def name(self):
        return '<img src=x onerror="alert(1)">'

    def memory_info(self):
        return NS(rss=1000)

    def cpu_percent(self):
        return 25


def test_process_identity_dedup_and_cpu():
    class NVML:
        def nvmlDeviceGetComputeRunningProcesses(self, h):
            return [NS(pid=7, usedGpuMemory=4096)]

        nvmlDeviceGetGraphicsRunningProcesses = nvmlDeviceGetComputeRunningProcesses

    g = GPUCollector(nvml=NVML())
    g.handles = {"GPU-0": 0}
    reading = GPUReading(source=Source(status="ok"), devices=[GPU(index=0, uuid="GPU-0")])
    processes = ProcessCollector(interval=5, provider=NS(Process=lambda pid: Proc()))
    first = processes.collect(reading, g, now=10, monotonic=0)
    assert len(first.processes) == 1
    assert first.processes[0].cpu_percent is None
    assert first.processes[0].gpu_util_percent is None
    assert first.processes[0].process_type == "compute+graphics"
    second = processes.collect(reading, g, now=15, monotonic=5)
    assert second.processes[0].cpu_percent == 25
    Proc.start = 20
    assert processes.collect(reading, g, now=20, monotonic=10).processes[0].cpu_percent is None
    Proc.start = 10


def test_process_access_denied():
    collector = ProcessCollector(
        provider=NS(Process=lambda pid: (_ for _ in ()).throw(psutil.AccessDenied(pid)))
    )
    from monitor.models import GPUProcess

    result = collector._enrich(GPUProcess(pid=1, gpu_uuid="GPU-x", process_type="compute"))
    assert result.ram_bytes is None
    assert result.errors["process"] == "AccessDenied"


def test_activity_does_not_count_gaps_as_idle():
    analyzer = ActivityAnalyzer(Settings())

    def reading(util):
        return GPUReading(
            devices=[GPU(index=0, uuid="GPU-0", gpu_util_percent=util, memory_used_bytes=1024)]
        )

    analyzer.analyze(reading(50), 0)
    analyzer.analyze(reading(50), 1)
    result = analyzer.analyze(reading(0), 10)[0]
    assert result.active_seconds == 1
    assert result.idle_seconds == 0
    assert result.coverage_percent == 10
    assert result.average_util_percent == 50
