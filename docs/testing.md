# Hands-on testing

What you can try yourself now, with the expected results. Every command and number below
was checked on the workstation: §0–7 on 2026-11-12 (engine branch `e1`, builder branch `b1`),
§8 on 2026-11-13 (engine branch `e2`).

**When something looks wrong**, report it in chat or as a GitHub issue in the repo concerned.
Include:
- the command and any change you made to `run.toml`;
- the full output, including the `ucmd 0.0.0 (<git hash>)` line;
- what you expected instead.

## 0. Set up once

```sh
cd ucmd-engine                       # inside the UnitcellMD workspace
git switch main                      # E1 is approved and merged
. "$HOME/.cargo/env"                 # only if `cargo` is not found
cargo build --release                # ~2 min the first time (it also builds HDF5)
alias ucmd="$PWD/target/release/ucmd"
```

## 1. Automated checks (about 2 minutes)

```sh
UCMD_REQUIRE_SPEC=1 cargo test --workspace
```

- **Expected:** every test passes ("test result: ok" for each crate, `0 failed`).
- `UCMD_REQUIRE_SPEC=1` makes the contract tests fail instead of skip when the spec fixtures in
  `../spec` are missing.

## 2. First run: liquid argon, 20 ps (about 10 seconds)

```sh
ucmd check examples/argon-quickstart/run.toml
ucmd run   examples/argon-quickstart/run.toml
```

**Expected output:**
- `OK` from the check;
- `done: 5000 steps in ~10 s (~180 ns/day), final T = 88.94 K`. The final T is exactly this
  value: same seed, same result.
- **From E2 on**, the same run prints `final T = 95.88 K` and a `hardware:` line.
  - E2 switched to machine-independent random samplers
    ([ADR 0010](decisions/0010-swappable-hardware.md)).
  - The value is the same on every computer and for any thread count, and a CI test proves it
    on GitHub's machines.

The outputs land in `examples/argon-quickstart/out/` (ignored by git).

**`thermo.tsv`** is a tab-separated table: step, time_ps, potential, kinetic, total, conserved
(kJ/mol), temperature_K, pressure_bar, volume_nm3. Open it in LibreOffice or gnuplot, or view
it with `column -t out/thermo.tsv | less`. What to look for:
- the potential energy rises from −5595 kJ/mol (the fixture starts from a lattice) to about
  −4690 within a few ps, as the crystal melts;
- the temperature fluctuates around 94.4 K (CSVR thermostat);
- `conserved_energy_kjmol` stays at −4578.7, changing by only ~0.04 kJ/mol over the run. This is the
  integrator plus thermostat bookkeeping.

**`trajectory.xyz`** is extended XYZ in Å. Open it in OVITO, VMD, Jmol or `ase gui`. Positions
are unwrapped, so atoms gradually leave the box. That is intended: molecules always stay whole
(PLAN.md D11).

**`checkpoint.ucchk`** is the restart file, written every 2500 steps.

## 3. Restart: a run continues bitwise

Inside `examples/argon-quickstart/`:

```sh
cd examples/argon-quickstart
sed -i 's/^steps = .*/steps = 7500/' run.toml
ucmd run run.toml && cp out/thermo.tsv /tmp/thermo-straight.tsv     # 7500 steps in one go
sed -i 's/^steps = .*/steps = 5000/' run.toml && rm -rf out
ucmd run run.toml                                                    # 5000 steps …
sed -i 's/^steps = .*/steps = 7500/' run.toml
ucmd run run.toml --restart out/checkpoint.ucchk                     # … plus 2500 after a restart
cmp out/thermo.tsv /tmp/thermo-straight.tsv && echo "bitwise identical"
git checkout run.toml
```

- **Expected:** the restart prints `steps 5000..7500 … (restart)`, and `cmp` reports nothing
  except `bitwise identical`.
- Changing anything other than `steps` makes the restart refuse, unless you pass `--force`.

## 4. Single point and export

```sh
ucmd singlepoint run.toml                 # JSON: energy, virial, max force of the initial state
ucmd export run.toml --checkpoint out/checkpoint.ucchk --out /tmp/argon-30ps.ucsys
ucmd check /tmp/argon-30ps.ucsys          # the exported package is a valid system package
```

