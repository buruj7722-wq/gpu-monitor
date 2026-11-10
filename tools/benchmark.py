"""Bounded read-only client benchmark. Run against a dedicated instance or approved preview."""

import argparse
import asyncio
import json
import math
import statistics
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from websockets.asyncio.client import connect


def summary(values: list[float]) -> dict[str, float | int | None]:
    ordered = sorted(values)
    return {
        "count": len(values),
        "mean": statistics.mean(values) if values else None,
        "p95": ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)] if ordered else None,
        "maximum": max(values) if values else None,
    }


async def benchmark(
    url: str, clients: int, seconds: float, warmup: float, label: str
) -> dict[str, object]:
    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Use an explicit HTTP origin without credentials")
    base = url.rstrip("/")
    ws_url = ("wss" if parsed.scheme == "https" else "ws") + "://" + parsed.netloc + "/ws/metrics"
    api_times: list[float] = []
    delivery: list[float] = []
    cpu: list[float] = []
    rss: list[float] = []
    latency: list[float] = []
    connection_count: list[float] = []
    collection_count: list[float] = []
    message_counts = [0] * clients
    errors: list[str] = []
    observers = []
    ready = [asyncio.Event() for _ in range(clients)]
    start_event = asyncio.Event()
    measure_at = math.inf
    deadline = math.inf

    async def stream(index: int) -> None:
        try:
            async with connect(ws_url, open_timeout=10, max_size=4 * 1024 * 1024) as websocket:
                ready[index].set()
                await start_event.wait()
                while time.monotonic() < deadline:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=3)
                    except TimeoutError:
                        continue
                    sample = json.loads(message)
                    if time.monotonic() >= measure_at:
                        message_counts[index] += 1
                        published = sample.get("published_at")
                        if published is not None:
                            elapsed = (time.time() - published) * 1000
                            if elapsed >= 0:
                                delivery.append(elapsed)
        except Exception as exc:
            errors.append(type(exc).__name__)
            ready[index].set()

    tasks = [asyncio.create_task(stream(i)) for i in range(clients)]
    await asyncio.gather(*(event.wait() for event in ready))
    measure_at = time.monotonic() + warmup
    deadline = measure_at + seconds
    start_event.set()
    async with httpx.AsyncClient(trust_env=False, timeout=5) as client:
        while time.monotonic() < deadline:
            started = time.monotonic()
            try:
                response = await client.get(base + "/api/metrics")
                response.raise_for_status()
                sample = response.json()
                if time.monotonic() >= measure_at:
                    api_times.append((time.monotonic() - started) * 1000)
                    observer = sample["observer"]
                    observers.append(observer)
                    for key, target in [
                        ("cpu_percent", cpu),
                        ("rss_bytes", rss),
                        ("collection_latency_ms", latency),
                        ("active_connections", connection_count),
                        ("collection_count", collection_count),
                    ]:
                        value = observer.get(key)
                        if value is not None:
                            target.append(float(value))
            except Exception as exc:
                errors.append(type(exc).__name__)
            await asyncio.sleep(max(0, 1 - (time.monotonic() - started)))
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    first, last = (observers[0], observers[-1]) if observers else ({}, {})
    delta = {
        key: last.get(key, 0) - first.get(key, 0)
        for key in [
            "dropped_samples",
            "replaced_messages",
            "collection_errors",
            "collection_count",
            "database_write_bytes",
            "database_write_operations",
        ]
    }
    return {
        "label": label,
        "hardware_proof": label == "real-idle",
        "requested_clients": clients,
        "seconds": seconds,
        "warmup_seconds": warmup,
        "api_ms": summary(api_times),
        "websocket_delivery_ms": summary(delivery),
        "process_cpu_percent": summary(cpu),
        "rss_bytes": summary(rss),
        "rss_growth_bytes": rss[-1] - rss[0] if rss else None,
        "collection_ms": summary(latency),
        "connections": summary(connection_count),
        "counter_deltas": delta,
        "client_messages": message_counts,
        "client_errors": errors,
        "database_bytes_per_minute": delta["database_write_bytes"] / (seconds / 60),
        "delivery_clock_note": "Client and server must share a synchronized clock. Same-host measurements include JSON transfer and decode.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:5001")
    parser.add_argument("--clients", type=int, default=20)
    parser.add_argument("--seconds", type=float, default=900)
    parser.add_argument("--warmup", type=float, default=30)
    parser.add_argument(
        "--label",
        choices=["synthetic", "real-idle", "real-ai", "real-memory", "real-multiprocess"],
        default="synthetic",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.clients <= 100 or not 1 <= args.seconds <= 3600 or not 0 <= args.warmup <= 300:
        parser.error("clients 1..100, seconds 1..3600, warmup 0..300 required")
    report = asyncio.run(benchmark(args.url, args.clients, args.seconds, args.warmup, args.label))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Benchmark written to {args.output}")


if __name__ == "__main__":
    main()
