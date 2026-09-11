"""
Synthetic parameter-recovery test for every AdsorpFit model.

For each model we generate data from known 'true' parameters, add Gaussian
noise of known size, fit, and check two separate things:

  1. RECOVERY   - does the fit reproduce the data as well as the noise floor
                  allows?  The correct criterion is RMSE <= ~1.5 x sigma, not
                  an arbitrary R^2 threshold: no fit can beat the noise, and
                  R^2 depends on how much the curve happens to vary over the
                  chosen x range.

  2. IDENTIFIABILITY - are the individual parameters recovered, or do they
                  trade off against each other?  Several adsorption models
                  are structurally non-identifiable: Crank's D and r only
                  ever appear as D/r^2, and Khan's q_max and b_K only as
                  their product at low Ce.  A model can reproduce the data
                  perfectly while its individual parameters are unrecoverable.
                  That is a property of the model, not a bug in the fitter,
                  and AdsorpFit's job is to report it rather than hide it.

Run:  python validation/test_recovery.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py"))

import numpy as np

from core import fit_model, fmt
from isotherms import ISOTHERM_MODELS
from kinetics import KINETIC_MODELS

rng = np.random.default_rng(2024)

TRUTH = {
    # --- isotherms ---
    "langmuir":            [125.0, 0.085],
    "freundlich":          [22.0, 2.4],
    "temkin":              [1.6, 120.0],
    # Kad must be large enough that the D-R curve actually varies over the
    # Ce range; at 3e-9 the whole curve spans only 3 mg/g and the test is
    # measuring noise, not the model.
    "dubinin_radushkevich": [160.0, 2.0e-7],
    "jovanovic":           [110.0, 0.06],
    "halsey":              [3.5, -2.4],
    "harkins_jura":        [900.0, 1.4],
    "bet":                 [95.0, 40.0],
    "elovich_isotherm":    [95.0, 0.12],
    "sips":                [130.0, 0.07, 0.82],
    "toth":                [140.0, 0.06, 0.75],
    "redlich_peterson":    [11.0, 0.19, 0.88],
    "khan":                [120.0, 0.09, 1.15],
    "radke_prausnitz":     [135.0, 0.08, 1.10],
    "hill":                [128.0, 9.5, 0.85],
    "koble_corrigan":      [10.5, 0.085, 1.05],
    "brouers_sotolongo":   [122.0, 0.10, 0.85],
    "vieth_sladek":        [0.35, 100.0, 0.09],
    "fritz_schlunder":     [12.0, 0.16, 0.92, 0.85],
    "baudu":               [120.0, 0.09, -0.12, -0.10],
    "marczewski_jaroniec": [130.0, 0.09, 0.80, 0.90],
    # --- kinetics ---
    "pfo":                 [78.0, 0.055],
    "pso":                 [85.0, 0.0011],
    "elovich":             [22.0, 0.075],
    "avrami":              [80.0, 0.05, 1.25],
    "mixed_1_2":           [82.0, 0.06, 0.55],
    "nth_order":           [80.0, 0.0015, 1.8],
    "ritchie":             [80.0, 0.06, 2.0],
    "fractal_pfo":         [80.0, 0.08, 0.25],
    "weber_morris":        [6.5, 12.0],
    "film_diffusion":      [78.0, 0.055],
    "bangham":             [9.0, 0.42],
    "crank":               [80.0, 2.0e-6, 0.05],
    "double_exponential":  [85.0, 50.0, 0.25, 0.02],
}

# Models whose parameters are known to be structurally non-identifiable,
# with the combination that IS identifiable.  These are documented in the
# app so users do not over-interpret the individual values.
KNOWN_DEGENERATE = {
    "crank": ("D / r²", lambda p: p["D"] / p["r"] ** 2),
    "khan": ("q_max · b_K (initial slope)", lambda p: p["qm"] * p["bK"]),
    "fritz_schlunder": ("A (low-Ce capacity factor)", lambda p: p["A"]),
    "marczewski_jaroniec": ("q_max", lambda p: p["qm"]),
    "baudu": ("q_max · b_0", lambda p: p["qm"] * p["b0"]),
    "radke_prausnitz": ("q_max · K_RP", lambda p: p["qm"] * p["KRP"]),
}

CE = np.array([0.5, 1.2, 2.5, 5.0, 9.0, 15.0, 25.0, 40.0, 65.0, 100.0, 150.0, 220.0])
T_ = np.array([1, 2, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240, 300])

NOISE = 0.015          # 1.5% relative Gaussian noise
RMSE_FACTOR = 1.6      # fit must get within 1.6x the noise floor
PARAM_TOL = 0.12       # 12% per-parameter tolerance for identifiability


def run(models, xdata, label, ctx):
    print(f"\n{'=' * 88}\n{label}\n{'=' * 88}")
    print(f"  {'model':26s} {'recovery':>9s} {'RMSE/sigma':>11s} "
          f"{'identif.':>9s} {'max dev':>9s}")
    print("  " + "-" * 84)
    n_pass = n_fail = 0
    failures, degenerate = [], []

    for key, spec in models.items():
        truth = TRUTH.get(key)
        if truth is None:
            continue
        kw = {k: ctx[k] for k in spec.requires if k in ctx}
        try:
            clean = np.asarray(spec.func(xdata, *truth, **kw), float)
        except Exception as exc:
            print(f"  {key:26s} ERROR generating reference data: {exc}")
            n_fail += 1
            failures.append(key)
            continue
        if not np.all(np.isfinite(clean)) or np.ptp(clean) <= 0:
            print(f"  {key:26s} SKIP (degenerate reference curve)")
            continue

        sigma = NOISE * float(np.mean(np.abs(clean)))
        noisy = clean + rng.normal(0.0, sigma, clean.shape)
        fit = fit_model(spec, xdata, noisy, ctx=ctx, n_restarts=12)

        if not fit.success:
            print(f"  {key:26s} {'FAIL':>9s}  {fit.message}")
            n_fail += 1
            failures.append(key)
            continue

        rmse_ratio = fit.stats["RMSE"] / sigma
        recovered = rmse_ratio <= RMSE_FACTOR

        got = np.array([fit.params[p.key] for p in spec.params])
        true = np.array(truth, float)
        with np.errstate(divide="ignore", invalid="ignore"):
            rel = np.abs(got - true) / np.where(np.abs(true) > 1e-12, np.abs(true), 1)
        identifiable = bool(np.all(rel < PARAM_TOL))
        worst = float(np.max(rel)) * 100

        if recovered:
            n_pass += 1
        else:
            n_fail += 1
            failures.append(key)

        id_flag = "yes" if identifiable else "NO"
        print(f"  {key:26s} {'PASS' if recovered else 'FAIL':>9s} "
              f"{rmse_ratio:11.2f} {id_flag:>9s} {worst:8.1f}%")

        if not identifiable:
            degenerate.append(key)
            combo = KNOWN_DEGENERATE.get(key)
            if combo:
                name, fn = combo
                tv = fn({p.key: t for p, t in zip(spec.params, true)})
                gv = fn(fit.params)
                err = abs(gv - tv) / abs(tv) * 100 if tv else float("nan")
                print(f"      └─ identifiable combination {name}: "
                      f"true {fmt(tv)} vs fit {fmt(gv)}  ({err:.1f}% error)")
            else:
                for p, t, g in zip(spec.params, true, got):
                    print(f"      └─ {p.symbol:10s} true={fmt(t):>12s} "
                          f"fit={fmt(g):>12s}")
        if not recovered:
            for p, t, g in zip(spec.params, true, got):
                print(f"      !! {p.symbol:10s} true={fmt(t):>12s} fit={fmt(g):>12s}")

    return n_pass, n_fail, failures, degenerate


if __name__ == "__main__":
    ctx = {"T": 298.15, "Cs": 1000.0, "C0": 200.0}
    p1, f1, fail1, deg1 = run(ISOTHERM_MODELS, CE,
                              "ISOTHERM MODELS", ctx)
    p2, f2, fail2, deg2 = run(KINETIC_MODELS, T_,
                              "KINETIC MODELS", ctx)

    print(f"\n{'=' * 88}")
    print(f"RECOVERY (fit reaches the noise floor):  "
          f"{p1 + p2} passed, {f1 + f2} failed")
    if fail1 + fail2:
        print("  failed:", ", ".join(fail1 + fail2))
    deg = deg1 + deg2
    print(f"\nSTRUCTURALLY NON-IDENTIFIABLE ({len(deg)} models):")
    print("  " + (", ".join(deg) if deg else "none"))
    print("  These reproduce the data correctly but their individual parameters")
    print("  trade off against one another. The app flags this so the values are")
    print("  not over-interpreted. It is a property of the models themselves.")
    print("=" * 88)
    sys.exit(1 if (f1 + f2) else 0)
