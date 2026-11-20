# Changelog

## 0.1.1 — 2026-11-20 (approved by the author for implementation; not yet tagged)

Backwards compatible: every 0.1.0 file stays valid.

- run-config: `[output.thermo] pressure_tensor` (bool, default false) adds the six components of
  the symmetrized pressure tensor to the thermo table (Green–Kubo viscosity, design E2.9 §4).

## 0.1.0 — 2026-11-12

Initial version, approved at Gate 0 (git tag `spec-v0.1.0`). Contents:

- units and conventions;
- the system package (`system.json` + NPY arrays);
- the run configuration and the machine profile;
- the H5MD trajectory profile;
- the required checkpoint content;
- the force-provider contract with the i-PI profile;
- JSON Schemas, fixtures, and the reference validator `ucmd-spec`.

The decisions are recorded in ADR 0003.
