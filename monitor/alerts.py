"""Sustained state transitions with hysteresis; no per-second notification events."""

import time
from dataclasses import dataclass
from typing import Literal

from monitor.config import AlertConfig, Threshold
from monitor.models import Alert, Snapshot
from monitor.normalization import ratio

Severity = Literal["warning", "critical"]


@dataclass
class State:
    active: Alert | None = None
    pending: Severity | None = None
    pending_since: float = 0
    recovery_since: float | None = None
    last_seen: float = 0


class AlertEngine:
    def __init__(self, config: AlertConfig) -> None:
        self.config = config
        self.states: dict[str, State] = {}
        self.network_seen: set[str] = set(config.network_interfaces)
        self.gpu_seen: set[str] = set()

    def _evaluate(
        self,
        key: str,
        value: float | None,
        warning: float,
        critical: float,
        message: str,
        mono: float,
        wall: float,
        duration: float | None = None,
        hysteresis: float | None = None,
    ) -> None:
        state = self.states.setdefault(key, State())
        state.last_seen = mono
        if value is None:
            state.pending = None
            state.recovery_since = None
            if state.active:
                state.active = state.active.model_copy(update={"value": None})
            return
        h = self.config.hysteresis_percent if hysteresis is None else hysteresis
        sustain = self.config.sustain_seconds if duration is None else duration
        severity: Severity | None = (
            "critical" if value >= critical else "warning" if value >= warning else None
        )
        if state.active:
            # Keep the current severity until it crosses its recovery boundary.
            boundary = critical if state.active.severity == "critical" else warning
            if value >= boundary - h and severity != "critical":
                severity = state.active.severity
            if severity == state.active.severity:
                state.active = state.active.model_copy(update={"value": value})
                state.pending = None
                state.recovery_since = None
                return
            if severity is None or (state.active.severity == "critical" and severity == "warning"):
                if state.recovery_since is None:
                    state.recovery_since = mono
                if mono - state.recovery_since < self.config.recovery_seconds:
                    return
                if severity == "warning":
                    state.active = Alert(
                        id=key,
                        severity="warning",
                        message=message,
                        since=wall,
                        value=value,
                        threshold=warning,
                    )
                    state.pending = None
                    state.recovery_since = None
                    return
                state.active = None
                state.recovery_since = None
        if severity is None:
            state.pending = None
            return
        if state.pending != severity:
            state.pending, state.pending_since = severity, mono
        if mono - state.pending_since >= sustain:
            state.active = Alert(
                id=key,
                severity=severity,
                message=message,
                since=wall,
                value=value,
                threshold=critical if severity == "critical" else warning,
            )
            state.pending = None

    def evaluate(self, snapshot: Snapshot, monotonic: float | None = None) -> list[Alert]:
        mono = time.monotonic() if monotonic is None else monotonic
        wall = snapshot.timestamp

        def rule(key: str, value: float | None, threshold: Threshold, message: str) -> None:
            self._evaluate(key, value, threshold.warning, threshold.critical, message, mono, wall)

        rule("cpu/high", snapshot.system.cpu.usage_percent, self.config.cpu, "CPU usage high")
        rule("ram/high", snapshot.system.memory.percent, self.config.ram, "RAM usage high")
        for disk in snapshot.system.disks:
            rule(
                f"disk/{disk.mountpoint}",
                disk.percent,
                self.config.disk,
                f"Disk space low: {disk.mountpoint}",
            )
        unavailable = not snapshot.gpu.devices or snapshot.gpu.source.status == "unavailable"
        self._evaluate(
            "gpu/unavailable",
            float(unavailable),
            0.5,
            1,
            "GPU data unavailable",
            mono,
            wall,
            duration=self.config.gpu_unavailable_seconds,
            hysteresis=0,
        )
        for gpu in snapshot.gpu.devices:
            self.gpu_seen.add(gpu.uuid)
            prefix = f"gpu/{gpu.uuid}"
            rule(prefix + "/vram", gpu.vram_percent, self.config.vram, "GPU memory pressure")
            rule(
                prefix + "/utilization",
                gpu.gpu_util_percent,
                self.config.utilization,
                "GPU utilization high (load indicator)",
            )
            rule(
                prefix + "/power",
                ratio(gpu.power_w, gpu.power_limit_w),
                self.config.power,
                "GPU power near limit",
            )
            critical = (
                self.config.temperature_critical_c
                or gpu.temperature_max_c
                or gpu.temperature_slowdown_c
            )
            warning = (
                self.config.temperature_warning_c
                if self.config.temperature_warning_c is not None
                else critical - 5
                if critical is not None
                else None
            )
            if warning is not None and critical is not None:
                self._evaluate(
                    prefix + "/temperature",
                    gpu.temperature_c,
                    warning,
                    critical,
                    "GPU temperature high",
                    mono,
                    wall,
                    hysteresis=self.config.hysteresis_c,
                )
            self._evaluate(
                prefix + "/ecc",
                float(gpu.ecc_uncorrected) if gpu.ecc_uncorrected is not None else None,
                0.5,
                1,
                "Uncorrected volatile ECC errors",
                mono,
                wall,
                hysteresis=0,
            )
            throttling = (
                None
                if gpu.throttle_reasons is None
                else float(
                    any("thermal" in r or r == "hardware_slowdown" for r in gpu.throttle_reasons)
                )
            )
            self._evaluate(
                prefix + "/throttling",
                throttling,
                1,
                2,
                "Sustained hardware throttling",
                mono,
                wall,
                hysteresis=0,
            )
        live = {g.uuid for g in snapshot.gpu.devices if g.status != "unavailable"}
        for uuid in self.gpu_seen:
            self._evaluate(
                f"gpu/{uuid}/unavailable",
                float(uuid not in live),
                0.5,
                1,
                "GPU device unavailable",
                mono,
                wall,
                duration=self.config.gpu_unavailable_seconds,
                hysteresis=0,
            )
        for net in snapshot.system.network:
            if net.is_up:
                self.network_seen.add(net.name)
        status = {n.name: n.is_up for n in snapshot.system.network}
        for name in self.network_seen:
            value = (
                None
                if snapshot.system.source.status == "unavailable"
                else float(not status.get(name))
            )
            self._evaluate(
                f"network/{name}",
                value,
                0.5,
                1,
                f"Network interface down: {name}",
                mono,
                wall,
                hysteresis=0,
            )
        if snapshot.storage.status != "initializing":
            self._evaluate(
                "history/unavailable",
                float(snapshot.storage.status == "unavailable"),
                0.5,
                1,
                "History storage unavailable",
                mono,
                wall,
                hysteresis=0,
            )
        # Missing metrics cannot prove recovery. Keep alert state but remove its value.
        for key, state in list(self.states.items()):
            if state.last_seen != mono:
                state.pending = None
                state.recovery_since = None
                if state.active:
                    state.active = state.active.model_copy(update={"value": None})
                elif mono - state.last_seen > 300:
                    del self.states[key]
        return sorted(
            [s.active for s in self.states.values() if s.active],
            key=lambda a: (a.severity != "critical", a.id),
        )
