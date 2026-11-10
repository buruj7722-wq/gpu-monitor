# Baseline audit (2026-11-10)

Eight tracked project files; Flask app.py, NVML gpu.py, static JS/CSS and a Jinja
template. Dependencies: Flask 3.1.0, nvidia-ml-py 12.575.51, psutil 6.1.1.
Keep the GPU/process views, dark dashboard, port and legacy API units.

Confirmed issues: import-time NVML crash, first-GPU-only, duplicated polling per
browser, missing metrics reported as zero, broad exceptions, unescaped process
HTML, debug server on all interfaces, root systemd service, no tests/history.

Observed Ubuntu 24.04.3, Python 3.12.3, kernel 7.0.0-42-generic. NVIDIA module
reports 595.91.07; nvcc reports Toolkit 12.0. These are not a successful NVML or
CUDA driver API query. /dev/nvidia* is absent in this execution environment;
nvidia-smi fails and systemd bus is inaccessible. No driver changes are justified.

Git main and cached origin/main at d8215a5, clean worktree, existing origin
https://github.com/buruj7722-wq/gpu-monitor.git. gh authentication invalid and API
unreachable during audit. Remote default branch, issues, permissions, PRs and
protection were not verified. No remote objects were created or modified.

## Follow-up outside the restricted execution sandbox

Read-only NVML access succeeded on the actual A40: driver 595.91.07, CUDA Driver
13.2, Ampere, 32 C in the observed idle sample, GPU operating/slowdown/shutdown
thresholds 88/95/98 C. These are observed values, not defaults for all GPUs.
The initial missing-device and invalid-auth results were sandbox limitations.
GitHub access subsequently verified main as the default branch, private
visibility and ADMIN repository permission. Labels/milestones/issues were absent
and have now been created as requested; no code push or PR was published.
Rulesets/protection API returns HTTP 403 requiring a plan upgrade for this
private repository. No protection was changed.

The old systemd unit used venv without FastAPI after the repository code update,
and was restarting. The owner explicitly approved stopping it temporarily.
The real preview is a separate loopback process on port 5001 using .venv.
