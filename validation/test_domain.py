"""
Regression tests for model domain and validity checking.

These exist because of a real defect: fitting Temkin to dilute-range data
produced a respectable R^2 = 0.958 while predicting q_e = -14.0 mg/g at the
lowest concentration.  Least squares has no objection to a negative loading,
so nothing in the fitting itself catches it.  Each test below pins one of
those failure modes.

Run:  python validation/test_domain.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py"))

import numpy as np

from core import fit_model, check_domain
from isotherms import ISOTHERM_MODELS
from kinetics import KINETIC_MODELS

PASS, FAIL = [], []


def expect(name, condition, detail=""):
    (PASS if condition else FAIL).append(name)
    print(("  [PASS] " if condition else "  [FAIL] ") + name)
    if detail:
        print("         " + detail)


def has(issues, code):
    return any(i["code"] == code for i in issues)


def level_of(issues, code):
    for i in issues:
        if i["code"] == code:
            return i["level"]
    return None


print("=" * 80)
print("DOMAIN AND VALIDITY REGRESSION TESTS")
print("=" * 80)

# --------------------------------------------------------------------------
print("\n1. Temkin on dilute data must be blocked, not merely fitted")
print("   The original bug: R^2 = 0.958 with a predicted q_e of -14.0 mg/g.")
ce = np.array([0.02, 0.05, 0.11, 0.25, 0.60, 1.4, 3.2, 7.0, 15.0, 30.0])
qe = np.array([1.9, 4.4, 8.8, 17.2, 33.0, 55.0, 78.0, 95.0, 106.0, 112.0])
f = fit_model(ISOTHERM_MODELS["temkin"], ce, qe, ctx={"T": 298.15})
neg = int(np.sum(f.y_cal < 0))
expect("negative predictions still occur (the model really is out of range)",
       neg > 0, f"{neg} of {len(ce)} predicted q_e are negative; "
                f"R2 = {f.stats['R2']:.4f}")
expect("Temkin threshold violation is reported",
       has(f.issues, "temkin_below_threshold"))
expect("it is reported at BLOCK level, not as a mild warning",
       level_of(f.issues, "temkin_below_threshold") == "block")
expect("the generic negative-prediction notice is suppressed as a duplicate",
       not has(f.issues, "negative_prediction"),
       "the Temkin-specific message already explains the same failure")

# --------------------------------------------------------------------------
print("\n2. Temkin on mid-range data is allowed")
ce2 = np.array([2.0, 5.0, 9.0, 15.0, 25.0, 40.0, 65.0, 100.0])
qe2 = np.array([32.0, 52.0, 68.0, 82.0, 96.0, 108.0, 118.0, 125.0])
f2 = fit_model(ISOTHERM_MODELS["temkin"], ce2, qe2, ctx={"T": 298.15})
expect("no blocking issue on data Temkin can actually describe",
       not any(i["level"] == "block" for i in f2.issues),
       f"R2 = {f2.stats['R2']:.4f}, min predicted q_e = {np.min(f2.y_cal):.3f}")
expect("predictions stay positive", float(np.min(f2.y_cal)) >= 0)

# --------------------------------------------------------------------------
print("\n3. BET above the saturation concentration is blocked before fitting")
iss = check_domain(ISOTHERM_MODELS["bet"], ce2, qe2, {"Cs": 50.0})
expect("Ce >= Cs is caught up front", has(iss, "bet_above_cs"),
       "BET has (Cs - Ce) in its denominator and diverges there")
expect("blocked at BLOCK level", level_of(iss, "bet_above_cs") == "block")
iss_ok = check_domain(ISOTHERM_MODELS["bet"], ce2, qe2, {"Cs": 5000.0})
expect("no block when Cs is safely above the data range",
       not has(iss_ok, "bet_above_cs"))
iss_none = check_domain(ISOTHERM_MODELS["bet"], ce2, qe2, {})
expect("missing Cs is warned about", has(iss_none, "bet_no_cs"))

# --------------------------------------------------------------------------
print("\n4. Harkins-Jura beyond its singularity is reported")
f4 = fit_model(ISOTHERM_MODELS["harkins_jura"], ce, qe, ctx={"T": 298.15})
b = f4.params["B"]
print(f"         fitted B = {b:.4f}, so the model is undefined at "
      f"Ce >= 10^B = {10 ** b:.4g}; your max Ce = {ce.max():.4g}")
expect("either the fit stays inside the valid range or the violation is flagged",
       (10 ** b > ce.max()) or has(f4.issues, "hj_above_threshold"))

# --------------------------------------------------------------------------
print("\n5. Baudu outside 0 < 1+x+y < 1 is rejected")
f5 = fit_model(ISOTHERM_MODELS["baudu"], ce2, qe2, ctx={"T": 298.15})
a = 1 + f5.params["x"] + f5.params["y"]
inside = 0 < a < 1 and 0 < 1 + f5.params["x"] < 1
expect("domain status matches the fitted parameters",
       inside != has(f5.issues, "baudu_domain"),
       f"1+x+y = {a:.4f}; reported = {has(f5.issues, 'baudu_domain')}")

# --------------------------------------------------------------------------
print("\n6. A saturation model fitted to non-saturating data is warned about")
ce6 = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0])
qe6 = np.array([5.0, 10.0, 20.0, 39.0, 76.0, 148.0, 290.0])   # still climbing
iss6 = check_domain(ISOTHERM_MODELS["langmuir"], ce6, qe6, {})
expect("no-plateau warning fires", has(iss6, "no_plateau"),
       "q_max would be an extrapolation, not a measurement")
ce7 = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0])
qe7 = 120 * 0.5 * ce7 / (1 + 0.5 * ce7)
expect("and does not fire on data that do plateau",
       not has(check_domain(ISOTHERM_MODELS["langmuir"], ce7, qe7, {}),
               "no_plateau"))

# --------------------------------------------------------------------------
print("\n7. Kinetics: an unequilibrated run is warned about")
t = np.array([1, 2, 5, 10, 20, 30, 45, 60.0])
q = 9.0 * np.sqrt(t)                      # never levels off
expect("no-equilibrium warning fires",
       has(check_domain(KINETIC_MODELS["pfo"], t, q, {}), "no_equilibrium"))
q_eq = 80 * (1 - np.exp(-0.09 * t))
expect("and not on a run that does equilibrate",
       not has(check_domain(KINETIC_MODELS["pfo"], t, q_eq, {}), "no_equilibrium"))

# --------------------------------------------------------------------------
print("\n8. Weber-Morris: a negative intercept is flagged as unphysical")
t8 = np.array([5, 10, 20, 30, 45, 60, 90, 120.0])
q8 = 7.5 * np.sqrt(t8) - 12.0             # forces C < 0
f8 = fit_model(KINETIC_MODELS["weber_morris"], t8, q8, ctx={})
expect("negative boundary-layer intercept reported",
       f8.params["C"] >= 0 or has(f8.issues, "wm_negative_intercept"),
       f"fitted C = {f8.params['C']:.4f} mg/g")

# --------------------------------------------------------------------------
print("\n9. Too few points for the parameter count is blocked")
iss9 = check_domain(ISOTHERM_MODELS["fritz_schlunder"],
                    np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0]), {})
expect("3 points cannot fit 4 parameters", has(iss9, "too_few_points"))
expect("blocked at BLOCK level", level_of(iss9, "too_few_points") == "block")

# --------------------------------------------------------------------------
print("\n10. Negative measured uptake is called out")
iss10 = check_domain(ISOTHERM_MODELS["langmuir"],
                     np.array([1.0, 2.0, 4.0, 8.0, 16.0]),
                     np.array([-0.5, 2.0, 4.0, 8.0, 12.0]), {})
expect("negative q values warned about", has(iss10, "negative_y"))

# --------------------------------------------------------------------------
print("\n" + "=" * 80)
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("Failed:", ", ".join(FAIL))
print("=" * 80)
sys.exit(1 if FAIL else 0)
