# Source publication and integration review — 2026-11-10

Repository: [buruj7722-wq/gpu-monitor](https://github.com/buruj7722-wq/gpu-monitor).
Visibility is public by the owner's explicit request. Source publication was
subsequently authorized. Default main remains at d8215a5; nothing has been
merged, tagged, released or installed as a production service by publication.

## Review entry points

- [Complete integration PR #33](https://github.com/buruj7722-wq/gpu-monitor/pull/33)
  targets main with the complete runnable product. It links issues #1–#15.
- Scoped draft PRs #16–#31 separate architecture, governance, collectors,
  integrations, history, alerts, APIs, UI, CI, validation, deployment and docs.
- [CI validation PR #32](https://github.com/buruj7722-wq/gpu-monitor/pull/32)
  adds dedicated `ci/**` push checks and fixes the proxy startup-test race.
- [Machine-readable PR index](github-prs.json) records exact branch/base mappings.
  [Roadmap](roadmap.md) links issues, specifications and review bodies.

Intermediate migration commits are review stages, not independently deployable
releases. Promote the complete tested integration coherently after review so
main stays runnable. No component or integration PR is merged automatically.

## Remote validation evidence

The [complete successful run](https://github.com/buruj7722-wq/gpu-monitor/actions/runs/42857906742)
validated code commit c61bfbc03ddd5aa964393c16140a4324b8eed107 on Ubuntu 24.04
with Python 3.12.16 and Node 22. Every job stage succeeded:

- Pinned dependency installation, Ruff, formatting, strict Mypy and JS checkJs.
- Unit/integration/API/WebSocket/proxy tests: 48 passed, one deliberately skipped
  real-hardware test. Hardware failure cases use mocks.
- Local Chart.js asset reproducibility, wheel/sdist build and package inventory.
- Desktop/mobile browser tests with synthetic fixture telemetry.
- Bandit, Python dependency audit, npm audit and secret scan.

The first push run failed because the proxy test waited for HTML availability
rather than completion of the collector's first sample. That race was fixed;
a separate regression confirms the API intentionally returns 503 during
initialization. No production behavior was weakened to pass the test.

This report/index commit changes publication documentation only. For the latest
commit's checks, use [PR #33 checks](https://github.com/buruj7722-wq/gpu-monitor/pull/33/checks),
which also provides current artifacts and screenshots. Earlier local A40 and
15-minute performance evidence remains in [validation.md](validation.md).

## Remaining approvals

- Review and merge of the coherent integration.
- Repository protection: public visibility removed the earlier plan restriction;
  rulesets API is available and returned an empty list. No rules were applied.
- Native service installation/activation and trusted LAN HTTPS configuration.
- Actual AI-load, memory-pressure and multiprocess benchmark window.
- Project license and stable release/tag approval.

Publication grants none of these approvals implicitly. The older failing unit
remains stopped under the owner's earlier approval; the loopback preview is a
separate process. No firewall, NVIDIA driver, CUDA or hardware-control setting
was changed.
