# Engineering rules

Read ARCHITECTURE.md and docs/roadmap.md before changes. This is one Python
service; collectors must never run per HTTP request or WebSocket connection.
Use typed models, null for unavailable sensors and explicit source status.
Never fabricate production telemetry or infer model performance from GPU load.

Work on one issue branch at a time, stacked on its dependency when unmerged.
No direct development on main, force pushes, history deletion or lost local work.
Use Conventional Commits. Associate changes with a real GitHub issue when
available; local Lxx identifiers are not GitHub issue numbers. Keep PRs scoped.

Run `.venv/bin/ruff check .`, `.venv/bin/ruff format --check .`,
`.venv/bin/mypy monitor app.py gpu.py`, `.venv/bin/pytest`, `npm run typecheck`,
`.venv/bin/python -m build --no-isolation` and security checks documented in
CONTRIBUTING.md. Run focused tests during development and full checks before PR.
Tests use NVML mocks; real-GPU checks are opt-in and never load AI models.

Do not push, merge, publish tags/releases, change protection or deploy without
the user's explicit approval. No production changes, driver/CUDA updates, power,
clock or cooling controls, firewall changes, stress workloads or file/database
deletion without approval. Prepare concrete reviewable changes first.
Do not read prompts, responses, process environments or command lines. Secrets
stay outside Git and logs. Do not add a project LICENSE until the owner chooses.

Report actual checks and limitations. Mock success is not hardware validation.
