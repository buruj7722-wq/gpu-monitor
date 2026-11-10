# Local delivery ledger

Local Lxx IDs remain stable. Real GitHub issues have been created; source branches have been pushed and draft PRs published with the owner's execution authorization. No tag or release is claimed.

| ID | Milestone | Branch | Depends on | Issue / PR body |
|---|---|---|---|---|
| L01 | M1 | `docs/local-l01-architecture` | none | [#1](https://github.com/buruj7722-wq/gpu-monitor/issues/1) · [spec](issues/L01.md) / [PR body](prs/L01.md) |
| L02 | M1 | `chore/local-l02-governance` | L01 | [#2](https://github.com/buruj7722-wq/gpu-monitor/issues/2) · [spec](issues/L02.md) / [PR body](prs/L02.md) |
| L03 | M1 | `refactor/local-l03-core` | L02 | [#3](https://github.com/buruj7722-wq/gpu-monitor/issues/3) · [spec](issues/L03.md) / [PR body](prs/L03.md) |
| L04 | M2 | `feature/local-l04-gpu` | L03 | [#4](https://github.com/buruj7722-wq/gpu-monitor/issues/4) · [spec](issues/L04.md) / [PR body](prs/L04.md) |
| L05 | M3 | `feature/local-l05-server` | L04 | [#5](https://github.com/buruj7722-wq/gpu-monitor/issues/5) · [spec](issues/L05.md) / [PR body](prs/L05.md) |
| L06 | M4 | `feature/local-l06-workloads` | L05 | [#6](https://github.com/buruj7722-wq/gpu-monitor/issues/6) · [spec](issues/L06.md) / [PR body](prs/L06.md) |
| L07 | M4 | `feature/local-l07-lmstudio` | L06 | [#7](https://github.com/buruj7722-wq/gpu-monitor/issues/7) · [spec](issues/L07.md) / [PR body](prs/L07.md) |
| L08 | M5 | `feature/local-l08-history` | L07 | [#8](https://github.com/buruj7722-wq/gpu-monitor/issues/8) · [spec](issues/L08.md) / [PR body](prs/L08.md) |
| L09 | M5 | `feature/local-l09-alerts` | L08 | [#9](https://github.com/buruj7722-wq/gpu-monitor/issues/9) · [spec](issues/L09.md) / [PR body](prs/L09.md) |
| L10 | M5 | `feature/local-l10-api` | L09 | [#10](https://github.com/buruj7722-wq/gpu-monitor/issues/10) · [spec](issues/L10.md) / [PR body](prs/L10.md) |
| L11 | M5 | `feature/local-l11-dashboard` | L10 | [#11](https://github.com/buruj7722-wq/gpu-monitor/issues/11) · [spec](issues/L11.md) / [PR body](prs/L11.md) |
| L12 | M6 | `chore/local-l12-ci` | L11 | [#12](https://github.com/buruj7722-wq/gpu-monitor/issues/12) · [spec](issues/L12.md) / [PR body](prs/L12.md) |
| L13 | M6 | `test/local-l13-validation` | L12 | [#13](https://github.com/buruj7722-wq/gpu-monitor/issues/13) · [spec](issues/L13.md) / [PR body](prs/L13.md) |
| L14 | M7 | `feature/local-l14-deployment` | L13 | [#14](https://github.com/buruj7722-wq/gpu-monitor/issues/14) · [spec](issues/L14.md) / [PR body](prs/L14.md) |
| L15 | M7 | `docs/local-l15-readiness` | L14 | [#15](https://github.com/buruj7722-wq/gpu-monitor/issues/15) · [spec](issues/L15.md) / [PR body](prs/L15.md) |

Milestones: M1 Audit & Architecture; M2 GPU Monitoring; M3 Server Monitoring;
M4 AI Workload Monitoring; M5 Dashboard & History; M6 Security & Testing;
M7 Production Release. Each branch starts at its predecessor until approved merges.

Do not mark remote governance complete until verified against GitHub.

Implementation is published on stacked branches; issues stay open until reviewed and merged. Existing local branch names are retained; future branches use real issue numbers.

Follow-up for issue #10: `fix/10-websocket-accept-cleanup` closes a handshake-disconnect queue leak and has its own tested commit. The final readiness branch is stacked above it.

Publication: [PR index](github-prs.json). The scoped PRs are #16–#31; #32 enables and validates pre-merge CI on dedicated integration branches. No PR has been merged.

The coherent integration is [PR #33](https://github.com/buruj7722-wq/gpu-monitor/pull/33) against main. Its complete code was remotely validated on ci/12-publication-validation. Intermediate snapshots remain scoped review stages.

Additional #10 fix: `fix/10-websocket-cancellation`, [PR #34](https://github.com/buruj7722-wq/gpu-monitor/pull/34). Its patch is included in the final integration to guarantee task and subscription cleanup during ASGI cancellation.
