"""Refit published raw data and compare against the published parameters.

This is the test the other two suites could not be: real measurements from a
paper, refitted here, checked against the numbers that paper reports. It
became possible once a dataset turned up whose authors deposited their raw
data openly alongside the article.

  Wang, P. et al. (2021) A comparative study on phosphate removal from water
  using Phragmites australis biochars loaded with different metal oxides.
  Royal Society Open Science 8, 201789.  (open access)
  Raw data: Zenodo 10.5281/zenodo.4711711  (CC0)

Six adsorbents, ten isotherm points and twelve kinetic points each, giving
twenty independent isotherm comparisons and twenty kinetic ones.

Tolerances are set by what the paper actually prints: capacities to three or
four significant figures, rate constants often to two, and in one case to a
single figure (k2 = 0.02), so a rate constant is accepted when it rounds to
the published value at the precision given.

Run:  python validation/test_literature.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "py"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "datasets"))

import numpy as np

from core import fit_model
from isotherms import ISOTHERM_MODELS
from kinetics import KINETIC_MODELS
import wang2021_phosphate as W

PASS, FAIL = [], []

QM_TOL = 0.02        # 2% on a capacity
R2_TOL = 0.03        # our R2 must be within 0.03 of theirs, and not worse


def rounds_to(ours, theirs):
    """Does our value round to theirs at the precision they printed?"""
    s = ("%g" % theirs)
    if "e" in s or "E" in s:
        return abs(ours - theirs) <= abs(theirs) * 0.10
    dec = len(s.split(".")[1]) if "." in s else 0
    return round(ours, dec) == round(theirs, dec)


def fits_at_least_as_well(spec, x, y, ours_params, published_params):
    """Compare residual sums of squares at the two parameter sets.

    A rate constant need not reproduce the published figure exactly to be
    correct. Where the data barely constrain it, two optimisers land in
    different places on a nearly flat surface, and the fair question is
    whether ours describes the data at least as well. On the La-BC run the
    entire signal is 0.09 mg/g against a measurement sd of 0.02, and our
    optimum has the lower SSE of the two.
    """
    import numpy as _np
    sse_ours = float(_np.sum((y - spec.func(x, *ours_params)) ** 2))
    sse_pub = float(_np.sum((y - spec.func(x, *published_params)) ** 2))
    return sse_ours <= sse_pub * 1.001, sse_ours, sse_pub


def check(name, ok, detail):
    (PASS if ok else FAIL).append(name)
    print("  [%s] %-44s %s" % ("PASS" if ok else "FAIL", name, detail))


print("=" * 94)
print("REFIT OF PUBLISHED RAW DATA")
print(W.CITATION)
print("=" * 94)

# --------------------------------------------------------------------------
print("\nISOTHERMS   (their q_max against ours, and whether our R2 is at least"
      " as good)\n")
print("  %-8s %-9s %10s %10s %7s %10s %10s" %
      ("sorbent", "model", "published", "AdsorpFit", "dev", "their R2", "our R2"))

for name in ("Al-BC", "Ca-BC", "Fe-BC", "La-BC", "Mg-BC"):
    d = W.ISOTHERMS[name]
    pub = W.PUBLISHED_ISOTHERM[name]
    ce = np.array(d["ce"], float)
    qe = np.array(d["qe"], float)
    for key in ("langmuir", "sips"):
        f = fit_model(ISOTHERM_MODELS[key], ce, qe, ctx={"T": 298.15}, n_restarts=14)
        ours, theirs = f.params["qm"], pub[key]["qm"]
        dev = abs(ours - theirs) / theirs
        r2_ours, r2_theirs = f.stats["R2"], pub[key]["R2"]
        print("  %-8s %-9s %10.1f %10.1f %6.2f%% %10.3f %10.4f" %
              (name if key == "langmuir" else "", key, theirs, ours,
               dev * 100, r2_theirs, r2_ours))
        check("%s %s q_max" % (name, key), dev <= QM_TOL,
              "%.2f%% from published" % (dev * 100))
        check("%s %s R2" % (name, key),
              r2_ours >= r2_theirs - 0.002 and abs(r2_ours - r2_theirs) <= R2_TOL,
              "ours %.4f vs theirs %.3f" % (r2_ours, r2_theirs))

# --------------------------------------------------------------------------
print("\nKINETICS   (q_e and the rate constant, in the authors' units of h)\n")
print("  %-8s %-5s %9s %9s %7s %11s %11s" %
      ("sorbent", "model", "pub q_e", "ours", "dev", "pub k", "ours"))

t = np.array(W.KIN_TIME, float)
for name in ("Al-BC", "Ca-BC", "Fe-BC", "La-BC", "Mg-BC"):
    q = np.array(W.KINETICS[name]["qt"], float)
    pub = W.PUBLISHED_KINETIC[name]
    for key, kk in (("pfo", "k1"), ("pso", "k2")):
        f = fit_model(KINETIC_MODELS[key], t, q, ctx={"T": 298.15}, n_restarts=14)
        ours_q, theirs_q = f.params["qe"], pub[key]["qe"]
        ours_k, theirs_k = f.params[kk], pub[key][kk]
        devq = abs(ours_q - theirs_q) / theirs_q
        print("  %-8s %-5s %9.2f %9.2f %6.2f%% %11.3f %11.3f" %
              (name if key == "pfo" else "", key, theirs_q, ours_q,
               devq * 100, theirs_k, ours_k))
        check("%s %s q_e" % (name, key), devq <= QM_TOL,
              "%.2f%% from published" % (devq * 100))
        if rounds_to(ours_k, theirs_k):
            check("%s %s %s" % (name, key, kk), True,
                  "%.4g rounds to the published %g" % (ours_k, theirs_k))
        else:
            better, so, sp = fits_at_least_as_well(
                KINETIC_MODELS[key], t, q, [ours_q, ours_k], [theirs_q, theirs_k])
            check("%s %s %s" % (name, key, kk), better,
                  "%.4g vs published %g, but our SSE %.6f <= theirs %.6f"
                  % (ours_k, theirs_k, so, sp))

# --------------------------------------------------------------------------
print("\nDIAGNOSTICS on the cases the authors themselves flagged\n")

# Al-BC never reached equilibrium in 72 h; the paper says so in the text
f = fit_model(KINETIC_MODELS["pfo"], t,
              np.array(W.KINETICS["Al-BC"]["qt"], float), ctx={})
check("Al-BC kinetics flagged as not equilibrated",
      any(i["code"] == "no_equilibrium" for i in f.issues),
      "the paper states uptake was still rising at 72 h")

# Al-BC isotherm likewise does not plateau over the measured range
f = fit_model(ISOTHERM_MODELS["langmuir"],
              np.array(W.ISOTHERMS["Al-BC"]["ce"], float),
              np.array(W.ISOTHERMS["Al-BC"]["qe"], float), ctx={})
check("Al-BC isotherm flagged as not plateauing",
      any(i["code"] == "no_plateau" for i in f.issues),
      "q_max is an extrapolation here")

# the unmodified biochar adsorbs nothing and records negative uptake
f = fit_model(ISOTHERM_MODELS["langmuir"],
              np.array(W.ISOTHERMS["BC"]["ce"], float),
              np.array(W.ISOTHERMS["BC"]["qe"], float), ctx={})
check("plain biochar flagged for negative uptake",
      any(i["code"] == "negative_y" for i in f.issues),
      "one measured q_e is below zero")

# La-BC equilibrated before the first sample, so the rate is undetermined
f = fit_model(KINETIC_MODELS["pfo"], t,
              np.array(W.KINETICS["La-BC"]["qt"], float), ctx={})
check("La-BC flagged for having no early points",
      any(i["code"] == "sparse_early" for i in f.issues),
      "adsorption was complete within the first half hour")


# ==========================================================================
# Zhang 2018: fluoride and arsenic on yak dung biochar
# ==========================================================================
import zhang2018_fluoride_arsenic as Z

print("\n" + "=" * 94)
print("REFIT OF PUBLISHED RAW DATA")
print(Z.CITATION)
print("=" * 94)
print("\nISOTHERMS   loadings reconstructed as q = (C0 - Ce) / 10 g/L\n")
print("  %-14s %10s %10s %7s %9s" %
      ("series", "published", "AdsorpFit", "dev", "our R2"))

for key in (("F", "BC3"), ("F", "Fe-BC3"), ("As", "Fe-BC3"), ("As", "BC3")):
    ce = np.array(Z.CE_ISOTHERM[key], float)
    qe = np.array(Z.qe(key), float)
    f = fit_model(ISOTHERM_MODELS["langmuir"], ce, qe, ctx={"T": 298.15},
                  n_restarts=14)
    pub = Z.PUBLISHED_LANGMUIR[key]["qm"]
    dev = abs(f.params["qm"] - pub) / pub
    print("  %-14s %10.4f %10.4f %6.1f%% %9.4f"
          % ("%s on %s" % key, pub, f.params["qm"], dev * 100, f.stats["R2"]))
    # Arsenic on the plain biochar never turns over, so its capacity is an
    # extrapolation and is not expected to agree closely with a fitted
    # value. It is checked through the diagnostic instead, just below.
    if key != ("As", "BC3"):
        check("%s on %s q_max" % key, dev <= 0.10,
              "%.1f%% from published" % (dev * 100))

f = fit_model(ISOTHERM_MODELS["langmuir"],
              np.array(Z.CE_ISOTHERM[("As", "BC3")], float),
              np.array(Z.qe(("As", "BC3")), float), ctx={})
check("As on BC3 flagged as not plateauing",
      any(i["code"] == "no_plateau" for i in f.issues),
      "its capacity is an extrapolation, which is why it differs from the paper")

print("\nKINETICS   pseudo-second-order q_e, times converted to minutes\n")
print("  %-14s %10s %10s %9s" % ("series", "published", "AdsorpFit", "last q"))
for key in (("F", "BC3"), ("F", "Fe-BC3"), ("As", "BC3"), ("As", "Fe-BC3")):
    t = np.array([h * 60 for h in Z.T_KINETIC], float)
    q = np.array(Z.qt(key), float)
    f = fit_model(KINETIC_MODELS["pso"], t, q, ctx={}, n_restarts=14)
    pub = Z.PUBLISHED_PSO_QE[key]
    print("  %-14s %10.4f %10.4f %9.4f" %
          ("%s on %s" % key, pub, f.params["qe"], q[-1]))
    if key == ("As", "Fe-BC3"):
        # The paper tabulates 1.069 mg/g, which its own deposited data
        # cannot reach: the measured loading never exceeds 0.364. The fit
        # has to follow the measurements rather than the table.
        check("As on Fe-BC3 q_e follows the raw data, not the table",
              abs(f.params["qe"] - q[-1]) / q[-1] <= 0.05,
              "fitted %.4f against a measured plateau of %.4f, where the "
              "paper prints %.3f" % (f.params["qe"], q[-1], pub))
    else:
        dev = abs(f.params["qe"] - pub) / pub
        check("%s on %s q_e" % key, dev <= 0.20,
              "%.1f%% from published" % (dev * 100))


# ==========================================================================
# Tao 2020: levofloxacin on cellulose nanocrystals / graphene oxide
# ==========================================================================
import tao2020_levofloxacin as TAO

print("\n" + "=" * 94)
print("REFIT OF PUBLISHED RAW DATA")
print(TAO.CITATION)
print("=" * 94)
print("\nISOTHERMS at three temperatures   (Sips capacity)\n")
print("  %-10s %10s %10s %8s" % ("T (K)", "published", "AdsorpFit", "our R2"))
caps = []
for T in TAO.TEMPERATURES:
    d = TAO.ISOTHERMS[T]
    f = fit_model(ISOTHERM_MODELS["sips"], np.array(d["ce"], float),
                  np.array(d["qe"], float), ctx={"T": T}, n_restarts=16)
    caps.append(f.params["qm"])
    pub = TAO.PUBLISHED_SIPS_QMAX[T]
    dev = abs(f.params["qm"] - pub) / pub
    print("  %-10.2f %10.2f %10.2f %8.4f"
          % (T, pub, f.params["qm"], f.stats["R2"]))
    check("levofloxacin Sips q_max at %.2f K" % T, dev <= 0.01,
          "%.2f%% from published" % (dev * 100))

# The uptake rising with temperature is what makes a van 't Hoff analysis of
# this set meaningful, and it is the reason it ships as the thermodynamic
# example.
check("levofloxacin capacity rises with temperature",
      caps[0] < caps[1] < caps[2],
      "%.2f < %.2f < %.2f mg/g, an endothermic signature" % tuple(caps))


# ==========================================================================
# Xue 2019: cadmium on a mesoporous ceramic, and the linearisation trap
# ==========================================================================
import xue2019_cadmium as XU
from core import fit_linear

print("\n" + "=" * 94)
print("REFIT OF PUBLISHED RAW DATA")
print(XU.CITATION)
print("=" * 94)

ce = np.array(XU.CE_ISOTHERM, float)
qe = np.array(XU.QE_ISOTHERM, float)
nl = fit_model(ISOTHERM_MODELS["langmuir"], ce, qe, ctx={"T": 298.15},
               n_restarts=14)
hanes = None
for form in ISOTHERM_MODELS["langmuir"].linear_forms:
    r = fit_linear(ISOTHERM_MODELS["langmuir"], form, ce, qe,
                   ctx={"T": 298.15})
    if r.success and "Hanes" in form.name:
        hanes = r

print("\n  published, from the linearised plot   q_max = %.2f, R2 = %.4f"
      % (XU.PUBLISHED_LANGMUIR["qm"], XU.PUBLISHED_LANGMUIR["R2"]))
print("  AdsorpFit non-linear                  q_max = %.2f, R2 = %.4f"
      % (nl.params["qm"], nl.stats["R2"]))
if hanes is not None:
    print("  AdsorpFit Hanes linearisation         q_max = %.2f, "
          "R2 of the line = %.4f, R2 on q = %.4f"
          % (hanes.params["qm"], hanes.stats["R2_linear"], hanes.stats["R2"]))
    dev = abs(hanes.params["qm"] - XU.PUBLISHED_LANGMUIR["qm"]) \
        / XU.PUBLISHED_LANGMUIR["qm"]
    check("cadmium: the linearised fit reproduces the published capacity",
          dev <= 0.10, "%.1f%% from the published 97.09 mg/g" % (dev * 100))
    check("cadmium: the straight line flatters the fit",
          hanes.stats["R2_linear"] > hanes.stats["R2"] + 0.3,
          "R2 = %.3f on the line against %.3f on the loadings"
          % (hanes.stats["R2_linear"], hanes.stats["R2"]))
    check("cadmium: the non-linear fit describes the loadings better",
          nl.stats["R2"] > hanes.stats["R2"],
          "non-linear R2 %.3f against %.3f for the linearised parameters"
          % (nl.stats["R2"], hanes.stats["R2"]))

f = fit_model(KINETIC_MODELS["pso"], np.array(XU.KINETIC_TIME, float),
              np.array(XU.KINETIC_Q, float), ctx={}, n_restarts=14)
check("cadmium kinetics q_e matches the measured plateau",
      abs(f.params["qe"] - XU.KINETIC_Q[-1]) / XU.KINETIC_Q[-1] <= 0.05,
      "fitted %.2f against a measured %.2f mg/g"
      % (f.params["qe"], XU.KINETIC_Q[-1]))

# --------------------------------------------------------------------------
print("\n" + "=" * 94)
print("RESULT: %d passed, %d failed" % (len(PASS), len(FAIL)))
if FAIL:
    print("Failed:", ", ".join(FAIL))
print("=" * 94)
sys.exit(1 if FAIL else 0)
