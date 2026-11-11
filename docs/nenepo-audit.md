# NeNePo_builder audit — input for UnitcellMD

- **Source:** https://github.com/PyProgMo/NeNePo_builder at commit `fd7f1e2` (MIT, © 2023 Moritz
  Limbacher). Inspected 2026-11-11. Line numbers refer to that commit.
- **Purpose:** record what exists, what to carry over, and what must not be carried over.
- **Review (P0.2, 2026-11-11):** all 46 file:line references were re-verified by script against
  the clone in `_reference/NeNePo_builder`, which is still at `fd7f1e2`. Additions from the
  review are marked *(P0.2)*.

## 1. What the code does (pipeline)

0. **Geometry optimization and frequencies** *(P0.2)* (`gaussian_create_opt/gaubuilder.py`,
   configured by `optionsan.py`). Writes the Gaussian `opt … freq` input (`optionsan.py:21`)
   and a SLURM script. The resulting fchk and log feed the sampler.
1. **Wigner sampling** (`ws_rhombus/WignerBase.py`, `WignerInterface.py`, `Wignernointerface.py`,
   `HarmonicBase.py`, `HarmonicGaussian.py`).
   - Reads a Hessian from a frequency calculation and builds the mass-weighted Hessian and its
     normal modes.
   - The program-specific reader is loaded by name, `'Harmonic' + qcp.capitalize()`
     (`Wignernointerface.py:143-145`): the same plugin pattern as the VV adapters. The
     interactive menu offers Molpro, Gaussian, Turbomole, MNDO and BAGEL, but only
     `HarmonicGaussian.py` is in the repo, so only Gaussian works in this snapshot *(P0.2)*.
   - `Wignernointerface.py` takes its inputs interactively, from a TOML file with a
     `[parameters]` table (`:108`), or as seven positional arguments (`:125`).
     `makedyn/builder.py:11` uses the positional form *(P0.2)*.
   - Samples (Q, P) per mode from the harmonic Wigner distribution at temperature T
     (`WignerBase.py:22-31`) and transforms back to Cartesians.
   - Writes `dynamics_XXXX.in`: N, then element + position in **bohr**, then velocities in
     **atomic units**.
2. **Ensemble construction** (`makedyn/builder.py`, configured by `makedyn/options.py`).
   - Runs the sampler and writes Gaussian `.com` templates for the anion, neutral and cation
     states, which include geometry and basis via `@file`.
   - Creates one `Traj_i/` directory per initial condition, plus a SLURM array script
     (`dynstart.bash`, `zekecalc.sub`).
3. **Propagation** (`site-packages/VV_8_*.py`, started by `makedyn/run_dynamic.py`). Velocity
   Verlet on the neutral surface, with gradients from a QC program at every step.
4. **Vertical energies along the trajectory** (`site-packages/catscfsp*.py`, `recalccat7.py`).
   Cation (and anion/VDE) single points on the neutral geometries, giving IP(t).
5. **Signal analysis** (`makedyn/get_signal_10.py`, `average_signal_*.py`, `kaiserstft1.py`,
   `stftsigmap2.py`). The NeNePo signal is averaged over the ensemble, then STFT/Kaiser-window
   frequency analysis is applied.
6. **Post-run housekeeping** *(P0.2)*.
   - `makedyn/cleanup.py` collects the SLURM outputs and plots SCF energy and temperature per
     trajectory (`checkstability`, `:59`) as a visual stability check.
   - `makedyn/remnonedyns.py` moves every trajectory whose `_Energy.out` contains `None` into
     `dynerror/` (`:24-29`).

## 2. The integrator (`site-packages/VV_8_12.py`, class `VelocityVerlet`)

- **Units:** atomic units throughout — bohr, hartree, atomic time; masses in electron masses
  (`aumas` at `:12`); `dt` is converted from fs (`:34`).
- **Update** (`:72-76`): `q_new = q + v·dt + a·dt²/2`, then the gradient at `q_new`, then
  `v_new = v + (a + a_new)·dt/2`. This is velocity Verlet, equivalent to the operator sequence
  B(½) A(1) F B(½).
