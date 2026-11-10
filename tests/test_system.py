import socket
from collections import namedtuple
from types import SimpleNamespace as NS

import pytest

from monitor.collectors.system import Rates, SystemCollector
from monitor.config import Settings


def test_rates_first_reset_and_disappearing():
    rates = Rates()
    assert rates.delta("n", (100, 200), 1) == [None, None]
    assert rates.delta("n", (300, 400), 3) == [100, 100]
    assert rates.delta("n", (2, 500), 4) == [None, 100]
    rates.retain(set())
    assert not rates.previous


class FakeSystem:
    tick = 0

    def cpu_times(self, percpu):
        t = namedtuple("Times", "user system idle iowait guest guest_nice")
        self.tick += 1
        return [t(10 * self.tick, 5 * self.tick, 30 * self.tick, 5 * self.tick, 0, 0)] * 2

    def cpu_count(self, logical):
        return 2 if logical else 1

    def cpu_freq(self):
        return NS(current=2000)

    def sensors_temperatures(self):
        return {}

    def virtual_memory(self):
        return NS(total=1000, used=400, available=600, percent=40)

    def swap_memory(self):
        return NS(total=0, used=0, percent=0)

    def disk_partitions(self, all):
        return [
            NS(mountpoint="/", device="/dev/root", fstype="ext4"),
            NS(mountpoint="/tmp", device="/dev/root", fstype="ext4"),
            NS(mountpoint="/proc", device="proc", fstype="proc"),
        ]

    def disk_usage(self, mount):
        return NS(total=1000, used=600, free=400, percent=60)

    def disk_io_counters(self, **kwargs):
        return {
            "sda": NS(
                read_bytes=self.tick * 100,
                write_bytes=self.tick * 200,
                read_count=self.tick * 2,
                write_count=self.tick * 3,
            )
        }

    def net_if_stats(self):
        return {"eth0": NS(isup=True)}

    def net_if_addrs(self):
        return {"eth0": [NS(family=socket.AF_INET, address="192.0.2.1")]}

    def net_io_counters(self, **kwargs):
        return {
            "eth0": NS(
                bytes_recv=self.tick * 100,
                bytes_sent=self.tick * 200,
                errin=1,
                errout=2,
                dropin=3,
                dropout=4,
            )
        }

    def boot_time(self):
        return 1


def test_system_cpu_memory_mounts_network(monkeypatch):
    monkeypatch.setattr("monitor.collectors.system.Path.exists", lambda p: True)
    monkeypatch.setattr(SystemCollector, "_mount_identity", staticmethod(lambda p: 1))
    collector = SystemCollector(Settings(), FakeSystem())
    first = collector.collect(now=10, monotonic=10)
    assert first.cpu.usage_percent is None
    assert first.network[0].receive_bytes_per_second is None
    result = collector.collect(now=12, monotonic=12)
    assert round(result.cpu.usage_percent) == 30
    assert result.cpu.per_core_percent == pytest.approx([30, 30])
    assert result.cpu.physical_cores == 1
    assert result.memory.percent == 40
    assert len(result.disks) == 1
    assert result.disk_io[0].read_bytes_per_second == 50
    assert result.network[0].receive_bytes_per_second == 50
    assert result.network[0].addresses == ["192.0.2.1"]
    assert result.network[0].drops_out == 4
    assert result.source.status == "ok"
    assert result.cpu.temperature_c is None


def test_missing_memory_does_not_stop_network():
    class Failed(FakeSystem):
        def virtual_memory(self):
            raise OSError("unavailable")

    reading = SystemCollector(Settings(), Failed()).collect()
    assert reading.memory.total_bytes is None
    assert reading.network[0].name == "eth0"
    assert reading.source.status == "degraded"


def test_real_system_read_only():
    reading = SystemCollector(Settings()).collect()
    assert reading.memory.total_bytes > 0
    assert reading.info.python
