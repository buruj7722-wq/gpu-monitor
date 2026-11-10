"""Legacy API projections. No initialization or hardware polling at import time."""

from monitor.models import GPUReading


def get_gpu(reading: GPUReading | None = None) -> dict[str, object]:
    gpu = reading.devices[0] if reading and reading.devices else None

    def mib(value: int | None) -> int | None:
        return round(value / 1024**2) if value is not None else None

    return {
        "name": gpu.name if gpu else None,
        "temperature": gpu.temperature_c if gpu else None,
        "gpu_util": gpu.gpu_util_percent if gpu else None,
        "memory_util": gpu.memory_activity_percent if gpu else None,
        "memory_used": mib(gpu.memory_used_bytes) if gpu else None,
        "memory_total": mib(gpu.memory_total_bytes) if gpu else None,
        "power": gpu.power_w if gpu else None,
        "power_limit": gpu.power_limit_w if gpu else None,
        "fan": gpu.fan_percent if gpu else None,
        "driver": gpu.driver if gpu else None,
        "cuda": gpu.cuda_driver if gpu else None,
        "status": reading.source.status if reading else "initializing",
    }


def get_processes(reading: GPUReading | None = None) -> list[dict[str, object]]:
    if not reading or not reading.devices:
        return []
    uuid = reading.devices[0].uuid
    return [
        {
            "pid": p.pid,
            "name": p.name,
            "memory": round(p.gpu_memory_bytes / 1024**2)
            if p.gpu_memory_bytes is not None
            else None,
        }
        for p in reading.processes
        if p.gpu_uuid == uuid
    ]
