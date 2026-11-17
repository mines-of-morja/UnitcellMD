# EC temperature scan (2026-11-17)

- **Question:** how do the 35 carbonate electrolyte test boxes behave from −10 to 50 °C with
  the working-horse force field `opls-aa-carbonates` (ADR 0009)? What changes with temperature,
  what does not, and what must be tuned?
- **Requested by:** the author, 2026-11-17, as a first look at the force field. Not a
  production protocol.
- **Plan:** [study.toml](study.toml). **Contents and progress:** `INDEX.md` (generated).

## What runs

- **Systems:** the 35 recipes of ucmd-builder `examples/EC/recipes`: five mixtures × seven
  concentrations, 5646–14835 atoms.
- **Conditions:** −10, 0, 10, 20, 30, 40, 50 °C, so 245 runs.
- **Protocol per system:** build with Packmol, then one FIRE minimization (max |F| < 100
  kJ mol⁻¹ nm⁻¹).
- **Protocol per run:** 10 ps NVT from the minimized box, with new Maxwell–Boltzmann velocities
  at the target temperature. Nosé–Hoover chain, τ = 0.1 ps; 1 fs steps without constraints;
  1.4 nm cutoff, PME to 10⁻⁵. These are Lehnert 2025's settings, as in M2a.
- **Outputs per run:** a thermo row every 10 fs, a frame every 0.1 ps (float32), a checkpoint
  every ps.

## Caveats: read before interpreting

1. **Constant volume.** The barostat (E2.7) is not built yet. Every box keeps the approximate
   edge from `boxes.csv` at every temperature, so the density does not follow the temperature.
   The pressure is the useful signal here: it shows how far each box is from the force field's
   own density, and how that changes with T.
2. **10 ps is short.** The first 1–2 ps are the transient after minimization (T dips, then
   recovers). INDEX.md averages over 5–10 ps. That is enough for T, P and energies, not for
   transport: diffusion and conductivity need nanoseconds.
3. **ζ is unset for EC:DMC and EMC:FEC.** The table has no value, so their ions are unscaled
   (charge ±1). The other mixtures use Lehnert's ζ (0.75; 0.73 for EC:EMC:MP).
4. **DMC, PC, MP and FEC** come from LigParGen (ADR 0009, amended 2026-11-17), like EC and EMC.
   They are not validated against densities yet.

## How to drive it

```sh
python3 tools/study/ucmd_study.py plan   studies/2026-11-17_ec-temperature-scan   # order, seeds
python3 tools/study/ucmd_study.py run    studies/2026-11-17_ec-temperature-scan   # resumable
python3 tools/study/ucmd_study.py status studies/2026-11-17_ec-temperature-scan   # INDEX.md
python3 tools/study/ucmd_study.py stop   studies/2026-11-17_ec-temperature-scan   # graceful
```

Open any run in the GUI:
`ucmd-builder/start-gui.sh studies/2026-11-17_ec-temperature-scan/runs/<system>/<T>`.
