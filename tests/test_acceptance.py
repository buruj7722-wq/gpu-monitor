import asyncio
import time
from types import SimpleNamespace as NS

import pynvml
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from monitor.api import create_app
from monitor.collectors.gpu import GPUCollector
from monitor.collectors.workloads import ProcessCollector
from monitor.config import Settings
from monitor.history import HistoryStore
from monitor.models import GPU, GPUReading, Snapshot, Source
from monitor.runtime import Runtime
from tests.fakes import FakePipeline
from tests.test_gpu import FakeNVML
from tests.test_workloads import Proc


def test_lost_gpu_closes_and_recovers():
    class Lost(FakeNVML):
        lost = True

        def nvmlDeviceGetMemoryInfo(self, handle):
            if self.lost:
                raise pynvml.NVMLError_GpuIsLost()
            return NS(used=1, free=3, total=4)

    nvml = Lost()
    collector = GPUCollector(nvml=nvml, fallback=False)
    assert collector.collect(now=0, monotonic=0).source.status == "degraded"
    assert nvml.shutdowns == 1
    nvml.lost = False
    assert collector.collect(now=2, monotonic=2).devices[0].memory_used_bytes == 1
    collector.close()


def test_invalid_sensor_numbers_are_null():
    class Invalid(FakeNVML):
        def nvmlDeviceGetFanSpeed(self, handle):
            return float("nan")

        def nvmlDeviceGetUtilizationRates(self, handle):
            return NS(gpu=200, memory=-1)

    gpu = GPUCollector(nvml=Invalid(), fallback=False).collect().devices[0]
    assert gpu.fan_percent is None and gpu.gpu_util_percent is None
    assert gpu.errors["fan_percent"] == "invalid_value"
    assert gpu.errors["gpu_util_percent"] == "invalid_value"


def test_same_process_on_two_gpus_sampled_once():
    class NVML:
        def nvmlDeviceGetComputeRunningProcesses(self, handle):
            return [NS(pid=7, usedGpuMemory=1024)]

        def nvmlDeviceGetGraphicsRunningProcesses(self, handle):
            return []

    collector = GPUCollector(nvml=NVML())
    collector.handles = {"GPU-0": 0, "GPU-1": 1}
    reading = GPUReading(
        source=Source(status="ok"), devices=[GPU(index=i, uuid=f"GPU-{i}") for i in range(2)]
    )
    processes = ProcessCollector(provider=NS(Process=lambda pid: Proc()))
    result = processes.collect(reading, collector, now=10, monotonic=0)
    assert len(result.processes) == 2
    assert all(p.cpu_percent is None for p in result.processes)
    result = processes.collect(reading, collector, now=15, monotonic=5)
    assert all(p.cpu_percent == 25 for p in result.processes)


def test_database_write_failure_keeps_live_history(tmp_path):
    store = HistoryStore(tmp_path / "h.db")
    store.record(Snapshot(timestamp=120))
    store.connection.execute("PRAGMA query_only=ON")
    # A metric makes the next completed minute perform a real write.
    from monitor.models import CPU, SystemReading

    store.record(Snapshot(timestamp=121, system=SystemReading(cpu=CPU(usage_percent=20))))
    store.record(Snapshot(timestamp=180))
    assert store.source.status == "unavailable"
    assert store.query("5m", now=181).points


async def test_sampler_failure_recovers_and_closes():
    calls = 0

    def sample():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("test-only failure")
        return Snapshot(timestamp=time.time())

    runtime = Runtime(Settings(sample_seconds=0.1), sample)
    await runtime.start()
    for _ in range(20):
        if runtime.latest:
            break
        await asyncio.sleep(0.02)
    assert runtime.latest is not None
    assert runtime.errors >= 1
    await runtime.stop()


def test_websocket_limit_and_cached_api(tmp_path):
    pipeline = FakePipeline(tmp_path / "h.db")
    app = create_app(Settings(max_connections=1, allowed_hosts=["testserver"]), pipeline)
    with TestClient(app) as client:
        with client.websocket_connect("/ws/metrics") as websocket:
            websocket.receive_json()
            before = pipeline.calls
            for _ in range(20):
                assert client.get("/api/metrics").status_code == 200
            assert pipeline.calls <= before + 1
            with pytest.raises(WebSocketDisconnect) as exc:
                with client.websocket_connect("/ws/metrics"):
                    pass
            assert exc.value.code == 1013


def test_logs_do_not_include_exception_payload(tmp_path, caplog):
    import httpx

    from monitor.config import LMConfig
    from monitor.integrations.lmstudio import LMStudioAdapter

    def denied(request):
        return httpx.Response(403, text="private conversation never logged")

    adapter = LMStudioAdapter(
        LMConfig(enabled=True), httpx.Client(transport=httpx.MockTransport(denied))
    )
    result = adapter.collect()
    assert "private conversation" not in caplog.text
    assert result.source.error == "HTTPStatusError"
    adapter.close()


async def test_disconnect_during_websocket_accept_does_not_leak_queue(tmp_path):
    app = create_app(Settings(), FakePipeline(tmp_path / "h.db"))
    endpoint = next(
        route.endpoint for route in app.routes if getattr(route, "path", None) == "/ws/metrics"
    )

    class Disconnected:
        headers = {}

        async def accept(self):
            raise RuntimeError("test disconnect before acceptance")

    await endpoint(Disconnected())
    assert not app.state.runtime.clients
