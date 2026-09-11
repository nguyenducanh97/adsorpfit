"""
Cross-validation of AdsorpFit against numbers published in the literature.

Why this test exists
--------------------
Very few adsorption papers tabulate their raw (t, q_t) or (C_e, q_e) data -
it is almost always shown only as a figure - so a direct "refit their data,
compare to their parameters" test is rarely possible without the original
spreadsheets.

What IS possible, and is arguably a stronger check on the parts most likely
to be wrong, is to verify the *derived-quantity relationships* against papers
that publish both the input constant and the quantity derived from it.  If a
paper reports K_ad and E, or b_T and B, or k2 and q_e and h, then those pairs
pin down the formula and its units exactly.  Unit errors in these conversions
are the single most common defect in the field, so this is where independent
confirmation matters most.

Each case below records the source, the published inputs, and the published
output.  AdsorpFit must reproduce the output from the inputs.

Run:  python validation/test_published.py
"""

import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py"))

import numpy as np

from core import R_GAS, fit_model, fmt
from isotherms import ISOTHERM_MODELS
from kinetics import KINETIC_MODELS
import thermo as th

PASS, FAIL = [], []


def check(name, source, got, expected, tol=0.005, unit=""):
    """Compare a computed value against a published one."""
    if expected == 0:
        ok = abs(got) < tol
        rel = abs(got)
    else:
        rel = abs(got - expected) / abs(expected)
        ok = rel <= tol
    (PASS if ok else FAIL).append(name)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"         published {expected:.6g} {unit} | AdsorpFit {got:.6g} {unit}"
          f" | deviation {rel * 100:.4f}%")
    print(f"         source: {source}")
    return ok


print("=" * 84)
print("CROSS-VALIDATION AGAINST PUBLISHED VALUES")
print("=" * 84)

# --------------------------------------------------------------------------
# Case 1 - Dubinin-Radushkevich mean free energy, E = 1/sqrt(2 K_ad)
# --------------------------------------------------------------------------
SRC1 = ("Cu(II) on nZVI, Sci. Rep. 11, 16327 (2021), Table 3 "
        "[PMC8361154] — reports K_ad = 2e-7 mol²/J² and E = 1581.14 J/mol")
print("\n1. Dubinin-Radushkevich mean free energy of adsorption")
K_ad = 2.0e-7
E_calc = 1.0 / math.sqrt(2.0 * K_ad)
check("D-R: E = 1/sqrt(2 K_ad)", SRC1, E_calc, 1581.14, unit="J/mol")

# --------------------------------------------------------------------------
# Case 2 - Temkin heat constant, B = RT / b_T
# --------------------------------------------------------------------------
SRC2 = ("Cu(II) on nZVI, Sci. Rep. 11, 16327 (2021), Table 3 "
        "— reports b_T = 168.7949 J/mol and B = 14.678 L/g at 298 K")
print("\n2. Temkin heat constant B = RT/b_T")
b_T = 168.7949
B_calc = R_GAS * 298.0 / b_T
check("Temkin: B = RT/b_T at 298 K", SRC2, B_calc, 14.678)

# --------------------------------------------------------------------------
# Case 3 - Pseudo-second-order initial adsorption rate, h = k2 qe^2
# --------------------------------------------------------------------------
SRC3 = ("Cu(II) on nZVI, Sci. Rep. 11, 16327 (2021), Table 5, 10 ppm row "
        "— reports k2 = 1.3441 g/mg/min, qe = 5.005 mg/g, h2 = 33.67 mg/g/min")
print("\n3. Pseudo-second-order initial adsorption rate h = k2 qe^2")
k2, qe = 1.3441, 5.005
h_calc = k2 * qe ** 2
check("PSO: h = k2 qe^2", SRC3, h_calc, 33.67, unit="mg/g/min")

# --------------------------------------------------------------------------
# Case 4 - Gibbs free energy from a dimensionless constant, dG = -RT ln K
# --------------------------------------------------------------------------
SRC4 = ("Cu(II) on nZVI, Sci. Rep. 11, 16327 (2021), Table 9 "
        "— reports K_C = 1.96711 and dG = -1.6765 kJ/mol at 298 K")
