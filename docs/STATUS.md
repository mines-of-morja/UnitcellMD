# Status

Last update: 2026-11-11. P0.1 and P0.2 are done; next is P0.3.

## Current

- Phase: **P0**. Done: P0.1, P0.2. Next task: **P0.3**, spec v0.1 documents and JSON Schemas.
- Decided by the author on 2026-11-11 (PLAN.md §10):
  - units nm/ps/amu/kJ mol⁻¹ (ADR 0001);
  - public GitHub hosting, with the repo names as proposed;
  - GUI stack PySide6 + pyvistaqt, pending spike S3; a web or Rust front end may follow on top;
  - cluster deferred to A2.2, under the standing rule "local-first, cluster-capable"
    (D13, ADR 0002).
- **Not yet pushed:** this machine has no GitHub access yet (no SSH key, no credential helper,
  no `gh`). See open question 1.

## Done

- 2026-11-11 — **P0.2** — audit reviewed against `_reference/NeNePo_builder` @ `fd7f1e2`:
  - all 46 file:line references verified by script;
  - added: the geometry-optimization step; the sampler's plugin-by-name and TOML input modes
    (only the Gaussian reader exists); post-run `None` filtering as evidence for issue 4;
    issue 13 (directory name vs. actual level of theory); a scripted fixture inventory (§6);
  - softened a speculative sentence about code origin (§7).
- 2026-11-11 — **P0.1** — workspace bootstrapped:
  - umbrella repo with README, MIT licence, `.gitignore`, ADRs 0001–0002, filled Commands table;
  - `ucmd-engine` (commit 66764a1): 7-crate Cargo workspace, lints, dependency guard, CI;
  - `ucmd-builder` (0da3426) and `ucmd-analysis` (d435751): Python package skeletons with
    import-boundary tests, CI;
  - NeNePo_builder cloned read-only to `_reference/` (gitignored).
- 2026-11-11 — PLAN.md, CLAUDE.md and docs/nenepo-audit.md drafted.

## Open questions for the author

1. **GitHub:** which account or organization should host the four repos (`UnitcellMD`,
   `ucmd-engine`, `ucmd-builder`, `ucmd-analysis`)? And how should pushes authenticate? Either
   create the four empty public repos on github.com, or install `gh` (`sudo apt install gh`)
   and run `gh auth login`.
2. **Commit email:** the configured git email is a regular address, and it becomes public with
   the first push. Use your GitHub noreply address instead? The initial commits can be
   re-authored before the first push.
3. **Licence:** MIT, as in the thesis, is in place. Confirm, or choose MIT/Apache-2.0 for the
   Rust code.
4. The **Lehnert 2025 supplementary information** (simulation parameters) is not in ../Lit.
5. **`libhdf5-dev`** (needs sudo) for spike S1, or let S1 try the bundled static build.
6. Still open in PLAN.md §10: 3 (formats; P0.3 will propose details), 5 (benchmark), 6
   (force-field sources), 7 (installs: uv, OpenMM, Packmol), 8 (agent setup).
7. `docs/nenepo-audit.md` lists issues in the thesis code and becomes public with the
   umbrella repo. Is that OK?

## Log

<!-- Newest first. One entry per task:
YYYY-MM-DD — <task ID> — <what changed> — evidence: <tests / report> — next: <task ID> -->

- 2026-11-11 — P0.2 — audit confirmed and amended (see Done) — evidence: reference-check
  script 46/46; fixture-inventory script over all fchk/log/Q-Chem files; md5 duplicate scan —
  next: P0.3
- 2026-11-11 — P0.1 — workspace and three component skeletons — evidence:
  - ucmd-engine: `cargo fmt --check` OK, `clippy -D warnings` OK, `cargo test` 1 passed (CLI
    smoke test), `scripts/check-architecture.sh` passed for 7 crates; the guard rejected both
    injected violations (provider dependency in ucmd-md; crate without a rule);
  - ucmd-builder and ucmd-analysis: ruff check and format OK, pytest 3 passed each;
  - scan for absolute paths and email in committed files: none —
  next: P0.2
