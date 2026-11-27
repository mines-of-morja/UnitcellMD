# Second reading of the Landesfeind 2019 density fit (task SC-8)

- **Label:** literature reading, 2026-11-25, from the authors' SI (Word file supplied by the author as
  `../Lit/Landesfeind_2009_sup.docx`, sha256 `783c1829…d89e`; the title and the file's dates show it is the 2019 SI;
  renamed 2026-11-27 to `../Lit/Landesfeind_2019_J._Electrochem._Soc._166_A3079_SI.docx`, same file).
- **Script:** `digitize_fig_s1.py` (Figure S1 pixels against Eq. S1; the figure is not in this repo).

## Reading

| EC:EMC 3:7 w:w, ρ = p₁ + p₂c + p₃T (g/cm³, mol/L, K) | ledger (first reading) | SI Table S1 | refit of the 16 points of Fig. S1 |
|---|---|---|---|
| p₁ (95 % bound 5 %) | 1.41 | 1.41E+00 | 1.414 ± 0.033 (SE) |
| p₂ (3 %) | 0.0912 | 9.12E-02 | 0.0900 ± 0.0013 |
| p₃ (22 %) | −0.00109 | −1.09E-03 | −0.00109 ± 0.00011 |
| R² | 0.997 | 0.997 | 0.9972 |

**The two readings agree.** The figure reproduces the fit and its R², so the table is not misprinted. Method:
gravimetric, 10 ml flask, in a glovebox.

## What it adds

1. **The reference is known to about ±0.6 %, not better.** Two-decimal rounding of p₁ alone is ±0.005 g/cm³
   (worst case of all three ±0.0065). The points scatter around the plane by 0.0066 g/cm³ (SD). At 1 M, 20 °C the
   printed fit gives 1.1817 and the refit of the figure 1.185 ± 0.002 (plus about ±0.003 from reading the axes);
   the three points at 1 M lie 0.002–0.009 above the printed fit.
2. **Consequence:** M0 (1.184, +0.2 %) and M1 (1.195, +1.1 %) are both inside twice that scatter. This density
   cannot separate M0 from M1, and a 1.5 % criterion is about 2.5 SD of the reference.
3. **Range.** The SI text says 0–50 °C and 0.1–3 M. The markers in Fig. S1 sit at **10–50 °C** and
   **0, 1, 2, 3 M** (x residuals below 2 px; 0.1 M would be 17 px, 10 °C is 24 px). The pure-solvent markers
   (1.087 at 25 °C) agree with ideal mixing of EC and EMC (1.0875, our estimate with EC extrapolated from 39 °C). So a
   comparison at 0 °C rests on the fit's extrapolation, whatever the caption says.

Uncertain: marker positions ±1 px (±0.002 g/cm³), five markers are partly covered by others, and the axis ticks
were read by hand.
