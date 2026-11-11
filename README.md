# UnitcellMD

A modular molecular-dynamics ecosystem for large periodic systems. The first target is Li-ion
battery electrolytes such as LiPF₆ in EC:EMC.

**The core idea: the engine owns the dynamics, force providers own the physics.** The
integrator never knows whether forces come from an analytic force field, a machine-learned
potential, a quantum-chemistry program or QM/MM. A separate builder prepares the systems, and
a separate analysis package interprets the trajectories. The parts talk to each other only
through documented file formats and protocols.

| Repository | Language | Role |
|---|---|---|
| **UnitcellMD** (this repo) | docs, JSON Schema | plan, shared spec (formats, units, provider contract), fixtures, validation tools |
| [ucmd-engine](https://github.com/mines-of-morja/ucmd-engine) | Rust | MD engine `ucmd`: integrators, thermostats, barostats, force providers, I/O |
| [ucmd-builder](https://github.com/mines-of-morja/ucmd-builder) | Python | system preparation: molecules, packing, crystals, force-field templates, GUI |
| [ucmd-analysis](https://github.com/mines-of-morja/ucmd-analysis) | Python | RDF, diffusion, Onsager coefficients, conductivity, transference numbers |

The same input files scale from one local command (classical forces, no scheduler, no external
programs) to cluster campaigns with external QM or ML force providers (see
[ADR 0002](docs/decisions/0002-local-first-execution.md)).

## Status

Phase 0 (foundations). [PLAN.md](PLAN.md) has the roadmap with acceptance criteria;
[docs/STATUS.md](docs/STATUS.md) has the progress.

## Workspace layout

The component repositories are cloned *inside* this one; they are gitignored here:

```sh
git clone https://github.com/mines-of-morja/UnitcellMD.git
cd UnitcellMD
git clone https://github.com/mines-of-morja/ucmd-engine.git
git clone https://github.com/mines-of-morja/ucmd-builder.git
git clone https://github.com/mines-of-morja/ucmd-analysis.git
```

## Background

UnitcellMD grows out of NeNePo_builder, an on-the-fly Ag₄ dynamics code for NeNePo pump–probe
spectroscopy; see [docs/nenepo-audit.md](docs/nenepo-audit.md). Development is agent-assisted:
[CLAUDE.md](CLAUDE.md) holds the rules that coding agents follow in this workspace.

## License

Apache-2.0; see [LICENSE](LICENSE) and [NOTICE](NOTICE).
