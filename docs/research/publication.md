# Working toward a publication

The author wants the research to lead to a publication (2026-11-21), not now, but with decisions
made so that the work done now can be used. This file holds the rules that follow from that and
the questions only the author can answer. The physics plan stays in
[forcefield-strategy.md](forcefield-strategy.md); its principles (§2: fit and test sets fixed in
advance, no tuning to the answer, pass criteria set before the runs) are the core of it and are not
repeated here.

## Rules from now on (agent's remit)

1. **Exploration and evidence are separate.** Everything run so far is exploration: one Li⁺ per
   box, 5 ns, bridge feature branches, a CPU and GPU shared with other work. A number goes into a
   paper only from a **production set**, which needs:
   - its question, design, analysis and pass criterion written in the study README before the
     first run (the replica study, `studies/2026-11-21_li-preference-replicas`, is the model);
   - tagged releases of engine, bridge and builder, and container images pinned by digest;
   - each study README labelled `exploration` or `production`.
2. **Error bars from independent starts.** Uncertainties come from the spread over independently
   packed and seeded replicas, at least 4 per model, not from blocks of one trajectory. Within-run
   numbers may be shown, but only next to the replica spread.
3. **Every literature number has a ledger entry.** For each number quoted from a paper: the value,
   the table or page, the version read (version of record, accepted manuscript, preprint), and
   whether it was checked against the version of record. Before submission every entry must be
   checked. Open items now: Olguin 2016 Table 1 was read from the OSTI manuscript; the DRS values
   (Self 2024) from the CC BY version of record.
4. **New reference calculations reproduce a published number first.** Any new QM or MD method
   reproduces a published value at the same level before it produces a value that has none. This
   caught a real error on 2026-11-21: Psi4's frozen-core rule correlates bare Li⁺ while the Li 1s
   in the complex stays frozen, which made every MP2/aug-cc-pVTZ binding energy 6.9 kcal/mol too
   weak (tools/qm/README.md).
5. **Errors and negative results stay on record.** A failed model or a corrected bug goes in the
   study README or the tool README with numbers, not only in a commit message. Reviewers ask for
   them, and they belong in the SI.
6. **Figures and tables come from scripts** that read the study data (as
   `docs/research/report/figures.py` does), never from numbers typed by hand.
7. **Data stays reproducible but small in git.** Plans, recipes, analysis JSON and figure scripts
   are in git. Trajectories stay local and are archived with a DOI only for the production set
   (see the questions below).

## Questions for the author (not urgent; before the production set)

1. **Scope.** One science paper, a software paper (e.g. JOSS) for UnitcellMD, or both? The
   candidate science result so far is the Li⁺ shell composition in EC:EMC: what the fixed-charge
   models get wrong, why (gas-phase QM), and whether a model chosen without fitting to transport
   matches the DRS estimate and κ(c,T).
2. **Lehnert's group.** When to contact them, and whether as co-authors or as an independent
   comparison. This decides how far we reproduce their model before diverging from it.
3. **Data archive.** Zenodo (or the university repository), and the licence for data (CC BY 4.0
   suggested; all four repos are Apache-2.0).
4. **Authorship and AI disclosure.** Journals require a statement on the use of AI tools. Commit
   trailers record which work was done with Claude; the author decides how to describe it.
5. **Target journal**, which fixes the SI format and the data-availability rules.
