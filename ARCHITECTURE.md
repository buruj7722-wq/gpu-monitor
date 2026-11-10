# Architecture

One Python process owns collection, history, alerts and streaming. One Uvicorn
worker is required: multiple workers would duplicate hardware polling.

```text
NVML / psutil / optional LM Studio
             |
    collectors (blocking worker thread)
             |
   normalized immutable snapshots
             |
 scheduler -> alerts -> memory ring + minute aggregation -> SQLite
             |
      latest snapshot -> REST / bounded WebSocket queues -> dashboard
```

Collectors never run in HTTP handlers. Missing sensors are null with an explicit
reason; failed readings are not replaced with the previous numeric reading.
Source timestamps identify freshness. GPU identity is its UUID; process identity
includes PID and creation time. GPU activity is not inference quality.

The service is observation-only. It never changes drivers, clocks, power limits,
fans, firewall rules, models or production workloads.

See [decisions](docs/adr/001-technology.md), [migration](docs/operations/migration.md)
and the [local issue ledger](docs/roadmap.md).
