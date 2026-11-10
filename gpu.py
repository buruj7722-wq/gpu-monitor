from pynvml import *
import psutil

nvmlInit()

def get_gpu():

    handle = nvmlDeviceGetHandleByIndex(0)

    memory = nvmlDeviceGetMemoryInfo(handle)
    utilization = nvmlDeviceGetUtilizationRates(handle)

    try:
        fan = nvmlDeviceGetFanSpeed(handle)
    except:
        fan = 0

    try:
        power = nvmlDeviceGetPowerUsage(handle) / 1000
        power_limit = nvmlDeviceGetEnforcedPowerLimit(handle) / 1000
    except:
        power = 0
        power_limit = 0

    gpu = {
        "name": nvmlDeviceGetName(handle),
        "temperature": nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU),
        "gpu_util": utilization.gpu,
        "memory_util": utilization.memory,
        "memory_used": round(memory.used / 1024 / 1024),
        "memory_total": round(memory.total / 1024 / 1024),
        "power": round(power,1),
        "power_limit": round(power_limit,1),
        "fan": fan,
        "driver": nvmlSystemGetDriverVersion(),
        "cuda": nvmlSystemGetCudaDriverVersion_v2()
    }

    return gpu


def get_processes():

    handle = nvmlDeviceGetHandleByIndex(0)

    processes = []

    try:
        running = nvmlDeviceGetComputeRunningProcesses(handle)

        for p in running:

            try:
                proc = psutil.Process(p.pid)

                processes.append({
                    "pid": p.pid,
                    "name": proc.name(),
                    "memory": round(p.usedGpuMemory / 1024 / 1024)
                })

            except:
                pass

    except:
        pass

    return processes
