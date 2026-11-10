"""Opt-in GET /api/v1/models only. Never observes or creates inference traffic."""

import json
import os
import time

import httpx

from monitor.config import LMConfig
from monitor.models import Integration, Source


class LMStudioAdapter:
    def __init__(self, config: LMConfig, client: httpx.Client | None = None) -> None:
        self.config = config
        self.client = client
        self.next_sample = 0.0
        self.latest = Integration()

    def collect(self, now: float | None = None, monotonic: float | None = None) -> Integration:
        if not self.config.enabled:
            return self.latest
        now = time.time() if now is None else now
        mono = time.monotonic() if monotonic is None else monotonic
        if mono < self.next_sample:
            return self.latest
        self.next_sample = mono + self.config.interval_seconds
        try:
            if self.client is None:
                self.client = httpx.Client(
                    timeout=self.config.timeout_seconds, trust_env=False, follow_redirects=False
                )
            token = os.environ.get(self.config.token_env) if self.config.token_env else None
            if self.config.token_env and not token:
                raise ValueError("missing_token")
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            with self.client.stream(
                "GET", self.config.base_url.rstrip("/") + "/api/v1/models", headers=headers
            ) as response:
                response.raise_for_status()
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > self.config.max_response_bytes:
                        raise ValueError("response_too_large")
                    chunks.append(chunk)
                body = json.loads(b"".join(chunks))
            if not isinstance(body, dict) or not isinstance(body.get("models"), list):
                raise ValueError("invalid_models_response")
            loaded = []
            for model in body["models"]:
                if not isinstance(model, dict):
                    raise ValueError("invalid_model")
                if model.get("loaded_instances"):
                    name = model.get("display_name") or model.get("key")
                    if isinstance(name, str):
                        loaded.append(name[:256])
            self.latest = Integration(
                source=Source(status="ok", timestamp=now, last_success=now),
                loaded_models=sorted(set(loaded)),
            )
        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            # Never log URLs, bearer tokens or response content.
            self.latest = Integration(
                source=Source(
                    status="unavailable",
                    timestamp=now,
                    last_success=self.latest.source.last_success,
                    error=type(exc).__name__,
                )
            )
        return self.latest

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