- **Expected:** `energy_kjmol` = −5594.75…, the same as step 0 in `thermo.tsv`.
- For `ucmd rerun`, write the trajectory as H5MD: rename `trajectory.xyz` to `trajectory.h5`
  in `run.toml` and run again. Then:

  ```sh
  ucmd rerun run.toml --trajectory out/trajectory.h5 --out /tmp/rerun.tsv
  ```

  This re-evaluates the energies of every frame. They match the ones recorded during the run.

## 5. Things to try, including breaking it

| Change in `run.toml` | What happens |
|---|---|
| `timestep_fs = 40.0` | still runs; the conserved energy now drifts by ~9 kJ/mol over 80 ps instead of ~0.04 |
| `timestep_fs = 100.0` | the dynamics explodes. The engine stops cleanly: `non-finite force on atom …; last good state (step 13) saved to out/checkpoint.emergency.ucchk`, exit code 1. It never continues with bad numbers |
| remove the `[thermostat]` block | NVE: the total energy is conserved, the temperature drifts freely |
| `temperature_K = 120` in both places | hotter liquid, higher pressure |
| `ucmd check ../spec/fixtures/invalid/<name>` (from `ucmd-engine/`) | every broken package gives its error code, e.g. `E_NET_CHARGE`, `E_MOLECULE_SPLIT` |

## 6. Physics validation against OpenMM (about 5 minutes)

This needs the two Python environments once (commands table in `CLAUDE.md`):
`spec/validator/.venv` and `tools/oracle/.venv`. Then:

```sh
validation/argon/run.sh
```

It equilibrates argon, runs 100 ps in ucmd and in OpenMM, and compares energies, temperature,
pressure, g(r), diffusion and drift. **Expected: PASS 8/8**, with numbers close to
`validation/argon/REPORT.md`. Exact values differ from the report (different random start),
but every check must pass.

## 7. The builder: an electrolyte box from a recipe (branch `b1` of ucmd-builder)

```sh
cd ucmd-builder
git switch b1
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'   # once; includes RDKit and Packmol
.venv/bin/pytest -q                                          # expected: 83 passed, about 25 s
```

What to try:

| Command | Expected result |
|---|---|
| `.venv/bin/ucmd-build library` | three data sets: `argon-rahman1964`, `opls-aa-carbonates` (EC, EMC, Li, PF6), `water-spcfw` |
| `.venv/bin/ucmd-build compose examples/lp57-1M.toml` | 47 Li, 47 PF6, 168 EC, 332 EMC; box 4.276 nm; 0.998 M |
| `.venv/bin/ucmd-build build examples/lp57-1M.toml -o /tmp/lp57.ucsys` | about 20 s; `wrote /tmp/lp57.ucsys: 7036 atoms …, closest intermolecular pair 0.220 nm`, and a note that the density is a placeholder |
| `../ucmd-engine/target/release/ucmd check /tmp/lp57.ucsys` | `OK`: the engine reads the builder's package. It cannot run it yet; molecular force fields arrive with E2 |
| `.venv/bin/ucmd-build xyz /tmp/lp57.ucsys -o /tmp/lp57.xyz` | open it in OVITO, VMD or `ase gui`: a periodic 4.3 nm box of whole molecules |

Things to try or break:
- Change `molarity_mol_L` or `solvent` in a copy of the recipe and watch `compose`.
- Set `charge_scale = 1.0`, and see `provenance.transforms` in `system.json` change.
- Add a typo to a key: you get an error that names it.
- Add a component with `molecule = { smiles = "CCO" }` (ethanol): `no template … matches`,
  because the library has no ethanol. A new molecule needs a cited source: a library template,
  or a GROMACS topology through `gromacs-top`.

**Validation against OpenMM** (needs `tools/oracle/.venv`):

```sh
python3 validation/b1-openmm/fetch_ligpargen.py /tmp/lpg && validation/b1-openmm/run.sh /tmp/lpg
```

Expected: `PASS` for EC and EMC, then finite PME energies for the full box. See
`validation/b1-openmm/REPORT.md`.

## 8. The engine runs the electrolyte box (branch `e2` of ucmd-engine)

E2 core: bonded terms, LJ with exclusions and 1-4 pairs, PME, the FIRE minimizer, Nosé–Hoover
chains and Langevin BAOAB, and threads that never change a result.

