"""Read-only real NVML test, skipped unless explicitly enabled by the operator."""

import os

import pytest

from monitor.collectors.gpu import GPUCollector


@pytest.mark.gpu
@pytest.mark.skipif(
    os.environ.get("GPU_MONITOR_REAL_GPU") != "1",
    reason="set GPU_MONITOR_REAL_GPU=1 for read-only hardware checks",
)
def test_real_nvidia_telemetry():
    collector = GPUCollector(fallback=False)
    try:
        reading = collector.collect()
        assert reading.source.status == "ok"
        assert reading.devices
        for gpu in reading.devices:
            assert gpu.uuid.startswith("GPU-")
            assert gpu.memory_total_bytes > 0
            assert gpu.temperature_c is not None
    finally:
        collector.close()
