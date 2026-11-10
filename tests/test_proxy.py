"""An isolated Nginx instance: temporary certificates and no system configuration changes."""

import asyncio
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import pytest
from websockets.asyncio.client import connect
from websockets.exceptions import InvalidStatus

from scripts.render_nginx import render


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


@pytest.mark.skipif(
    not shutil.which("nginx") or not shutil.which("openssl"),
    reason="nginx and openssl required for isolated TLS proxy test",
)
def test_tls_auth_protects_http_and_websocket():
    with tempfile.TemporaryDirectory(prefix="gpu-monitor-proxy-") as directory:
        root = Path(directory)
        root.chmod(0o755)  # let the unprivileged nginx worker read test-only files
        cert, key, passwords = root / "cert.pem", root / "key.pem", root / "htpasswd"
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-nodes",
                "-newkey",
                "rsa:2048",
                "-subj",
                "/CN=127.0.0.1",
                "-addext",
                "subjectAltName=IP:127.0.0.1",
                "-keyout",
                str(key),
                "-out",
                str(cert),
                "-days",
                "1",
            ],
            check=True,
            capture_output=True,
        )
        # Only a fixture credential, never used for deployment or printed.
        test_password = "fixture-access-only"
        digest = subprocess.run(
            ["openssl", "passwd", "-apr1", "-stdin"],
            input=test_password,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        passwords.write_text("fixture:" + digest + "\n")
        passwords.chmod(0o644)
        backend_port, proxy_port = free_port(), free_port()
        snippet = render("127.0.0.1", str(cert), str(key), str(passwords))
        snippet = (
            snippet.replace("listen 443 ssl;", f"listen 127.0.0.1:{proxy_port} ssl;")
            .replace("listen [::]:443 ssl;", "")
            .replace("http://127.0.0.1:5000", f"http://127.0.0.1:{backend_port}")
        )
        config = root / "nginx.conf"
        config.write_text(
            f"pid {root}/nginx.pid;\nerror_log {root}/error.log;\nevents {{ worker_connections 256; }}\nhttp {{ access_log off; client_body_temp_path {root}/body; proxy_temp_path {root}/proxy;\n"
            + snippet
            + "\n}\n"
        )
        nginx = shutil.which("nginx")
        subprocess.run(
            [nginx, "-t", "-p", str(root), "-c", str(config)], check=True, capture_output=True
        )
        backend = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "tests.ui_app:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(backend_port),
                "--no-access-log",
                "--log-level",
                "warning",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        proxy = subprocess.Popen(
            [nginx, "-p", str(root), "-c", str(config), "-g", "daemon off;"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        context = ssl.create_default_context(cafile=str(cert))
        base = f"https://127.0.0.1:{proxy_port}"
        try:
            with httpx.Client(verify=context, trust_env=False, timeout=2) as client:
                for _ in range(100):
                    try:
                        if client.get(base, auth=("fixture", test_password)).status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.05)
                else:
                    pytest.fail("isolated proxy/backend did not start")
                for path in [
                    "/",
                    "/api/health",
                    "/api/metrics",
                    "/api/system",
                    "/api/gpu",
                    "/api/processes",
                    "/api/history",
                    "/ws/metrics",
                    "/static/app.js",
                    "/docs",
                ]:
                    assert client.get(base + path).status_code == 401
                assert (
                    client.get(base + "/api/metrics", auth=("fixture", test_password)).status_code
                    == 200
                )

            async def websocket_checks():
                import base64

                address = f"wss://127.0.0.1:{proxy_port}/ws/metrics"
                with pytest.raises(InvalidStatus) as denied:
                    async with connect(address, ssl=context):
                        pass
                assert denied.value.response.status_code == 401
                auth = base64.b64encode(f"fixture:{test_password}".encode()).decode()
                async with connect(
                    address, ssl=context, additional_headers={"Authorization": "Basic " + auth}
                ) as ws:
                    assert '"schema_version":1' in await asyncio.wait_for(ws.recv(), 3)

            asyncio.run(websocket_checks())
        finally:
            for process in [proxy, backend]:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