```sh
cd ucmd-engine
git switch e2
cargo build --release
UCMD_REQUIRE_SPEC=1 cargo test --workspace           # expected: all pass (about 1 minute)
cd examples/electrolyte
../../../ucmd-builder/.venv/bin/ucmd-build build ../../../ucmd-builder/examples/lp57-1M.toml -o box.ucsys
../../target/release/ucmd minimize minimize.toml --out minimized.ucsys
../../target/release/ucmd run run.toml
```

| Step | Expected result |
|---|---|
| build | about 20 s; 7036 atoms (as in §7) |
| `ucmd minimize` | about 40 s: `converged: 618 steps …, E 63594.0496 → -51451.80 kJ/mol, max \|F\| 18838.5 → 99.88 kJ/mol/nm`, then `wrote minimized.ucsys` |
| `ucmd run` | about 2.5 min on 16 threads (70 ms per step); the banner shows `N_dof = 21105` and the hardware; `final T = 301.19 K`. In `out/thermo.tsv`, T falls to about 170 K within 10 fs and is back near 298 K after 0.5 ps: the minimized structure turns kinetic into potential energy at once, then the thermostat heats it |

Things to try:
- **Threads change only the speed.** Set `steps = 200` and run once with all cores. Move
  `out/` to `out-all/`. Then write `threads = 4` into a machine profile
  (`printf 'threads = 4\n' > /tmp/t4.toml`) and run with `UCMD_MACHINE_PROFILE=/tmp/t4.toml`.
  - The banner says `4 threads`; the 200 steps take about 30 s instead of 15 s.
  - `cmp out/thermo.tsv out-all/thermo.tsv` prints nothing: the files are byte-identical.
- **Restart:** set `steps = 1000`, run, set `steps = 2000`, and continue with
  `ucmd run run.toml --restart out/checkpoint.ucchk`. The thermo table equals the one of a run
  in one go.
- **Langevin instead of Nosé–Hoover:** `integrator = "langevin-baoab"` and
  `[thermostat] kind = "langevin"`, `temperature_K = 298.15`, `friction_per_ps = 1.0`. The
  `conserved_energy_kjmol` column is then K + U minus the heat exchanged.
- **Break it:** set `cutoff_nm = 2.5`, larger than half the box. The run stops at once with
  `error: force provider failed at step 0: invalid input: cutoff + skin (2.7 nm) exceeds half
  the smallest cell height (2.1379638559193115 nm)`.

### 8a. Watch the box and a running simulation

Until the GUI preview (B2a) exists, three tools do the job. Run them from
`ucmd-engine/examples/electrolyte`, after `box.ucsys` and `minimized.ucsys` exist (see above):

```sh
B=../../../ucmd-builder/.venv/bin
# the unit cell: 7036 atoms in the 4.28 nm box; -r 2,2,2 adds periodic images
$B/ucmd-build xyz minimized.ucsys -o minimized.xyz && $B/ase gui -r 2,2,2 minimized.xyz &
# start 2 ps of NVT that writes an XYZ trajectory (out-watch/)
../../target/release/ucmd run watch.toml &
# live plots of temperature, energies, pressure and energy terms, refreshed every second
$B/python ../../../tools/watch/live_plot.py out-watch/thermo.tsv &
# the movie: every frame written so far (one per 20 fs); Tools → Movie … plays it
$B/ase gui out-watch/trajectory.xyz
```

- `ase gui` reads the trajectory once. Open it again to get newer frames.
- The positions are unwrapped, so that molecules stay whole. Over a long run, molecules move
  out of the drawn cell; that is expected.
- With 7036 atoms, `ase gui` redraws slowly. The B2a GUI will render with VTK (ADR 0006).

**Milestone M2a, the full check** (about 30 minutes on 16 threads; needs `tools/oracle/.venv`):

```sh
cd ucmd-engine && validation/m2a/run.sh
```

It builds the box, compares single points with OpenMM before and after minimization, runs
10 ps of NVT, restarts in the middle, repeats 200 steps on 1, 4 and 16 threads, and checks the
step-size dependence of the energy in NVE. Expected: `**Result: PASS**` in
`validation/m2a/REPORT.md`.

## Coming next

- **The GUI preview (B2a):** design in `docs/design/B2a.md`, for your approval.
- **The rest of E2:** constraints (E2.5), the barostat for the density (E2.7), speed (E2.8).
