"""Versioned public telemetry models. Bytes, seconds, watts, Celsius and MHz."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Source(Model):
    status: Literal["ok", "degraded", "unavailable", "disabled", "initializing"] = "initializing"
    error: str | None = None
    timestamp: float | None = None
    last_success: float | None = None


class GPUProcess(Model):
    pid: int
    name: str | None = None
    start_time: float | None = None
    gpu_uuid: str
    process_type: str
    gpu_memory_bytes: int | None = None
    ram_bytes: int | None = None
    cpu_percent: float | None = None
    gpu_util_percent: float | None = None
    errors: dict[str, str] = Field(default_factory=dict)


class GPU(Model):
    index: int
    uuid: str
    name: str | None = None
    driver: str | None = None
    cuda_driver: int | None = None
    cuda_driver_display: str | None = None
    pci_bus_id: str | None = None
    architecture: str | None = None
    persistence_mode: str | None = None
    compute_mode: str | None = None
    performance_state: int | None = None
    gpu_util_percent: float | None = None
    memory_activity_percent: float | None = None
    memory_used_bytes: int | None = None
    memory_free_bytes: int | None = None
    memory_total_bytes: int | None = None
    vram_percent: float | None = None
    temperature_c: float | None = None
    temperature_max_c: float | None = None
    temperature_slowdown_c: float | None = None
    temperature_shutdown_c: float | None = None
    power_w: float | None = None
    power_limit_w: float | None = None
    sm_clock_mhz: int | None = None
    memory_clock_mhz: int | None = None
    graphics_clock_mhz: int | None = None
    fan_percent: float | None = None
    ecc_enabled: bool | None = None
    ecc_corrected: int | None = None
    ecc_uncorrected: int | None = None
    pcie_generation: int | None = None
    pcie_width: int | None = None
    pcie_max_generation: int | None = None
    pcie_max_width: int | None = None
    throttle_reasons: list[str] | None = None
    source: str = "nvml"
    status: str = "ok"
    errors: dict[str, str] = Field(default_factory=dict)


class GPUReading(Model):
    source: Source = Field(default_factory=Source)
    devices: list[GPU] = Field(default_factory=list)
    processes: list[GPUProcess] = Field(default_factory=list)
    processes_source: Source = Field(default_factory=Source)


class CPU(Model):
    usage_percent: float | None = None
    per_core_percent: list[float] = Field(default_factory=list)
    physical_cores: int | None = None
    logical_cores: int | None = None
    frequency_mhz: float | None = None
    load_average: list[float] = Field(default_factory=list)
    temperature_c: float | None = None


class Memory(Model):
    total_bytes: int | None = None
    used_bytes: int | None = None
    available_bytes: int | None = None
    percent: float | None = None
    swap_total_bytes: int | None = None
    swap_used_bytes: int | None = None
    swap_percent: float | None = None


class Disk(Model):
    device: str
    mountpoint: str
    filesystem: str
    total_bytes: int | None = None
    used_bytes: int | None = None
    free_bytes: int | None = None
    percent: float | None = None


class DiskIO(Model):
    device: str
    read_bytes: int
    write_bytes: int
    read_operations: int
    write_operations: int
    read_bytes_per_second: float | None = None
    write_bytes_per_second: float | None = None
    read_iops: float | None = None
    write_iops: float | None = None


class Network(Model):
    name: str
    addresses: list[str] = Field(default_factory=list)
    is_up: bool | None = None
    received_bytes: int | None = None
    sent_bytes: int | None = None
    receive_bytes_per_second: float | None = None
    transmit_bytes_per_second: float | None = None
    errors_in: int | None = None
    errors_out: int | None = None
    drops_in: int | None = None
    drops_out: int | None = None


class SystemInfo(Model):
    hostname: str = "unknown"
    os: str = "unknown"
    kernel: str = "unknown"
    python: str = "unknown"
    boot_time: float | None = None
    uptime_seconds: float | None = None
    service_status: str = "unknown"


class SystemReading(Model):
    source: Source = Field(default_factory=Source)
    cpu: CPU = Field(default_factory=CPU)
    memory: Memory = Field(default_factory=Memory)
    disks: list[Disk] = Field(default_factory=list)
    disk_io: list[DiskIO] = Field(default_factory=list)
    network: list[Network] = Field(default_factory=list)
    info: SystemInfo = Field(default_factory=SystemInfo)
    errors: dict[str, str] = Field(default_factory=dict)


class Activity(Model):
    gpu_uuid: str
    window_seconds: float
    coverage_percent: float
    active_seconds: float
    idle_seconds: float
    average_util_percent: float | None = None
    peak_util_percent: float | None = None
    average_power_w: float | None = None
    peak_temperature_c: float | None = None
    vram_change_bytes: int | None = None
    vram_growth_bytes_per_second: float | None = None
    process_count: int
    memory_pressure: bool
    patterns: list[str] = Field(default_factory=list)


class Integration(Model):
    source: Source = Field(default_factory=lambda: Source(status="disabled"))
    loaded_models: list[str] = Field(default_factory=list)
    requests: int | None = None
    tokens_per_second: float | None = None
    prompt_tokens_per_second: float | None = None
    time_to_first_token_seconds: float | None = None
    latency_seconds: float | None = None
    concurrent_requests: int | None = None


class Alert(Model):
    id: str
    severity: Literal["warning", "critical"]
    message: str
    since: float
    value: float | None = None
    threshold: float | None = None


class Observer(Model):
    cpu_percent: float | None = None
    rss_bytes: int | None = None
    collection_latency_ms: float = 0
    active_connections: int = 0
    dropped_samples: int = 0
    replaced_messages: int = 0
    collection_errors: int = 0
    collection_count: int = 0
    collection_error_rate: float = 0
    api_response_ms: float | None = None
    websocket_send_ms: float | None = None
    database_write_bytes: int = 0
    database_write_operations: int = 0


class Snapshot(Model):
    schema_version: int = 1
    host_id: str = "unknown"
    timestamp: float
    sequence: int = 0
    stale_after_seconds: float = 5
    collector: Source = Field(default_factory=Source)
    gpu: GPUReading = Field(default_factory=GPUReading)
    system: SystemReading = Field(default_factory=SystemReading)
    activity: list[Activity] = Field(default_factory=list)
    integration: Integration = Field(default_factory=Integration)
    alerts: list[Alert] = Field(default_factory=list)
    storage: Source = Field(default_factory=Source)
    observer: Observer = Field(default_factory=Observer)
