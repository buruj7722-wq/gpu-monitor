# Changelog

## Unreleased — 0.5.0.dev0

- Replace the development Flask server with a single-worker FastAPI service while preserving legacy routes and MiB fields.
- Add isolated NVML metrics, multi-GPU support, reconnect/backoff and one-query XML fallback.
- Add server telemetry, GPU processes, bounded activity analysis and optional LM Studio model listings.
- Add bilingual dashboard, local charts, shared WebSocket updates, SQLite history and configurable sustained alerts.
- Add validated TOML, structured logging, secure proxy/service templates, backup/recovery tools and automated quality checks.
- Unavailable values are now null instead of misleading zeros. Consumers must handle null.
- Production installation, branch protection, merge and release remain approval gates. Source branches and PRs are published; no tag or release is claimed.

## Existing baseline (unversioned)

Flask dashboard with GPU index zero and compute-process list. Historical commits
are retained. No retrospective version tag has been created.
