# Contributing to UnitcellMD

The rules in [CLAUDE.md](CLAUDE.md) apply to every contributor, human or AI agent: units,
architecture invariants, test-first physics, no invented parameters, errors on record. This file
adds how to get the current code and where to commit.

## Get the current state

`main` holds only what the author has approved at a gate, so it lags behind. The current work is
on the review branches:

| repo | start from | what it holds |
|---|---|---|
| UnitcellMD (this repo) | `b2a` | plan, spec, studies, research, tools |
| ucmd-builder | `b2a` | builder library, CLI, GUI |
| ucmd-analysis | `a1` | analysis library and CLI (transport, structure, ε, ΔH_vap, viscosity) |
| ucmd-engine | `e25-constraints` | engine and OpenMM bridge; the tip of a stack: `b2a` → `e27-barostat` → `e37-openmm` → `e37-identity` → `e29-pressure-tensor` → `e25-constraints` |

```sh
git clone -b b2a https://github.com/mines-of-morja/UnitcellMD.git
cd UnitcellMD
git clone -b e25-constraints https://github.com/mines-of-morja/ucmd-engine.git
git clone -b b2a https://github.com/mines-of-morja/ucmd-builder.git
git clone -b a1  https://github.com/mines-of-morja/ucmd-analysis.git
```

Setup, test and lint commands for each repo are in the table in CLAUDE.md. Read
[docs/STATUS.md](docs/STATUS.md) first: it says what is done, what runs and what is open.

## Tasks

Open tasks are GitHub issues with the label `task`, in all repos of the organization:
[all open tasks](https://github.com/issues?q=is%3Aopen+label%3Atask+org%3Amines-of-morja).
The author (or the author's agent) posts them; each says its goal, context, deliverable,
acceptance criteria and the review branch.

- **Claim** a task by assigning yourself or commenting on it, before you start.
- **`needs-design`:** the first deliverable is a design note as a draft pull request. Implement
  only after the author approves it in the pull request.
- **`blocked`:** waits for something outside the task (named in the issue). Don't start it.
- **`literature`:** sources for the literature ledger, no code.
- Name the branch `<your-name>/<issue-number>-<short-title>` and write `Closes #<n>` in the pull
  request.
- Found more work? Open an issue without the `task` label; the author decides whether it
  becomes one.

## Where to commit

- **`main`:** only the author merges, after a gate.
- **Review branches** (`b2a`, `a1`, `e…`): the author's agent commits here every day. Do not
  commit to them directly.
- **Your work:** one branch per task, `<your-name>/<task-id>-<short-title>`, made from the review
  branch of that repo. Open a pull request into that review branch. Rebase on it before asking
  for review.
- **Tasks** come from [PLAN.md](PLAN.md) (IDs like `A1.5`) or from the author. A new task, or a
  change to an interface, a spec file or a physical parameter, needs the author's approval
  first: open a draft pull request with a short design note and wait.
- Small pull requests. Commit messages `<area>: <what>`, with the why in the body.

## Before a pull request

- The repo's tests, `ruff` (Python) or `cargo fmt`/`clippy` (Rust) pass; CI is green.
- Physics comes with its validation test: an analytic case, a finite-difference check, a
  synthetic system with a known answer, or a published number reproduced.
- New literature values go into the ledger with their source
  (`docs/research/summary/literature.json`).

## Never commit

Secrets; absolute paths from your machine; papers or other copyrighted PDFs; run outputs and
large binaries (study data stays local); names or details of people outside the project.

## AI agents

Agents are welcome; the project's policy on AI use is open
([docs/research/publication.md](docs/research/publication.md)). Your agent follows CLAUDE.md.
Name it in a `Co-Authored-By:` trailer of the commits it writes.

## Windows

Use WSL2 with Ubuntu. CI runs on Linux; ucmd-engine's `scripts/check-architecture.sh` and the validation
scripts are bash; the Rust HDF5 build needs cmake and a C compiler.
