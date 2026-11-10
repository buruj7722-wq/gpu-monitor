import sqlite3

import pytest

from monitor.config import load_settings
from scripts.render_nginx import render
from tools.backup import backup


def test_example_config_is_valid():
    settings = load_settings("config.example.toml")
    assert settings.sample_seconds == 1
    assert not settings.lmstudio.enabled


def test_render_proxy_covers_all_paths_and_rejects_injection():
    config = render(
        "monitor.example.internal",
        "/etc/ssl/monitor.pem",
        "/etc/ssl/monitor.key",
        "/etc/nginx/monitor.htpasswd",
    )
    assert "__SERVER" not in config
    assert 'auth_basic "GPU Monitor"' in config
    assert "location / {" in config
    assert "proxy_set_header Upgrade $http_upgrade" in config
    with pytest.raises(ValueError):
        render("evil; include /etc/passwd", "/cert", "/key", "/passwd")
    with pytest.raises(ValueError):
        render("host", "/cert;evil", "/key", "/passwd")


def test_backup_restorable_and_never_overwrites(tmp_path):
    source, destination = tmp_path / "source.db", tmp_path / "backup.db"
    with sqlite3.connect(source) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE evidence (value INTEGER)")
        db.execute("INSERT INTO evidence VALUES (42)")
    backup(source, destination)
    with sqlite3.connect(destination) as db:
        assert db.execute("SELECT value FROM evidence").fetchone()[0] == 42
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with pytest.raises(FileExistsError):
        backup(source, destination)
