# Calculation plan: what to run, why, in which order

- **Companion** of [reproduction-plan.md](reproduction-plan.md) (the strategy) and
  [report/report.md](report/report.md) (the results so far).
- **Principle (author, 2026-11-19):** knowing what the model *cannot* explain matters as much as
  what it can. Every calculation either tests the model against an independent number, or
  explains a measured trend. Results that only reproduce a fitted number (κ at the ζ-fit point)
  count as calibration, not as evidence.
- **Cost unit:** GPU hours on the Radeon VII, mixed precision, 7000 atoms ≈ 55 ns/day,
  i.e. 2.3 ns/h or 0.44 h/ns (76 ns/day measured on 2026-11-19). Earlier versions of this
  table read 2.3 h/ns, which overstated every GPU cost about 5×. One GPU job at a time (2026-11-18 hang).
- **Status:** ✅ done · ⏳ running or queued · ⬜ planned · 🔧 needs a tool first ·
  ❓ needs a decision.

## Stage A: assess the current model (LigParGen set, ADR 0009)

| ID | Calculation | Tests | Cost | Status |
|---|---|---|---|---|
| A1 | Pure EC, EMC, DMC, PC, MP: NPT 1 atm, 25 and 40 °C, 0.5 ns, tail correction on | density against Lehnert SI Table S2 (±2 %) | 10 × 0.2 h | ✅ 10/10: DMC, PC, MP within 2 %; EMC +2.9 %, EC −3.5 % (at 40 °C) fail (report §3.2) |
| A2 | 1 M EC:EMC, NPT 1 atm, 20 °C, 3 ns (GPU) plus 0.6 ns (CPU twin) | electrolyte density against Lehnert's model; equilibration time; backend agreement | GPU 1.3 h; CPU twin about 14 h | ✅ ρ = 1.1850 ± 0.0008 g/cm³ (−1.4 %); shell 1.5–3 ns in report §3.4 |
| A3 | Transport pilot: A2's end state, 20 ns NVT at 20 °C | whole transport chain on real data; noise of L₊₋; κ, t₊, D with the current model | about 9 h at 55 ns/day (took 10 h, with 10 GPU hangs) | ✅ κ 0.42 ± 0.09 S/m, t₊ 0.29 ± 0.11; L₊₋ unresolved after 20 ns; report §3.5 |
| A4 | Li⁺ preference: one Li⁺PF₆⁻ pair in pure EC and in pure EMC, plus 1 Li⁺ in EC:EMC 1:1 (dilute), 5 ns each | which carbonyl Li⁺ binds, without salt crowding; isolates the charge effect | 3 × ≤ 2.5 h | ✅ done 2026-11-20 20:06Z (OpenCL, many hang restarts; 0 label swaps). Last 4 ns, one Li⁺: **pure EC** 4.8 EC O=C, free; **pure EMC** 3.4 EMC O=C + 0.88 PF₆⁻ (contact pair); **1:1** first shell EC 0.89 / EMC 3.65 (**EC 20 %** of the carbonyl O at 50 % of the molecules), within 0.516 nm EC 29 %. Residence at Li⁺: EC 24 ps, EMC 250 ps (continuous); 25 EC and 15 EMC molecules visited. EC depletion is parametric, not crowding. M1 counterpart: `studies/2026-11-20_li-preference-m1` (queue 4) |
| A5 | Enthalpy of vaporization of each solvent: liquid run (A1) plus a single molecule in vacuum (non-periodic, 10 ns) | ΔH_vap against experiment: cohesion, independent of density | 5 × 2 h CPU | ❓ experimental ΔH_vap source needed |
| A6 | Viscosity of the pure solvents and of 1 M EC:EMC (Green–Kubo, 5–10 ns NVT each) | η against Logan 2018 (EC:EMC); independent of ζ | 6 × ≤ 4.5 h | 🔧 pressure-tensor output (spec addition) |
| A7 | Static dielectric constant of EC and EMC from dipole fluctuations (10 ns NVT) | ε against literature: the screening that ion pairing depends on | 2 × 4.5 h | 🔧 analysis (dipole series); ❓ ε source |
| A8 | Density of 1 M EC:EMC over T: −10, 20, 50 °C, NPT 2 ns | thermal expansion of the electrolyte | 3 × 1 h | ⬜ |

## Stage B: improve the force field (decision D1)

| ID | Calculation | Purpose | Status |
|---|---|---|---|
| B1 | Literature survey: published, citable OPLS-AA/AMBER carbonate parameters (EC, EMC, DMC, PC, MP, FEC), with licences | candidates for D1 (b) | ⏳ first pass: [forcefield-survey.md](forcefield-survey.md) |
| B2 | Charges from quantum chemistry: RESP fits for all solvents with one method | candidate for D1 (c) | ❓ QC program (psi4 in a container) and method |
| B3 | For each candidate set: repeat A1, A4 and A5 | choose the set by evidence, not by name | ⬜ after B1/B2 |
| B4 | Repeat A2 with the chosen set | electrolyte density and Li⁺ shell with EC in it | ⬜ |

