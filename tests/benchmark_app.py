"""One-Hz synthetic benchmark instance, never included in production packaging."""

import os
import tempfile
from pathlib import Path

from monitor.api import create_app
from monitor.config import Settings
from tests.fakes import FakePipeline

app = create_app(
    Settings(),
    FakePipeline(Path(tempfile.gettempdir()) / f"gpu-monitor-benchmark-{os.getpid()}.db"),
)
