# GitHub governance and publication

Verified repository: https://github.com/buruj7722-wq/gpu-monitor, public by the
owner's explicit request; default branch main. ADMIN access was verified.
The initial invalid-auth result occurred inside the restricted sandbox.
Never copy credentials into source, shell arguments, issue text or logs.

The requested 18 scoped labels, seven milestones and 15 issues were created
without duplicates. See docs/github-issues.json. `scripts/sync_issues.py` is
idempotent and dry-run by default. Existing branches keep their original local
names; new work uses real issue numbers.

The owner subsequently authorized execution of source publication. Sixteen
scoped branches and draft PRs #16–#31 were published, followed by CI branch/PR
#32. See docs/github-prs.json and docs/publication.md for the exact stack and
actual CI results. Integration PR #33 targets main with the complete runnable
stack and links all fifteen tasks. No merge, tag, release or production deployment is authorized
by that publication step.

PRs target their immediate dependency for scoped review. The complete tested
stack should be promoted to main coherently after review: some intermediate
snapshots are architecture/migration stages, not independently deployable
releases. Retain the dependency history and do not force-push or rewrite it.

The owner made the repository public, so the earlier private-plan HTTP 403
restriction no longer applies. Rulesets API is now accessible and returned an
empty list. Proposed rules, pending explicit approval: require a PR, successful
`quality` status, resolved conversations, block force push and branch deletion,
and restrict bypass. Require one independent approval only when an independent
reviewer is actually available. Do not invent CODEOWNERS. Prefer squash for
independent tasks after considering the stacked dependencies.

CI uses read-only token permissions and pinned Actions. Dedicated `ci/**` push
triggers allow validating the complete integration before merging to main.
The proxy integration test must wait for metrics readiness, not merely HTML
availability; initial 503 responses are expected until the first sample.

No automatic production CD. A future deployment workflow needs environment
approval, a verified artifact, scoped credentials and rollback. Any self-hosted
GPU runner must be isolated and run trusted jobs only, not arbitrary fork code
on the production monitoring server.
