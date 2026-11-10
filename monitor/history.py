"""Bounded in-memory samples and minute SQLite aggregates; no unbounded raw writes."""

import json
import logging
import math
import sqlite3
import threading
import time
from collections import deque
from pathlib import Path

import psutil
from pydantic import Field

from monitor.models import Model, Snapshot, Source

logger = logging.getLogger(__name__)
WINDOWS = {"5m": 300, "1h": 3600, "24h": 86400, "7d": 604800}


class Aggregate(Model):
    mean: float
    minimum: float
    maximum: float
    count: int


class HistoryPoint(Model):
    timestamp: float
    metrics: dict[str, Aggregate] = Field(default_factory=dict)


class HistoryResponse(Model):
    window: str
    resolution_seconds: float
    source: Source
    points: list[HistoryPoint]
    gaps_are_missing: bool = True


def flatten(snapshot: Snapshot) -> dict[str, float]:
    result: dict[str, float] = {}

    def add(key: str, value: float | int | None) -> None:
        if value is not None:
            result[key] = float(value)

    add("cpu/usage_percent", snapshot.system.cpu.usage_percent)
    add("cpu/temperature_c", snapshot.system.cpu.temperature_c)
    add("ram/percent", snapshot.system.memory.percent)
    add("ram/used_bytes", snapshot.system.memory.used_bytes)
    add("swap/percent", snapshot.system.memory.swap_percent)
    for gpu in snapshot.gpu.devices:
        for key in [
            "gpu_util_percent",
            "memory_activity_percent",
            "memory_used_bytes",
            "vram_percent",
            "temperature_c",
            "power_w",
            "sm_clock_mhz",
            "memory_clock_mhz",
            "graphics_clock_mhz",
        ]:
            add(f"gpu/{gpu.uuid}/{key}", getattr(gpu, key))
    for disk in snapshot.system.disks:
        add(f"disk/{disk.mountpoint}/percent", disk.percent)
    for disk_io in snapshot.system.disk_io:
        for key in ["read_bytes_per_second", "write_bytes_per_second", "read_iops", "write_iops"]:
            add(f"io/{disk_io.device}/{key}", getattr(disk_io, key))
    for network in snapshot.system.network:
        for key in ["receive_bytes_per_second", "transmit_bytes_per_second"]:
            add(f"network/{network.name}/{key}", getattr(network, key))
    return result


