# UnitcellMD specification

Version **0.1.0**, draft pending author review at Gate 0. This is the contract between
`ucmd-builder`, `ucmd-engine`, `ucmd-analysis` and every force provider: the components share
these files and protocols, and nothing else.

| Document | Content |
|---|---|
| [units.md](units.md) | unit system, constants, geometry and mechanics conventions |
| [system-package.md](system-package.md) | system package: `system.json`, molecule types, force field, state arrays, error codes |
| [run-config.md](run-config.md) | `run.toml` and the machine profile |
| [trajectory-h5md.md](trajectory-h5md.md) | H5MD trajectory profile |
| [checkpoint.md](checkpoint.md) | required checkpoint content |
| [force-provider.md](force-provider.md) | force-provider contract, i-PI profile, conformance tests |
| [schemas/](schemas/) | JSON Schemas for `system.json` and the parsed `run.toml` |
| [fixtures/](fixtures/) | normative valid and invalid examples |
| [validator/](validator/) | Python reference validator `ucmd-spec` |
| [CHANGELOG.md](CHANGELOG.md) | version history |

The design decisions behind this version are collected in
[ADR 0003](../docs/decisions/0003-spec-v0.1-formats.md).

## Validating

```sh
cd spec/validator
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/ucmd-spec validate ../fixtures/valid/argon-864          # system package
.venv/bin/ucmd-spec validate-run ../fixtures/runs/argon-nvt.toml   # run configuration
```

Exit status: 0 = valid (warnings possible), 1 = invalid, 2 = usage error. Add `--json` for
machine-readable output.

## Fixtures for other repositories

- Contract tests in the component repositories read the fixtures from `$UCMD_SPEC_DIR`. If it is
  unset, they use `../spec` relative to the component repo root, which is the location in the
  workspace layout.
- Each invalid fixture contains an `expected.json` with the error code a reader must report.

## Changing the spec

A change consists of:

- an ADR in `docs/decisions/`;
- an entry in `CHANGELOG.md`;
- updated schemas and fixtures;
- updates to every reader (validator, engine, builder, analysis), made in one coordinated
  change.

The versioning rules are in system-package.md §9.
