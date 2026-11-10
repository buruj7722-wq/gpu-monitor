# Validation and release readiness — 2026-11-10

Status: implemented and locally verified; **not yet an approved stable production release**.
Source branches have been pushed and scoped draft PRs #16–#32 and integration PR #33 published. Main
is unchanged; no merge, tag or release has been performed. The real preview runs on loopback
port 5001, independently of the old systemd unit, which the owner approved
stopping temporarily. The preview's SQLite data lives in ignored data/preview.sqlite3.

## Actual checks

| Check | Result / evidence |
|---|---|
| Python unit/integration/API/WebSocket/config/history/alerts | 48 passed with real-hardware opt-in enabled; no skipped acceptance tests in that run |
| General CI without GPU opt-in | Hardware test is intentionally skipped; mocks cover GPU errors and multiple devices |
| Coverage | 90% of monitor statements in the final 48-case suite; this is not proof of exhaustive behavior |
| Ruff lint and formatting | Passed |
| Mypy strict | Passed for monitor, app.py and gpu.py |
| JavaScript checkJs / TypeScript noEmit | Passed |
| Prettier UI format check | Passed |
| Chromium desktop/mobile | 2 passed: Arabic/English, RTL/LTR, local charts, mobile width, safe process text, theme and history selector |
| Bandit | No findings; narrow justified suppressions for fixed nvidia-smi command and XML type annotation only |
| Python dependency audit | No known vulnerabilities found for pinned runtime/development closure |
| npm audit | 0 vulnerabilities |
| Secret detector | 0 findings; only the dummy credential URL and isolated proxy fixture password are allowlisted |
| Wheel and sdist | Built; local HTML/CSS/JS/Chart.js/license verified inside wheel |
| Installed wheel outside checkout | Imports and serves page/assets successfully |
| Nginx isolated TLS test | Passed: all tested paths and WSS reject unauthenticated access with 401; authenticated HTTP/WSS succeed |
| systemd unit syntax | Passed with an existing executable substituted in a temporary copy; actual /opt executable is not installed yet |
| SQLite online backup | Verified readable backup, integrity_check and refusal to overwrite |
| GitHub synchronization | 15 real issues (#1–#15), seven milestones and 18 scoped labels created; scoped PRs #16–#32 and integration PR #33 published |
| Remote GitHub Actions | Passed on integration commit c61bfbc: [complete run](https://github.com/buruj7722-wq/gpu-monitor/actions/runs/42857906742); see publication results |

A pinned Starlette TestClient dependency emits one deprecation warning about
its httpx compatibility path. Tests pass; do not hide this or describe the run
as warning-free. The serving application uses neither TestClient nor pytest.
Browser screenshots are test artifacts under ignored test-results/, generated
with explicitly synthetic fixture telemetry, not proof of the actual A40 readings.

## Actual NVIDIA A40 observations

Outside the restricted execution sandbox, NVML returned NVIDIA A40 / Ampere,
driver 595.91.07 and CUDA Driver 13.2. The installed nvcc Toolkit reported 12.0;
these are distinct version concepts. One idle observation was 32 C, about 25 W,
300 W power limit, 48,305,799,168 total VRAM bytes, ECC enabled and no volatile
ECC errors. Reported operating/slowdown/shutdown temperatures were 88/95/98 C.
These are observed readings, never universal defaults. Fan 0% was returned by
NVML; A40 is passively cooled, so this is not chassis-fan telemetry.

Read-only actual-GPU pytest passed. Multi-GPU, lost-GPU and unsupported-field
scenarios were verified with mocks; only one real GPU was available. No model
was loaded, no inference was generated, and no driver/clocks/power/cooling
setting was changed.

## Measured monitoring cost

[Real idle report](benchmarks/real-idle.json): 30-second warmup + 900 measured
seconds, one real A40, 1Hz collection, 20 benchmark clients plus an existing
interactive browser (21 observed connections).

| Metric | Observed | Initial budget |
|---|---:|---:|
| Mean process CPU (one logical core scale) | 4.01% | <=5% |
| Maximum RSS | 91.4 MiB | <=200 MiB |
| Collection p95 | 19.01 ms | <250 ms |
| Cached REST p95 | 8.20 ms | <100 ms |
| Publish-to-client delivery p95 | 19.01 ms | <250 ms |
| Missed collection schedules | 0 | <1% |
| Collection errors | 0 | Report and investigate |
| Slow-client queue replacements | 0 | Report separately |
| SQLite bytes/minute | about 25.9 KiB | <=1 MiB |
| Minute database transactions | 15 | About one per minute |

RSS increased about 9.5 MiB during ring-buffer/allocator warmup. The following
[60-second stabilization check](benchmarks/memory-tail.json) grew 8 KiB. This
supports bounded idle behavior; it is not a long-duration leak test under AI load.
All 20 benchmark clients received 900 messages and reported no client errors.

Transport-only synthetic checks at 1Hz (10-second measurements, two-second warmup):

| Clients | REST p95 | WSS delivery p95 | Mean process CPU |
|---:|---:|---:|---:|
| 1 | 7.87 ms | 1.88 ms | 0.8% |
| 20 | 7.47 ms | 9.74 ms | 1.6% |
| 100 | 6.95 ms | 24.53 ms | 3.2% |

Each run advanced the same single collection sequence by nine between its first
and last sampled API observations; adding clients did not multiply collection.
Reports are in benchmarks/synthetic-*.json. They do not include real NVML cost.

## Remaining stable-release gates

| Criterion | Status | Required action |
|---|---|---|
| Actual non-root systemd startup/restart/reboot | Awaiting approval | Install reviewed wheel/service/account/config in /opt, /etc and /var/lib; test permissions |
| Actual LAN HTTPS and WSS | Awaiting configuration/approval | Supply exact hostname, trusted cert/key paths and password file; review and install proxy |
| AI-loaded / high-memory / multiprocess benchmark | Not verified | Arrange an approved workload window; monitoring does not launch stress or AI requests |
| LM Studio live integration | Not verified | Explicitly enable against the installed documented API; mock tests passed |
| CPU temperature | Unavailable on observed sensor API | Dashboard shows N/A; no fabricated zero |
| Real process GPU utilization / restricted metadata | Hardware/permission dependent | Remains N/A unless the interface returns reliable recent samples |
| Remote CI and PR review | CI passed; review pending | See docs/publication.md and PR #33 checks; independent review and explicit merge approval remain required |
| Branch protection / rulesets | Available; awaiting approval | Owner made the repository public; rulesets API is accessible and currently empty. No protection changes applied |
| Project LICENSE | Deferred by owner | Choose before public stable distribution |
| Stable tag and Release | Awaiting acceptance and approval | No version tag or release has been published |

Do not infer deployed production safety from passing local mocks. Installation,
certificate trust, reboot persistence and the repository's review arrangement
must be verified in their actual environments. Follow the deployment/recovery
and performance guides; preserve the old unit/environment/database backups.

## Publication CI follow-up

The remote Linux runner exposed a proxy fixture race between serving HTML and
finishing its first sample. The fixture now waits for authenticated metrics
readiness, with a regression test for the deliberate initial 503 contract.
The updated mock suite has 49 tests: 48 pass and one real-GPU test is deliberately
skipped on the hosted runner. Lint, Python/JS types, formatting, build, browser
tests and security gates passed on c61bfbc. See publication.md for the run and PR
links. This does not claim production installation or an independent review.

A later remote run found cancellation propagating out of WebSocket cleanup.
The isolated fix in PR #34 uses an AnyIO task group, drains both socket tasks
and always releases the subscriber slot. The regression asserts ASGI cancellation
cleanup directly, and 100 immediate reconnect cycles passed locally. The final
suite now contains 50 cases; latest integration checks are on PR #33. The c61bfbc
run above is retained as baseline evidence, not a claim about the later commit.
