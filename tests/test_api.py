import time

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from monitor.api import create_app
from monitor.config import Settings
from monitor.history import HistoryStore
from monitor.models import GPU, GPUProcess, GPUReading, Snapshot, Source


class FakePipeline:
    def __init__(self, path):
        self.history = HistoryStore(path)
        self.calls = 0
        self.closed = False

    def sample(self):
        self.calls += 1
        snapshot = Snapshot(
            timestamp=time.time(),
            collector=Source(status="ok"),
            gpu=GPUReading(
                source=Source(status="ok"),
                devices=[
                    GPU(
                        index=0,
                        uuid="GPU-0",
                        name="A40",
                        memory_used_bytes=1024**3,
                        memory_total_bytes=2 * 1024**3,
                    )
                ],
                processes=[
                    GPUProcess(
                        pid=1,
                        gpu_uuid="GPU-0",
                        process_type="compute",
                        gpu_memory_bytes=1024**2,
                        name="<script>unsafe</script>",
                    )
                ],
            ),
        )
        self.history.record(snapshot)
        return snapshot

    def close(self):
        self.closed = True
        self.history.close()


def make_app(tmp_path):
    pipeline = FakePipeline(tmp_path / "history.db")
    settings = Settings(
        sample_seconds=0.1, allowed_hosts=["testserver"], allowed_origins=["http://testserver"]
    )
    return create_app(settings, pipeline), pipeline


def wait_ready(client):
    for _ in range(50):
        if client.get("/api/health").status_code == 200:
            return
        time.sleep(0.01)
    pytest.fail("collector did not become ready")


def test_api_legacy_security_and_history(tmp_path):
    app, pipeline = make_app(tmp_path)
    with TestClient(app) as client:
        wait_ready(client)
        old = client.get("/api/gpu").json()
        assert old["memory_used"] == 1024
        assert old["fan"] is None
        assert client.get("/api/processes").json()[0]["memory"] == 1
        assert client.get("/api/metrics").json()["schema_version"] == 1
        assert client.get("/api/system").status_code == 200
        assert client.get("/api/history?window=7d").status_code == 200
        assert client.get("/api/history?window=forever").status_code == 422
        assert client.get("/api/history?max_points=1000000").status_code == 422
        assert client.get("/api/metrics", headers={"host": "evil.invalid"}).status_code == 400
        assert (
            "frame-ancestors 'none'" in client.get("/api/health").headers["content-security-policy"]
        )
        app.state.runtime.last_completed = time.monotonic() - 100
        assert client.get("/api/health").status_code == 503
        assert any(
            a["id"] == "collector/stopped" for a in client.get("/api/metrics").json()["alerts"]
        )
    assert pipeline.closed


def test_websocket_disconnect_reconnect_and_origin(tmp_path):
    app, pipeline = make_app(tmp_path)
    with TestClient(app) as client:
        wait_ready(client)
        before = pipeline.calls
        for _ in range(3):
            with client.websocket_connect(
                "/ws/metrics", headers={"origin": "http://testserver"}
            ) as ws:
                assert ws.receive_json()["gpu"]["devices"][0]["name"] == "A40"
        assert pipeline.calls <= before + 3
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(
                "/ws/metrics", headers={"origin": "https://evil.invalid"}
            ):
                pass
    assert not app.state.runtime.clients
