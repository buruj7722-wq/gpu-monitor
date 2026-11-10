"""Native service entry point. LAN access belongs behind the authenticated proxy."""

import uvicorn

from monitor.logging import configure_logging


def main() -> None:
    configure_logging()
    uvicorn.run(
        "monitor.api:create_app",
        factory=True,
        host="127.0.0.1",
        port=5000,
        log_config=None,
        workers=1,
        access_log=False,
        proxy_headers=True,
        forwarded_allow_ips="127.0.0.1",
    )
