# Measured liquid densities of the solvents (task SC-5)

- **Label:** literature collection, 2026-11-25. Values from NIST ThermoML files, extracted by `parse_thermoml.py`
  (`python3 -I parse_thermoml.py FILE.xml …`). **None of the papers was read**, so every ledger entry
  (`density_*` in `../summary/literature.json`) has `checked_vor = false`.

## What Lehnert's Table S2 refers to

| solvent | Table S2 | measured | reading |
|---|---|---|---|
| DMC | 1.069 | 1.0698–1.0699 at 20 °C (4 sources); 1.0632–1.0633 at 25 °C (3 values, two from one group) | 20 °C |
| PC | 1.204 | 1.2047 at 20 °C (Comelli); 1.2034 ± 0.0018 (pycnometer) | 20 °C |
| EMC | 1.006 | 1.00688 at 25 °C (one source) | 25 °C |
| MP | 0.915 | 0.91028 at 25 °C; slope −1.28 kg/m³/K to 45 °C gives about 0.917 at 20 °C | nearer 20 °C |
| EC | 1.321 | 1.3214 at 39 °C (DIPPR, Caleman SI); 1.3157 at 45 °C | 39 °C |

So the table **mixes temperatures**. A comparison of one column with 25 °C and 40 °C runs is not like for like.

## The LigParGen runs at the measured temperature (report §3.2 densities)

| solvent | 25 °C: measured, deviation | 40 °C: measured, deviation | report §3.2 (Table S2) |
|---|---|---|---|
| EC | supercooled, none | 1.3204 ᵃ, **−3.4 %** | −3.5 % |
| PC | 1.1993 ᵇ, −0.2 % | 1.1831, −0.2 % | −0.6 %, −2.0 % |
| DMC | 1.0633, **+2.3 %** | 1.0433, **+2.6 %** | +1.7 %, +0.2 % |
| EMC | 1.0069, **+2.8 %** | not found | +2.9 %, +1.2 % |
| MP | 0.9103, +1.6 % | 0.8910 ᵇ, +1.6 % | +1.1 %, −1.1 % |

ᵃ between 39 °C (DIPPR) and 45 °C. ᵇ linear between the two measured temperatures.

- **DMC fails the ±2 % criterion at both temperatures** (the report has it passing). EMC and EC fail, PC and MP pass.
- The three open-chain solvents are 1.6–2.8 % too dense, PC is right, EC (M0) is too light. The thermal
  expansion of DMC, PC and MP is right to a few tenths of a percent over 15 K.
- M1's EC (1.3192 at 39 °C) is −0.2 % against 1.3214.

## Gaps

- **EMC against temperature:** one value, 298.15 K. The same paper's DMC (1060.87) is 0.23 % below the other
  25 °C values, so EMC may carry an error of that size. A pycnometer value (1010 ± 100 kg/m³) is useless.
- **ΔH_vap of EMC:** no measurement found. NIST WebBook has no entry; Cheméo's values are calculated or a
  ChemSep correlation; a search excerpt quotes 36.1 kJ/mol from a source not seen.
- **ΔH_vap, others** (NIST WebBook table, 298 K, primary papers not read, so not in the ledger): DMC 38.0 ± 0.2
  (Kozlova 2008, doi 10.1016/j.jct.2008.02.012) and 37.7 ± 0.2 (Steele 1997) kJ/mol; MP 35.95 (Majer and
  Svoboda 1985), 35.82 ± 0.09 (Sunner 1979). EC and PC: WebBook averages of 6 scattered values (80 ± 80, 60 ± 30), unusable.
- Not reachable: ACS, ScienceDirect and Semantic Scholar pages (HTTP 403). NIST/TRC Web Thermo Tables list EMC density
  and ΔH_vap from 218 K on but need an interactive session.
