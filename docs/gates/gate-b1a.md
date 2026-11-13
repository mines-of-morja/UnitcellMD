# Gate B1a report — headless builder

- **Date:** 2026-11-12.
- **Where:**
  - branch `b1` of `ucmd-builder` (9 commits);
  - branch `b1a` of this repo (oracle v1, this report).
- **Design:** [design/B1.md](../design/B1.md), approved 2026-11-12, with the working horse of
  [ADR 0009](../decisions/0009-working-horse-force-field.md).
- **Asked of the author:**
  - try it (testing.md §7);
  - approve or change §3 and §4;
  - then `b1` and `b1a` are merged.

## 1. Summary

- **The builder makes Lehnert's electrolyte box from a recipe.**
  - `ucmd-build build examples/lp57-1M.toml` gives 1 M LiPF₆ in EC:EMC 3:7: 47 Li⁺, 47 PF₆⁻,
    168 EC and 332 EMC, i.e. 7036 atoms, exactly as in SI Table S1.
  - It is packed by Packmol in about 20 s and validated by the spec's reference validator.
  - The engine's reader accepts it.
- **Force-field sources are plug-ins** (ADR 0008).
  - The built-in `library` and `gromacs-top` register through the same entry points that a
    third-party package uses; a test installs such a package without touching the builder.
  - A source test kit checks every source.
- **The parameters are independently validated.** The builder's EC and EMC packages equal
  OpenMM's reading of the original LigParGen topologies, term by term, to 1.5×10⁻¹² relative
  ([REPORT](https://github.com/mines-of-morja/ucmd-builder/blob/b1/validation/b1-openmm/REPORT.md)).
- **Gate criterion met:** "recipe → valid package → OpenMM runs it". OpenMM runs the full box
  with PME at 1.4 nm, with finite energies and forces.
- **State:** 83 tests in about 25 s; ruff clean; CI green on Python 3.12 and 3.13, with spec
  fixtures and Packmol required.

## 2. Acceptance criteria and evidence

| Task | Criterion | Evidence |
|---|---|---|
| B1.1 | minimal recipe → valid package; recipe round trip | `test_build.py` (argon, electrolyte), `test_recipe_composition.py` (strict parsing, round trip, error messages) |
| B1.2 | round trips; EC, EMC, PF₆⁻ graphs correct | `test_molecule.py`: SMILES/MOL/PDB/XYZ; angle, dihedral and 1-4 counts checked against hand counts and LigParGen's lists (EC: 17, 19, 14) |
| B1.3 | test kit per source; source tables reproduced; `library` = `gromacs-top` | `test_sources.py`: every template passes the kit; LigParGen, JJ06, CL&P, SPC/Fw and argon values checked; GROMACS import equals the library for EC, EMC, PF₆⁻ and Li⁺; plug-in and duplicate-name tests; refusals for what spec v0.1 cannot express |
| B1.4 | Lehnert Table S1; round trips | 3:7 w:w with 500 (1000) solvent molecules gives 168/332 (336/664); at the placeholder density, 47 ion pairs = 0.998 M; molality and volume-fraction paths |
| B1.5 | deterministic; minimum distance across PBC; whole molecules | `test_packing.py`: Packmol and insertion, the same seed giving the same bytes; cell list = brute force; timeout and failure paths |
| B1.8 | byte-identical rebuild | `test_the_same_recipe_gives_a_byte_identical_package` |
| Gate | recipe → valid package → OpenMM runs it | `validation/b1-openmm/REPORT.md` |

## 3. Deviations from the design (to review)

1. **The geometry travels with the parameters** (design §4.4). Instead of requiring template
   parameters to be invariant under graph automorphisms, every template carries its reference
   geometry and is mapped together with it.
   - The PF₆⁻ angles are geometry-dependent: only the 12 cis angles have a term, and a
     topology-only automorphism check would reject them.
   - With the geometry attached, any graph match is correct.
   - The source's geometry is used for packing; the input's geometry only when a source has
     none.
2. **Atom-type names** carry their molecule type (`EC.opls_800`), because LigParGen numbers
   types per molecule (ADR 0009).
3. **Converted values are rounded to 12 significant digits**, e.g. so that 3100 kJ mol⁻¹ Å⁻²
   becomes exactly 310000 kJ mol⁻¹ nm⁻². The relative change is at most 5×10⁻¹³.
4. **The Packmol distance check accepts 90 % of the tolerance** (Packmol converges to a
   residual); the measured minimum is recorded. In practice the minimum was 0.220 nm for a
   0.2 nm tolerance.
5. **Not done in B1a:** unparameterized packages (`source = "none"`, for ML/QM). They need an
   element-mass table and come with E3.
6. **Pulled forward from B1b:** the extended-XYZ export (`ucmd-build xyz`), so that built boxes
   can be viewed before the GUI exists.
7. **Element recognition in `gromacs-top`:** for files without atomic numbers, the element
   comes from the mass, using a short table of standard atomic weights for recognition only.
   A wrong guess cannot pass, because the graph match then fails.

## 4. Found, and needing the author

1. **A bug in the spec validator.** As a normal (non-editable) install, `ucmd-spec` 0.1.0
   cannot find its JSON Schemas: it looks for them next to its source in a checkout.
   - **Workaround in place:** the builder points it at `spec/` via `UCMD_SPEC_DIR`, falling
     back to the workspace's `../spec`; CI does the same.
   - **Proposed fix:** ship the schemas in the validator wheel and look them up as package data
     first; release it as validator 0.1.1. The spec itself stays 0.1.0.
   - This changes files under `spec/` after the tag, so it needs your approval (CLAUDE.md).
2. **Densities:** Landesfeind 2019 gives its density fit only in the SI (Table S1, Eq. S1),
   which is not in `../Lit`. Please add it. Until then recipes use the placeholder
   1.2 g/cm³, and every package built with it says so in its provenance.
3. **Gate E1** is still open, pending your hands-on tests ([testing.md](../testing.md) §1–6).

## 5. Next

- **E2 design** (engine molecular force field), then E2 core:
  - bonded terms, exclusions and 1-4 pairs, Ewald/PME, Nosé–Hoover, FIRE minimizer;
  - the oracle v1 and these packages are ready as references.
- **M2a** after that, then the frontend preview **B2a**.
