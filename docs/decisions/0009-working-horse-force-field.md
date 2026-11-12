# 0009 — Working-horse force field for carbonate electrolytes: OPLS-AA from open sources

- **Status:** accepted 2026-11-12 by the author ("That sounds good. Lets go with it."), on the
  proposal in docs/design/B1.md §5.
- **Context:**
  - Lehnert 2025 used OPLS with solvent parameters from commercial Schrödinger software.
  - ADR 0008 asks for an open working horse, chosen on evidence.
  - The family should stay the benchmark's, so that deviations can be attributed.
- **Decision:** the library set `opls-aa-carbonates` uses OPLS-AA conventions throughout:
  geometric combination rule, 1-4 scales 0.5/0.5, harmonic bonds and angles with the ½k form,
  and Ryckaert–Bellemans or periodic dihedrals. Its sources:

| Species | Parameters | Source, as obtained |
|---|---|---|
| EC, EMC | OPLS-AA types, LJ, bonded terms; 1.14·CM1A-LBCC charges | LigParGen 3.0.1 (BOSS 5.1, RDKit 2023.03.3), run 2026-11-12 from the SMILES `O=C1OCCO1` and `CCOC(=O)OC`, net charge 0, no optimization rounds. Cite Dodda et al., Nucleic Acids Res. 45, W331 (2017); Dodda et al., J. Phys. Chem. B 121, 3864 (2017); Jorgensen & Tirado-Rives, J. Comput. Chem. 26, 1689 (2005) |
| Li⁺ | σ = 0.287 nm, ε = 0.002092 kJ/mol (2.87 Å, 0.0005 kcal/mol), q = +1, m = 6.941 | Jensen & Jorgensen, J. Chem. Theory Comput. 2, 1499 (2006), as in Lehnert. The values were confirmed by two independent copies: BOSS 5.1 via LigParGen (`opls_406`) and mdgo's `ion_lj_params.json` (`jensen_jorgensen`, TIP4P) |
| PF₆⁻ | P: q +1.34, σ 3.74 Å, ε 0.83680 kJ/mol; F: q −0.39, σ 3.12 Å, ε 0.25520 kJ/mol; P–F 1.606 Å, k 3100 kJ mol⁻¹ Å⁻²; F–P–F 90.0°, k 1165 kJ mol⁻¹ rad⁻² (½k forms) | CL&P database `il.ff`, version 2026/10/09 (github.com/paduagroup/clandp, MIT). The file cites Kaminski & Jorgensen, J. Chem. Soc., Perkin Trans. 2 (1999) 2365; the Lehnert SI cites CL&P |
| ζ | 0.75 for Li⁺ and PF₆⁻ in EC:EMC | Lehnert 2025 SI, Table S3; applied as a recorded transform (ADR 0008 §4) |

- **Details:**
  - **PF₆⁻ trans angles.** CL&P's tool `fftool` generates all 15 F–P–F angles. It then removes
    those more than 15° from the force-field value, i.e. the three trans angles at 180°. The
    template therefore has 6 bonds and the 12 cis angles at 90°, and no dihedrals.
  - **Atom-type names.** LigParGen numbers its types (`opls_800 …`) per molecule, so the names
    collide between EC and EMC. The builder prefixes every atom type with its molecule-type
    name (`EC.opls_800`).
  - **Symmetry.** LigParGen charges of symmetry-equivalent atoms differ in the sixth decimal
    (e.g. 0.133872 vs 0.133874 e). The template check over automorphisms therefore uses
    10⁻⁴ e for charges; LJ and bonded values must match exactly.
  - **No third-party files are committed.** The values are transcribed into the library format
    with these citations (CLAUDE.md: no files with third-party headers).
- **Evidence before this set becomes the default** (proposed in B1 §5, accepted with it):
  - pure EC (313 K) and EMC (298 K) densities within 2 % of experiment;
  - 1 M LiPF₆ in EC:EMC 3:7 at 293 K within 2 % of Landesfeind 2019;
  - Li⁺ first-shell structure reported against Lehnert and the literature.

  These run in E2.9. If the set fails, OpenFF Sage and our own refit are next (ADR 0008).
- **Consequences:**
  - The deviation from Lehnert is confined to the solvent parameters: Maestro OPLS_2005
    versus OPLS-AA with 1.14·CM1A-LBCC charges.
  - Densities: Landesfeind 2019 gives them only in its SI (Table S1, Eq. S1), which is not yet
    in `../Lit`. Until it is, recipes and tests use explicitly marked placeholder densities.
