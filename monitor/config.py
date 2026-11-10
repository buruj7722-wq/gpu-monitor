"""Validated non-secret configuration. Unknown keys fail startup."""

import os
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Threshold(ConfigModel):
    warning: float = Field(default=90, ge=0, le=100)
    critical: float = Field(default=98, ge=0, le=100)

    @model_validator(mode="after")
    def ordered(self) -> "Threshold":
        if self.warning >= self.critical:
            raise ValueError("warning must be lower than critical")
        return self


class AlertConfig(ConfigModel):
    sustain_seconds: float = Field(default=30, ge=0, le=3600)
    recovery_seconds: float = Field(default=10, ge=0, le=3600)
    hysteresis_percent: float = Field(default=5, ge=0, le=50)
    hysteresis_c: float = Field(default=3, ge=0, le=30)
    gpu_unavailable_seconds: float = Field(default=10, ge=0, le=3600)
    cpu: Threshold = Field(default_factory=Threshold)
    ram: Threshold = Field(default_factory=Threshold)
    vram: Threshold = Field(default_factory=Threshold)
    utilization: Threshold = Field(default_factory=Threshold)
    power: Threshold = Field(default_factory=Threshold)
    disk: Threshold = Field(default_factory=lambda: Threshold(warning=85, critical=95))
    temperature_warning_c: float | None = Field(default=None, gt=0, le=150)
    temperature_critical_c: float | None = Field(default=None, gt=0, le=150)
    network_interfaces: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def thermal_pair(self) -> "AlertConfig":
        w, c = self.temperature_warning_c, self.temperature_critical_c
        if (w is None) != (c is None) or (w is not None and c is not None and w >= c):
            raise ValueError("set both thermal thresholds with warning < critical")
        return self


class LMConfig(ConfigModel):
    enabled: bool = False
    base_url: str = "http://127.0.0.1:1234"
    interval_seconds: float = Field(default=15, ge=5, le=3600)
    timeout_seconds: float = Field(default=2, gt=0, le=10)
    max_response_bytes: int = Field(default=1048576, ge=1024, le=4194304)
    token_env: str | None = None

    @model_validator(mode="after")
    def valid_url(self) -> "LMConfig":
        url = urlsplit(self.base_url)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in {"", "/"}
        ):
            raise ValueError("base_url must be an explicit HTTP origin without credentials")
        return self


class Settings(ConfigModel):
    sample_seconds: float = Field(default=1, ge=0.1, le=60)
    process_seconds: float = Field(default=5, ge=1, le=300)
    gpu_fallback: bool = True
    database: Path = Path("data/history.sqlite3")
    retention_days: int = Field(default=7, ge=1, le=90)
    stale_seconds: float = Field(default=5, ge=1, le=300)
    activity_threshold: float = Field(default=5, ge=0, le=100)
    activity_window_seconds: int = Field(default=300, ge=30, le=3600)
    disk_include: list[str] = Field(default_factory=list)
    disk_exclude: list[str] = Field(default_factory=lambda: ["/snap", "/boot/efi"])
    network_exclude: list[str] = Field(default_factory=lambda: ["lo"])
    allowed_hosts: list[str] = Field(default_factory=lambda: ["127.0.0.1", "localhost", "[::1]"])
    allowed_origins: list[str] = Field(
        default_factory=lambda: ["http://127.0.0.1:5000", "http://localhost:5000"]
    )
    max_connections: int = Field(default=100, ge=1, le=1000)
    alerts: AlertConfig = Field(default_factory=AlertConfig)
    lmstudio: LMConfig = Field(default_factory=LMConfig)

    @model_validator(mode="after")
    def safe_limits(self) -> "Settings":
        if self.stale_seconds < self.sample_seconds * 2:
            raise ValueError("stale_seconds must be at least twice sample_seconds")
        if not self.allowed_hosts or "*" in self.allowed_hosts:
            raise ValueError("explicit allowed_hosts required")
        for origin in self.allowed_origins:
            u = urlsplit(origin)
            if (
                u.scheme not in {"http", "https"}
                or not u.netloc
                or u.path
                or u.query
                or u.fragment
                or u.username
            ):
                raise ValueError("allowed_origins must contain exact HTTP origins")
        return self


def load_settings(path: str | Path | None = None) -> Settings:
    chosen = path or os.environ.get("GPU_MONITOR_CONFIG")
    if not chosen:
        return Settings()
    with Path(chosen).open("rb") as stream:
        return Settings.model_validate(tomllib.load(stream))