- **Each step** (`:156-168`):
  - positions are shifted to the centre of mass (`:158`);
  - COM translation and rotation are removed from the velocities (`:161`, via
    `rem_trans_rot`, `:99-105`);
  - optional Berendsen velocity scaling (`:118-121`);
  - outputs are written.
- **Masses:** looked up from a hard-coded table by atomic number (`:15`). Element symbols come
  from `element_d` (`:17`), which covers H, He, C, N, O, F, Ne and Ag only.
- **Outputs:**
  - `<job>_dynamics.xyz` (Å, for VMD);
  - `<job>_dynamics.out` (q and v);
  - `<job>_<Energy>.out` (one row per step, with columns configured in `readenergy.txt`);
  - `time.txt` (one timestamp per step; the cluster script counts its lines).
- **Cluster copies** *(P0.2)*: `site-packages/forcluster/` holds `VV_8`–`VV_8_3` and
  `catscfsp`/`catscfsp2` for the cluster; its `VV_8_3.py` is identical to the `site-packages`
  copy. `site-packages/old/` holds older versions.

## 3. The adapter pattern — already the ForceProvider idea

- `VV_8_12.py:22` loads the adapter by name: `importlib.import_module('VV_8_' + method[0])`.
- An adapter module provides two functions:
  - `calc(comname, writexyz, N, n, q, fchk, get, aulen)`, which writes the geometry, runs the
    program and returns a dict;
  - `initcalc(...)`, for the first step, which may use a different input — e.g. ORCA copies the
    `.gbw` guess.
- The dict holds `gradient` (Eh/bohr) plus any requested quantities (energies of several states,
  dipole moment, …). `readenergy.txt` selects them per program in `write` / `read` / `calc`
  sections (`catscfsp5.py`, `whichenread`).
- Existing adapters: `VV_8_gaussian.py` (g16 + formchk; parser `parse_gau.py` on top of
  `gaussian_parser.py`) and `VV_8_orca.py` (parser `parse_orca.py`, reading `.engrad`). The
  history mentions BAGEL and Q-Chem. The default `method=['qchem', …]` refers to a `VV_8_qchem`
  module that is not in the repo.

**Carry over:** the selection of a force source by name, input templates that the user writes
(maximum flexibility for QC methods), arbitrary per-step observables, and reuse of the
wavefunction guess between steps.
**Formalize as:** the `ForceProvider` trait, `ForceResult.observables` and provider state
(PLAN.md §2.4, E3.3–E3.4).

## 4. Mapping to UnitcellMD

| NeNePo piece | New home | Action |
|---|---|---|
| `VelocityVerlet` (VV_8_12) | `ucmd-md`, operators B·A·F·B | port behaviour; golden test E1.5(d) |
| `VV_8_<program>.calc/initcalc` | `ForceProvider` + i-PI bridge | hardened Python calculators (E3.3) |
| `parse_orca.py`, `parse_gau.py`, `gaussian_parser.py` | `ucmd-bridge` parsers | reimplement with tests; see §7 on authorship |
| `readenergy.txt` write/read/calc | `ForceResult.observables` + output config | redesign |
| Berendsen scaling | CSVR (E1.6), NHC/Langevin (E2.6) | replace |
| `rem_trans_rot` | momentum-removal option, angular only if non-periodic | port |
| Wigner sampler | `ucmd_builder` initial-conditions module (B1.7) | reimplement from the equations |
| `builder.py`, `options.py`, SLURM templates | campaign tool (A2.2) + recipes | redesign |
| `catscfsp*`, `recalccat7.py` (energies along a trajectory) | `ucmd rerun` with a second provider (E1.11, E3.5) | redesign |
| NeNePo signal / STFT scripts | optional `ucmd_analysis.nenepo` module | port later if wanted |

## 5. Issues found — fix them in the new design, do not port them

1. **Temperature uses the wrong number of degrees of freedom.**
   - `VV_8_12.py:111` computes `T = 2·Ekin / (3N·k_B)`. But translation and rotation are removed
     at `:52` and `:161`, so the kinetic energy lives in 3N−6 degrees of freedom.
   - The reported T is therefore low by a factor (3N−6)/3N, i.e. ½ for Ag₄. A Berendsen run
     would target the wrong temperature.
   - Production had the thermostat off (`makedyn/run_dynamic.py:14`), so the thesis trajectories
     are unaffected; only the reported temperature is.
   - *Rule:* N_dof is computed in exactly one place and includes constraints and removed
     momenta.
