"""Process metadata and bounded, sample-derived GPU activity analysis."""

import time
from collections import deque
from typing import Any

import psutil
from defusedxml import ElementTree

from monitor.collectors.gpu import GPUCollector, error_code
from monitor.config import Settings
from monitor.models import GPU, Activity, GPUProcess, GPUReading, Source
from monitor.normalization import number, text


class ProcessCollector:
    def __init__(self, interval: float = 5, provider: Any = psutil) -> None:
        self.interval = interval
        self.ps = provider
        self.next_sample = 0.0
        self.cached: list[GPUProcess] = []
        self.source = Source()
        self.processes: dict[int, tuple[float, Any]] = {}
        self.util_timestamps: dict[str, int] = {}

    def _enrich(self, row: GPUProcess) -> GPUProcess:
        errors = dict(row.errors)
        fields: dict[str, Any] = {}
        try:
            candidate = self.ps.Process(row.pid)
            created = candidate.create_time()
            previous = self.processes.get(row.pid)
            first = previous is None or previous[0] != created
            proc = previous[1] if previous is not None and not first else candidate
            self.processes[row.pid] = (created, proc)
            fields.update(
                start_time=created, name=proc.name()[:256], ram_bytes=proc.memory_info().rss
            )
            cpu = proc.cpu_percent()
            fields["cpu_percent"] = None if first else number(cpu)
        except (psutil.Error, OSError) as exc:
            errors["process"] = type(exc).__name__
        return row.model_copy(update={**fields, "errors": errors})

    def collect(
        self,
        gpu: GPUReading,
        collector: GPUCollector,
        now: float | None = None,
        monotonic: float | None = None,
    ) -> GPUReading:
        now = time.time() if now is None else now
        mono = time.monotonic() if monotonic is None else monotonic
        if not gpu.devices or gpu.source.status == "unavailable":
            self.cached = []
            self.processes.clear()
            return gpu.model_copy(
                update={
                    "processes": [],
                    "processes_source": Source(
                        status="unavailable", timestamp=now, error="gpu_unavailable"
                    ),
                }
            )
        if mono < self.next_sample:
            live = {d.uuid for d in gpu.devices if d.status != "unavailable"}
            return gpu.model_copy(
                update={
                    "processes": [p for p in self.cached if p.gpu_uuid in live],
                    "processes_source": self.source,
                }
            )
        self.next_sample = mono + self.interval
        rows: list[GPUProcess] = []
        errors = []
        for uuid, handle in collector.handles.items():
            merged: dict[int, tuple[set[str], int | None]] = {}
            for kind, fn in [
                ("compute", "nvmlDeviceGetComputeRunningProcesses"),
                ("graphics", "nvmlDeviceGetGraphicsRunningProcesses"),
            ]:
                try:
                    for p in getattr(collector.nvml, fn)(handle):
                        memory = number(p.usedGpuMemory, 2**63 - 1)
                        previous = merged.get(p.pid, (set(), None))
                        previous[0].add(kind)
                        mem = int(memory) if memory is not None else previous[1]
                        merged[p.pid] = (previous[0], mem)
                except Exception as exc:
                    errors.append(error_code(exc))
            usage: dict[int, float] = {}
            try:
                samples = collector.nvml.nvmlDeviceGetProcessUtilization(
                    handle, self.util_timestamps.get(uuid, 0)
                )
                for sample in sorted(samples, key=lambda s: s.timeStamp):
                    self.util_timestamps[uuid] = max(
                        self.util_timestamps.get(uuid, 0), sample.timeStamp
                    )
                    if 0 <= now * 1e6 - sample.timeStamp <= self.interval * 1e6 * 2:
                        value = number(sample.smUtil, 100)
                        if value is not None:
                            usage[sample.pid] = value
            except Exception:
                # Discard an incomplete optional utilization result; never apportion load.
                usage = {}
            for pid, (kinds, memory) in merged.items():
                rows.append(
                    GPUProcess(
                        pid=pid,
                        gpu_uuid=uuid,
                        process_type="+".join(sorted(kinds)),
                        gpu_memory_bytes=memory,
                        gpu_util_percent=usage.get(pid),
                        errors={}
                        if pid in usage
                        else {"gpu_util_percent": "not_supported_or_no_recent_sample"},
                    )
                )
        if not collector.handles and collector.fallback_xml:
            root = ElementTree.fromstring(collector.fallback_xml)
            for device in root.findall("gpu"):
                fallback_uuid = device.findtext("uuid")
                if not fallback_uuid:
                    continue
                for proc in device.findall("processes/process_info"):
                    fallback_pid = number(proc.findtext("pid"), 2**31 - 1)
                    raw_memory = proc.findtext("used_memory", "").split()
                    memory = number(raw_memory[0]) if raw_memory else None
                    if fallback_pid is not None:
                        rows.append(
                            GPUProcess(
                                pid=int(fallback_pid),
                                gpu_uuid=fallback_uuid,
                                name=text(proc.findtext("process_name")),
                                process_type=proc.findtext("type") or "unknown",
                                gpu_memory_bytes=int(memory * 1024**2)
                                if memory is not None
                                else None,
                                errors={"gpu_util_percent": "not_supported"},
                            )
                        )
        self.cached = [self._enrich(row) for row in rows]
        self.processes = {
            pid: p for pid, p in self.processes.items() if pid in {r.pid for r in rows}
        }
        self.util_timestamps = {
            k: v for k, v in self.util_timestamps.items() if k in {d.uuid for d in gpu.devices}
        }
        self.source = Source(
            status="degraded" if errors else "ok",
            timestamp=now,
            last_success=now if not errors else self.source.last_success,
            error="process_queries_partial" if errors else None,
        )
        return gpu.model_copy(update={"processes": self.cached, "processes_source": self.source})