**Exit criterion of stage B:**
- pure-solvent densities within 2 %;
- ΔH_vap within about 5 %, if a source is approved;
- in 1 M EC:EMC the Li⁺ shell has EC above its share of the solvent (34 % of the molecules).
  - Model reference: Lehnert SI Fig. S10, EC ≈ 47 % of the carbonyl O within rs = 5.16 Å at
    1 M, 20 °C. An experimental source is still open.
  - Counted two ways: Lehnert's (Li–carbonyl-O ≤ 0.516 nm) and ours (first Li–O minimum).
    Baseline A3: 20 % and 11–12 % (report §3.4).
- the strategy behind stage B, and what is deliberately left out:
  [forcefield-strategy.md](forcefield-strategy.md).

## Stage C: production with the chosen model (the reproduction)

| ID | Calculation | Compared with | Cost | Status |
|---|---|---|---|---|
| C1 | ζ fit: 1 M EC:EMC, 20 °C, 3 values of ζ × 30 ns | Landesfeind κ (1 M, 20 °C): **calibration** | 3 × 13 h | ⬜ |
| C2 | Concentration series, EC:EMC, 20 °C: 0.1, 0.5, 1.0, 1.5, 2.0, 3.0 M, 3 replicas × 30 ns | κ(c) and the position of the maximum (Landesfeind, Lehnert); t₊(c) | 18 × 13 h | ⬜ |
| C3 | Temperature series, 1 M EC:EMC: −10, 0, 20, 40 °C, 3 replicas × 30 ns (−10 °C: 60 ns) | κ(T), D(T), t₊(T); Walden behaviour | 9 × 13 h + 3 × 26 h | ⬜ |
| C4 | Finite size: 1 M, 20 °C in a box 2× larger, 1 replica | Yeh–Hummer correction of D; box independence of κ | 1 × 26 h | ⬜ |
| C5 | EMC:FEC 19:1 at 0.5, 1.0, 1.5, 2.0 M, 20 °C (needs its own ζ, FEC parameters from B) | the shifted κ maximum of the EC-free electrolyte | 12 × 13 h | ⬜ |

## Stage D: explanations (what the measurements cannot see)

| ID | Analysis or calculation | Question | Tool |
|---|---|---|---|
| D1 | Split κ into self (Nernst–Einstein) and distinct parts (L₊₊, L₋₋, L₊₋) along C2 and C5 | which correlation sets the κ maximum, and why it shifts without EC | ✅ tool; on the pilot no distinct part is resolved after 20 ns |
| D2 | Walden analysis along C3 (κ against 1/η), and ionicity against T | how much of κ(T) is viscosity, how much association | needs A6 (η) |
| D3 | Li⁺–PF₆⁻ potential of mean force at −10, 20, 50 °C (umbrella sampling) | energy and entropy of ion pairing: why association grows with T | 🔧 distance restraint in the engine |
| D4 | Cluster populations (free, pairs, triple ions, larger) and their share of the current, at −10 °C | can charged clusters make t₊ negative (Landesfeind) or not (Lehnert, eNMR)? | ✅ tool; pilot: 77 % free, 21 % pairs |
| D5 | Solvent residence times at Li⁺ against the Li⁺ diffusion time | vehicular or exchange transport of Li⁺, and why Li⁺ is slower than PF₆⁻ | ✅ tool; pilot: EMC stays ≈ 0.6 ns, EC 28 ps |
| D6 | Volume-fixed frame and electrophoretic mobilities | comparison with eNMR (Lehnert: 20 % gap for EC:EMC:MP) | 🔧 VOL frame (needs partial molar volumes from C2) |

## What we can only partly test, or not at all (recorded on purpose)

- **TDF and D±** depend on the experimental a(c,T) (Lehnert Eq. 6), so agreement there does not
  validate the model (validation plan §4).
- **Freezing below 0 °C:** fixed-charge MD stays a supercooled liquid; EC melts at 36 °C.
- **Polarization:** ζ stands in for electronic screening. A constant ζ cannot follow the
  concentration dependence of screening, and Lehnert's κ at 3 M is already off.
- **Interphases and SEI** (the reason for the t₊ dispute) are outside a bulk model. MD can only
  say what bulk transport looks like.

## Order of work (proposal)

1. **Now:** finish A1–A3 (tonight). Build the tools for D1, D4 and D5 while the GPU runs, and
   test them on A3.
2. **Next:** B1 (survey) and the decision on D1. Run A4 on the current set as the baseline.
3. Then B3/B4, C1, and C2 + C3 (about 430 GPU hours, i.e. three weeks), with D1–D5 running alongside as the
   data arrive.
4. C5 and D3/D4 last.
