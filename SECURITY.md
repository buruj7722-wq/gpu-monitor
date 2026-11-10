# Security policy

The default service binds 127.0.0.1. Local users on the same host can access it;
this assumes a trusted administrator host. LAN access must use the supplied
Nginx TLS + Basic Auth configuration on every path, including API and WebSocket.
No automatic firewall, driver, clock, cooling or power changes are permitted.

Never put credentials in Git, URLs or log messages. LM Studio credentials are
optional and read from a named service environment variable; no process command
lines/environments or inference content are collected. Snapshot process names,
hostnames, IPs and model names are operational metadata: restrict dashboard
access, database/backup permissions and screenshot sharing accordingly.

WebSocket browser Origins and HTTP Hosts must match explicit configuration.
API inputs are bounded; snapshots are read-only. Logs record exception classes,
not exception response bodies. CSP forbids external scripts, frames and objects.
Dependencies and workflow actions are pinned, audited in CI and tracked with
Dependabot. No privileged pull_request_target jobs or automatic production CD.

Until a stable release is approved, only the current development branch receives
fixes. Do not claim an SLA or independent security audit. Report vulnerabilities
using GitHub private vulnerability reporting if enabled; otherwise contact the
repository owner privately before publishing details. Do not open a public issue
containing tokens, prompts, private host data or exploit credentials.
