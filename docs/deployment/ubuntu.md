# Ubuntu deployment (requires administrator approval)

These are operator commands, not actions performed by the development session.
Do not enable a second service while the old service is running. The old unit
references the working repository and its `venv/`; it needs explicit migration.
The owner approved stopping that failing unit temporarily during development.

## Prepare and validate

On Ubuntu 24.04, Python 3.12 is the verified baseline. Install `python3-venv`
and Nginx only if missing and approved. Keep the existing NVIDIA driver/CUDA.
Check `nvidia-smi`, device permissions and the read-only hardware test first.

Build a reviewed wheel in the checkout:
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m build --no-isolation
.venv/bin/python scripts/check_wheel.py
```
The wheel includes local web assets; Node is only needed to change/check them.
No release tag is required for local testing. Stable release requires the
readiness gates and the owner's release approval.

## Install after approval

Check whether `gpu-monitor` already exists before creating it. Preserve an
existing account's policy rather than modifying it automatically.
```bash
getent passwd gpu-monitor
sudo useradd --system --user-group --home-dir /var/lib/gpu-monitor --no-create-home --shell /usr/sbin/nologin gpu-monitor
sudo install -d -o root -g root -m 0755 /opt/gpu-monitor
sudo install -d -o root -g gpu-monitor -m 0750 /etc/gpu-monitor
sudo install -d -o gpu-monitor -g gpu-monitor -m 0750 /var/lib/gpu-monitor
sudo python3 -m venv /opt/gpu-monitor/venv
sudo /opt/gpu-monitor/venv/bin/python -m pip install dist/a40_server_monitor-0.5.0.dev0-py3-none-any.whl
sudo install -o root -g gpu-monitor -m 0640 config.example.toml /etc/gpu-monitor/config.toml
```

Run `useradd` only if the preceding lookup confirmed absence. For upgrades, do
not overwrite config.example over an existing config: compare and merge it.
Likewise back up the existing service unit before replacing it:
```bash
sudo cp -a /etc/systemd/system/gpu-monitor.service /etc/systemd/system/gpu-monitor.service.pre-migration
sudo install -o root -g root -m 0644 deploy/gpu-monitor.service /etc/systemd/system/gpu-monitor.service
sudo systemd-analyze verify /etc/systemd/system/gpu-monitor.service
sudo -u gpu-monitor /opt/gpu-monitor/venv/bin/python -c 'from monitor.collectors.gpu import GPUCollector; c=GPUCollector(fallback=False); r=c.collect(); print(r.source.status, [g.name for g in r.devices]); c.close()'
```
If the dedicated account cannot access `/dev/nvidia*`, inspect `stat`, udev rules
and existing `video`/`render` groups. Grant only an actually required group after
review; do not chmod devices globally or grant root/CAP_SYS_ADMIN. Unavailable
process metadata is acceptable and remains N/A. Do not enable PrivateDevices.

The service code should be root-owned and read-only to the service account;
only `/var/lib/gpu-monitor` is writable. `/root` is hidden from the service.

## Start and operate after approval

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gpu-monitor.service
sudo systemctl status gpu-monitor.service --no-pager
curl --fail http://127.0.0.1:5000/api/health
```

Start: `sudo systemctl start gpu-monitor`

Stop: `sudo systemctl stop gpu-monitor`

Restart: `sudo systemctl restart gpu-monitor`

Status: `systemctl status gpu-monitor --no-pager`

Logs: `journalctl -u gpu-monitor -f` (use sudo only if journal access requires it).

The startup restart limit stops a repeated crash loop after five starts/minute.
Fix configuration/dependencies first, then `sudo systemctl reset-failed
gpu-monitor` and start it. Never mask a failed deployment with endless restarts.

## Authenticated LAN HTTPS

Use a trusted certificate with the correct DNS/IP SAN, including intermediate
certificates. Provision trust on client devices through the existing authority.
The project does not generate or install a new production CA.

Add the exact hostname to `allowed_hosts`, and `https://<hostname>` to
`allowed_origins` in the TOML file. Do not add wildcards. Restart the backend
after an approved configuration change. Keep it bound to loopback.

Create a password file interactively; never put a password in command arguments:
```bash
sudo htpasswd -c /etc/nginx/gpu-monitor.htpasswd monitor
sudo chown root:www-data /etc/nginx/gpu-monitor.htpasswd
sudo chmod 0640 /etc/nginx/gpu-monitor.htpasswd
```
Use `-c` only for a new file; it would overwrite an existing password file.
If `htpasswd` is absent, its Ubuntu package is `apache2-utils`; install only
with administrator approval. Passwords are managed at the proxy, not in Git.

Render a new reviewable file using real approved values (replace examples):
```bash
python3 scripts/render_nginx.py --server-name monitor.example.internal --certificate /etc/ssl/monitor/fullchain.pem --private-key /etc/ssl/monitor/privkey.pem --htpasswd /etc/nginx/gpu-monitor.htpasswd --output /tmp/gpu-monitor-nginx.conf
```
Review existing Nginx virtual hosts/listeners, then install the snippet into its
`http` context, commonly sites-available/sites-enabled on Ubuntu. Back up existing
configuration, run `sudo nginx -t`, and reload only after approval. TLS + Basic
Auth must protect `/`, static files, `/api/*`, `/docs` and WebSocket upgrades.
No firewall rule or Internet exposure is automatically configured.

For access without LAN publication, SSH forwarding remains available:
`ssh -L 5000:127.0.0.1:5000 user@server`. Preview uses port 5001 instead.

## Acceptance on the actual deployment

Verify reboot startup, non-root execution, GPU permissions, HTTPS certificate
trust, HTTP 401 without credentials, authenticated WSS and auto-reconnection,
history persistence after restart, backups and rollback. The isolated proxy test
does not prove the installed certificate or firewall configuration.
