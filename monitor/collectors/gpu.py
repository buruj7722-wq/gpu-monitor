"""Read-only NVML telemetry with per-field isolation and one XML fallback query."""

import logging

# Fixed read-only executable; no shell or user input.
import subprocess  # nosec B404
import time
from collections.abc import Callable
from typing import Any, Literal

# Annotation only; parsing uses defusedxml.
from xml.etree.ElementTree import Element  # nosec B405

import pynvml
from defusedxml import ElementTree

from monitor.models import GPU, GPUReading, Source
from monitor.normalization import number, ratio, text

logger = logging.getLogger(__name__)

THROTTLE_BITS = {
    1: "gpu_idle",
    2: "application_clocks",
    4: "software_power_cap",
    8: "hardware_slowdown",
    16: "sync_boost",
    32: "software_thermal_slowdown",
    64: "hardware_thermal_slowdown",
    128: "hardware_power_brake",
    256: "display_clocks",
    512: "board_limit",
    1024: "reliability",
}
ARCHITECTURES = {
    2: "Kepler",
    3: "Maxwell",
    4: "Pascal",
    5: "Volta",
    6: "Turing",
    7: "Ampere",
    8: "Ada",
    9: "Hopper",
    10: "Blackwell",
    13: "Rubin",
}


def cuda_display(value: int | None) -> str | None:
    return f"{value // 1000}.{(value % 1000) // 10}" if value is not None else None


def error_code(exc: Exception) -> str:
    if isinstance(exc, pynvml.NVMLError_NotSupported) or isinstance(exc, AttributeError):
        return "not_supported"
    if isinstance(exc, pynvml.NVMLError_NoPermission):
        return "permission_denied"
    return type(exc).__name__


def run_smi() -> str:
    # Fixed executable/arguments, no shell, no user input. Driver is never modified.
    result = subprocess.run(  # nosec B603
        ["/usr/bin/nvidia-smi", "-q", "-x"],
        capture_output=True,
        text=True,
        timeout=2,
        check=True,
    )
    if len(result.stdout) > 8 * 1024 * 1024:
        raise ValueError("gpu_response_too_large")
    return result.stdout


