# Architecture decision records

One file per decision, named `NNNN-short-title.md`, numbered in order and never renumbered.
A superseded ADR stays in place; its replacement says which ADR it supersedes.

| # | Decision | Status |
|---|---|---|
| [0001](0001-units.md) | Units: nm, ps, amu, kJ/mol, e, K | accepted 2026-11-11 |
| [0002](0002-local-first-execution.md) | Local-first, cluster-capable execution | accepted 2026-11-11 |
| [0003](0003-spec-v0.1-formats.md) | Spec v0.1 formats | provisional (agent), Gate 0 review |
| [0004](0004-h5md-writer-rust.md) | H5MD from Rust: hdf5-metno, bundled static HDF5 | accepted (agent, spike S1), Gate 0 review |
| [0005](0005-openmm-oracle.md) | OpenMM 8.6 as validation oracle | accepted (agent, spike S2), Gate 0 review |
| [0006](0006-gui-viewer-stack.md) | GUI viewer: PySide6 + pyvistaqt confirmed | accepted (agent, spike S3), Gate 0 review |
| [0007](0007-ipi-wire-conventions.md) | i-PI wire conventions; ASE as universal provider | accepted (agent, spike S4), Gate 0 review |

## Template

```markdown
# NNNN — Title

- **Status:** proposed | accepted (date, by whom) | superseded by NNNN
- **Context:** what forces the decision (2–5 lines)
- **Decision:** what we do
- **Consequences:** what follows, including the costs
```
