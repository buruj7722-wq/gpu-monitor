# Local delivery ledger

These IDs are local, not GitHub issues. No remote issue, PR, tag or release is claimed.

| ID | Milestone | Branch | Depends on | Issue / PR body |
|---|---|---|---|---|
| L01 | M1 | `docs/local-l01-architecture` | none | [issue](issues/L01.md) / [PR](prs/L01.md) |
| L02 | M1 | `chore/local-l02-governance` | L01 | [issue](issues/L02.md) / [PR](prs/L02.md) |
| L03 | M1 | `refactor/local-l03-core` | L02 | [issue](issues/L03.md) / [PR](prs/L03.md) |
| L04 | M2 | `feature/local-l04-gpu` | L03 | [issue](issues/L04.md) / [PR](prs/L04.md) |
| L05 | M3 | `feature/local-l05-server` | L04 | [issue](issues/L05.md) / [PR](prs/L05.md) |
| L06 | M4 | `feature/local-l06-workloads` | L05 | [issue](issues/L06.md) / [PR](prs/L06.md) |
| L07 | M4 | `feature/local-l07-lmstudio` | L06 | [issue](issues/L07.md) / [PR](prs/L07.md) |
| L08 | M5 | `feature/local-l08-history` | L07 | [issue](issues/L08.md) / [PR](prs/L08.md) |
| L09 | M5 | `feature/local-l09-alerts` | L08 | [issue](issues/L09.md) / [PR](prs/L09.md) |
| L10 | M5 | `feature/local-l10-api` | L09 | [issue](issues/L10.md) / [PR](prs/L10.md) |
| L11 | M5 | `feature/local-l11-dashboard` | L10 | [issue](issues/L11.md) / [PR](prs/L11.md) |
| L12 | M6 | `chore/local-l12-ci` | L11 | [issue](issues/L12.md) / [PR](prs/L12.md) |
| L13 | M6 | `test/local-l13-validation` | L12 | [issue](issues/L13.md) / [PR](prs/L13.md) |
| L14 | M7 | `feature/local-l14-deployment` | L13 | [issue](issues/L14.md) / [PR](prs/L14.md) |
| L15 | M7 | `docs/local-l15-readiness` | L14 | [issue](issues/L15.md) / [PR](prs/L15.md) |

Milestones: M1 Audit & Architecture; M2 GPU Monitoring; M3 Server Monitoring;
M4 AI Workload Monitoring; M5 Dashboard & History; M6 Security & Testing;
M7 Production Release. Each branch starts at its predecessor until approved merges.

Do not mark remote governance complete until verified against GitHub.
