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

## Decisions (author, 2026-11-21)

1. **Rules 4 and 5 matter most:** reproduce a published number first, and keep errors on record.
2. **Scope: a software paper** in a journal close to MD, electrochemistry or a related field, not a
   pure science paper as the first publication. The electrolyte work (LiPF₆ in EC:EMC) is its
   application and validation case.
3. **Before contacting Lehnert's group**, a first PDF summarizing our results, which the author
   will send with an email. It is written once there is something to present.
4. **Code and data are published in the GitHub organization `mines-of-morja`.** A DOI archive
   (e.g. Zenodo, which can mint one per GitHub release) is still open.
5. **AI disclosure: open.** Claude Code wrote the code, and helped validate results and develop
   ideas. The results themselves come from computation: MD with cited force fields and quantum
   chemistry with Psi4. Draft wording for the paper:

   > The UnitcellMD software was written by Claude Code (Anthropic), an AI coding agent, under the
   > direction of the author, who set the requirements, reviewed the work and approved every
   > physical parameter and acceptance criterion. Claude Code was also used to plan and run
   > validation and to propose research directions. All numerical results were produced by the
   > computations described here (molecular dynamics with published force fields and quantum
   > chemistry with Psi4), from inputs, scripts and outputs that are public at
   > github.com/mines-of-morja. No number was written or changed by a language model.

   The last sentence holds only while rule 6 holds (figures and tables from scripts), so rule 6
   is now part of the disclosure.

6. **Target journal: J. Chem. Inf. Model. (JCIM), as an Application Note** (chosen by the agent at
   the author's request). Why: reviewers there judge software and validation, not a new
   electrochemical finding; MD software is a standard topic; no fee unless open access is chosen.
   Requirements from the ACS author guidelines (checked 2026-11-21, last updated 2026-11-09):
   - at most 4000 words including abstract and captions, excluding references; at least one
     figure;
   - the software must be available to reviewers and at publication, or the manuscript is
     returned without review;
   - a standalone package must show **at least six months of active development in an open
     repository** before submission, plus community uptake metrics such as downloads. Our repos
     start on 2026-11-11, so **the earliest submission is 2027-05-11**. Uptake has to be built
     up until then: releases, documentation, and people other than the author running it (e.g.
     the JMU contact).
   - Fallback without the six-month rule: Digital Discovery (RSC; open access, a data reviewer
     reproduces the results).

## Still open

1. **Lehnert's group:** co-authors or an independent comparison. This follows from their reply to
   the summary PDF.
2. **DOI archive and data licence** (CC BY 4.0 suggested; all four repos are Apache-2.0).
