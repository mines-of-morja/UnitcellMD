# 0008 — Force-field parameters and forces come from pluggable sources

- **Status:** accepted 2026-11-12 by the author at Gate 0 (§5.2).
  - The author asked for "a modular design that enables plugging in different sources to obtain
    gradients", an open-source working horse, and an own force field if nothing good can be
    found: "keep an open approach and we can plug in stuff into that pipe".
  - The concrete working-horse parameter set is a separate decision, proposed in the B1 design.
- **Context:**
  - The benchmark's parameters are not open. Lehnert 2025 took the solvent parameters from
    Schrödinger Maestro, and Ringsby et al. 2021 (J. Electrochem. Soc. 168, 080501, ref. 39)
    used MacroModel/Maestro as well. Both are commercial.
  - New parameter generators and force models appear quickly: graph-network parameterizers,
    differentiable fitting of OPLS to experiment, hybrid physics/neural force fields, ML
    potentials. Hard-wiring one force field would age fast.
  - The spec is already force-field-agnostic. Spec v0.1 packages carry:
    - explicit per-interaction bonded parameters in four functional forms;
    - per-type LJ parameters;
    - one combination rule (`geometric` or `lorentz-berthelot`) and one pair of 1-4 scale
      factors per package;
    - a provenance list of sources.
- **Decision:**
  1. **There are two pipes; both are pluggable, and they meet only at spec'd data.**
     - **Parameter sources** (builder, PLAN.md B1.3):
       - A source turns a molecule into classical force-field parameters.
       - Input: the molecule graph in canonical atom order, plus formal charge and optional
         coordinates.
       - Output: explicit parameters in spec units, the force-field conventions (combination
         rule, 1-4 scales) and citations.
       - Sources register by name through the Python entry-point group
         `ucmd_builder.forcefield_sources`. A new generator is an installable plug-in, not a
         change to the builder.
     - **Force (gradient) sources** (engine): unchanged (D7, ADR 0007).
       - In-process Rust providers compute the classical terms.
       - The i-PI socket serves everything else: ML potentials, quantum chemistry, OpenMM as a
         provider.
       - `run.toml` chooses the source; the engine never learns which parameter source built the
         package.
  2. **Provenance:** every source records its name, version, options and citations in the
     package's `provenance.sources`.
  3. **One convention set per package:** a package uses one combination rule and one pair of 1-4
     scales, as the spec requires. The builder refuses to combine sources whose conventions
     differ. Per-pair overrides would need a spec extension.
  4. **Transforms are separate steps after parameterization**, recorded in provenance. This
     covers the ion charge scaling ζ, for example. No source applies them silently.
  5. **Built-in sources in B1:**
     - `library`: curated parameter sets stored as data files with a citation per set,
       assigned to molecules by graph isomorphism.
     - `gromacs-top`: an importer for GROMACS `.top`/`.itp` files, the most widely shared
       topology format. LigParGen, for example, writes it.
     - Further sources are separate optional plug-ins, each with its own dependencies. Examples:
       OpenFF, GAFF2, graph-network generators, our own fitted force field.
  6. **The working horse is chosen on evidence:** density, structure and transport compared
     with experiment and with Lehnert 2025. It gets its own ADR. If no open parameter set is
     good enough, we fit our own; that is just one more source.
  7. **Physics that the spec cannot express goes through the force pipe** until a spec
     extension and an engine provider exist. Examples: polarization (Drude particles, induced
     dipoles), pair-specific overrides, neural corrections. Such force fields run as external
     providers, e.g. OpenMM through the bridge.
- **Consequences:**
  - PLAN.md B1.3 becomes "Force-field sources". The spec needs no change now.
  - Heavy toolchains stay out of the builder's core dependencies (CLAUDE.md: ask before heavy
    dependencies). They live in plug-in packages, or their output is imported as GROMACS files.
    Examples: AmberTools, or OpenFF's charge models from conda-forge.
  - A sensitivity study on the same system with two force fields is a recipe change.
  - Mixing force-field families inside one package (e.g. OpenFF solvent with OPLS ions) is not
    possible until the spec supports per-pair overrides.

## Landscape, 2026-11 (orientation, not a decision)

| Source | Openness (checked 2026-11-12) | Remarks |
|---|---|---|
| Schrödinger OPLS (Lehnert 2025, Ringsby 2021) | commercial | the benchmark's parameterization; not available to us |
| OPLS-AA with 1.14·CM1A-LBCC charges from **LigParGen** | free web server; the generator (BOSS) is "free for academic use", not open source; no stated terms for the output files | same family as the benchmark. Writes GROMACS, OpenMM, LAMMPS and other formats. Cite Dodda et al. 2017 (Nucleic Acids Res.; J. Phys. Chem. B) |
| Li⁺ Jensen & Jorgensen 2006; PF₆⁻ CL&P (Canongia Lopes & Pádua 2004) | published; the CL&P database (`paduagroup/clandp`) is MIT-licensed | the ion parameters Lehnert used |
| **OpenFF** (Sage) | `openff-toolkit` 0.18 and `openff-interchange` 0.5 are on PyPI (MIT). The charge models (AmberTools AM1-BCC, NAGL) and the force-field files need conda-forge | fully open pipeline. Lorentz–Berthelot mixing, AMBER-style 1-4 scaling |
| GAFF2 + AM1-BCC | AmberTools, conda-forge | widely used for organic liquids |
| ByteFF / ByteFF-Pol (ByteDance) | code Apache-2.0; ByteFF-Pol weights CC BY-NC 4.0; needs a patched OpenMM 8.3.1 | graph-network parameters; ByteFF-Pol is polarizable, so it goes through the force pipe |
| Grappa | `grappa-ff` on PyPI, GPL | graph-network bonded parameters |
| Differentiable OPLS fitting (DMFF) | method paper: Huang et al., arXiv 2607.04633 (2026) | LJ fitted to experimental densities for >10,000 electrolyte formulations; a route to our own force field |
| ML potentials (e.g. BAMBOO for carbonate electrolytes) | various | force pipe (PLAN.md E3.6) |
