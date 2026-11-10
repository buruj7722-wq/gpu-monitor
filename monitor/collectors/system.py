"""Linux CPU, memory, storage and network; optional sensors fail independently."""

import os
import platform
import socket
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import psutil

from monitor.config import Settings
from monitor.models import CPU, Disk, DiskIO, Memory, Network, Source, SystemInfo, SystemReading
from monitor.normalization import number

T = TypeVar("T")
PSEUDO = {
    "proc",
    "sysfs",
    "tmpfs",
    "devtmpfs",
    "devpts",
    "cgroup",
    "cgroup2",
    "squashfs",
    "securityfs",
    "debugfs",
    "tracefs",
    "fusectl",
    "mqueue",
    "hugetlbfs",
    "pstore",
    "configfs",
    "autofs",
    "nsfs",
    "efivarfs",
}


class Rates:
    def __init__(self) -> None:
        self.previous: dict[str, tuple[float, tuple[int, ...]]] = {}

    def delta(self, key: str, counters: tuple[int, ...], now: float) -> list[float | None]:
        old = self.previous.get(key)
        self.previous[key] = (now, counters)
        if old is None or now <= old[0]:
            return [None] * len(counters)
        elapsed = now - old[0]
        return [
            (current - before) / elapsed if current >= before else None
            for current, before in zip(counters, old[1], strict=True)
        ]

    def retain(self, keys: set[str]) -> None:
        self.previous = {k: v for k, v in self.previous.items() if k in keys}