2. **The Berendsen "divergence" is expected, not a bug.** `README_VV_8.txt` (8_3) notes that
   Ekin+Epot grows when the thermostat is on. Every thermostat exchanges energy with a bath, so
   that sum is not conserved.
   - *Rule:* every thermostat/barostat reports a conserved quantity (H plus the accumulated bath
     work).
3. **External calls are unchecked.**
   - `VV_8_orca.py:12,20-21` and `VV_8_gaussian.py:10-11` call `os.system` without checking the
     exit status.
   - Nothing deletes the previous step's `.engrad`/`.fchk`, and nothing checks that the parsed
     geometry is the one just written. A failed QC run can therefore feed the previous step's
     gradient into the integrator without any error.
   - *Rule:* use fresh outputs, check the exit status, and compare the geometry echoed by the
     program with the requested one (E3.3).
4. **Parse errors are swallowed.**
   - `parse_orca.py:53-65` turns any exception into `{}` and then `''`.
   - The fallback `get_Energy` (`parse_orca.py:5-10`, `parse_gau.py:35-40`, used at
     `parse_gau.py:31-32`) returns the last number on the first line that contains the key
     string. For a key like `gradient` this can be a single float, which NumPy broadcasts to
     every atom in `grad_to_a` (`VV_8_12.py:69-70`): wrong forces, no error.
   - Evidence that this happened in practice *(P0.2)*: after a run, `makedyn/remnonedyns.py:24-29`
     filters out every trajectory whose energy table contains `None`. Failures surfaced only
     afterwards, in the outputs.
   - *Rule:* missing or wrongly shaped data raises `ForceError::Parse`, and the engine checks the
     length and finiteness of every result.
5. **Executables are found via PATH.** On the author's workstation, `/usr/bin/orca` is the GNOME
   screen reader (Debian package `orca`). `os.system('orca …')` would start the screen reader.
   - *Rule:* absolute paths from config, plus a version probe in `initialize()`.
   - Note: ORCA's parallel mode also requires the full path.
6. **Masses come from an element table.** The table covers only a few elements (`VV_8_12.py:15,17`);
   Li and P (for LiPF₆) are missing.
   - *Rule:* masses come from the system package. The engine has no element table.
7. **Gas-phase assumptions.** COM and rotation are removed every step. That is right for an
   isolated cluster and wrong under periodic boundaries, where angular momentum is not conserved.
   - *Rule:* momentum removal is a config option; angular removal is forbidden with PBC.
8. **Configuration is positional and lives in code.** The integrator takes `jobname[0..5]`,
   `Tempr[0..2]` and `write[0..1]` (`VV_8_12.py:21-38`); the ensemble is configured in a Python
   module (`options.py`).
   - *Rule:* named, schema-validated TOML, with the resolved config stored in every output.
9. **It is unclear which version produced the thesis data.** `makedyn/run_dynamic.py:3` imports
   `VV_8_4`, while `site-packages/` holds `VV_8_1` … `VV_8_12` as separate files, and outputs do
   not record the version.
   - *Rule:* git tags, plus provenance (engine git hash, config hash) in every output.
10. **Constants are duplicated with different roundings.**
    - k_B in hartree/K: `3.1671e-6` at `WignerBase.py:26`, but the scipy value at
      `VV_8_12.py:13`.
    - amu → m_e: `1822.88848492937` at `VV_8_12.py:12`, but `1822.8884845` at
      `HarmonicBase.py:8`.
    - Physically negligible, but this is exactly why there is one constants module per language.
11. **A process is launched and files are written on every step.** That is acceptable when DFT
    dominates the cost, and dominates for cheap providers.
    - *Rule:* persistent providers over a socket (i-PI, E3.1).
12. **The SCF guess is provider state.** `Guess(Read,TCheck)` in the Gaussian templates and the
    `.gbw` copy at `VV_8_orca.py:21` carry state between steps.
    - *Rule:* provider state is checkpointed (E3.4).
