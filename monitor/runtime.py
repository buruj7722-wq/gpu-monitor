"""One sequential collector, bounded fan-out, no hardware work in request handlers."""

import asyncio
import logging
import time
from collections.abc import Callable

import psutil

from monitor.config import Settings
from monitor.models import Snapshot

logger = logging.getLogger(__name__)


class Runtime:
    def __init__(
        self,
        settings: Settings,
        sample: Callable[[], Snapshot],
        close: Callable[[], None] = lambda: None,
    ) -> None:
        self.settings = settings
        self.sample = sample
        self.close_resources = close
        self.latest: Snapshot | None = None
        self.last_completed: float | None = None
        self.clients: set[asyncio.Queue[Snapshot]] = set()
        self.task: asyncio.Task[None] | None = None
        self.stop_event = asyncio.Event()
        self.dropped_samples = 0
        self.replaced_messages = 0
        self.errors = 0
        self.count = 0
        self.api_response_ms: float | None = None
        self.websocket_send_ms: float | None = None
        self.process = psutil.Process()
        self.process.cpu_percent()

    def subscribe(self) -> asyncio.Queue[Snapshot]:
        if len(self.clients) >= self.settings.max_connections:
            raise RuntimeError("connection_limit")
        queue: asyncio.Queue[Snapshot] = asyncio.Queue(maxsize=1)
        self.clients.add(queue)
        if self.latest is not None:
            queue.put_nowait(self.latest)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Snapshot]) -> None:
        self.clients.discard(queue)

    async def start(self) -> None:
        if self.task is not None:
            return
        self.stop_event.clear()
        self.task = asyncio.create_task(self.run(), name="metrics-collector")

    async def stop(self) -> None:
        self.stop_event.set()
        if self.task is not None:
            await self.task  # let the in-flight thread finish before closing NVML/SQLite
            self.task = None
        await asyncio.to_thread(self.close_resources)
        self.clients.clear()

    async def run(self) -> None:
        deadline = time.monotonic()
        while not self.stop_event.is_set():
            started = time.monotonic()
            try:
                snapshot = await asyncio.to_thread(self.sample)
                self.count += 1
                if (
                    snapshot.gpu.source.status in {"degraded", "unavailable"}
                    or snapshot.system.source.status != "ok"
                ):
                    self.errors += 1
                observer = snapshot.observer.model_copy(
                    update={
                        "collection_latency_ms": (time.monotonic() - started) * 1000,
                        "active_connections": len(self.clients),
                        "dropped_samples": self.dropped_samples,
                        "replaced_messages": self.replaced_messages,
                        "collection_errors": self.errors,
                        "collection_count": self.count,
                        "collection_error_rate": self.errors / self.count,
                        "cpu_percent": self.process.cpu_percent(),
                        "rss_bytes": self.process.memory_info().rss,
                        "api_response_ms": self.api_response_ms,
                        "websocket_send_ms": self.websocket_send_ms,
                    }
                )
                snapshot = snapshot.model_copy(
                    update={
                        "sequence": self.count,
                        "observer": observer,
                        "published_at": time.time(),
                    }
                )
                self.latest = snapshot
                self.last_completed = time.monotonic()
                for queue in tuple(self.clients):
                    if queue.full():
                        queue.get_nowait()
                        self.replaced_messages += 1
                    queue.put_nowait(snapshot)
            except Exception as exc:
                self.count += 1
                self.errors += 1
                logger.error("collection_failed:%s", type(exc).__name__)
            deadline += self.settings.sample_seconds
            now = time.monotonic()
            if deadline < now:
                missed = int((now - deadline) / self.settings.sample_seconds) + 1
                self.dropped_samples += missed
                deadline += missed * self.settings.sample_seconds
            try:
                await asyncio.wait_for(
                    self.stop_event.wait(), timeout=max(0, deadline - time.monotonic())
                )
            except TimeoutError:
                pass

    def stale(self) -> bool:
        return (
            self.last_completed is None
            or time.monotonic() - self.last_completed > self.settings.stale_seconds
        )
