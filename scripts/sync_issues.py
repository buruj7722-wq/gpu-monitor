"""Idempotent issue/label/milestone preparation. Dry-run unless --apply is explicit."""

import argparse
import json
import subprocess
from pathlib import Path

REPOSITORY = "buruj7722-wq/gpu-monitor"
MILESTONES = [
    "M1 — Audit & Architecture",
    "M2 — GPU Monitoring",
    "M3 — Server Monitoring",
    "M4 — AI Workload Monitoring",
    "M5 — Dashboard & History",
    "M6 — Security & Testing",
    "M7 — Production Release",
]
TYPES = {
    "Docs": "Documentation",
    "Chore": "Enhancement",
    "Refactor": "Refactor",
    "Feature": "Feature",
    "Test": "Testing",
}
AREAS = {
    "L01": "documentation",
    "L02": "devops",
    "L03": "backend",
    "L04": "gpu",
    "L05": "server",
    "L06": "gpu",
    "L07": "backend",
    "L08": "backend",
    "L09": "backend",
    "L10": "backend",
    "L11": "frontend",
    "L12": "devops",
    "L13": "backend",
    "L14": "devops",
    "L15": "documentation",
}


def api(path: str, payload: dict[str, object] | None = None) -> object:
    command = ["gh", "api", path]
    if payload is not None:
        command.extend(["--method", "POST", "--input", "-"])
    result = subprocess.run(
        command,
        input=json.dumps(payload) if payload is not None else None,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent

    # Paginate reads so reruns never duplicate tasks hidden on another page.
    def listing(resource: str) -> list[dict[str, object]]:
        result = subprocess.run(
            ["gh", "api", "--paginate", f"repos/{REPOSITORY}/{resource}"],
            text=True,
            capture_output=True,
            check=True,
        )
        remaining = result.stdout.strip()
        rows = []
        decoder = json.JSONDecoder()
        while remaining:
            page, consumed = decoder.raw_decode(remaining)
            rows.extend(page)
            remaining = remaining[consumed:].strip()
        return rows

    labels = {str(row["name"]): row for row in listing("labels?per_page=100")}
    milestones = {str(row["title"]): row for row in listing("milestones?state=all&per_page=100")}
    issues = {
        str(row["title"]): row
        for row in listing("issues?state=all&per_page=100")
        if "pull_request" not in row
    }
    definitions = {
        **{
            f"type:{name}": "6b73d6"
            for name in [
                "feature",
                "bug",
                "enhancement",
                "refactor",
                "performance",
                "security",
                "documentation",
                "testing",
                "technical-debt",
            ]
        },
        **{
            f"area:{name}": "138a72"
            for name in ["gpu", "server", "frontend", "backend", "devops", "documentation"]
        },
        **{
            f"priority:{name}": color
            for name, color in [("high", "b60205"), ("medium", "fbca04"), ("low", "c2e0c6")]
        },
    }
    for name, color in definitions.items():
        if name not in labels:
            print("Create label:", name)
            if args.apply:
                api(f"repos/{REPOSITORY}/labels", {"name": name, "color": color})
    for title in MILESTONES:
        if title not in milestones:
            print("Create milestone:", title)
            if args.apply:
                milestones[title] = api(f"repos/{REPOSITORY}/milestones", {"title": title})
    mapping = {}
    for path in sorted((root / "docs/issues").glob("L*.md")):
        local = path.stem
        body = path.read_text()
        title = body.splitlines()[0].removeprefix("# ")
        original_type = title.split("]", 1)[0].removeprefix("[")
        issue_type = TYPES.get(original_type, original_type)
        title = title.replace(f"[{original_type}]", f"[{issue_type}]", 1)
        body = body.replace(body.splitlines()[0], "# " + title, 1)
        milestone_key = body.split("milestone: ", 1)[1].split(";", 1)[0]
        milestone_title = next(t for t in MILESTONES if t.startswith(milestone_key + " "))
        if title not in issues:
            print("Create issue:", local, title)
            if args.apply:
                issues[title] = api(
                    f"repos/{REPOSITORY}/issues",
                    {
                        "title": title,
                        "body": body
                        + "\nImplementation is prepared on local stacked branches; source publication and PRs await owner approval.\n",
                        "milestone": milestones[milestone_title]["number"],
                        "labels": [
                            f"type:{issue_type.lower()}",
                            f"area:{AREAS[local]}",
                            "priority:high"
                            if local in {"L03", "L04", "L10", "L12", "L14"}
                            else "priority:medium",
                        ],
                    },
                )
        if title in issues:
            issue = issues[title]
            mapping[local] = {"number": issue["number"], "url": issue["html_url"], "title": title}
            if args.apply:
                body = body.replace(body.splitlines()[0], "# " + title, 1).replace(
                    "remote issue: not created.",
                    f"remote issue: #{issue['number']} ({issue['html_url']}).",
                )
                path.write_text(body)
                pr_path = root / f"docs/prs/{local}.md"
                pr_body = pr_path.read_text().replace(
                    f"Local {local}; replace with Closes #<real-number> after remote issue creation.",
                    f"Closes #{issue['number']}\nLocal tracking: {local}. No remote PR has been published.",
                )
                pr_path.write_text(pr_body)
    if args.apply:
        (root / "docs/github-issues.json").write_text(json.dumps(mapping, indent=2) + "\n")
    print("No branch, push, PR, protection, tag, release or deployment operation is performed.")


if __name__ == "__main__":
    main()