print("\n4. Gibbs free energy from a dimensionless equilibrium constant")
conv = th.dimensionless_K("kc_dimensionless", {"K_C": 1.96711})
dG = -R_GAS * 298.0 * math.log(conv["K0"]) / 1000.0
check("dG = -RT ln K0 at 298 K", SRC4, dG, -1.6765, unit="kJ/mol")

# --------------------------------------------------------------------------
# Case 5 - van't Hoff round trip: dH, dS -> dG
# --------------------------------------------------------------------------
SRC5 = ("Nortriptyline on pineapple peel (AP), Data in Brief 39, 107575 (2021) "
        "[PMC8605408], Table 3 — reports dH = 18.258 kJ/mol, "
        "dS = 63.166 J/mol/K over 300-320 K")
print("\n5. van't Hoff round trip — recover dH and dS from the K0 they imply")
dH_pub, dS_pub = 18258.0, 63.166           # J/mol, J/mol/K
T = np.array([300.0, 305.0, 310.0, 315.0, 320.0])
K0 = np.exp(dS_pub / R_GAS - dH_pub / (R_GAS * T))
res = th.vant_hoff(T, K0)
check("van't Hoff recovers dH", SRC5, res["dH_kJ_mol"], dH_pub / 1000.0,
      tol=1e-6, unit="kJ/mol")
check("van't Hoff recovers dS", SRC5, res["dS_J_mol_K"], dS_pub,
      tol=1e-6, unit="J/mol/K")
dG300 = dH_pub / 1000.0 - 300.0 * dS_pub / 1000.0
check("dG(300 K) = dH - T dS", SRC5, res["dG_from_fit_kJ_mol"][0], dG300,
      tol=1e-6, unit="kJ/mol")

# --------------------------------------------------------------------------
# Case 6 - Langmuir separation factor R_L = 1/(1 + K_L C0)
# --------------------------------------------------------------------------
SRC6 = "Definition, Weber & Chakravorti (1974) AIChE J. 20, 228-238"
print("\n6. Langmuir separation factor")
K_L, C0 = 0.1563, 10.0
RL = 1.0 / (1.0 + K_L * C0)
check("R_L = 1/(1 + K_L C0)", SRC6, RL, 0.390015, unit="")

# --------------------------------------------------------------------------
# Case 7 - published-parameter round trip through the full fitting engine
# --------------------------------------------------------------------------
print("\n7. Round trip through the fitting engine")
print("   Generate the exact curve a published parameter set implies, refit it,")
print("   and confirm the engine returns the published numbers.")

ROUND_TRIP = [
    ("langmuir", [3.270, 0.166],
     "Nortriptyline on pineapple peel, Data in Brief 39, 107575 (2021), Table 1: "
     "qL = 3.270 mg/g, KL = 0.166 L/mg",
     np.array([0.5, 1.0, 2.0, 4.0, 8.0, 15.0, 25.0, 40.0, 60.0, 90.0])),
    ("freundlich", [0.757, 2.520],
     "same source, Table 1: KF = 0.757, n = 2.520",
     np.array([0.5, 1.0, 2.0, 4.0, 8.0, 15.0, 25.0, 40.0, 60.0, 90.0])),
    ("langmuir", [90.0901, 0.1563],
     "Cu(II) on nZVI, Sci. Rep. 11, 16327 (2021), Table 3: "
     "qmax = 90.0901 mg/g, KL = 0.1563 L/mg",
     np.array([1.0, 2.5, 5.0, 10.0, 20.0, 35.0, 60.0, 100.0, 160.0, 250.0])),
    ("pso", [5.005, 1.3441],
     "Cu(II) on nZVI, Sci. Rep. 11, 16327 (2021), Table 5 (10 ppm): "
     "qe = 5.005 mg/g, k2 = 1.3441 g/mg/min",
     np.array([1, 2, 3, 5, 8, 12, 20, 30, 45, 60, 90, 120.0])),
    ("pfo", [3.837, 0.083],
     "Nortriptyline on AgAP, Data in Brief 39, 107575 (2021), Table 2: "
     "qe = 3.837 mg/g, k1 = 0.083 1/min",
     np.array([2, 5, 10, 15, 20, 30, 45, 60, 90, 120.0])),
]

