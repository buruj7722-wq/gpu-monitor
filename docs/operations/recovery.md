# Backup, restore, upgrade and rollback

The database contains aggregate operational metadata, not prompts or responses.
Keep backups outside the repository, with the same restricted permissions as
the database. Back up configuration, the previous wheel and systemd/Nginx files
separately; never bundle secret environment files into a public artifact.

Online backup uses SQLite's backup API, including committed WAL data:
```bash
sudo -u gpu-monitor /opt/gpu-monitor/venv/bin/python /path/to/checkout/tools/backup.py /var/lib/gpu-monitor/history.sqlite3 /var/lib/gpu-monitor/history-backup-YYYYMMDD.sqlite3
```
If the checkout is under /root, the service account cannot read that script.
Copy the reviewed tool to an accessible operator directory first, or run it as
an authorized administrator and set backup ownership/permissions afterwards.
The tool refuses overwrite, verifies integrity, and preserves failed artifacts
for inspection. A raw copy of only the main database while WAL is active is not
a valid backup strategy.

Restore procedure (requires approval): stop the service, preserve the entire
current database/WAL/SHM set under new names, restore the verified backup to a
fresh path, set ownership to gpu-monitor and mode 0600, configure that path and
start. Do not leave old WAL/SHM sidecars beside a restored main database. Verify
`PRAGMA integrity_check`, schema version and historical queries before retiring
the preserved files. Never delete the user's database as an automatic repair.

Upgrade procedure: verify tests and the new wheel, make backups, note the exact
old artifact/config versions, stop the service, install the reviewed wheel into
a new virtual environment under /opt/gpu-monitor, validate imports/config as the
service user, switch ExecStart to that environment, daemon-reload and start.
Retain the previous environment. Validate health, GPU, WSS and history.

Rollback: stop the service, restore the previous ExecStart/config and compatible
wheel/environment. If a future migration changed schema incompatibly, restore
the matching verified database backup to a fresh path. Reload systemd, start and
verify. The old Flask baseline cannot read the new history; it also needs its
original code/template/static files together, not just the old venv.

SQLite schema is currently version 1. Unknown schemas are left untouched and
storage degrades; live monitoring continues. No destructive automatic migration
or downgrade is implemented.
