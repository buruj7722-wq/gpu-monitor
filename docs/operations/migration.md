# Migration and compatibility

Baseline: Flask, GPU index zero, MiB in /api/gpu and /api/processes, HTTP port
5000. Import-time nvmlInit currently prevents startup without a driver.

The new app keeps `python app.py`, `/`, `/api/gpu` and `/api/processes`.
Legacy memory fields remain MiB; CUDA remains the integer driver API version.
Unsupported numbers become null (previous misleading zero behavior is removed).
New consumers use schema_version=1 in `/api/metrics`: bytes, seconds, watts,
Celsius and MHz are named explicitly. API handlers read cached data only.

The original venv is retained; use .venv for the new dependencies. Back up the
existing systemd unit before an approved installation. Never run an old and new
collector against the same database. TOML configuration is new; no existing
configuration or historical database exists in the audited baseline.

SQLite user_version identifies the schema. Unknown versions must fail storage
initialization without modifying existing tables; live telemetry continues in a
degraded state. Before any future schema migration, use the online backup tool,
then apply an explicit versioned migration. Downgrade only to a compatible schema
or restore a verified backup; do not blindly reuse a newer database.
