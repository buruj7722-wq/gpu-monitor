# Proposed release notes — not published

Candidate: 0.5.0.dev0. Stable 1.0.0 is withheld until readiness gates pass.

The dashboard now combines NVIDIA GPU, Ubuntu resources, GPU workload metadata,
historical trends and sustained alerts in one service. Unsupported sensors are
explicitly unavailable and a missing driver no longer prevents server monitoring.

Upgrade requires a new environment with pinned FastAPI dependencies, TOML
configuration and an approved systemd migration to a dedicated service account.
The previous venv and Flask unit are not sufficient for the new code. Keep the
legacy API MiB units; handle null values. New clients should use /api/metrics.

SQLite schema 1 is new; preserve backups before future upgrades. See the
migration and recovery guides. No driver, CUDA, firewall or hardware setting is
changed. LM Studio remains opt-in and does not expose inference content.

Known release gates: owner-selected project license; production deployment as
non-root; installed TLS/auth verification and reboot test; approved remote CI
and PR review; available GitHub protection plan; AI-load/memory/multiprocess
performance scenarios not run without an approved workload window.
