"""Fail CI on detector findings without printing potentially sensitive values."""

import json
import sys
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text())
count = sum(len(items) for items in report.get("results", {}).values())
print(f"Secret detector findings: {count}")
if count:
    raise SystemExit("Review findings locally before committing; never print secret values in CI.")
