# 1 M EC:EMC, NPT at 1 atm and 20 °C, tail correction on (GPU), 2026-11-17

- **Question:** at Lehnert's density (1.205 g/cm³) the electrolyte was still at about +390 bar
  after 100 ps (tail correction included), while pure EMC is 2.8 % too dense. Which density does
  the electrolyte reach once the Li⁺ solvation shells have formed, and how long does that take?
- **System:** Lehnert's 1 M box (47 Li, 47 PF₆, 168 EC, 332 EMC; ζ = 0.75), packed at 1.205
  g/cm³ and minimized.
- **Run:** 3000 ps NPT on the GPU backend (machine-gpu profile; precision from ADR 0012's check). A trajectory frame every 5 ps, for the
  time evolution of the Li⁺ solvation (`ucmd-analyze rdf`).
- **Twin study:** `2026-11-17_electrolyte-npt-cpu`, the same protocol on the other backend.
  Together they give the statistical comparison of ADR 0010.