def combine(points: list[HistoryPoint], resolution: float, max_points: int) -> list[HistoryPoint]:
    buckets: dict[int, dict[str, list[float]]] = {}
    for point in points:
        group = buckets.setdefault(int(point.timestamp // resolution) * int(resolution), {})
        for key, stat in point.metrics.items():
            old = group.get(key)
            if old is None:
                group[key] = [stat.mean * stat.count, stat.minimum, stat.maximum, float(stat.count)]
            else:
                old[0] += stat.mean * stat.count
                old[1], old[2], old[3] = (
                    min(old[1], stat.minimum),
                    max(old[2], stat.maximum),
                    old[3] + stat.count,
                )
    return [
        HistoryPoint(
            timestamp=t,
            metrics={
                k: Aggregate(mean=s[0] / s[3], minimum=s[1], maximum=s[2], count=int(s[3]))
                for k, s in metrics.items()
            },
        )
        for t, metrics in sorted(buckets.items())
    ][-max_points:]


class HistoryStore:
    def __init__(self, path: Path, retention_days: int = 7, sample_seconds: float = 1) -> None:
        self.path = path
        self.retention_days = retention_days
        self.sample_seconds = sample_seconds
        self.ring: deque[HistoryPoint] = deque(maxlen=int(300 / sample_seconds) + 2)
        self.lock = threading.RLock()
        self.connection: sqlite3.Connection | None = None
        self.source = Source()
        self.next_retry = 0.0
        self.last_cleanup = 0.0
        self.bucket: int | None = None
        self.pending: dict[str, list[float]] = {}
        self.write_bytes = 0
        self.write_operations = 0

    def initialize(self) -> None:
        with self.lock:
            connection = None
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                connection = sqlite3.connect(self.path, timeout=1, check_same_thread=False)
                version = connection.execute("PRAGMA user_version").fetchone()[0]
                tables = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                if version not in {0, 1} or (version == 0 and tables):
                    raise ValueError("unsupported_database_schema")
                if version == 0:
                    with connection:
                        connection.execute(
                            "CREATE TABLE aggregates (bucket INTEGER PRIMARY KEY, metrics TEXT NOT NULL)"
                        )
                        connection.execute("PRAGMA user_version=1")
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("PRAGMA synchronous=NORMAL")
                self.connection = connection
                self.source = Source(status="ok", timestamp=time.time(), last_success=time.time())
            except (sqlite3.Error, OSError, ValueError) as exc:
                if connection is not None:
                    connection.close()
                self.connection = None
                self._failed(exc)

    def _failed(self, exc: Exception) -> None:
        self.source = Source(
            status="unavailable",
            timestamp=time.time(),
            last_success=self.source.last_success,
            error=type(exc).__name__,
        )
        self.next_retry = time.monotonic() + 60
        logger.warning("history_unavailable:%s", type(exc).__name__)

    def record(self, snapshot: Snapshot) -> None:
        point = HistoryPoint(
            timestamp=snapshot.timestamp,
            metrics={
                k: Aggregate(mean=v, minimum=v, maximum=v, count=1)
                for k, v in flatten(snapshot).items()
            },
        )
        with self.lock:
            self.ring.append(point)
            while self.ring and self.ring[0].timestamp < snapshot.timestamp - 300:
                self.ring.popleft()
            if self.connection is None and time.monotonic() >= self.next_retry:
                self.initialize()
            bucket = int(snapshot.timestamp // 60) * 60
            if self.bucket is not None and bucket != self.bucket:
                self._flush(snapshot.timestamp)
                self.pending.clear()
            self.bucket = bucket
            for key, stat in point.metrics.items():
                state = self.pending.setdefault(key, [0, stat.minimum, stat.maximum, 0])
                state[0] += stat.mean
                state[1], state[2], state[3] = (
                    min(state[1], stat.minimum),
                    max(state[2], stat.maximum),
                    state[3] + 1,
                )

    def _flush(self, now: float) -> None:
        if self.connection is None or self.bucket is None or not self.pending:
            return
        aggregates = {
            key: Aggregate(
                mean=s[0] / s[3], minimum=s[1], maximum=s[2], count=int(s[3])
            ).model_dump()
            for key, s in self.pending.items()
        }
        payload = json.dumps(aggregates, separators=(",", ":"), allow_nan=False)
        try:
            before = self._physical_bytes()
            with self.connection:
                self.connection.execute(
                    "INSERT OR REPLACE INTO aggregates VALUES (?, ?)", (self.bucket, payload)
                )
                if now - self.last_cleanup >= 3600:
                    self.connection.execute(
                        "DELETE FROM aggregates WHERE bucket < ?",
                        (now - self.retention_days * 86400,),
                    )
                    self.last_cleanup = now
            after = self._physical_bytes()
            self.write_bytes += max(0, after - before)
            self.write_operations += 1
            self.source = Source(status="ok", timestamp=now, last_success=now)
        except (sqlite3.Error, OSError) as exc:
            self.connection.close()
            self.connection = None
            self._failed(exc)

    def _physical_bytes(self) -> int:
        # Linux process write_bytes around this transaction includes SQLite/WAL
        # writes, not only file growth. A fallback reports growth as a lower bound.
        try:
            return psutil.Process().io_counters().write_bytes
        except (psutil.Error, AttributeError):
            return sum(
                p.stat().st_size for p in [self.path, Path(str(self.path) + "-wal")] if p.exists()
            )

    def query(
        self, window: str, now: float | None = None, max_points: int = 600
    ) -> HistoryResponse:
        if window not in WINDOWS or not 1 <= max_points <= 600:
            raise ValueError("invalid_history_query")
        now = time.time() if now is None else now
        cutoff = now - WINDOWS[window]
        resolution: float = 900 if window == "7d" else 60
        with self.lock:
            points = []
            if self.connection is not None:
                try:
                    for bucket, payload in self.connection.execute(
                        "SELECT bucket, metrics FROM aggregates WHERE bucket >= ? AND bucket <= ? ORDER BY bucket",
                        (cutoff, now),
                    ):
                        points.append(
                            HistoryPoint(
                                timestamp=bucket,
                                metrics={
                                    k: Aggregate.model_validate(v)
                                    for k, v in json.loads(payload).items()
                                },
                            )
                        )
                except (sqlite3.Error, ValueError, TypeError) as exc:
                    self._failed(exc)
            if self.bucket is not None and cutoff <= self.bucket <= now and self.pending:
                points = [p for p in points if p.timestamp != self.bucket]
                points.append(
                    HistoryPoint(
                        timestamp=self.bucket,
                        metrics={
                            k: Aggregate(
                                mean=s[0] / s[3], minimum=s[1], maximum=s[2], count=int(s[3])
                            )
                            for k, s in self.pending.items()
                        },
                    )
                )
            if window == "5m":
                ring = [p for p in self.ring if cutoff <= p.timestamp <= now]
                if ring:
                    first_bucket = int(min(p.timestamp for p in ring) // 60) * 60
                    points = [p for p in points if p.timestamp < first_bucket] + ring
                    resolution = (
                        self.sample_seconds
                        if not any(p.timestamp < first_bucket for p in points)
                        else 60
                    )
            if window != "5m" or len(points) > max_points:
                resolution = math.ceil(max(resolution, WINDOWS[window] / max_points))
                points = combine(points, resolution, max_points)
            return HistoryResponse(
                window=window,
                resolution_seconds=resolution,
                source=self.source,
                points=sorted(points, key=lambda p: p.timestamp)[-max_points:],
            )

    def close(self) -> None:
        with self.lock:
            self._flush(time.time())
            if self.connection is not None:
                self.connection.close()
                self.connection = None
