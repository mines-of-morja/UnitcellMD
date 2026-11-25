# Research plan: reproduce and explain the transport data of LiPF₆/carbonate electrolytes

- **Question:** can UnitcellMD reproduce the transport data of Lehnert 2025, Landesfeind 2019
  and Logan 2018, and explain them with the underlying physics?
- **Data:** κ(c,T), t₊, TDF, D±, η and ρ of LiPF₆ in EC:EMC 3:7, EC:DMC:PC 27:63:10,
  EC:EMC:MP 2:6:2, EC:DMC 1:1 and EMC:FEC 19:1.
- **Basis:** the author's literature summary and MD validation plan (`../Lit/summary/`; the
  papers are not in this repo). This file maps that plan onto the engine: what exists, what is
  missing, in which order. Written 2026-11-17.

## 1. Where the engine stands per validation level

| Level (validation plan §3) | Needs | Exists | Missing |
|---|---|---|---|
| **Engine correctness** (precondition) | the force field evaluated exactly; integrator; ensembles | forces/energies = OpenMM to 1e-13 (M2a); virial = finite difference to 1e-6; NVE Δt-scaling 4.2; NHC and CSVR canonical; C-rescale density = OpenMM (E2.7); bitwise reproducible on any thread count and across restarts (ADR 0010) | water NPT check (E2.7) |
| **0 Pipeline check** (rebuild Lehnert's setup, compare with his MD) | his force field, boxes, ζ, protocol | boxes (SI Table S1), ζ, protocol settings, PME, NHC, barostat | **his solvent parameters are commercial** (Maestro OPLS). With LigParGen we can only compare to within the force-field difference. → decision D1 |
| **1 Pure solvents** | ρ, η, D_self, ε_r, ΔH_vap of EC, EMC, DMC, PC, MP | NPT/NVT; pure-solvent recipes are easy; non-periodic runs for the gas phase | analysis: MSD, Green–Kubo η (needs the pressure-tensor time series, a new output), dipole fluctuations for ε_r |
| **2 Electrolyte structure** | ρ(c,T), Li⁺ coordination, ion pairing, β(t) | trajectories (H5MD, unwrapped, molecules whole) | analysis A1: RDFs, coordination numbers, cluster statistics |
| **3 Transport** | L₊₊, L₋₋, L₊₋ from collective MSDs (Fong); κ, t₊ (COM → VOL); η | trajectories | analysis A1: Onsager coefficients, frame transform, ionicity; replicas; **long runs** |
| **Extension** (validation plan §5) | TDF from Kirkwood–Buff integrals | trajectories | analysis; large boxes |

## 2. What the first measurements say (2026-11-17)

- **Pressure is a force-field test, not a unit-cell artefact.**
  - The mean pressure is intensive, so a correct force field gives about 1 bar at the reference
    density in any box size. Only the fluctuations (±600 bar at 78 nm³) shrink with size.
  - Lehnert tuned his ion counts at 20 °C until the simulated concentration was exact. So his
    force field gives 1.20 g/cm³ for 1 M EC:EMC, which is our box (L = 4.27 nm).
- **The pressure at that density is still relaxing after 25 ps,** averaging about 1000 bar over
  12.7–25.4 ps:
  - the kinetic part, 2K/(3V), is +3650 bar and constant;
  - the force part keeps falling as the liquid's structure relaxes (Li⁺ solvation, Packmol
    packing).
  - Plateau and verdict: `studies/2026-11-17_pressure-at-reference-density` (100 ps), with pure
    EMC at its manufacturer density for attribution.
- **Start-up artefacts, not errors:**
  - T falls to half within 0.05 ps (equipartition into the bonds of a minimized structure);
  - P starts near 8000 bar (bonds at rest length carry no tension yet).
  - Production protocols equilibrate for nanoseconds anyway.
- **The LJ tail correction** (off, as recorded for Lehnert) changes P by about −160 bar here.
  OPLS-AA was parametrized with it. → decision D2.

## 3. The throughput problem

- **Lehnert's campaign:** 3 electrolytes × 7 c × 5 T × 3 replicas = 315 runs. Each run is
  about 10 ns of equilibration plus 50–170 ns of production at 1 fs: some 30–60 µs in total.
- **Our CPU reference backend:** about 1 ns/day for a 7000-atom box on 16 threads, so roughly
  100 years for the campaign. It is the reference for correctness, not for production
  (ADR 0010).
- **Options:**
  - OpenMM on the GPUs as a provider (E3.7): the RX 580 and Radeon VII via OpenCL; expect of
    order 100 ns/day per GPU, to be measured;
  - a cluster (ADR 0002; Lehnert used bwForCluster JUSTUS 2);
  - a reduced campaign (§4).
  The reference backend checks every production backend on short runs.

## 4. Proposed order

1. **Force-field diagnosis** (now): the pressure plateau at the reference density; pure-solvent
   densities (EC at 40 °C, EMC, DMC, PC, MP) against Lehnert SI Table S2.
   *(Correction 2026-11-25, SC-6: Table S2 mixes 20, 25 and 39 °C; use solvent-densities/README.md.)*
2. **Force-field decisions** D1–D3, then fix the parameters until level 1 passes (ρ within
   1–2 %).
3. **Outputs and analysis for transport** (A1):
   - collective MSDs and Onsager coefficients;
   - κ and t₊ in the COM and VOL frames;
   - RDFs and coordination;
   - Green–Kubo η, which needs a pressure-tensor output (a spec addition).
4. **Throughput:** E3.7, the OpenMM GPU provider, checked against the reference backend.
5. **A first transport point:** 1 M EC:EMC at 20 °C, 3 replicas. Fit ζ to κ; compare t₊ with
   eNMR (0.343) and Lehnert's MD (0.373); compare η with Logan.
