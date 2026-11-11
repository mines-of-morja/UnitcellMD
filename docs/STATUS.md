# Status

Last update: 2026-11-12. P0.1 and P0.2 are done; P0.3 onward is in progress on branch `phase-0`.

## Current

- Phase: **P0**. Done: P0.1, P0.2. In progress: P0.3–P0.6 on branch `phase-0` (umbrella repo).
  `main` holds only what the author has already seen or decided.
- The author is away until 2026-11-12 and asked the agent to "make the best decisions for the
  project" meanwhile. Every decision taken on the author's behalf is listed in "Decisions taken
  by the agent", to be reviewed.
- **Not yet on GitHub:** `gh` is installed but not logged in, and there is no SSH key or
  credential helper. Everything is committed locally. To publish:
  `gh auth login`, then `gh auth setup-git`, then `tools/publish-github.sh --prs`.

## Decisions by the author

- 2026-11-11: units nm/ps/amu/kJ mol⁻¹ (ADR 0001); public GitHub hosting; GUI stack PySide6 +
  pyvistaqt, pending spike S3; cluster deferred, with the rule "local-first, cluster-capable"
  (ADR 0002).
- 2026-11-12: GitHub organization `mines-of-morja` (email morja@mailbox.org); licence
  Apache-2.0; add the Lehnert 2025 SI to `../Lit`; the agent continues autonomously until the
  author returns.

## Decisions taken by the agent (to review)

1. **Commit identity:** `Moritz Limbacher <morja@mailbox.org>`, set as repo-local `user.email`
   in all four repos. The five unpublished commits were re-authored, so the personal address
   never reaches GitHub. The global git config is untouched.
2. **Licence files:** canonical Apache-2.0 text from `/usr/share/common-licenses`, plus a
   `NOTICE` file reading "Copyright 2026 The UnitcellMD Authors". This is the usual Apache
   convention for multi-contributor projects; replace it with your name if you prefer.
3. **Review via branches:** new work goes on branches (`phase-0`, later per phase or track). The
   publish script can open them as pull requests, so a gate review is a PR review with CI.
   CI now runs on pushes to every branch.

## Done

- 2026-11-12 — housekeeping on `main` in all repos: Apache-2.0 + NOTICE, CI on all branches,
  links to `mines-of-morja`, `tools/publish-github.sh`.
- 2026-11-11 — **P0.2** — audit reviewed against `_reference/NeNePo_builder` @ `fd7f1e2`:
  - all 46 file:line references verified by script;
  - added: the geometry-optimization step; the sampler's plugin-by-name and TOML input modes
    (only the Gaussian reader exists); post-run `None` filtering as evidence for issue 4;
    issue 13 (directory name vs. actual level of theory); a scripted fixture inventory (§6).
- 2026-11-11 — **P0.1** — workspace bootstrapped: umbrella repo; `ucmd-engine` (7-crate Cargo
  workspace, lints, dependency guard, CI); `ucmd-builder` and `ucmd-analysis` (Python skeletons
  with import-boundary tests, CI); NeNePo_builder cloned read-only to `_reference/`.

## Open questions for the author

1. Log in to GitHub (see "Current"), so the repos can be published and CI can run.
2. PLAN.md §10 items still open: 3 (formats; P0.3 proposes the details), 5 (benchmark),
   6 (force-field sources), 7 (installs), 8 (agent setup).

## Log

<!-- Newest first. One entry per task:
YYYY-MM-DD — <task ID> — <what changed> — evidence: <tests / report> — next: <task ID> -->

- 2026-11-12 — housekeeping — licence, CI triggers, URLs, commit identity, publish script —
  evidence: all checks re-run green in the three component repos — next: P0.3
- 2026-11-11 — P0.2 — audit confirmed and amended — evidence: reference-check script 46/46;
  fixture-inventory script; md5 duplicate scan — next: P0.3
- 2026-11-11 — P0.1 — workspace and three component skeletons — evidence: ucmd-engine fmt,
  clippy, test (1 passed) and dependency check (7 crates) green, guard rejects both injected
  violation types; ucmd-builder/ucmd-analysis ruff OK, pytest 3 passed each — next: P0.2
