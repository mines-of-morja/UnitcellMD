# Instructions for coding agents (GitHub Copilot and others)

At the start of every session, read `CLAUDE.md` (the rules), `CONTRIBUTING.md` (branches) and
`docs/STATUS.md` (current state). They are binding. The essentials:

- **Branches:** never commit to `main` or to the review branches (`b2a`, `a1`, `e…`). Work on
  `<name>/<task-id>-<short-title>`, made from the review branch of the repo, and open a pull
  request into that review branch.
- **Tasks:** work only on GitHub issues labelled `task`
  (https://github.com/issues?q=is%3Aopen+label%3Atask+org%3Amines-of-morja). For `needs-design`,
  deliver the design note as a draft pull request and stop. Never start a `blocked` issue.
  Pull requests say `Closes #<n>`.
- **Workspace:** `ucmd-engine`, `ucmd-builder` and `ucmd-analysis` are separate git repos cloned
  inside this one. Run git commands in the repo you change. Components never import each other.
- **Units:** nm, ps, amu, kJ/mol, e, K; pressure in bar. Config keys carry their unit
  (`cutoff_nm`). Constants come from the one constants module per language.
- **Never invent a physical parameter.** Every value cites a source. Ask the author before
  choosing force-field values, charge scaling or validation cutoffs.
- **Test-first physics:** write the validation test with the code. Reproduce a published number
  before reporting a new one. Never loosen a tolerance, skip or delete a failing test.
- **Design before code:** a new task or interface starts as a short design note in a draft pull
  request. Implement only after the author approves it. Stop at the end of a task.
- **Errors propagate.** Never replace a failed result with zero, a stale or a default value.
- **Never commit** secrets, absolute paths, papers, run outputs, or names of people outside the
  project. Never force-push.
- **Python:** a venv per repo (`python3 -m venv .venv`), ruff, pytest, type hints on the public
  API. **Rust:** `cargo fmt`, `cargo clippy -- -D warnings`, no `unwrap` in library code.