6. **Then the grid:** first the c-dependence at 20 °C for the three Lehnert blends, then T.
   Landesfeind's EC:DMC and EMC:FEC need their own ζ fits.

## 4a. Progress

- **2026-11-17, step 4 pulled forward (E3.7):** OpenMM on the Radeon VII, double precision,
  22–34 ns/day for the 7036-atom box, about 25× the CPU. Validation:
  - conformance 1e-8;
  - identical NVE trajectory for 0.5 ps;
  - same temperature in NVT.
  Details in `ucmd-engine/validation/e37-openmm/REPORT.md`.
- **Step 1, running:**
  - `studies/2026-11-17_pure-solvent-densities`: 5 solvents × 25/40 °C, NPT on the GPU;
  - `studies/2026-11-17_pressure-at-reference-density`: 1 M EC:EMC at Lehnert's density, CPU.
    After 77 ps: about 555 bar and still falling.

- **Step 3, A1 core** (`ucmd-analysis`, branch `a1`): readers, centres of mass, FFT MSD, Onsager
  L_ij → κ and t₊ (COM), RDF and coordination numbers, block errors. Validated on synthetic data
  with known answers.
  - First real use, 1 M EC:EMC after 20 ps from packing:
    - Li–O(carbonyl) at 0.20–0.21 nm;
    - first-shell coordination number 3.3 (EC 1.0, EMC 1.9, F 0.3), no EC preference yet;
    - the solvation shells are still forming.
  - Transport from 10 ps is meaningless (not diffusive), as expected.
- Open in A1: VOL-frame transform, Green–Kubo cross-check, Yeh–Hummer, ion association
  (FI/NTI/PTI), MDAnalysis comparison.

- **2026-11-19, 1 M EC:EMC NPT at 20 °C, 1 atm, tail correction on**
  (`studies/2026-11-17_electrolyte-npt-{cpu,gpu}`): CPU 600 ps; GPU 1877 ps, then a GPU hang
  (below). Li⁺ first shell from per-frame counts within the first minimum of g(r) over the
  second half: EC carbonyl O 0.27–0.28 nm, EMC carbonyl O 0.29 nm, PF₆ F 0.26 nm.

  | window | ρ CPU | ρ GPU | EC O=C | EMC O=C | PF₆ F | Li⁺ without anion contact |
  |---|---|---|---|---|---|---|
  | 0–10 ps | 1.094 | 1.136 | 0.9 | 1.4 | 1.0 | 0.38 |
  | 100–200 ps | 1.188 | 1.181 | 0.9 | 2.6 | 0.8 | 0.50 |
  | 450–600 ps | 1.187 | 1.184 | 0.6–0.7 | 3.1–3.2 | 0.5–0.6 | 0.62–0.68 |
  | 1500–1875 ps (GPU) | – | 1.185 | 0.43 | 3.65 | 0.26 | 0.81 |

  - **The density settles within about 100 ps** at 1.185–1.187 g/cm³, 1.6 % below Lehnert's
    1.205. It does not follow the solvation shells, which keep changing for about 2 ns.
    *(Correction 2026-11-25, SC-6: 1.205, more precisely 1.202, is the nominal density at exactly 1.0 M and no
    result of Lehnert's model. Against the Landesfeind fit, 1.182, the box is +0.3 to +0.4 %.)*
  - **CPU and GPU agree** over the shared 600 ps (density and solvation trend).
  - **EC is pushed out of the Li⁺ shell.** EC is 34 % of the solvent molecules but gives
    about 10 % of the carbonyl O at the end, still falling. The common picture for
    EC/linear-carbonate electrolytes is the opposite (to be checked against a cited source).
  - **Cause, a parameter artefact:** LigParGen charges each molecule on its own, so the two
    carbonyl O differ. EC: O −0.393 e, C +0.579 e. EMC: O −0.531 e, C +0.588 e. Li⁺ at 0.21 nm
    binds the more negative EMC oxygen, although EC's dipole is far larger (6.0 D vs 0.9 D in
    the liquid, from the fixed charges). The engine is not involved: it evaluates these
    parameters exactly (M2a, B1a).
  - **Consequence for D1:** option (a) is ruled out for transport, because the shell sets t₊
    and κ. Next: published OPLS-AA carbonate parameters (b), carbonyl charges first.
  - **Protocol:** the shells need several ns, so equilibration is ns-long, as with
    Lehnert's 10 ns.
- **2026-11-18, GPU hang:** both GPU jobs (this run and `solvent-densities-tail-on` EC 40 °C)
  stopped writing at 02:04 local time within a minute of each other. They sat idle until the
  shutdown at 23:39. Speed before the hang: about 50 ns/day for 7036 atoms (mixed precision).
  The study driver now has a watchdog (`--stall-minutes`, default 30), and `--retry-failed`
  continues from the checkpoint.

## 5. Decisions for the author

- **D1 Solvent parameters.** Lehnert's Maestro OPLS parameters are not open. Options:
  - (a) keep LigParGen and accept a force-field difference to Lehnert;
  - (b) published OPLS-AA carbonate parameters from the literature, with a citation per
    molecule;
  - (c) our own refit of LJ/charges to pure-solvent densities and ΔH_vap (ADR 0008).
  The level-1 results decide between them.
- **D2 LJ tail correction:** on (OPLS-AA convention) or off (as assumed for Lehnert's LAMMPS
  setup)? About −160 bar.
- **D3 Throughput:** GPU provider first (E3.7), or a cluster account, or a reduced campaign?