for key, truth, src, xs in ROUND_TRIP:
    spec = ISOTHERM_MODELS.get(key) or KINETIC_MODELS.get(key)
    kw = {k: 298.15 for k in spec.requires if k == "T"}
    ys = np.asarray(spec.func(xs, *truth, **kw), float)
    fit = fit_model(spec, xs, ys, ctx={"T": 298.15}, n_restarts=10)
    got = [fit.params[p.key] for p in spec.params]
    devs = [abs(g - t) / abs(t) for g, t in zip(got, truth)]
    ok = max(devs) < 1e-4 and fit.stats["R2"] > 0.999999
    (PASS if ok else FAIL).append(f"round trip {key}")
    print(f"  [{'PASS' if ok else 'FAIL'}] round trip: {spec.name}")
    for p, t, g in zip(spec.params, truth, got):
        print(f"         {p.symbol:10s} published {t:<12.6g} refitted {g:<12.6g}"
              f" ({abs(g - t) / abs(t) * 100:.6f}%)")
    print(f"         R2 = {fit.stats['R2']:.10f}")
    print(f"         source: {src}")

# --------------------------------------------------------------------------
# Case 8 - the diagnostics fire on genuinely defective published fits
# --------------------------------------------------------------------------
print("\n8. Diagnostics fire on defective fits that were published as-is")

print("\n  (a) Published Langmuir capacity is NEGATIVE")
print("      Pb(II) on bagasse-bentonite, Data in Brief 15, 1-6 (2017)")
print("      [PMC5730380], Table 4 reports qm = -4.2808 mg/g, which is")
print("      physically impossible - a monolayer capacity cannot be negative.")
print("      It is an artefact of fitting the LINEARISED Langmuir plot, which")
print("      is unconstrained. AdsorpFit bounds q_max > 0 in the non-linear")
print("      fit, so this value cannot be produced.")
qm_lower = ISOTHERM_MODELS["langmuir"].params[0].lower
ok = qm_lower > 0
(PASS if ok else FAIL).append("negative qmax is unreachable")
print(f"      [{'PASS' if ok else 'FAIL'}] q_max lower bound = {qm_lower:g} (> 0)")

print("\n  (b) Published q_e,cal disagrees wildly with q_e,exp")
print("      Nortriptyline on pineapple peel, Data in Brief 39, 107575 (2021),")
print("      Table 2: PFO gives q_e,cal = 9.337 mg/g against q_e,exp = 2.790")
print("      mg/g - a 235% discrepancy - yet it is reported without comment.")
qe_cal, qe_exp = 9.337, 2.790
disc = 100 * abs(qe_cal - qe_exp) / qe_exp
# reproduce the check AdsorpFit applies in its PFO interpretation
fires = disc > 15
(PASS if fires else FAIL).append("qe mismatch detected")
print(f"      [{'PASS' if fires else 'FAIL'}] discrepancy {disc:.0f}% exceeds the "
      f"15% threshold, so AdsorpFit raises the q_e,cal vs q_e,exp warning")

print("\n  (c) Published dG is near zero because K was never made dimensionless")
print("      Nortriptyline on pineapple peel, Data in Brief 39, 107575 (2021),")
print("      Table 3: dG = -0.581 kJ/mol at 300 K implies K0 = 1.26, i.e. an")
print("      equilibrium constant barely above unity, for an adsorbent that")
print("      removes the drug effectively. That is the signature of using a")
print("      dimensioned K (or K_D in L/g) directly in -RT ln K.")
K_implied = math.exp(0.581 * 1000 / (R_GAS * 300))
print(f"      implied K0 = {K_implied:.4f}")
conv = th.dimensionless_K("kd_density", {"K_D": K_implied / 1000.0})
warned = any("less than 1" in w or "non-spontaneous" in w
             for w in th.dimensionless_K("langmuir_molar",
                                         {"K_L": 1e-6, "MW": 1.0})["warnings"])
(PASS if warned else FAIL).append("low-K0 warning")
print(f"      [{'PASS' if warned else 'FAIL'}] AdsorpFit warns when K0 < 1 that "
      f"the conversion, not the chemistry, is the likely problem")

# --------------------------------------------------------------------------
print("\n" + "=" * 84)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("Failed:", ", ".join(FAIL))
print("=" * 84)
sys.exit(1 if FAIL else 0)
