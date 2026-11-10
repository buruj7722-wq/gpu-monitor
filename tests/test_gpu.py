from types import SimpleNamespace

import pynvml
import pytest
from defusedxml.common import EntitiesForbidden

from monitor.collectors.gpu import GPUCollector, parse_smi


class FakeNVML:
    def __init__(self, count=1, failed=False):
        self.count = count
        self.failed = failed
        self.init_calls = 0
        self.shutdowns = 0

    def nvmlInit(self):
        self.init_calls += 1
        if self.failed:
            raise pynvml.NVMLError_DriverNotLoaded()

    def nvmlShutdown(self):
        self.shutdowns += 1

    def nvmlDeviceGetCount(self):
        return self.count

    def nvmlDeviceGetHandleByIndex(self, index):
        return index

    def __getattr__(self, name):
        mapping = {
            "nvmlDeviceGetUUID": lambda h: f"GPU-{h}",
            "nvmlDeviceGetName": lambda h: b"NVIDIA A40",
            "nvmlDeviceGetMemoryInfo": lambda h: SimpleNamespace(used=1024, free=3072, total=4096),
            "nvmlDeviceGetUtilizationRates": lambda h: SimpleNamespace(gpu=40, memory=20),
            "nvmlDeviceGetPciInfo": lambda h: SimpleNamespace(busId=b"0000:01:00.0"),
            "nvmlDeviceGetArchitecture": lambda h: 7,
            "nvmlDeviceGetEccMode": lambda h: (1, 1),
            "nvmlDeviceGetCurrentClocksEventReasons": lambda h: 64,
            "nvmlSystemGetDriverVersion": lambda: b"595.91.07",
            "nvmlSystemGetCudaDriverVersion_v2": lambda: 13000,
            "nvmlDeviceGetPowerUsage": lambda h: 150000,
            "nvmlDeviceGetEnforcedPowerLimit": lambda h: 300000,
            "nvmlDeviceGetTemperature": lambda *a: 52,
            "nvmlDeviceGetTemperatureThreshold": lambda *a: 90,
            "nvmlDeviceGetPerformanceState": lambda h: 2,
        }
        if name in mapping:
            return mapping[name]

        def unsupported(*args):
            raise pynvml.NVMLError_NotSupported()

        return unsupported


@pytest.mark.parametrize("count", [0, 1, 2])
def test_gpu_normal_and_multiple(count):
    nvml = FakeNVML(count)
    collector = GPUCollector(nvml=nvml, fallback=False)
    result = collector.collect(now=10, monotonic=0)
    assert len(result.devices) == count
    assert result.source.status == "ok"
    if count:
        gpu = result.devices[0]
        assert gpu.name == "NVIDIA A40"
        assert gpu.power_w == 150
        assert gpu.vram_percent == 25
        assert gpu.memory_activity_percent == 20
        assert gpu.fan_percent is None
        assert gpu.errors["fan_percent"] == "not_supported"
        assert gpu.cuda_driver_display == "13.0"
        assert gpu.architecture == "Ampere"
        assert gpu.throttle_reasons == ["hardware_thermal_slowdown"]
    collector.close()
    assert nvml.shutdowns == 1


def test_nvml_failure_backoff_and_recovery():
    nvml = FakeNVML(failed=True)
    collector = GPUCollector(nvml=nvml, fallback=False)
    assert collector.collect(now=0, monotonic=0).source.status == "unavailable"
    collector.collect(now=0.2, monotonic=0.2)
    assert nvml.init_calls == 1
    nvml.failed = False
    assert collector.collect(now=2, monotonic=2).devices[0].uuid == "GPU-0"


XML = """<nvidia_smi_log><driver_version>595</driver_version><cuda_version>13.0</cuda_version>
<gpu><uuid>GPU-x</uuid><product_name>A40</product_name><fan_speed>N/A</fan_speed>
<fb_memory_usage><used>100 MiB</used><free>300 MiB</free><total>400 MiB</total></fb_memory_usage>
<utilization><gpu_util>10 %</gpu_util></utilization></gpu></nvidia_smi_log>"""


def test_one_fallback_call_and_units():
    calls = []
    collector = GPUCollector(nvml=FakeNVML(failed=True), smi=lambda: calls.append(1) or XML)
    reading = collector.collect(now=0, monotonic=0)
    assert calls == [1]
    gpu = reading.devices[0]
    assert gpu.source == "nvidia-smi"
    assert gpu.memory_used_bytes == 100 * 1024**2
    assert gpu.fan_percent is None
    assert gpu.vram_percent == 25


def test_xml_entities_rejected():
    with pytest.raises(EntitiesForbidden):
        parse_smi(
            '<!DOCTYPE x [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><nvidia_smi_log>&xxe;</nvidia_smi_log>'
        )


def test_field_error_does_not_stop_other_gpus():
    class Partial(FakeNVML):
        def nvmlDeviceGetFanSpeed(self, handle):
            raise pynvml.NVMLError_NoPermission()

    result = GPUCollector(nvml=Partial(2)).collect()
    assert len(result.devices) == 2
    assert result.source.status == "degraded"
    assert result.devices[1].gpu_util_percent == 40
