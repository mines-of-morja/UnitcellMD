# ucmd-spec — reference validator

Implements every validation rule and error code of the UnitcellMD spec (`../*.md`). The Rust
engine reader, the builder and the analysis package must agree with it on all fixtures.

```sh
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/ucmd-spec validate ../fixtures/valid/argon-864
.venv/bin/ucmd-spec validate-run ../fixtures/runs/argon-nvt.toml --with-system
.venv/bin/ucmd-spec validate-trajectory out/trajectory.h5      # needs the [trajectory] extra
.venv/bin/pytest
```

The JSON Schemas are read from `$UCMD_SPEC_DIR/schemas` if that variable is set, else from the
copy bundled in the wheel (`ucmd_spec/schemas`), else from `spec/schemas` of the checkout. The
fixtures are read from `$UCMD_SPEC_DIR` or the checkout.
