"""Synthetic browser-test server, deliberately outside the installed package."""

import os
import tempfile
from pathlib import Path

from monitor.api import create_app
from monitor.config import Settings
from tests.fakes import FakePipeline

app = create_app(
    Settings(sample_seconds=0.1, allowed_origins=["http://127.0.0.1:5501"]),
    FakePipeline(Path(tempfile.gettempdir()) / f"gpu-monitor-ui-{os.getpid()}.db"),
)
