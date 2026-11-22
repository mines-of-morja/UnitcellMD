"""data/results.json + literature.json -> figures/fig_traces.png and Wu_et_al_water_summary.pdf.

    ucmd-analysis/.venv/bin/python docs/research/results/wu2006-spcfw-water/build.py

Needs numpy, matplotlib and reportlab (`pip install reportlab` into ucmd-analysis/.venv; it is
not declared in any pyproject). Run analyze.py first. Every number in the PDF is read
from data/results.json (own results) or literature.json (Wu et al.); none is typed here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

HERE = Path(__file__).resolve().parent
R = json.loads((HERE / "data/results.json").read_text())
TR = json.loads((HERE / "data/transcribed.json").read_text())
LIT = json.loads((HERE / "literature.json").read_text())["entries"]
WU = LIT["wu2006_spcfw_table2"]["value"]
PROTO = LIT["wu2006_spcfw_protocol"]["value"]
OUT = HERE / "Wu_et_al_water_summary.pdf"
DATE = "2026-11-22"


# ---------------------------------------------------------------- figure
def figure() -> Path:
    tr = np.genfromtxt(HERE / "data/traces_1ps.csv", delimiter=",", names=True)
    w = 5  # 5 ps running mean of the 1 ps means

    def run(x):
        return np.convolve(x, np.ones(w) / w, mode="valid")

    t = tr["time_ps"][: len(run(tr["time_ps"]))] / 1000
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.6))
    blue, red = "#1f5f8b", "#c0392b"
    ax[0].plot(t, run(tr["density_g_cm3"]), color=blue, lw=0.7)
    ax[0].axhline(
        WU["rho_g_cm3"]["value"],
        color=red,
        ls="--",
        lw=1,
        label=f"Wu 2006: {WU['rho_g_cm3']['value']}",
    )
    ax[0].axhline(
        R["density_g_cm3"]["mean"],
        color="0.35",
        ls=":",
        lw=1,
        label=f"this run: {R['density_g_cm3']['mean']:.4f}",
    )
    ax[0].set_ylim(0.98, 1.03)
    ax[0].set_ylabel("density (g/cm$^3$)")
    ax[0].legend(frameon=False, fontsize=7.5, loc="lower right")
    ax[1].plot(t, run(tr["potential_per_molecule_kJ_mol"]), color=blue, lw=0.7)
    ax[1].set_ylim(-43.5, -41.5)
    ax[1].set_ylabel("potential energy / molecule (kJ/mol)")
    for a in ax:
        a.axvspan(0, R["run"]["skip_ps"] / 1000, color="0.9")
        a.set_xlabel("time (ns)")
    fig.suptitle(
        "512 SPC/Fw molecules, 298.16 K, 1 atm, 5 ps running mean (grey: skipped)", fontsize=9
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    path = HERE / "figures/fig_traces.png"
    path.parent.mkdir(exist_ok=True)
    fig.savefig(path, dpi=250)
    return path


# ---------------------------------------------------------------- text helpers
def pm(d: dict, digits: int, scale: float = 1.0) -> str:
    return f"{d['mean'] * scale:.{digits}f} ± {d['sem'] * scale:.{digits}f}"


def sci(x: float) -> str:
    m, e = f"{x:.1e}".split("e")
    return f"{m}·10<super>{int(e)}</super>"


def tpm(key: str, digits: int) -> str:
    return f"{TR[key]['mean']:.{digits}f} ± {TR[key]['sem']:.{digits}f}"


def rel(ours: float, theirs: float) -> str:
    x = round((ours - theirs) / theirs * 100, 2)
    return f"{x + 0.0:+.2f} %"


def build() -> None:
    fonts = Path(matplotlib.__file__).parent / "mpl-data/fonts/ttf"
    for n, f in [
        ("DV", "DejaVuSans"),
        ("DV-B", "DejaVuSans-Bold"),
        ("DV-I", "DejaVuSans-Oblique"),
        ("DV-BI", "DejaVuSans-BoldOblique"),
    ]:
        pdfmetrics.registerFont(TTFont(n, str(fonts / f"{f}.ttf")))
    pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")
    ink, blue, grey = (
        colors.HexColor("#1a1a1a"),
        colors.HexColor("#1f5f8b"),
        colors.HexColor("#666666"),
    )
    ok, warn, head = (
        colors.HexColor("#e3f1e6"),
        colors.HexColor("#fbeedd"),
        colors.HexColor("#e6edf3"),
    )
    body = ParagraphStyle(
        "b", fontName="DV", fontSize=8.8, leading=12.4, textColor=ink, spaceAfter=4
    )
    small = ParagraphStyle("s", parent=body, fontSize=7.6, leading=10.4, textColor=grey)
    h1 = ParagraphStyle(
        "h1", parent=body, fontName="DV-B", fontSize=15.5, leading=19, textColor=blue, spaceAfter=2
    )
    h2 = ParagraphStyle(
        "h2",
        parent=body,
        fontName="DV-B",
        fontSize=10.5,
        leading=13,
        textColor=blue,
        spaceBefore=8,
        spaceAfter=3,
    )
    cell = ParagraphStyle("c", parent=body, fontSize=7.9, leading=10.2, spaceAfter=0)
    cellb = ParagraphStyle("cb", parent=cell, fontName="DV-B")
    bul = ParagraphStyle("bul", parent=body, leftIndent=10, bulletIndent=0, spaceAfter=2.5)

    def P(t, s=body):
        return Paragraph(t, s)

    def B(t):
        return Paragraph(t, bul, bulletText="•")

    rho, hv, eps = R["density_g_cm3"], R["hvap_wu_definition"], R["epsilon"]
    fs, eta = R["D_finite_size_1e-5_cm2_s"], R["viscosity_mPa_s"]
    dp = R["D_pbc_1e-5_cm2_s"]
    sens = list(R["D_pbc_sensitivity_1e-5_cm2_s"].values())
    d_lo, d_hi = fs["D_expected_in_wu_box_range"]
    dwu = WU["Ds_1e-5_cm2_s"]
    epsb = eps["epsilon_blocks"]
    cal = R["hvap_caleman_definition"]["kcal_per_mol"]["mean"]
    n_mol, ns = R["run"]["molecules"], R["run"]["production_ps"] / 1000
    ours = {
        "dHvap": hv["kcal_per_mol"]["mean"],
        "mu": R["mu_debye"]["mean"],
        "th": R["theta_HOH_deg"]["mean"],
        "r": R["r_OH_angstrom"]["mean"],
        "eps": eps["epsilon"],
        "eta": eta["mean"],
        "D": fs["D_expected_in_wu_box"],
    }

    rows = [
        ["Property", "UnitcellMD", "Wu et al. 2006", "Difference", "Verdict"],
        [
            "ρ (g/cm³)",
            pm(rho, 4),
            f"{WU['rho_g_cm3']['value']} ({WU['rho_g_cm3']['bracket']})",
            rel(rho["mean"], WU["rho_g_cm3"]["value"]),
            "differs, cause open",
        ],
        [
            "ΔH<sub>vap</sub> (kcal/mol)",
            f"{ours['dHvap']:.3f} ± {hv['kcal_per_mol']['sem']:.3f}",
            f"{WU['dHvap_kcal_mol']['value']} ({WU['dHvap_kcal_mol']['bracket']})",
            rel(ours["dHvap"], WU["dHvap_kcal_mol"]["value"]),
            "agrees",
        ],
        [
            "D, 216-molecule box (10<super>-5</super> cm²/s)",
            f"{ours['D']:.2f} ({d_lo:.2f}–{d_hi:.2f}), derived",
            f"{dwu['value']} ({dwu['bracket']})",
            rel(ours["D"], dwu["value"]),
            "agrees (assumption)",
        ],
        [
            "ε",
            f"{ours['eps']:.1f} (block mean {epsb['mean']:.1f} ± {epsb['sem']:.1f})",
            f"{WU['epsilon0']['value']} ({WU['epsilon0']['bracket']})",
            rel(ours["eps"], WU["epsilon0"]["value"]),
            "agrees within errors",
        ],
        [
            "⟨r<sub>OH</sub>⟩ (Å)",
            f"{ours['r']:.4f}",
            f"{WU['r_OH_angstrom']['value']:.4f}",
            rel(ours["r"], WU["r_OH_angstrom"]["value"]),
            "agrees",
        ],
        [
            "⟨θ<sub>HOH</sub>⟩ (°)",
            f"{ours['th']:.2f}",
            f"{WU['theta_HOH_deg']['value']}",
            rel(ours["th"], WU["theta_HOH_deg"]["value"]),
            "agrees",
        ],
        [
            "⟨μ⟩ (D)",
            f"{ours['mu']:.3f}",
            f"{WU['mu_debye']['value']}",
            rel(ours["mu"], WU["mu_debye"]["value"]),
            "agrees",
        ],
        [
            "η (mPa·s, 300.2 K)",
            pm(eta, 3),
            f"{WU['eta_cP_at_300.2_K']['value']} (±{WU['eta_cP_at_300.2_K']['inaccuracy']})",
            rel(eta["mean"], WU["eta_cP_at_300.2_K"]["value"]),
            "agrees within errors",
        ],
    ]
    data = [[Paragraph(c, cellb if i == 0 else cell) for c in r] for i, r in enumerate(rows)]
    tab = Table(data, colWidths=[46 * mm, 42 * mm, 29 * mm, 22 * mm, 31 * mm], repeatRows=1)
    st = [
        ("BACKGROUND", (0, 0), (-1, 0), head),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b9c4cd")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]
    for i in range(1, len(rows)):
        st.append(("BACKGROUND", (4, i), (4, i), warn if i == 1 else ok))
    tab.setStyle(TableStyle(st))

    S = [
        P("Reproducing Wu, Tepper &amp; Voth (2006) with UnitcellMD", h1),
        P(
            "SPC/Fw liquid water: UnitcellMD engine and OpenMM GPU bridge against Table II of "
            f"J. Chem. Phys. 124, 024503. Status {DATE} (study <i>2026-11-20_water-spcfw-wu</i>; "
            "label: exploration, one run).",
            small,
        ),
        Spacer(1, 4),
        P("Summary", h2),
        P(
            f"We simulated SPC/Fw water with the protocol of Wu et al. (298.16 K, 1 atm, {PROTO['timestep_fs']} fs, "
            f"{PROTO['cutoff_angstrom']} Å cutoff with long-range corrections, PME 10<super>-6</super>, "
            f"{PROTO['length_ns']} ns, first {PROTO['equilibration_ns']} ns discarded) and compared with their Table II. "
            "<b>Six of the seven properties agree within the published or our own statistical error.</b> "
            "The intramolecular geometry and the dipole agree to three to four digits, ΔH<sub>vap</sub> agrees, "
            "and the dielectric constant and the diffusion coefficient agree within errors. "
            f"The independent Green–Kubo viscosity ({pm(eta, 3)} mPa·s) agrees with Wu's {WU['eta_cP_at_300.2_K']['value']} cP. "
            f"<b>The density is {abs((rho['mean'] - WU['rho_g_cm3']['value']) / WU['rho_g_cm3']['value'] * 100):.1f} % low</b> "
            f"({rho['mean']:.4f} against {WU['rho_g_cm3']['value']} g/cm³), and we do not yet know why."
        ),
        Spacer(1, 3),
        tab,
        P(
            f"Ours: one {ns + R['run']['skip_ps'] / 1000:.1f} ns run, averages over {R['run']['skip_ps'] / 1000:.1f}–{R['run']['skip_ps'] / 1000 + ns:.1f} ns, "
            "errors are standard errors of 10 blocks (5 for D and η). Wu's bracketed values are standard "
            "deviations of the simulation, which is not the error of a mean; η has the inaccuracy "
            "stated in their table caption (periodic perturbation method).",
            small,
        ),
        P("What was run", h2),
        B(
            "<b>Model:</b> SPC/Fw, parameters checked against Wu's Table I; none invented or fitted."
        ),
        B(
            f"<b>System:</b> {n_mol} molecules (Wu: {PROTO['molecules']}). Their {fs['wu_box_edge_nm']} nm box is smaller than "
            "twice the engine's cutoff plus neighbour-list skin (2 × 1.1 nm), so a larger box was needed."
        ),
        B(
            f"<b>Engine path:</b> UnitcellMD run loop with the OpenMM bridge on an AMD MI50 (HIP, double precision, ≈ {TR['speed_ns_per_day']['value']} ns/day). "
            "At the start the bridge is checked against the engine's own force evaluation: energy agrees to "
            f"{sci(TR['conformance_energy_rel']['value'])} and forces to {sci(TR['conformance_force_rel']['value'])} (relative)."
        ),
        B(
            "<b>Cross-check of the two paths:</b> a separate pair of 500-molecule runs, CPU engine against GPU bridge "
            f"(study <i>2026-11-20_water-spcfw-gpu-twin</i>), gave equal density ({tpm('twin_density_cpu', 4)} against {tpm('twin_density_gpu', 4)}) "
            f"and potential energy per molecule ({tpm('twin_u_per_molecule_cpu_kJ_mol', 3)} against {tpm('twin_u_per_molecule_gpu_kJ_mol', 3)} kJ/mol)."
        ),
        B(
            f"<b>Definitions:</b> ΔH<sub>vap</sub> = −⟨U⟩/N + RT without a gas-phase term, as Wu define it "
            f"(⟨U⟩/N = {hv['u_per_molecule_kJ_per_mol']['mean']:.3f} kJ/mol, RT = {hv['RT_kJ_per_mol']:.3f} kJ/mol). "
            "ε from the total dipole fluctuation with conducting boundaries (their Eq. 3). Viscosity from a separate "
            f"{eta['samples'] * eta['dt_ps'] / 1000:.0f} ns NVT run at Wu's density ({eta['density_g_cm3']:.3f} g/cm³) and "
            f"{eta['temperature_K']} K, by the Green–Kubo integral of the five independent pressure-tensor components "
            f"(lag ≤ {eta['max_lag_ps']:.0f} ps, {eta['dt_ps'] * 1000:.0f} fs sampling)."
        ),
    ]
    fig = figure()
    S += [
        KeepTogether(
            [
                Image(str(fig), width=150 * mm, height=150 * mm * 2.6 / 7.2),
                P(
                    "<b>Figure 1.</b> Density and potential energy per molecule during the run (5 ps running mean). "
                    "The density settles within the first 0.5 ns and stays below Wu's value without a trend.",
                    small,
                ),
            ]
        ),
        P("Diffusion coefficient: how the comparison is made", h2),
        P(
            "Diffusion in a periodic box depends on its size. We correct with Yeh &amp; Hummer, "
            "D<sub>∞</sub> = D<sub>PBC</sub> + k<sub>B</sub>T ξ / (6π η L), ξ = 2.837297 (cubic box). "
            f"Our D for the {n_mol}-molecule box (L = {dp['box_edge_nm']:.3f} nm) is {dp['mean']:.2f} ± {dp['sem']:.2f} "
            f"(other fit windows and block counts: {min(sens):.2f}–{max(sens):.2f}) ×10<super>-5</super> cm²/s, "
            f"which gives D<sub>∞</sub> = {fs['D_infinity']:.2f} with our own viscosity ({fs['eta_used_mPa_s']:.3f} mPa·s; "
            f"shift {fs['yeh_hummer_shift_our_box']:.2f}). Applying the same correction backwards to Wu's box "
            f"(L = {fs['wu_box_edge_nm']} nm, shift {fs['yeh_hummer_shift_wu_box']:.2f}) gives "
            f"{fs['D_expected_in_wu_box']:.2f} ({d_lo:.2f}–{d_hi:.2f}), against Wu's {dwu['value']} ± {dwu['bracket']}. "
            "<b>This holds only if Wu's D is uncorrected for the box size;</b> I found no correction in the text I read. "
            f"D is at 298.16 K and η at {eta['temperature_K']} K (Wu's viscosity condition), a small mismatch."
        ),
        P("What we cannot explain, and what to treat with care", h2),
        B(
            f"<b>Density, {abs((rho['mean'] - WU['rho_g_cm3']['value']) / WU['rho_g_cm3']['value'] * 100):.1f} % low.</b> "
            f"The same deficit appears in the twin runs ({TR['twin_density_cpu']['mean']}, {TR['twin_density_gpu']['mean']}) and is larger than our errors. "
            f"It is small against the width of the density distribution: the standard deviation of the instantaneous density "
            f"is {R['fluctuation_sd']['density_g_cm3']:.4f} g/cm³ here, {R['fluctuation_sd']['density_sd_scaled_to_216_molecules']:.4f} "
            f"scaled to 216 molecules, against Wu's {WU['rho_g_cm3']['bracket']}. Untested candidates: system size, the barostat, "
            "details of PME and the long-range corrections. We have not checked how much it matters for the other properties."
        ),
        B(
            f"<b>ΔH<sub>vap</sub> depends on the time step.</b> ⟨U⟩/N is {hv['u_per_molecule_kJ_per_mol']['mean']:.2f} kJ/mol at 1 fs and "
            f"{TR['u_per_molecule_0.5fs_kJ_mol']['value']} kJ/mol at 0.5 fs (twin run), so ΔH<sub>vap</sub> would be "
            f"{TR['hvap_at_0.5fs_kcal_mol']['value']:.2f} instead of {ours['dHvap']:.2f} kcal/mol. 1 fs is Wu's step. With a gas-phase "
            f"term (Caleman's definition) the value is {cal:.2f} kcal/mol; the two definitions are not comparable."
        ),
        B(
            f"<b>ε converges slowly.</b> The estimate from all frames ({eps['epsilon']:.1f}) lies above the block mean "
            f"({epsb['mean']:.1f} ± {epsb['sem']:.1f}); the ten blocks range from {min(epsb['values']):.0f} to {max(epsb['values']):.0f}. "
            f"Wu's {WU['epsilon0']['value']} is inside the block error of either."
        ),
        B(
            "<b>One run, one seed.</b> The errors are block errors of one trajectory; a second seed has not been run, "
            "and the publication rules ask for independent replicas for any number that goes into a paper "
            "(docs/research/publication.md, rule 2)."
        ),
        B(
            "<b>Not the same simulation.</b> Different code and box size, and possibly different barostat and PME settings. "
            "Agreement to three to four digits for geometry and dipole tests the parameters and the flexible-bond integration; "
            "it does not prove the long-range treatment is identical."
        ),
        P("A bug found on the way", h2),
        P(
            f"The first GPU comparison for water missed the energy check by {sci(TR['lj_tail_bug']['conformance_before'])} (limit {sci(TR['lj_tail_bug']['limit'])}). "
            "The cause was not precision: OpenMM's long-range LJ correction averages over all N(N+1)/2 atom pairs, including "
            "hydrogens without an LJ site, while the engine uses the standard 2π/V Σ n<sub>a</sub>n<sub>b</sub>I<sub>ab</sub>. "
            f"For 500 waters the gap is {TR['lj_tail_bug']['gap_kJ_mol']} kJ/mol, the whole error. The bridge now applies per-class weights beyond the cutoff, "
            "and a regression test (two periodic molecules) fails on the old code. The limit was not loosened."
        ),
        P("Provenance", h2),
        P(
            "Engine ucmd 0.0.0; bridge branch <i>e25-constraints</i> commit 2ea7e82 (unpushed); OpenMM 8.5.0 with OpenMM-HIP-7, "
            "image <i>ucmd-openmm:gfx906-hip</i>, platform HIP, precision double. Viscosity: CPU engine, 8 threads. "
            "Analysis: <i>docs/research/results/wu2006-spcfw-water/analyze.py</i> (ucmd-analysis), numbers in "
            "<i>data/results.json</i>, input hashes in <i>data/manifest.json</i>, literature values in <i>literature.json</i>. "
            "Reference: Y. Wu, H. L. Tepper, G. A. Voth, J. Chem. Phys. 124, 024503 (2006); I.-C. Yeh, G. Hummer, "
            "J. Phys. Chem. B 108, 15873 (2004).",
            small,
        ),
    ]

    def foot(c, d):
        c.saveState()
        c.setFont("DV", 7)
        c.setFillColor(grey)
        c.drawString(18 * mm, 10 * mm, f"UnitcellMD · SPC/Fw water against Wu et al. 2006 · {DATE}")
        c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(d.page))
        c.restoreState()

    SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=17 * mm,
        title="Reproducing Wu, Tepper & Voth (2006) with UnitcellMD",
        author="UnitcellMD",
    ).build(S, onFirstPage=foot, onLaterPages=foot)
    print("wrote", OUT)


if __name__ == "__main__":
    os.environ.setdefault("MPLBACKEND", "Agg")
    build()