class SystemCollector:
    def __init__(self, settings: Settings, provider: Any = psutil) -> None:
        self.settings = settings
        self.ps = provider
        self.rates = Rates()
        self.cpu_previous: list[tuple[float, float]] | None = None
        self.last_success: float | None = None
        self.info = SystemInfo(
            hostname=socket.gethostname(),
            kernel=platform.release(),
            python=platform.python_version(),
            os=self._os_version(),
        )

    @staticmethod
    def _os_version() -> str:
        try:
            return platform.freedesktop_os_release().get("PRETTY_NAME", platform.system())
        except OSError:
            return platform.system()

    def collect(self, now: float | None = None, monotonic: float | None = None) -> SystemReading:
        now = time.time() if now is None else now
        mono = time.monotonic() if monotonic is None else monotonic
        errors: dict[str, str] = {}

        def safe(key: str, fn: Callable[[], T], default: T) -> T:
            try:
                return fn()
            except (OSError, RuntimeError, ValueError, psutil.Error, NotImplementedError) as exc:
                errors[key] = type(exc).__name__
                return default

        cpu = safe("cpu", self._cpu, CPU())
        memory = safe("memory", self._memory, Memory())
        disks: list[Disk] = safe("disks", lambda: self._disks(errors), [])
        io: list[DiskIO] = safe("disk_io", lambda: self._disk_io(mono), [])
        network: list[Network] = safe("network", lambda: self._network(mono), [])
        self.rates.retain({f"disk:{d.device}" for d in io} | {f"net:{n.name}" for n in network})
        boot = safe("boot_time", self.ps.boot_time, None)
        info = self.info.model_copy(
            update={
                "boot_time": boot,
                "uptime_seconds": max(0, now - boot) if boot else None,
                "service_status": "running" if os.environ.get("INVOCATION_ID") else "unknown",
            }
        )
        # Optional temperature absence is represented explicitly but does not fail CPU readings.
        if cpu.temperature_c is None:
            errors["cpu_temperature_c"] = "not_supported"
        degraded = any(v != "not_supported" for v in errors.values())
        if not degraded:
            self.last_success = now
        return SystemReading(
            cpu=cpu,
            memory=memory,
            disks=disks,
            disk_io=io,
            network=network,
            info=info,
            errors=errors,
            source=Source(
                status="degraded" if degraded else "ok",
                timestamp=now,
                last_success=self.last_success,
                error="partial_read_failure" if degraded else None,
            ),
        )

    def _cpu(self) -> CPU:
        times = self.ps.cpu_times(percpu=True)
        current: list[tuple[float, float]] = []
        for core in times:
            fields = core._asdict()
            total = sum(fields.values()) - fields.get("guest", 0) - fields.get("guest_nice", 0)
            idle = fields.get("idle", 0) + fields.get("iowait", 0)
            current.append((total, idle))
        per_core = []
        total_delta, idle_delta = 0.0, 0.0
        if self.cpu_previous is not None and len(current) == len(self.cpu_previous):
            for (total, idle), (old_total, old_idle) in zip(
                current, self.cpu_previous, strict=True
            ):
                dt, di = total - old_total, idle - old_idle
                value = number(100 * (1 - di / dt), 100) if dt > 0 and di >= 0 else None
                if value is not None:
                    per_core.append(value)
                    total_delta += dt
                    idle_delta += di
        self.cpu_previous = current
        try:
            frequency = self.ps.cpu_freq()
            mhz = number(frequency.current) if frequency else None
        except (OSError, NotImplementedError):
            mhz = None
        try:
            sensors = self.ps.sensors_temperatures()
            entries = [
                s.current
                for name, group in sensors.items()
                if name in {"coretemp", "k10temp", "cpu_thermal", "zenpower"}
                for s in group
            ]
            temperature = number(max(entries), 200) if entries else None
        except (AttributeError, OSError, NotImplementedError):
            temperature = None
        return CPU(
            usage_percent=100 * (1 - idle_delta / total_delta) if total_delta > 0 else None,
            per_core_percent=per_core,
            physical_cores=self.ps.cpu_count(logical=False),
            logical_cores=self.ps.cpu_count(logical=True),
            frequency_mhz=mhz,
            load_average=list(os.getloadavg()),
            temperature_c=temperature,
        )

    def _memory(self) -> Memory:
        ram, swap = self.ps.virtual_memory(), self.ps.swap_memory()
        return Memory(
            total_bytes=ram.total,
            used_bytes=ram.used,
            available_bytes=ram.available,
            percent=number(ram.percent, 100),
            swap_total_bytes=swap.total,
            swap_used_bytes=swap.used,
            swap_percent=number(swap.percent, 100),
        )

    def _disks(self, errors: dict[str, str]) -> list[Disk]:
        rows, seen = [], set()
        partitions = self.ps.disk_partitions(all=True)
        # Some restricted mount namespaces expose no root through disk_partitions.
        if not any(p.mountpoint == "/" for p in partitions):
            from types import SimpleNamespace

            partitions = [
                *partitions,
                SimpleNamespace(mountpoint="/", device="root", fstype="unknown"),
            ]
        for p in sorted(partitions, key=lambda p: (len(p.mountpoint), p.mountpoint)):
            mount = str(p.mountpoint)

            def below(prefix: str, mount: str = mount) -> bool:
                return mount == prefix or mount.startswith(prefix.rstrip("/") + "/")

            if self.settings.disk_include and not any(below(x) for x in self.settings.disk_include):
                continue
            if any(below(x) for x in self.settings.disk_exclude) or p.fstype in PSEUDO:
                continue
            if p.fstype == "overlay" and mount != "/":
                continue
            try:
                identity = self._mount_identity(mount)
                if identity in seen:
                    continue
                usage = self.ps.disk_usage(mount)
                seen.add(identity)
                rows.append(
                    Disk(
                        device=p.device,
                        mountpoint=mount,
                        filesystem=p.fstype,
                        total_bytes=usage.total,
                        used_bytes=usage.used,
                        free_bytes=usage.free,
                        percent=number(usage.percent, 100),
                    )
                )
            except (OSError, psutil.Error) as exc:
                errors[f"disk:{mount}"] = type(exc).__name__
        return rows

    @staticmethod
    def _mount_identity(mount: str) -> int:
        return os.stat(mount).st_dev

    def _disk_io(self, now: float) -> list[DiskIO]:
        rows = []
        for name, c in (self.ps.disk_io_counters(perdisk=True, nowrap=False) or {}).items():
            if name.startswith(("loop", "ram", "zram")) or not Path(f"/sys/block/{name}").exists():
                continue
            rates = self.rates.delta(
                f"disk:{name}", (c.read_bytes, c.write_bytes, c.read_count, c.write_count), now
            )
            rows.append(
                DiskIO(
                    device=name,
                    read_bytes=c.read_bytes,
                    write_bytes=c.write_bytes,
                    read_operations=c.read_count,
                    write_operations=c.write_count,
                    read_bytes_per_second=rates[0],
                    write_bytes_per_second=rates[1],
                    read_iops=rates[2],
                    write_iops=rates[3],
                )
            )
        return rows

    def _network(self, now: float) -> list[Network]:
        stats, addresses = self.ps.net_if_stats(), self.ps.net_if_addrs()
        rows = []
        for name, c in self.ps.net_io_counters(pernic=True, nowrap=False).items():
            if name in self.settings.network_exclude:
                continue
            rates = self.rates.delta(f"net:{name}", (c.bytes_recv, c.bytes_sent), now)
            rows.append(
                Network(
                    name=name,
                    addresses=[
                        a.address
                        for a in addresses.get(name, [])
                        if a.family in {socket.AF_INET, socket.AF_INET6}
                    ],
                    is_up=stats[name].isup if name in stats else None,
                    received_bytes=c.bytes_recv,
                    sent_bytes=c.bytes_sent,
                    receive_bytes_per_second=rates[0],
                    transmit_bytes_per_second=rates[1],
                    errors_in=c.errin,
                    errors_out=c.errout,
                    drops_in=c.dropin,
                    drops_out=c.dropout,
                )
            )
        return rows
