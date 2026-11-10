# Release 0.0.1

Initial source and package release, authorized by the owner. This version replaces
the unpublished development label 0.5.0.dev0; it does not certify production readiness.

## Included

- One shared, typed Python service for NVIDIA GPU and Ubuntu resource monitoring.
- Nullable sensor readings and explicit source availability/freshness.
- GPU workload metadata, opt-in LM Studio model listings, SQLite history and alerts.
- Cached REST APIs, bounded WebSocket streaming and an Arabic/English dashboard.
- WebSocket acceptance/cancellation cleanup, pinned CI and deployment/recovery templates.

Integration PR #33 and cancellation PR #34 were merged into main. Scoped PRs
#16–#32 are included in the integration; redundant open review stages were closed.
Release metadata is tracked under issue #15.

## Installation and compatibility

Python 3.12+ is required. Install the attached wheel in an isolated environment;
see README.md for configuration and startup. The old Flask environment must be
replaced before using the new service. Legacy API memory units remain MiB;
unavailable readings are null. New consumers should use /api/metrics.
SQLite uses schema 1. Follow docs/operations/migration.md and recovery.md and
preserve backups before an upgrade.

## Validation and limitations

Local release checks passed: Ruff lint/format, strict Mypy, JavaScript types and
formatting, 49 Python tests, two desktop/mobile browser tests, wheel/sdist build,
vendored asset verification, Bandit, Python/npm dependency audits and secret scan.
One opt-in real-GPU test was skipped; the Python suite reports the existing
Starlette TestClient deprecation warning. Real-GPU checks are
opt-in; mock success is not hardware validation. Earlier read-only A40 observations
and idle benchmarks are recorded in docs/validation.md.

Production non-root installation, trusted TLS/authentication and reboot validation
remain outstanding, as do AI-load/memory-pressure/multiprocess benchmarks and live
LM Studio validation. No deployment or hardware/driver/firewall changes accompany
this release. The project license is still undecided; the bundled Chart.js license
covers that dependency only.
