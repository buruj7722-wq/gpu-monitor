import asyncio
import time

import pytest
from pydantic import ValidationError

from monitor.config import Settings, load_settings
from monitor.models import Snapshot
from monitor.normalization import number, ratio
from monitor.runtime import Runtime


def test_config_validation(tmp_path):
    with pytest.raises(ValidationError):
        Settings(sample_seconds=0)
    with pytest.raises(ValidationError):
        Settings(allowed_hosts=["*"])
    with pytest.raises(ValidationError):
        Settings(alerts={"cpu": {"warning": 99, "critical": 50}})
    path = tmp_path / "config.toml"
    path.write_text("retention_days = 3\n")
    assert load_settings(path).retention_days == 3
    path.write_text("typo = 1\n")
    with pytest.raises(ValidationError):
        load_settings(path)


def test_normalization():
    assert number(float("nan")) is None
    assert number(-1) is None
    assert number(101, 100) is None
    assert ratio(2, 0) is None
    assert ratio(2, 4) == 50


async def test_one_sampler_backpressure_and_stop():
    calls = 0
    closed = []

    def sample():
        nonlocal calls
        calls += 1
        return Snapshot(timestamp=time.time())

    runtime = Runtime(Settings(sample_seconds=0.1), sample, lambda: closed.append(True))
    queues = [runtime.subscribe() for _ in range(20)]
    await runtime.start()
    await runtime.start()
    await asyncio.sleep(0.35)
    assert 2 <= calls <= 6
    assert all(q.qsize() == 1 for q in queues)
    assert runtime.replaced_messages > 0
    runtime.unsubscribe(queues[0])
    await runtime.stop()
    count = calls
    await asyncio.sleep(0.15)
    assert calls == count
    assert closed == [True]
    assert runtime.task is None
