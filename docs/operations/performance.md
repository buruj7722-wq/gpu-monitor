# Performance measurement

The initial budget is one GPU, one-second collection, 20 clients, 30-second
warmup and 15 measured minutes. CPU <=5% of one logical core on average, RSS
<=200 MiB without sustained growth, collection p95 <250 ms, cached API p95
<100 ms, publish-to-client WSS p95 <250 ms, missed cycles <1%, and SQLite writes
<=1 MiB/minute averaged over the run. These are site acceptance targets, not
universal promises for any number of devices/mounts/interfaces.

Run against an approved loopback instance with a synchronized client clock:
```bash
.venv/bin/python tools/benchmark.py --url http://127.0.0.1:5001 --clients 20 --seconds 900 --warmup 30 --label real-idle --output /tmp/gpu-monitor-idle.json
```

The harness only reads cached metrics and opens WebSockets. It never loads a
model or creates CPU/RAM/GPU stress. `real-ai`, `real-memory` and
`real-multiprocess` labels describe an independently approved workload that the
operator must arrange. A label alone is not proof; record the scenario alongside
its report. Do not run an authenticated remote URL with secrets in arguments.
For LAN timing, add an approved credential mechanism separately; loopback tests
avoid putting credentials in a benchmark file.

`process_cpu_percent` uses psutil's per-process scale (100%=one logical core).
Database bytes are Linux process write_bytes deltas surrounding transactions,
including WAL; file-growth fallback is a lower bound on platforms without that
counter. Reports distinguish completed collection cycles, missed schedules,
source errors and queue replacements. Internal send_ms is not end-to-end
latency; client delivery uses published_at and includes JSON transfer/decoding.

Synthetic transport instances live only in tests/benchmark_app.py. They run at
1Hz, with no actual NVML cost. Compare 1/20/100 clients there to verify fan-out,
then use real hardware for the actual resource budget. Earlier 10Hz fixture
measurements are exploratory and are not the production acceptance result.
