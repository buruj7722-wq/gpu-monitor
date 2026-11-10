import sqlite3

import pytest

from monitor.history import HistoryStore
from monitor.models import CPU, Snapshot, SystemReading


def sample(t, value):
    return Snapshot(timestamp=t, system=SystemReading(cpu=CPU(usage_percent=value)))


def test_initialization_aggregation_reopen_and_gaps(tmp_path):
    path = tmp_path / "history.sqlite3"
    store = HistoryStore(path)
    store.record(sample(120, 20))
    store.record(sample(121, 40))
    store.record(sample(240, 80))
    assert store.write_operations == 1
    hour = store.query("1h", now=250)
    assert len(hour.points) == 2  # no invented sample for minute 180
    assert hour.points[0].metrics["cpu/usage_percent"].mean == 30
    assert hour.points[0].metrics["cpu/usage_percent"].count == 2
    assert len(store.query("5m", now=250).points) == 3
    # Flush with a contemporary synthetic timestamp so retention doesn't remove fixtures.
    store._flush(250)
    store.connection.close()
    reopened = HistoryStore(path)
    reopened.initialize()
    assert reopened.query("1h", now=250).points[0].metrics["cpu/usage_percent"].maximum == 40
    reopened.connection.close()


def test_retention_and_query_bounds(tmp_path):
    store = HistoryStore(tmp_path / "h.db", retention_days=1)
    store.record(sample(120, 1))
    store.record(sample(180, 2))
    store.record(sample(200000, 3))
    store.record(sample(200060, 4))
    rows = store.connection.execute("SELECT bucket FROM aggregates").fetchall()
    assert all(row[0] > 100000 for row in rows)
    assert len(store.query("7d", now=200061, max_points=1).points) <= 1
    with pytest.raises(ValueError):
        store.query("forever")
    store.close()


def test_unknown_schema_preserved_and_live_ring_survives(tmp_path):
    path = tmp_path / "future.db"
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA user_version=99")
        db.execute("CREATE TABLE keep_me (value TEXT)")
        db.execute("INSERT INTO keep_me VALUES ('preserve')")
    store = HistoryStore(path)
    store.record(sample(100, 50))
    assert store.source.status == "unavailable"
    assert store.query("5m", now=101).points
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT value FROM keep_me").fetchone()[0] == "preserve"


def test_no_missing_values_aggregated_as_zero(tmp_path):
    store = HistoryStore(tmp_path / "h.db")
    store.record(sample(120, None))
    store.record(sample(121, 50))
    store.record(sample(180, 90))
    metric = store.query("1h", now=181).points[0].metrics["cpu/usage_percent"]
    assert metric.mean == 50 and metric.count == 1
    store.close()