class GPUCollector:
    def __init__(
        self, fallback: bool = True, nvml: Any = pynvml, smi: Callable[[], str] = run_smi
    ) -> None:
        self.nvml = nvml
        self.fallback = fallback
        self.smi = smi
        self.initialized = False
        self.next_retry = 0.0
        self.backoff = 1.0
        self.fallback_retry = 0.0
        self.last_success: float | None = None
        self.handles: dict[str, Any] = {}
        self.identity_cache: dict[int, str] = {}
        self._fatal = False
        self.fallback_xml: str | None = None

    def close(self) -> None:
        if self.initialized:
            try:
                self.nvml.nvmlShutdown()
            except Exception:
                logger.warning("nvml_shutdown_failed")
        self.initialized = False
        self.handles.clear()

    def _read(self, errors: dict[str, str], key: str, function: str, *args: Any) -> Any:
        try:
            return getattr(self.nvml, function)(*args)
        except Exception as exc:
            errors[key] = error_code(exc)
            if isinstance(
                exc,
                (
                    pynvml.NVMLError_GpuIsLost,
                    pynvml.NVMLError_Uninitialized,
                    pynvml.NVMLError_DriverNotLoaded,
                ),
            ):
                self._fatal = True
            return None

    def _device(self, index: int, handle: Any) -> GPU:
        errors: dict[str, str] = {}

        def read(key: str, fn: str, *args: Any) -> Any:
            return self._read(errors, key, fn, handle, *args)

        def numeric(
            key: str, fn: str, *args: Any, maximum: float | None = None, scale: float = 1
        ) -> float | None:
            raw = read(key, fn, *args)
            value = number(raw, maximum)
            if value is None and raw is not None:
                errors[key] = "invalid_value"
            return value / scale if value is not None else None

        def integer(key: str, fn: str, *args: Any) -> int | None:
            value = numeric(key, fn, *args, maximum=2**63 - 1)
            return int(value) if value is not None else None

        uuid = text(read("uuid", "nvmlDeviceGetUUID")) or self.identity_cache.get(
            index, f"unidentified-index-{index}"
        )
        self.identity_cache[index] = uuid
        self.handles[uuid] = handle
        memory = read("memory", "nvmlDeviceGetMemoryInfo")
        utilization = read("utilization", "nvmlDeviceGetUtilizationRates")
        pci = read("pci_bus_id", "nvmlDeviceGetPciInfo")
        architecture = read("architecture", "nvmlDeviceGetArchitecture")
        ecc = read("ecc_enabled", "nvmlDeviceGetEccMode")
        bits = read("throttle_reasons", "nvmlDeviceGetCurrentClocksEventReasons")
        if bits is None and errors.get("throttle_reasons") == "not_supported":
            bits = read("throttle_reasons", "nvmlDeviceGetCurrentClocksThrottleReasons")
            if bits is not None:
                errors.pop("throttle_reasons", None)
        driver = text(self._read(errors, "driver", "nvmlSystemGetDriverVersion"))
        cuda = self._read(errors, "cuda_driver", "nvmlSystemGetCudaDriverVersion_v2")
        cuda = int(cuda) if number(cuda, 1000000) is not None else None

        def mem(key: str) -> int | None:
            value = number(getattr(memory, key, None), 2**63 - 1)
            if value is None:
                errors[f"memory_{key}_bytes"] = errors.get("memory", "invalid_value")
            return int(value) if value is not None else None

        used, free, total = mem("used"), mem("free"), mem("total")
        performance = integer("performance_state", "nvmlDeviceGetPerformanceState")
        values: dict[str, Any] = {
            "index": index,
            "uuid": uuid,
            "name": text(read("name", "nvmlDeviceGetName")),
            "driver": driver,
            "cuda_driver": cuda,
            "cuda_driver_display": cuda_display(cuda),
            "pci_bus_id": text(getattr(pci, "busId", None)),
            "architecture": ARCHITECTURES.get(
                architecture, f"architecture-{architecture}" if architecture is not None else None
            ),
            "persistence_mode": text(read("persistence_mode", "nvmlDeviceGetPersistenceMode")),
            "compute_mode": text(read("compute_mode", "nvmlDeviceGetComputeMode")),
            "performance_state": performance
            if performance is not None and performance <= 15
            else None,
            "gpu_util_percent": number(getattr(utilization, "gpu", None), 100),
            "memory_activity_percent": number(getattr(utilization, "memory", None), 100),
            "memory_used_bytes": used,
            "memory_free_bytes": free,
            "memory_total_bytes": total,
            "vram_percent": ratio(used, total),
            "temperature_c": numeric(
                "temperature_c",
                "nvmlDeviceGetTemperature",
                pynvml.NVML_TEMPERATURE_GPU,
                maximum=200,
            ),
            "temperature_max_c": numeric(
                "temperature_max_c",
                "nvmlDeviceGetTemperatureThreshold",
                pynvml.NVML_TEMPERATURE_THRESHOLD_GPU_MAX,
                maximum=200,
            ),
            "temperature_slowdown_c": numeric(
                "temperature_slowdown_c",
                "nvmlDeviceGetTemperatureThreshold",
                pynvml.NVML_TEMPERATURE_THRESHOLD_SLOWDOWN,
                maximum=200,
            ),
            "temperature_shutdown_c": numeric(
                "temperature_shutdown_c",
                "nvmlDeviceGetTemperatureThreshold",
                pynvml.NVML_TEMPERATURE_THRESHOLD_SHUTDOWN,
                maximum=200,
            ),
            "power_w": numeric("power_w", "nvmlDeviceGetPowerUsage", scale=1000),
            "power_limit_w": numeric(
                "power_limit_w", "nvmlDeviceGetEnforcedPowerLimit", scale=1000
            ),
            "fan_percent": numeric("fan_percent", "nvmlDeviceGetFanSpeed", maximum=100),
            "ecc_enabled": bool(ecc[0]) if ecc is not None else None,
            "ecc_corrected": integer(
                "ecc_corrected",
                "nvmlDeviceGetTotalEccErrors",
                pynvml.NVML_MEMORY_ERROR_TYPE_CORRECTED,
                pynvml.NVML_VOLATILE_ECC,
            ),
            "ecc_uncorrected": integer(
                "ecc_uncorrected",
                "nvmlDeviceGetTotalEccErrors",
                pynvml.NVML_MEMORY_ERROR_TYPE_UNCORRECTED,
                pynvml.NVML_VOLATILE_ECC,
            ),
            "throttle_reasons": [name for bit, name in THROTTLE_BITS.items() if int(bits) & bit]
            if bits is not None
            else None,
        }
        for key, kind in [
            ("sm_clock_mhz", pynvml.NVML_CLOCK_SM),
            ("memory_clock_mhz", pynvml.NVML_CLOCK_MEM),
            ("graphics_clock_mhz", pynvml.NVML_CLOCK_GRAPHICS),
        ]:
            values[key] = integer(key, "nvmlDeviceGetClockInfo", kind)
        for key, fn in [
            ("pcie_generation", "nvmlDeviceGetCurrPcieLinkGeneration"),
            ("pcie_width", "nvmlDeviceGetCurrPcieLinkWidth"),
            ("pcie_max_generation", "nvmlDeviceGetMaxPcieLinkGeneration"),
            ("pcie_max_width", "nvmlDeviceGetMaxPcieLinkWidth"),
        ]:
            values[key] = integer(key, fn)
        for key, value in values.items():
            if value is None:
                errors.setdefault(key, "not_supported")
        if utilization is not None:
            for key in ["gpu_util_percent", "memory_activity_percent"]:
                if values[key] is None:
                    errors[key] = "invalid_value"
        values["errors"] = errors
        values["status"] = (
            "degraded" if any(e != "not_supported" for e in errors.values()) else "ok"
        )
        return GPU.model_validate(values)

    def collect(self, now: float | None = None, monotonic: float | None = None) -> GPUReading:
        now = time.time() if now is None else now
        mono = time.monotonic() if monotonic is None else monotonic
        failure = "nvml_reconnecting"
        self.handles.clear()
        self.fallback_xml = None
        try:
            if not self.initialized and mono >= self.next_retry:
                self.nvml.nvmlInit()
                self.initialized = True
                self.backoff = 1
            if self.initialized:
                self._fatal = False
                devices = []
                for index in range(self.nvml.nvmlDeviceGetCount()):
                    try:
                        devices.append(
                            self._device(index, self.nvml.nvmlDeviceGetHandleByIndex(index))
                        )
                    except Exception as exc:
                        failure = error_code(exc)
                        devices.append(
                            GPU(
                                index=index,
                                uuid=self.identity_cache.get(index, f"unidentified-index-{index}"),
                                status="unavailable",
                                errors={"device": failure},
                            )
                        )
                        self._fatal = True
                if self._fatal:
                    self.close()
                    self.next_retry = mono + 1
                status: Literal["degraded", "ok"] = (
                    "degraded" if any(d.status != "ok" for d in devices) else "ok"
                )
                if status == "ok":
                    self.last_success = now
                return GPUReading(
                    devices=devices,
                    source=Source(
                        status=status,
                        timestamp=now,
                        last_success=self.last_success,
                        error="partial_read_failure" if status != "ok" else None,
                    ),
                )
        except Exception as exc:
            failure = error_code(exc)
            self.close()
            self.next_retry = mono + self.backoff
            self.backoff = min(self.backoff * 2, 60)
            logger.warning("nvml_unavailable:%s", failure)
        if self.fallback and mono >= self.fallback_retry:
            try:
                self.fallback_xml = self.smi()
                devices = parse_smi(self.fallback_xml)
                self.last_success = now
                return GPUReading(
                    devices=devices,
                    source=Source(
                        status="degraded", timestamp=now, last_success=now, error="using_nvidia_smi"
                    ),
                )
            except Exception as exc:
                self.fallback_retry = mono + min(self.backoff, 60)
                logger.warning("nvidia_smi_unavailable:%s", type(exc).__name__)
        return GPUReading(
            source=Source(
                status="unavailable", timestamp=now, last_success=self.last_success, error=failure
            )
        )


