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
