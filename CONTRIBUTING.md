# Contributing

Use Python 3.12+, an isolated .venv and the pinned requirements-dev.txt.
The existing `venv/` is retained for rollback; do not install into system Python.
Use Node 22 LTS for the optional JavaScript type check (`npm ci`). No Node runtime
is needed to serve the dashboard.

Follow GitHub Flow and Conventional Commits. Search existing issues/labels before
creating new ones. Use the templates. Until GitHub is accessible, use the local
ledger and issue/PR bodies in docs/issues and docs/prs. Stacked PRs target their
dependency branch until it merges, then retarget the default branch. Do not merge
dependencies just to continue local development.

Quality gate:
```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy monitor app.py gpu.py
.venv/bin/pytest
npm run typecheck
.venv/bin/python -m build --no-isolation
.venv/bin/bandit -r monitor -c pyproject.toml
.venv/bin/pip-audit -r requirements.txt
.venv/bin/detect-secrets scan --all-files --exclude-files '(package-lock.json|requirements.*|static/vendor/.*|.*\\.lock)' > /tmp/gpu-monitor-secrets.json
python scripts/check_secrets.py /tmp/gpu-monitor-secrets.json
```

Use tools/benchmark.py for a bounded client benchmark against a separately
started test instance. Never stress the production host without permission.
See docs/operations for backup, restore, migration and deployment.
