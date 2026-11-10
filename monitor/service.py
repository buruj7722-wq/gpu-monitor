"""Compose the single-service data pipeline; boundaries fail independently."""

import hashlib
import logging
import socket
import time

from monitor.alerts import AlertEngine
from monitor.collectors.gpu import GPUCollector
from monitor.collectors.system import SystemCollector
from monitor.collectors.workloads import ActivityAnalyzer, ProcessCollector
from monitor.config import Settings
from monitor.history import HistoryStore
from monitor.integrations.lmstudio import LMStudioAdapter
from monitor.models import GPUReading, Observer, Snapshot, Source, SystemReading

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, settings: Settings) -> None:
        self.stale_seconds = settings.stale_seconds
        self.gpu = GPUCollector(fallback=settings.gpu_fallback)
        self.system = SystemCollector(settings)
        self.processes = ProcessCollector(settings.process_seconds)
        self.activity = ActivityAnalyzer(settings)
        self.integration = LMStudioAdapter(settings.lmstudio)
        self.history = HistoryStore(
            settings.database, settings.retention_days, settings.sample_seconds
        )
        self.alerts = AlertEngine(settings.alerts)
        self.host_id = hashlib.sha256(socket.gethostname().encode()).hexdigest()[:16]

    def sample(self) -> Snapshot:
        now, mono = time.time(), time.monotonic()
        try:
            gpu = self.gpu.collect(now, mono)
            gpu = self.processes.collect(gpu, self.gpu, now, mono)
        except Exception as exc:
            logger.error("gpu_pipeline_failed:%s", type(exc).__name__)
            gpu = GPUReading(
                source=Source(status="unavailable", timestamp=now, error=type(exc).__name__)
            )
        try:
            system = self.system.collect(now, mono)
        except Exception as exc:
            logger.error("system_pipeline_failed:%s", type(exc).__name__)
            system = SystemReading(
                source=Source(status="unavailable", timestamp=now, error=type(exc).__name__)
            )
        snapshot = Snapshot(
            stale_after_seconds=self.stale_seconds,
            host_id=self.host_id,
            timestamp=now,
            collector=Source(status="ok", timestamp=now, last_success=now),
            gpu=gpu,
            system=system,
            activity=self.activity.analyze(gpu, mono),
            integration=self.integration.collect(now, mono),
        )
        self.history.record(snapshot)
        snapshot = snapshot.model_copy(update={"storage": self.history.source})
        return snapshot.model_copy(
            update={
                "alerts": self.alerts.evaluate(snapshot, mono),
                "observer": Observer(
                    database_write_bytes=self.history.write_bytes,
                    database_write_operations=self.history.write_operations,
                ),
            }
        )

    def close(self) -> None:
        for close in [self.gpu.close, self.integration.close, self.history.close]:
            try:
                close()
            except Exception as exc:
                logger.warning("resource_close_failed:%s", type(exc).__name__)