def parse_smi(xml: str) -> list[GPU]:
    if len(xml) > 8 * 1024 * 1024:
        raise ValueError("gpu_response_too_large")
    root = ElementTree.fromstring(xml)
    driver = root.findtext("driver_version")
    cuda_text = root.findtext("cuda_version", "")
    try:
        major, minor = cuda_text.split(".")[:2]
        cuda: int | None = int(major) * 1000 + int(minor) * 10
    except ValueError:
        cuda = None
    devices = []
    for index, element in enumerate(root.findall("gpu")):
        devices.append(_parse_device(element, index, driver, cuda))
    return devices


def _parse_device(e: Element, index: int, driver: str | None, cuda: int | None) -> GPU:
    errors: dict[str, str] = {}
    values: dict[str, Any] = {
        "index": index,
        "uuid": e.findtext("uuid") or f"unidentified-index-{index}",
        "name": e.findtext("product_name"),
        "driver": driver,
        "cuda_driver": cuda,
        "cuda_driver_display": cuda_display(cuda),
        "source": "nvidia-smi",
    }
    paths = {
        "temperature_c": "temperature/gpu_temp",
        "temperature_max_c": "temperature/gpu_max_operating_temp",
        "temperature_slowdown_c": "temperature/gpu_temp_slow_threshold",
        "temperature_shutdown_c": "temperature/gpu_temp_max_threshold",
        "gpu_util_percent": "utilization/gpu_util",
        "memory_activity_percent": "utilization/memory_util",
        "memory_used_bytes": "fb_memory_usage/used",
        "memory_free_bytes": "fb_memory_usage/free",
        "memory_total_bytes": "fb_memory_usage/total",
        "power_w": "gpu_power_readings/power_draw",
        "power_limit_w": "gpu_power_readings/enforced_power_limit",
        "sm_clock_mhz": "clocks/sm_clock",
        "graphics_clock_mhz": "clocks/graphics_clock",
        "memory_clock_mhz": "clocks/mem_clock",
        "fan_percent": "fan_speed",
        "performance_state": "performance_state",
        "pcie_generation": "pci/pci_gpu_link_info/pcie_gen/current_link_gen",
        "pcie_max_generation": "pci/pci_gpu_link_info/pcie_gen/max_link_gen",
        "pcie_width": "pci/pci_gpu_link_info/link_widths/current_link_width",
        "pcie_max_width": "pci/pci_gpu_link_info/link_widths/max_link_width",
        "ecc_corrected": "ecc_errors/volatile/single_bit/total",
        "ecc_uncorrected": "ecc_errors/volatile/double_bit/total",
    }
    for key, path in paths.items():
        raw = e.findtext(path)
        if raw is None and key in {"power_w", "power_limit_w"}:
            raw = e.findtext(path.replace("gpu_power_readings", "power_readings"))
        value = number(raw.split()[0].removeprefix("P").removesuffix("x")) if raw else None
        if value is None:
            errors[key] = "not_supported"
        if key.endswith("_bytes") and value is not None:
            value = int(value * 1024**2)
        if (
            key.endswith("_mhz")
            or key.startswith("pcie_")
            or key.startswith("ecc_")
            or key == "performance_state"
        ):
            value = int(value) if value is not None else None
        if key.endswith("percent"):
            value = number(value, 100)
        values[key] = value
    for key, path in [
        ("architecture", "product_architecture"),
        ("pci_bus_id", "pci/pci_bus_id"),
        ("compute_mode", "compute_mode"),
        ("persistence_mode", "persistence_mode"),
    ]:
        raw = e.findtext(path)
        values[key] = raw if raw not in {None, "N/A"} else None
        if values[key] is None:
            errors[key] = "not_supported"
    ecc = e.findtext("ecc_mode/current_ecc")
    values["ecc_enabled"] = ecc == "Enabled" if ecc in {"Enabled", "Disabled"} else None
    throttle = e.find("clocks_event_reasons")
    if throttle is None:
        throttle = e.find("clocks_throttle_reasons")
    values["throttle_reasons"] = (
        [child.tag for child in throttle if child.text == "Active"]
        if throttle is not None
        else None
    )
    for key in ["ecc_enabled", "throttle_reasons", "cuda_driver"]:
        if values.get(key) is None:
            errors[key] = "not_supported"
    values["vram_percent"] = ratio(values["memory_used_bytes"], values["memory_total_bytes"])
    values["errors"] = errors
    return GPU.model_validate(values)
