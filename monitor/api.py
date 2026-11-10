"""Cached REST and WebSocket access; no collector is constructed per client."""

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from gpu import get_gpu, get_processes
from monitor import __version__
from monitor.config import Settings, load_settings
from monitor.history import HistoryResponse
from monitor.models import Alert, Snapshot, Source, SystemReading
from monitor.runtime import Runtime
from monitor.service import Pipeline


def visible_snapshot(runtime: Runtime) -> Snapshot:
    if runtime.latest is None:
        raise HTTPException(status_code=503, detail="collector_initializing")
    snapshot = runtime.latest
    if runtime.stale():
        snapshot = snapshot.model_copy(
            update={
                "collector": Source(
                    status="unavailable", error="collector_stale", last_success=snapshot.timestamp
                ),
                "alerts": [
                    *snapshot.alerts,
                    Alert(
                        id="collector/stopped",
                        severity="critical",
                        message="Collection stopped or stale",
                        since=snapshot.timestamp + runtime.settings.stale_seconds,
                    ),
                ],
            }
        )
    return snapshot


def create_app(settings: Settings | None = None, pipeline: Pipeline | None = None) -> FastAPI:
    settings = settings or load_settings()
    pipeline = pipeline or Pipeline(settings)
    runtime = Runtime(settings, pipeline.sample, pipeline.close)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await runtime.start()
        try:
            yield
        finally:
            await runtime.stop()

    app = FastAPI(title="A40 Server Monitor", version=__version__, lifespan=lifespan)
    app.state.runtime = runtime
    app.state.pipeline = pipeline
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started = time.monotonic()
        response = await call_next(request)
        runtime.api_response_ms = (time.monotonic() - started) * 1000
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    async def health() -> JSONResponse:
        if runtime.stale():
            return JSONResponse(
                {
                    "status": "not_ready",
                    "reason": "collector_stale",
                    "last_update": runtime.latest.timestamp if runtime.latest else None,
                },
                status_code=503,
            )
        latest = visible_snapshot(runtime)
        degraded = (
            latest.gpu.source.status != "ok"
            or latest.system.source.status != "ok"
            or latest.storage.status != "ok"
        )
        return JSONResponse(
            {
                "status": "degraded" if degraded else "ok",
                "last_update": latest.timestamp,
                "gpu": latest.gpu.source.status,
                "system": latest.system.source.status,
                "storage": latest.storage.status,
            }
        )

    @app.get("/api/metrics", response_model=Snapshot)
    async def metrics() -> Snapshot:
        return visible_snapshot(runtime)

    @app.get("/api/system", response_model=SystemReading)
    async def system() -> SystemReading:
        return visible_snapshot(runtime).system

    @app.get("/api/gpu")
    async def legacy_gpu() -> dict[str, object]:
        return get_gpu(visible_snapshot(runtime).gpu)

    @app.get("/api/processes")
    async def legacy_processes() -> list[dict[str, object]]:
        return get_processes(visible_snapshot(runtime).gpu)

    @app.get("/api/history", response_model=HistoryResponse)
    async def history(
        window: Literal["5m", "1h", "24h", "7d"] = "5m",
        max_points: int = Query(default=600, ge=1, le=600),
    ) -> HistoryResponse:
        return await asyncio.to_thread(pipeline.history.query, window, None, max_points)

    @app.websocket("/ws/metrics")
    async def websocket(websocket: WebSocket) -> None:
        origin = websocket.headers.get("origin")
        if origin is not None and origin not in settings.allowed_origins:
            await websocket.close(code=1008)
            return
        try:
            queue = runtime.subscribe()
        except RuntimeError:
            await websocket.close(code=1013)
            return
        await websocket.accept()

        async def receive() -> None:
            while True:
                event = await websocket.receive()
                if event["type"] == "websocket.disconnect":
                    return
                if len(event.get("text") or event.get("bytes") or b"") > 1024:
                    await websocket.close(code=1009)
                    return

        async def send() -> None:
            while True:
                try:
                    snapshot = await asyncio.wait_for(queue.get(), timeout=settings.stale_seconds)
                except TimeoutError:
                    if runtime.latest is None:
                        continue
                    snapshot = visible_snapshot(runtime)
                started = time.monotonic()
                await asyncio.wait_for(
                    websocket.send_json(snapshot.model_dump(mode="json")), timeout=5
                )
                runtime.websocket_send_ms = (time.monotonic() - started) * 1000

        tasks = [asyncio.create_task(receive()), asyncio.create_task(send())]
        try:
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
        except (WebSocketDisconnect, RuntimeError, TimeoutError):
            pass
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            runtime.unsubscribe(queue)

    root = Path(__file__).resolve().parent.parent
    assets = root if (root / "templates/index.html").exists() else Path(__file__).parent / "web"
    app.mount("/static", StaticFiles(directory=assets / "static"), name="static")

    @app.get("/", response_class=FileResponse)
    async def index() -> FileResponse:
        return FileResponse(assets / "templates/index.html")

    return app