class ActivityAnalyzer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.samples: dict[str, deque[tuple[float, GPU]]] = {}
        self.started: float | None = None

    def analyze(self, reading: GPUReading, monotonic: float | None = None) -> list[Activity]:
        mono = time.monotonic() if monotonic is None else monotonic
        if self.started is None:
            self.started = mono
        cutoff = mono - self.settings.activity_window_seconds
        for uuid in list(self.samples):
            queue = self.samples[uuid]
            while queue and queue[0][0] < cutoff:
                queue.popleft()
            if not queue:
                del self.samples[uuid]
        result = []
        for gpu in reading.devices:
            queue = self.samples.setdefault(
                gpu.uuid,
                deque(
                    maxlen=int(self.settings.activity_window_seconds / self.settings.sample_seconds)
                    + 2
                ),
            )
            queue.append((mono, gpu))
            covered = active = weighted = power_sum = power_time = 0.0
            util, temperatures = [], []
            for (before, old), (after, current) in zip(queue, list(queue)[1:], strict=False):
                dt = after - before
                if (
                    dt <= 0
                    or dt > self.settings.sample_seconds * 1.5
                    or old.gpu_util_percent is None
                    or current.gpu_util_percent is None
                ):
                    continue
                covered += dt
                weighted += old.gpu_util_percent * dt
                util.append(old.gpu_util_percent)
                if old.gpu_util_percent >= self.settings.activity_threshold:
                    active += dt
                if old.power_w is not None:
                    power_sum += old.power_w * dt
                    power_time += dt
            if gpu.gpu_util_percent is not None:
                util.append(gpu.gpu_util_percent)
            temperatures = [g.temperature_c for _, g in queue if g.temperature_c is not None]
            memory = [(t, g.memory_used_bytes) for t, g in queue if g.memory_used_bytes is not None]
            change = memory[-1][1] - memory[0][1] if len(memory) >= 2 else None
            duration = memory[-1][0] - memory[0][0] if len(memory) >= 2 else 0
            pressure = (
                gpu.vram_percent is not None
                and gpu.vram_percent >= self.settings.alerts.vram.warning
            )
            patterns = []
            if any("thermal" in r or r == "hardware_slowdown" for r in gpu.throttle_reasons or []):
                patterns.append("hardware_throttling")
            if pressure:
                patterns.append("memory_pressure")
            if change is not None and change > 256 * 1024**2:
                patterns.append("vram_growth_observed")
            window = min(self.settings.activity_window_seconds, max(0, mono - self.started))
            result.append(
                Activity(
                    gpu_uuid=gpu.uuid,
                    window_seconds=window,
                    coverage_percent=min(100, covered / window * 100) if window else 0,
                    active_seconds=active,
                    idle_seconds=max(0, covered - active),
                    average_util_percent=weighted / covered if covered else None,
                    peak_util_percent=max(util) if util else None,
                    average_power_w=power_sum / power_time if power_time else None,
                    peak_temperature_c=max(temperatures) if temperatures else None,
                    vram_change_bytes=change,
                    vram_growth_bytes_per_second=change / duration
                    if change is not None and duration > 0
                    else None,
                    process_count=len({p.pid for p in reading.processes if p.gpu_uuid == gpu.uuid}),
                    memory_pressure=pressure,
                    patterns=patterns,
                )
            )
        return result
