# Changelog

## 0.1.3 — 2026-11-25 (approved by the author, SC-3 question 3a; not yet tagged)

Backwards compatible: every older file stays valid and means the same. Readers without 0.1.3 reject
a run configuration that uses the new key (unknown key, `E_SCHEMA`), so they fail closed.

- units: the molecular pressure is defined (§4). The definition of `pressure_bar` is unchanged.
- run-config: `[output.thermo] pressure_molecular` (bool, default false) adds the column
  `pressure_molecular_bar` to the thermo table.
- fixtures: `runs/argon-pressure-molecular.toml`, `runs/invalid/pressure-molecular-not-bool.toml`.

## 0.1.2 — 2026-11-22 (decided by the author's delegation, ADR 0015; not yet tagged)

Backwards compatible: every 0.1.0 and 0.1.1 file stays valid and means the same. Readers without
0.1.2 reject packages that use the new key (unknown key, `E_SCHEMA`), so they fail closed.

- system package: `forcefield.pair_overrides`, per-type-pair Lennard-Jones σ and ε that replace
  the combination rule for that pair, 1-4 pairs included (§5.2). New error code
  `E_PAIR_OVERRIDE` (a repeated pair); an unknown type in an override is `E_REFERENCE`.
- fixtures: `valid/kob-andersen-500` (the binary LJ mixture of Kob & Andersen 1995, whose A–B pair
  no combination rule gives), `invalid/pair-override-unknown-type`,
  `invalid/pair-override-duplicate`.

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
