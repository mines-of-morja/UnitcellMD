# EMC: enthalpy of vaporization, density over T, viscosity (search of 2026-11-27, for SC-7)

- **Label:** literature search by an agent of session unitcellmd-c8, 2026-11-27. **Nothing here is checked against the version of
  record** (publication.md rule 3), and nothing is in the ledger yet. Each line says how the value was read.

## Enthalpy of vaporization and vapour pressure

- **No directly measured Δ_vap H of EMC was found.**
- **Dougassa, Jacquemin, El Ouatani, Tessier, Anouti, J. Chem. Thermodyn. 79, 49 (2014), doi 10.1016/j.jct.2014.07.004:** vapour
  pressure of pure EMC, static method, 13 points from 277.96 to 333.15 K, e.g. 3.658 kPa at 298.15 K.
  - *Read from the NIST ThermoML file of the paper, not the paper.* No uncertainty; table number unknown.
  - The agent's own Clausius–Clapeyron fit gives about 40.7 kJ/mol near 302 K. That is not a published value, and its script
    is not in this repo. Redo it with a committed script before any use.
  - The points scatter (ln p residuals up to ±0.07).
- **Franke, J. Electrochem. Soc. 172, 070520 (2025), doi 10.1149/1945-7111/adee4e:** Table II, Δ_vap H = 40.7 kJ/mol at
  298.15 K, "calculated in this work" from fitted vapour pressures. No uncertainty.
  - *Read from a summary of the HTML full text, not the PDF.*
  - It may rest on the same vapour-pressure data as above, so it is not an independent check.
- **Only from excerpts, not verified:** Goldberg, Herdegen, Braeuer, J. Chem. Eng. Data 2026 (vapour pressures, possibly from a
  binary data file); ECHA dossier, 43 hPa at 25 °C.
- **Calculated, not usable as a target:** Cheméo 43.08 kJ/mol (ChemSep).

## Density of pure EMC against temperature

Not found beyond the 25 °C values already known. Not searched: NIST/TRC Web Thermo Tables (need a login), ScienceDirect and ACS
full text.

## Viscosity (Logan et al., J. Electrochem. Soc. 165, A21 (2018), doi 10.1149/2.0271802jes, open access; read in the PDF)

- **Pure EMC:** 0.65 cP at 25 °C (Table I), a value Logan quote from Barthel & Gores, not their own measurement.
- **EC:EMC 30:70 w:w with LiPF₆, molal (mol/kg),** Ostwald viscometer, ±2 %:

  | | 10 °C | 20 °C | 30 °C | 40 °C |
  |---|---|---|---|---|
  | 0 m | 1.30 cP | 1.11 cP | 0.97 cP | 0.87 cP |
  | 1.0 m | 3.88 cP | 3.05 cP | 2.47 cP | 2.06 cP |

  Tables II–V. 1.0 m is not 1 M; converting needs the solution density. These are the T4 reference values the plan names.

## What it means for SC-7

A density-and-Δ_vap H refit of EMC would rest on one vapour-pressure set, read from ThermoML. Before SC-7: read Dougassa 2014
itself, find a second, independent source if one exists, and commit the Δ_vap H derivation as a script.
