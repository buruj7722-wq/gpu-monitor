from pathlib import Path

from fastapi.testclient import TestClient

from monitor.api import create_app
from monitor.config import Settings


def test_dashboard_assets_are_local_and_safe(tmp_path):
    app = create_app(Settings(database=tmp_path / "h.db", allowed_hosts=["testserver"]))
    # Asset routes don't need lifespan, hardware or a running collector.
    client = TestClient(app)
    html = client.get("/")
    assert html.status_code == 200
    assert 'dir="rtl"' in html.text
    assert "{{" not in html.text
    assert "/static/vendor/chart.umd.min.js" in html.text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/vendor/chart.umd.min.js").status_code == 200
    script = Path("static/app.js").read_text()
    assert "innerHTML" not in script
    assert "textContent" in script
    assert "new WebSocket" in script
    assert "cdn." not in html.text
