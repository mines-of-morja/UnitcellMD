# SC-6: proposed corrections (for approval; nothing below is changed yet)

**Finding.** 1.202 g/cm³ (1.205 in older notes) is 56 497 g/mol per 47 ion pairs at *exactly* 1.0 M. It is neither
measured nor a density that Lehnert's SI reports: the SI says the counts were the most consistent with the target,
and one ion pair of 47 is 2 % in c. Our NPT densities at 20 °C are 1.184 (M0) and 1.195 (M1), +0.2 % and +1.1 %
against the Landesfeind fit (1.1817, one reading).

| place | now | proposal |
|---|---|---|
| `trials/T3-density-protocol.md` | "boxes 2.2 % denser (1.202 against 1.176 at 25 °C)" | dated amendment: the number compared is the start box, not the NPT density; the defect to test is +1.1 % (M1). Plan and decision rule unchanged |
| `STATUS.md`, waiting item 2 | "our boxes 1.202" | "our NPT boxes 1.184 (M0), 1.195 (M1) at 20 °C" |
| `report/report.md` abstract, §3.3, §4 | "1.4 % below Lehnert's model" | correction note: the reference is a nominal density with ±1–2 % of its own |
| `report/report.md` §3.2 | deviations from Table S2 | table of `research/solvent-densities/README.md`; DMC no longer passes |
| `reproduction-plan.md` §2, §4a; `calculation-plan.md` A1, A2; `forcefield-strategy.md:19,24` | as above | one correction line each, old text kept |
| `design/A1.5.md:70,130,161` | 1.205 | note: nominal; t₊ effect below 0.003 as stated there |
| `summary/literature.json` `lehnert2025_box_density` | "density of Lehnert's box" | quantity reworded to "nominal, 47 pairs at exactly 1.0 M" |
| `forcefield-strategy.md` §8 (DRS) | c(EC) from 1.202 | c(EC) changes by −1.7 %; "≈ 2.2 EC per Li⁺" stays within its ± 0.1. T2's verdict is unaffected |

Old numbers stay on record (publication.md, rule 5).
