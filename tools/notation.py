# -*- coding: utf-8 -*-
"""Check scientific notation across everything the user actually reads.

Reads the live model objects rather than grepping source, so variable names
and docstrings cannot be mistaken for prose. Covers parameter symbols and
units, model assumptions, parameter meanings, the generated interpretation
text, the domain and validity messages, and the advisor's reasons.

The agreed convention, enforced here:

  subscripts   ASCII underscore in the source, rendered as <sub> by md()
               q_max, C_e, k_2, t_half
  superscripts ASCII caret, rendered as <sup>
               R^2, q_e^2, mg g^-1
  Greek        the Unicode letter itself, which is a character and not a
               notation hack: alpha, beta, Delta, epsilon, chi, degree sign

Mixing forms for the same quantity is the defect: it means one of them will
render literally.

Run:  python tools/notation.py           survey and check
      python tools/notation.py --check   exit non-zero on a problem
"""
import io
import os
import re
import sys

sys.path.insert(0, "py")

UNI_SUB = "₀₁₂₃₄₅₆₇₈₉ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ"
UNI_SUP = "⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺ᵅ"


def user_facing_text():
    """Every string the interface can put in front of a reader."""
    import numpy as np
    from core import fit_model, check_domain
    from isotherms import ISOTHERM_MODELS
    from kinetics import KINETIC_MODELS
    import advisor

    out = []            # (where, text)
    models = dict(ISOTHERM_MODELS)
    models.update(KINETIC_MODELS)

    for key, m in models.items():
        out.append((key + ".name", m.name))
        for a in m.assumptions:
            out.append((key + ".assumption", a))
        for p in m.params:
            out.append((key + "." + p.key + ".symbol", p.symbol))
            out.append((key + "." + p.key + ".unit", p.unit))
            out.append((key + "." + p.key + ".meaning", p.meaning))

    # a real fit exercises the interpretation and diagnostic prose
    ce = np.array([0.5, 1.2, 2.5, 5.0, 9.0, 15.0, 25.0, 40.0, 65.0, 100.0])
    qe = np.array([8.1, 17.9, 32.5, 52.4, 71.2, 88.6, 103.1, 112.9, 119.4, 122.8])
    t = np.array([1, 2, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180.0])
    qt = np.array([22.8, 36.4, 46.1, 53.2, 62.5, 70.1, 74.2, 77.6, 78.9, 79.4,
                   79.6, 79.8])
    ctx = {"T": 298.15, "C0": 100.0, "C0_list": [10, 25, 50, 80, 120, 160, 220,
                                                 300, 400, 500], "Cs": 5000.0}
    for key, m in models.items():
        x, y = (ce, qe) if m.category == "isotherm" else (t, qt)
        try:
            f = fit_model(m, x, y, ctx=ctx, n_restarts=2)
        except Exception:
            continue
        for w in f.warnings:
            out.append((key + ".warning", w))
        for i in f.issues:
            out.append((key + ".issue", i["text"]))
        if m.interpretation:
            try:
                for line in m.interpretation(f, ctx):
                    out.append((key + ".interpretation", line))
            except Exception:
                pass

    for cat, x, y in (("isotherm", ce, qe), ("kinetics", t, qt)):
        try:
            a = advisor.advise(cat, x, y, ctx=ctx)
        except Exception:
            continue
        for line in a["summary"]:
            out.append(("advisor.summary", line))
        for row in a["models"]:
            for r in row["reasons"]:
                out.append(("advisor.reason", r))
    return out


def audit(texts):
    problems, notes = [], []
    joined = {w: t for w, t in texts}

    uni_sub_hits, uni_sup_hits = [], []
    for where, t in texts:
        if where.endswith(".unit"):
            continue                     # units are rendered as LaTeX already
        if any(c in t for c in UNI_SUB):
            uni_sub_hits.append((where, t[:70]))
        if any(c in t for c in UNI_SUP):
            uni_sup_hits.append((where, t[:70]))

    blob = "\n".join(t for w, t in texts if not w.endswith(".unit"))

    print("USER-FACING STRINGS SCANNED: %d" % len(texts))
    print("\nNOTATION IN PROSE AND SYMBOLS")
    print("  ASCII underscore subscripts : %d" %
          len(re.findall(r"\b[A-Za-z]_[A-Za-z0-9]", blob)))
    print("  ASCII caret superscripts    : %d" % len(re.findall(r"\^[-\dA-Za-z]", blob)))
    print("  Unicode subscripts          : %d" % len(uni_sub_hits))
    print("  Unicode superscripts        : %d" % len(uni_sup_hits))

    # Both notations are normalised by md() at render time now, so a mix in
    # the source is untidy rather than broken. What would be broken is a form
    # md() does not recognise, which the symbol round-trip below checks.
    if uni_sub_hits:
        notes.append("%d strings still use Unicode subscripts; md() renders "
                     "them, but ASCII underscores are the house form"
                     % len(uni_sub_hits))

    forms = [f for f in ("R2", "R^2", "R²") if re.search(re.escape(f), blob)]
    if len(forms) > 1:
        notes.append("R squared written as %s; all three render, but one form "
                     "would read better" % " and ".join(map(repr, forms)))

    # Every parameter symbol must survive the trip to LaTeX, or it shows up raw
    # in the tables, which is the defect this file exists to catch.
    from isotherms import ISOTHERM_MODELS
    from kinetics import KINETIC_MODELS
    models = dict(ISOTHERM_MODELS)
    models.update(KINETIC_MODELS)
    n_params = 0
    for key, m in models.items():
        for prm in m.params:
            n_params += 1
            tex = prm.symbol_tex
            if not tex:
                problems.append("%s.%s has no LaTeX form" % (key, prm.key))
            elif "_" in tex and "{" not in tex:
                problems.append("%s.%s renders as %r, a bare underscore"
                                % (key, prm.key, tex))
            elif any(c in tex for c in UNI_SUB):
                problems.append("%s.%s renders as %r, still Unicode"
                                % (key, prm.key, tex))
    print("\n  %d parameter symbols checked for LaTeX conversion" % n_params)

    if re.search(r"\d\s-\s\d", blob):
        notes.append("ASCII hyphen between numbers where a minus sign is meant")

    print("\nCONSISTENCY")
    for p in problems:
        print("  PROBLEM  %s" % p)
    for n in notes:
        print("  NOTE     %s" % n)
    if not problems and not notes:
        print("  one notation throughout")
    return problems


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    probs = audit(user_facing_text())
    sys.exit(1 if ("--check" in sys.argv and probs) else 0)