13. **Directory names can disagree with the calculation** *(P0.2)*.
    `ws_rhombus/QcUwB97XD_def2tzvp/` suggests ωB97X-D, but its `force.inp` runs unrestricted
    TPSSh/def2-TZVP (`force.inp:35,37`).
    - *Rule:* provenance records the level of theory read from the program's own input or output,
      never from paths.

## 6. Files in the repo that can serve as test fixtures

Inventory from P0.2, scripted. The table lists unique files only. Six pairs of files are
byte-identical:
- the top-level `ws_rhombus/force.fchk` and `optstruct.log` are copies of the files in
  `TPSSh_def2svpU/`;
- the top-level `ani.log` and `forcean.fchk` are copies of the files in `CCSD20K1/`;
- `wB97XD/` duplicates `wB97XD_def2tzvp/`.

Note that the top-level `force.fchk` (UTPSSh/def2-SVP) and the top-level `ani.log` (CCSD) belong
to different calculations.

| Files (in `ws_rhombus/`) | Program, job | Level of theory | System | Contains | Use for |
|---|---|---|---|---|---|
| `TPSSh_def2svpU/force.fchk` + `optstruct.log` | g16 opt + freq | UTPSSh/def2-SVP | Ag₄⁻ doublet | gradient, Hessian, dipole, energy; 6 frequencies | fchk parser (E3.3); Hessian → frequencies and Wigner input (B1.7). Smallest Gaussian pair (1 MB + 0.4 MB) |
| `TPSSh_tzvpU/force.fchk` + `optstruct.log` | g16 opt + freq | UTPSSh/def2-TZVP | Ag₄⁻ doublet | as above | the sampler input named in `makedyn/options.py` |
| `TPSSh_def2svp/`, `TPSSh_tzvp/`, `TPSSh_tzvppd/` (`forcean.fchk` + `ani.log`) | g16 opt + freq | UTPSSh, three basis sets | Ag₄⁻ doublet | as above | basis-set variants |
| `wB97XD_def2tzvp/`, `UwB97XD_def2tzvp/` (`force.fchk` + log) | g16 opt + freq | UωB97X-D/def2-TZVP | Ag₄⁻ doublet | as above | second functional |
| `20Ktraj/force.fchk` + `rhombus.log` | g16 opt + freq | ROωB97X-D/def2-TZVP | Ag₄⁻ doublet | as above | restricted open-shell variant |
| `CCSD20K1/forcean.fchk` + `ani.log` | g16 opt + freq | UCCSD (frozen core) | Ag₄⁻ doublet | as above | correlated-method fchk |
| `Ag8_wB97XD_28/forceneut.fchk` + `neut.log` | g16 opt + freq | RωB97X-D | Ag₈, neutral singlet | as above; 18 frequencies | parser generality (N ≠ 4, q = 0) |
| `QcUwB97XD_def2tzvp/force.inp`, `force.inp.out`, `force.fchk` | Q-Chem force | UTPSSh/def2-TZVP (issue 13) | Ag₄⁻ doublet | gradient only in `force.inp.out` ("Gradient of SCF Energy"); the Q-Chem fchk has no gradient or Hessian section | a Q-Chem output parser, if one is ever needed |
| `dynamics_0000.in` … `dynamics_0039.in` (40 files) | Wigner sampler output | — | Ag₄ rhombus, 20 K | positions (bohr), velocities (atomic units) | statistical checks of the reimplemented sampler (B1.7); starting points for the thesis regression (E3.9) |

- **ORCA:** no outputs in the repo. The `.engrad` format is simple, so use a recorded file from a
  real run, or a synthetic one, for the tests.
- **Failure-injection fixtures** (E3.3) don't exist yet. Create them as truncated or stale
  copies of the files above.

## 7. Provenance and licence notes

- The repo is MIT-licensed by the author.
- `gaussian_parser.py` carries the header `author: j.hoche`, and one `read_xyz.py` carries
  `@author: xmiao`. Do not copy these files into UnitcellMD; reimplement the parsing with tests,
  or get permission and keep the attribution.
- The Wigner sampler files have no author header. Confirm their origin with the author before
  copying any code. Reimplementing the sampler from the equations (B1.7) is unproblematic.
