# GitHub governance (prepared, not applied)

Audit connectivity with `gh auth status` and `gh repo view --json
defaultBranchRef,viewerPermission`. Authentication must be repaired by the owner;
never copy credentials into files or chat. Then list issues, PRs, labels,
milestones and rulesets before creating anything. Local roadmap IDs are not
remote issue numbers. Push and PR publication require owner approval.

Labels: type:{feature,bug,enhancement,refactor,performance,security,documentation,
testing,technical-debt}; area:{gpu,server,frontend,backend,devops,documentation};
priority:{high,medium,low}. Milestones are M1–M7 from docs/roadmap.md. Projects
are optional; the issue ledger is enough for the initial linear delivery.

Proposed default-branch ruleset, pending owner approval and plan capability:
require PR, successful `quality` check, resolved conversations, block force push
and branch deletion, restrict bypass. Require one approving reviewer only when
an independent reviewer exists. Do not add a fictional CODEOWNERS entry. Prefer
squash merge for independent tasks. Review stacked PRs bottom-up.

No automatic production CD. A later deployment workflow must use an environment
with manual approval, a verified artifact, scoped credentials and rollback.
Self-hosted GPU runners must be isolated and restricted to trusted jobs; do not
run arbitrary fork PR code on the monitored production server.

## Verified follow-up

Outside the restricted sandbox, gh 2.45.0 authenticates successfully. The target
repository is private, default main, with ADMIN access. The requested 18 scoped
labels, seven milestones and 15 issues were created. See docs/github-issues.json
for exact mappings. `scripts/sync_issues.py` is idempotent and dry-run by default.
No branch was pushed and no PR was published. Rulesets and branch-protection
APIs returned HTTP 403 requiring GitHub Pro or public visibility. Do not change
visibility or purchase a plan automatically; that owner decision remains a
release gate. CI files are local until push is approved.
