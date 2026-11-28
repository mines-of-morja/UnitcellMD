"""EC preference in the Li+ shell: experiments and our 1 M runs on one scale.

P = (n_EC / n_linear) * (1 - x_EC) / x_EC, with n the molecules bound per Li+ and x_EC the mole
fraction of EC in the solvent. P = 1 means the shell has the composition of the solvent. P is also
the ratio of the bound fractions of the two solvents, so it equals chi of Su 2019.

Reads ../summary/literature.json and ../trials/T2/t2_result.json. Standard library only.
Usage: python3 docs/research/li-shell/ec_preference.py
"""

import json
import math
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
LIT = json.loads((RESEARCH / "summary/literature.json").read_text(encoding="utf-8"))["entries"]
T2 = json.loads((RESEARCH / "trials/T2/t2_result.json").read_text(encoding="utf-8"))

# Lehnert's 1 M box (T2 plan): 168 EC, 332 EMC.
X_EC_1M = 168 / 500
# Relative error of one diffusion coefficient: Su 2018, Table 1 note b. An assumption for Su 2019,
# which prints no error.
REL_ERR_D = 0.02
M_EC, M_DMC = 88.1, 90.1  # g/mol, Morita 1998 Table 1


def preference(n_ec: float, n_lin: float, x_ec: float) -> float:
    return n_ec / n_lin * (1 - x_ec) / x_ec


def bound_fraction(ratio: float, d_neat: float, d_salt: float, d_li: float) -> float:
    """Su's D-alpha analysis: D_salt = alpha D_Li + (1 - alpha) ratio D_neat."""
    free = ratio * d_neat
    return (free - d_salt) / (free - d_li)


def su2019(args: list[float]) -> tuple[float, float, float]:
    tol0, ec0, emc0, tol, ec, emc, li = args
    a = bound_fraction(tol / tol0, ec0, ec, li)
    b = bound_fraction(tol / tol0, emc0, emc, li)
    return a, b, a / b


def su2019_with_error() -> list[tuple[float, float]]:
    v = LIT["nmr_su2019_dosy_ec_emc"]["value"]
    n, s = v["neat_1_1"], v["LiPF6_1_4_4"]
    args = [n["D_toluene"], n["D_EC"], n["D_EMC"]]
    args += [s["D_toluene"], s["D_EC"], s["D_EMC"], s["D_Li"]]
    base = su2019(args)
    var = [0.0, 0.0, 0.0]
    for i, d in enumerate(args):
        up, down = list(args), list(args)
        up[i], down[i] = d * (1 + REL_ERR_D), d * (1 - REL_ERR_D)
        for k, (u, w) in enumerate(zip(su2019(up), su2019(down), strict=True)):
            var[k] += ((u - w) / 2) ** 2
    return [(b, math.sqrt(x)) for b, x in zip(base, var, strict=True)]


def mean_se(xs: list[float]) -> tuple[float, float]:
    m = sum(xs) / len(xs)
    return m, math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1) / len(xs))


def main() -> None:
    a, b, chi = su2019_with_error()
    print("Su 2019, LiPF6:EC:EMC 1:4:4, recomputed from the printed D, 2 % error per D:")
    print(f"  alpha_EC {a[0]:.3f} +- {a[1]:.3f}  alpha_EMC {b[0]:.3f} +- {b[1]:.3f}")
    print(f"  P = chi {chi[0]:.2f} +- {chi[1]:.2f}  number {4 * (a[0] + b[0]):.2f}")

    s = LIT["nmr_su2018_dosy_ec_emc_dmc"]["value"]
    print("Su 2018, 1:3:3:3 with DMC:")
    print(f"  P(EC/EMC) {s['alpha_EC'] / s['alpha_EMC']:.2f}", end="")
    print(f"  P(EC/DMC) {s['alpha_EC'] / s['alpha_DMC']:.2f}")

    m = LIT["raman_morita1998_ec_dmc"]["value"]
    ec, dmc = m["density_EC_g_cm3"] / M_EC, m["density_DMC_g_cm3"] / M_DMC
    x = ec / (ec + dmc)
    print(f"Morita 1998, EC/DMC, x_EC {x:.2f} (from the printed densities), P:")
    for c, p, q in zip(m["c_LiPF6_mol_per_L"], m["N_EC"], m["N_DMC"], strict=True):
        print(f"  {c} mol/L  EC {p}  DMC {q}  P {preference(p, q, x):.2f}")

    u = LIT["raman_uchida2021_ec_dmc"]["value"]
    d = LIT["nmr_uchida2021_diffusion_ec_dmc"]["value"]
    print("Uchida 2021, EC/DMC 1 mol/kg: Raman numbers, P, bound fractions,")
    print("  and alpha by Su's equation with the viscosity ratio in place of toluene:")
    rows = zip(u["x_EC"], u["n_DMC_ct"], u["n_DMC_cc"], u["n_EC"], strict=True)
    for i, (xe, ct, cc, ne) in enumerate(rows):
        if xe == 0:
            continue
        nd = ct + cc
        ratio = d["solvent"]["viscosity"][i] / d["LiPF6"]["viscosity"][i]
        ar = []
        for sp in ("D_EC", "D_DMC"):
            args = d["solvent"][sp][i], d["LiPF6"][sp][i], d["LiPF6"]["D_Li"][i]
            ar.append(bound_fraction(ratio, *args))
        fe, fd = ne / (xe * u["solvent_per_Li"]), nd / ((1 - xe) * u["solvent_per_Li"])
        print(f"  x {xe:.3f}  EC {ne:.2f}  DMC {nd:.2f}  sum {ne + nd:.2f}", end="")
        print(f"  P {preference(ne, nd, xe):.2f}  Raman bound EC {fe:.2f} DMC {fd:.2f}", end="")
        print(f"  viscosity alpha EC {ar[0]:+.2f} DMC {ar[1]:+.2f}")

    print(f"Ours, trial T2, 1 M, 3:7 w:w, x_EC {X_EC_1M:.3f}, mean +- SE of the runs:")
    for model in ("M0", "M1"):
        for shell in ("first_shell_0.28nm", "within_0.516nm"):
            runs = [r[shell] for r in T2["runs"].values() if r["model"] == model]
            ps = [preference(r["EC:O:1"], r["EMC:O:1"], X_EC_1M) for r in runs]
            es = [r["EC:O:1"] for r in runs]
            tot = [r["EC:O:1"] + r["EMC:O:1"] for r in runs]
            (p, pe), (e, ee), (t, te) = mean_se(ps), mean_se(es), mean_se(tot)
            print(f"  {model} {shell:19s} EC {e:.2f} +- {ee:.2f}", end="")
            print(f"  sum {t:.2f} +- {te:.2f}  P {p:.2f} +- {pe:.2f}")
    le = LIT["lehnert2025_shell_fig_s10"]["value"]
    p = preference(le["EC"], le["EMC"], X_EC_1M)
    err = p * math.hypot(0.1 / le["EC"], 0.1 / le["EMC"])
    print(f"Lehnert 2025 (their MD, 0.516 nm, plot reading +-0.1): P {p:.2f} +- {err:.2f}")


if __name__ == "__main__":
    main()
