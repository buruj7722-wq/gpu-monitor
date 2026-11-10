"""Copy exactly the pinned local Chart.js asset and preserve upstream licensing."""

import hashlib
import json
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
package = root / "node_modules/chart.js"
version = json.loads((package / "package.json").read_text())["version"]
expected = json.loads((root / "package.json").read_text())["devDependencies"]["chart.js"]
if version != expected:
    raise SystemExit("Chart.js version mismatch")
target = root / "static/vendor"
target.mkdir(parents=True, exist_ok=True)
shutil.copyfile(package / "dist/chart.umd.min.js", target / "chart.umd.min.js")
shutil.copyfile(package / "LICENSE.md", target / "Chart-LICENSE.md")
digest = hashlib.sha256((target / "chart.umd.min.js").read_bytes()).hexdigest()
(target / "README.md").write_text(
    f"# Chart.js {version}\n\nVendored from npm chart.js@{version}; run `npm ci && npm run vendor` to reproduce.\n\nSHA256: `{digest}`\n\nUpstream license: [MIT](Chart-LICENSE.md). This does not license the project itself.\n"
)
