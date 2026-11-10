"""Check the artifact contains Python code, entry point and local web assets."""

from pathlib import Path
from zipfile import ZipFile

wheel = next(Path("dist").glob("*.whl"))
required = {
    "gpu.py",
    "monitor/api.py",
    "monitor/cli.py",
    "monitor/collectors/gpu.py",
    "monitor/web/templates/index.html",
    "monitor/web/static/app.js",
    "monitor/web/static/style.css",
    "monitor/web/static/vendor/chart.umd.min.js",
    "monitor/web/static/vendor/Chart-LICENSE.md",
}
with ZipFile(wheel) as archive:
    missing = required - set(archive.namelist())
    if missing:
        raise SystemExit(f"Incomplete wheel: {sorted(missing)}")
print("Wheel includes service code and local dashboard assets")
