# Architecture decision records

One file per decision, named `NNNN-short-title.md`, numbered in order and never renumbered.
A superseded ADR stays in place; its replacement says which ADR it supersedes.

| # | Decision | Status |
|---|---|---|
| [0001](0001-units.md) | Units: nm, ps, amu, kJ/mol, e, K | accepted 2026-11-11 |
| [0002](0002-local-first-execution.md) | Local-first, cluster-capable execution | accepted 2026-11-11 |

## Template

```markdown
# NNNN — Title

- **Status:** proposed | accepted (date, by whom) | superseded by NNNN
- **Context:** what forces the decision (2–5 lines)
- **Decision:** what we do
- **Consequences:** what follows, including the costs
```
