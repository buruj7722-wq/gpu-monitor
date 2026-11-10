# ADR 001: one Python service and a buildless dashboard

Status: accepted for the first single-server release. No measured performance
advantage for a rewrite has been established.

| Backend | NVML / Linux | Runtime and streaming | Testing / maintenance | Migration cost |
|---|---|---|---|---|
| Python + FastAPI | NVIDIA's nvidia-ml-py; psutil | Async WebSocket; blocking calls moved off loop; interpreter overhead | Existing code and mature test/mocking tools | Lowest |
| Go | NVIDIA go-nvml and Linux APIs | Compiled binary, goroutines; potentially lower overhead, unmeasured here | Good tests; cgo/native library still required | Rewrite collectors and API |
| Rust | FFI/wrappers and Linux crates | Compiled, strong ownership; async libraries available | Strong types; FFI safety and expertise add work | Highest current complexity |

Choose Python, Pydantic models, FastAPI and nvidia-ml-py. Reconsider only after
profiling shows a budget violation that cannot be fixed locally, or a concrete
fleet requirement. Do not claim Go/Rust benchmark wins without measurements.

| Frontend | Benefits | Cost / decision |
|---|---|---|
| ES modules + JSDoc | Reuses existing HTML/CSS/JS; no runtime framework | Selected, checked by TypeScript with noEmit |
| TypeScript source | Strong static contracts | Adds compilation; reconsider as UI grows |
| React | Component ecosystem | Runtime/build dependency unnecessary for these panels |
| Vue | Component ergonomics | Same additional tooling tradeoff |

Chart.js is vendored at a fixed version with its license and checksum. No CDN,
font, analytics or remote asset requests are needed at runtime.

SQLite stores minute aggregates (mean/min/max/count), retained for seven days.
A bounded five-minute memory ring supplies live resolution. Fifteen-minute
query aggregation bounds week charts. A time-series database and external cache
are unjustified for one monitored server. SQLite and queues remain bounded.

Nginx terminates trusted TLS and authenticates every path, including upgrades.
The backend binds only loopback, checks Host/Origin, and trusts proxy headers
only from loopback. Native systemd runs an unprivileged dedicated account.

References: [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/),
[NVIDIA NVML](https://docs.nvidia.com/deploy/nvml-api/),
[NVIDIA A40](https://www.nvidia.com/en-us/data-center/a40/),
[LM Studio API](https://lmstudio.ai/docs/developer/rest/list),
[Nginx WebSocket](https://nginx.org/en/docs/http/websocket.html).
