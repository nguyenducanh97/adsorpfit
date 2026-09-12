"""
AdsorpFit - model advisor.

Reads the shape of the raw data, works out what it physically implies, then
screens every model and sorts them into three buckets with a reason attached:

    recommend   the data support this model and it is inside its own domain
    usable      it will fit, but with a caveat you should state
    avoid       the data cannot support it, or the model is out of bounds

The point is not to pick a model for you.  It is to stop you selecting
twenty models, reading off whichever has the highest R^2, and reporting a
mechanism that the data never contained.  Two things drive the verdict:

  1. Data physics - does the isotherm plateau? is it linear, concave,
     sigmoidal? did the kinetics reach equilibrium? are there enough early
     points to fix a rate constant? how many decades of concentration?
  2. A fast screening fit - each model is fitted once, cheaply, and judged on
     AICc plus whether it violated its own domain.

Physics vetoes statistics: a model that predicts negative loading is rejected
however well it fits.
"""

from __future__ import annotations

import numpy as np

from core import (fit_model, rank_models, check_domain, fmt,
                  terminal_slope_ratio)
from isotherms import ISOTHERM_MODELS
from kinetics import KINETIC_MODELS
from lang import tr


# --------------------------------------------------------------------------
# Reading the data
# --------------------------------------------------------------------------

def describe_isotherm(x, y) -> dict:
    """Characterise the shape of an equilibrium isotherm."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    o = np.argsort(x)
    x, y = x[o], y[o]
    n = x.size
    d = {"n": n, "x_min": float(x.min()), "x_max": float(x.max()),
         "y_min": float(y.min()), "y_max": float(y.max())}

    d["decades"] = (float(np.log10(x.max() / x.min()))
                    if x.min() > 0 else float("inf"))

    span = float(y.max() - y.min())
    k = max(1, n // 3)
    d["tail_rise"] = ((float(y[-k:].max()) - float(y[-k:].min())) / span
                      if span > 0 else 0.0)
    d["slope_ratio_end"] = terminal_slope_ratio(x, y)
    d["plateaus"] = d["slope_ratio_end"] < 0.10 and d["tail_rise"] < 0.12
    d["still_rising"] = d["slope_ratio_end"] > 0.30 or d["tail_rise"] > 0.25

    # Henry's-law linearity: does q vs C pass through the origin as a line?
    if n >= 3:
        sl = float(np.sum(x * y) / np.sum(x * x)) if np.sum(x * x) > 0 else 0.0
        resid = y - sl * x
        sst = float(np.sum((y - y.mean()) ** 2))
        d["linear_R2"] = 1.0 - float(np.sum(resid ** 2)) / sst if sst > 0 else 0.0
    else:
        d["linear_R2"] = 0.0
    d["is_linear"] = d["linear_R2"] > 0.98

    # log-log slope at the two ends: Freundlich 1/n, and its drift
    m = (x > 0) & (y > 0)
    d["loglog_slope"] = np.nan
    d["slope_drift"] = np.nan
    if m.sum() >= 4:
        lx, ly = np.log(x[m]), np.log(y[m])
        h = max(2, m.sum() // 2)
        s_lo = float(np.polyfit(lx[:h], ly[:h], 1)[0])
        s_hi = float(np.polyfit(lx[-h:], ly[-h:], 1)[0])
        d["loglog_slope"] = float(np.polyfit(lx, ly, 1)[0])
        d["slope_lo"], d["slope_hi"] = s_lo, s_hi
        d["slope_drift"] = s_lo - s_hi
    d["strongly_favourable"] = (np.isfinite(d.get("loglog_slope", np.nan))
                                and d["loglog_slope"] < 0.35)

    # sigmoidal? look for an inflection in the smoothed curve
    d["sigmoidal"] = False
    if n >= 6:
        dy = np.gradient(y, x)
        if np.all(np.isfinite(dy)) and dy.size >= 5:
            # a sigmoid's slope rises then falls; a Langmuir's only falls
            i_peak = int(np.argmax(dy))
            d["sigmoidal"] = bool(i_peak >= 2 and dy[0] < 0.6 * dy[i_peak])

    d["coverage"] = float(y.max() / (y.max() * 1.0))  # placeholder, set below
    return d


def describe_kinetics(x, y) -> dict:
    """Characterise the shape of an uptake-versus-time curve."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    o = np.argsort(x)
    x, y = x[o], y[o]
    n = x.size
    d = {"n": n, "t_min": float(x.min()), "t_max": float(x.max()),
         "q_max": float(y.max())}

    span = float(y.max() - y.min())
    k = max(2, n // 3)
    d["tail_rise"] = ((float(y[-k:].max()) - float(y[-k:].min())) / span
                      if span > 0 else 0.0)
    d["slope_ratio_end"] = terminal_slope_ratio(x, y)
    d["equilibrated"] = d["slope_ratio_end"] < 0.05 and d["tail_rise"] < 0.08
    d["still_rising"] = d["slope_ratio_end"] > 0.15 or d["tail_rise"] > 0.25

    q_end = float(y.max())
    d["n_early"] = int(np.sum(y < 0.5 * q_end)) if q_end > 0 else 0
    d["n_before_90pct"] = int(np.sum(y < 0.9 * q_end)) if q_end > 0 else 0
    d["well_sampled_early"] = d["n_early"] >= 3

    dy = np.diff(y)
    d["monotonic"] = bool(np.all(dy >= -0.02 * max(span, 1e-9)))

    # two-stage shape: a clear break in the rate of uptake against sqrt(t)
    d["two_stage"] = False
    if n >= 7:
        sq = np.sqrt(np.clip(x, 0, None))
        half = n // 2
        s1 = float(np.polyfit(sq[:half], y[:half], 1)[0])
        s2 = float(np.polyfit(sq[half:], y[half:], 1)[0])
        d["slope_ratio"] = s1 / s2 if abs(s2) > 1e-12 else np.inf
        d["two_stage"] = bool(d["slope_ratio"] > 2.5)
    return d


# --------------------------------------------------------------------------
# Screening
# --------------------------------------------------------------------------

def advise(category: str, x, y, ctx: dict | None = None,
           models: list[str] | None = None) -> dict:
    """Screen every model and return a recommendation for each."""
    ctx = ctx or {}
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]

    registry = ISOTHERM_MODELS if category == "isotherm" else KINETIC_MODELS
    keys = models or list(registry.keys())

    shape = (describe_isotherm(x, y) if category == "isotherm"
             else describe_kinetics(x, y))

    fits, rows = [], {}
    for key in keys:
        spec = registry[key]
        pre = check_domain(spec, x, y, ctx)
        if any(i["level"] == "block" for i in pre):
            rows[key] = {"verdict": "avoid", "score": None, "issues": pre,
                         "reasons": [i["text"] for i in pre
                                     if i["level"] == "block"]}
            continue
        # cheap screening fit - fewer restarts than the real thing
        f = fit_model(spec, x, y, ctx=ctx, n_restarts=3)
        fits.append(f)
        rows[key] = {"fit": f, "issues": list(pre) + list(f.issues)}

    ranking = {r["model_key"]: r for r in rank_models(fits, "AICc")}

    out = []
    for key in keys:
        spec = registry[key]
        row = rows[key]
        if row.get("verdict") == "avoid":
            out.append({"key": key, "name": tr(spec.name), "family": spec.family,
                        "n_params": spec.n_params, "verdict": "avoid",
                        "reasons": row["reasons"], "R2": None, "delta": None,
                        "rank": None})
            continue

        f = row["fit"]
        iss = row["issues"]
        rank = ranking.get(key)
        blocking = [i for i in iss if i["level"] == "block"]
        warning = [i for i in iss if i["level"] == "warn"]

        reasons, verdict = [], "usable"
        if not f.success:
            verdict, reasons = "avoid", [
                tr("The fit did not converge on these data.")]
        elif blocking:
            verdict = "avoid"
            reasons = [i["text"] for i in blocking]
        else:
            delta = rank["delta"] if rank else np.inf
            r2 = f.stats.get("R2", np.nan)
            # "Avoid" is reserved for a model that is out of its domain or that
            # genuinely fails to describe the data. A large delta-AICc alongside
            # an excellent R^2 means "another model is more efficient", not
            # "this model is wrong", and saying otherwise would be misleading.
            if r2 is not None and np.isfinite(r2) and r2 < 0.90:
                verdict = "avoid"
                reasons.append(tr(
                    "It reproduces only {pct:.0f}% of the variance in your "
                    "data (R² = {r2}), so it is not describing this system.",
                    pct=max(0.0, r2) * 100, r2=fmt(r2)))
            elif delta < 2:
                simpler = _simplest_within(rows, ranking, registry, 2.0)
                if simpler and spec.n_params > simpler[1]:
                    verdict = "usable"
                    reasons.append(tr(
                        "Fits as well as anything here (R² = {r2}), but {other} "
                        "matches it with only {np_other} parameters instead of "
                        "{np_this}. The extra parameters are not earning their "
                        "place, so prefer the simpler model unless you need "
                        "this one's specific physical meaning.",
                        r2=fmt(r2), other=simpler[0], np_other=simpler[1],
                        np_this=spec.n_params))
                else:
                    verdict = "recommend"
                    reasons.append(tr(
                        "Best-supported model for these data, and the most "
                        "parsimonious of the equally good ones (ΔAICc = "
                        "{delta}, R² = {r2}, {np} parameters).",
                        delta=fmt(delta), r2=fmt(r2), np=spec.n_params))
            elif delta < 10:
                verdict = "usable"
                reasons.append(tr(
                    "Describes the data well (R² = {r2}) but is ΔAICc = "
                    "{delta} behind the leading model, so it costs accuracy "
                    "or parameters without a compensating gain.",
                    r2=fmt(r2), delta=fmt(delta)))
            else:
                verdict = "usable"
                reasons.append(tr(
                    "Still reproduces the data (R² = {r2}), but at ΔAICc = "
                    "{delta} the evidence clearly favours another model. "
                    "Report it only if its physical interpretation is what "
                    "you specifically need.", r2=fmt(r2), delta=fmt(delta)))

        # physics-driven reasons layered on top of the statistics
        reasons.extend(_physics_notes(category, key, spec, shape, ctx))
        if verdict != "avoid" and warning:
            reasons.extend(i["text"] for i in warning[:2])
            if verdict == "recommend" and any(
                    i["code"] in ("no_plateau", "no_equilibrium") for i in warning):
                verdict = "usable"

        out.append({
            "key": key, "name": tr(spec.name), "family": spec.family,
            "n_params": spec.n_params, "verdict": verdict, "reasons": reasons,
            "R2": f.stats.get("R2") if f.success else None,
            "delta": rank["delta"] if rank else None,
            "rank": rank["rank"] if rank else None,
        })

    order = {"recommend": 0, "usable": 1, "avoid": 2}
    out.sort(key=lambda r: (order[r["verdict"]],
                            r["delta"] if r["delta"] is not None else 1e9))
    return {"shape": _clean_shape(shape), "models": out,
            "summary": _shape_summary(category, shape, ctx)}


def _simplest_within(rows, ranking, registry, delta_max):
    """The fewest-parameter model among those statistically tied for best.

    Standard practice when several models are indistinguishable on AICc is to
    report the simplest, not the one with the nominally lowest value.
    """
    best = None
    for key, row in rows.items():
        r = ranking.get(key)
        if not r or r["delta"] > delta_max:
            continue
        n = registry[key].n_params
        if best is None or n < best[1] or (n == best[1] and r["delta"] < best[2]):
            best = (registry[key].name, n, r["delta"])
    return best


def _clean_shape(d):
    return {k: (None if isinstance(v, float) and not np.isfinite(v) else v)
            for k, v in d.items()}


# --------------------------------------------------------------------------
# What the data shape implies, per model
# --------------------------------------------------------------------------

def _physics_notes(category, key, spec, s, ctx) -> list[str]:
    r = []
    if category == "isotherm":
        saturating = key in ("langmuir", "jovanovic", "sips", "toth", "khan",
                             "radke_prausnitz", "hill", "brouers_sotolongo",
                             "marczewski_jaroniec", "koble_corrigan",
                             "elovich_isotherm", "baudu", "vieth_sladek")
        if saturating and s["still_rising"]:
            r.append(tr("This model's capacity parameter is a saturation plateau, "
                     "and your data have not reached one, so q_max will be an "
                     "extrapolation well beyond the measured range."))
        if saturating and s["plateaus"]:
            r.append(tr("Your data reach a clear plateau, which is exactly what this "
                     "model's saturation capacity is meant to describe."))
        if key == "freundlich":
            if s["plateaus"]:
                r.append(tr("Freundlich has no plateau: it rises without limit: so "
                         "it cannot reproduce the flat region your data show, and "
                         "K_F must not be quoted as a capacity."))
            else:
                r.append(tr("Freundlich suits data that are still rising, as yours "
                         "are, because it makes no saturation assumption."))
        if key == "temkin":
            r.append(tr("Temkin is a mid-coverage model with no plateau and a "
                     "logarithmic divergence at low C_e; it is best kept for the "
                     "middle of a concentration series."))
        if key == "hill" and s.get("sigmoidal"):
            r.append(tr("Your isotherm looks sigmoidal, and Hill is one of the few "
                     "models here that can produce an S-shape; that is a genuine "
                     "reason to prefer it over Langmuir."))
        if key in ("langmuir", "sips", "toth") and s.get("sigmoidal"):
            r.append(tr("Your isotherm appears sigmoidal. This model is strictly "
                     "concave and cannot reproduce an inflection point."))
        if s["is_linear"] and key in ("langmuir", "sips", "toth", "hill"):
            r.append(tr(
                "Your data are close to a straight line through the origin "
                "(R² = {r2}). In the Henry's-law regime the affinity and "
                "capacity parameters become strongly correlated and neither "
                "is well determined.", r2=fmt(s["linear_R2"])))
        if spec.n_params >= 4 and s["n"] < 8:
            r.append(tr(
                "{np} parameters against {n} data points leaves very little "
                "to constrain them, so this model will fit almost anything at "
                "this sample size.", np=spec.n_params, n=s["n"]))
        if key in ("sips", "toth", "redlich_peterson", "marczewski_jaroniec") \
                and np.isfinite(s.get("slope_drift", np.nan)) \
                and abs(s["slope_drift"]) > 0.15:
            r.append(tr("The log–log slope changes noticeably from the dilute to the "
                     "concentrated end of your data, which is the signature of a "
                     "heterogeneous surface: the situation this model's extra "
                     "exponent exists to capture."))
    else:
        needs_eq = key in ("pfo", "pso", "avrami", "mixed_1_2", "nth_order",
                           "ritchie", "fractal_pfo", "film_diffusion",
                           "double_exponential", "crank")
        if needs_eq and s["still_rising"]:
            r.append(tr("This model fits an equilibrium capacity, and your run has "
                     "not equilibrated: q_e and the rate constant will trade off "
                     "against each other."))
        if needs_eq and s["equilibrated"]:
            r.append(tr("Your run reaches a clear plateau, so q_e is well defined."))
        if not s["well_sampled_early"]:
            r.append(tr(
                "Only {k} point(s) before half the uptake was reached, and "
                "rate constants are determined by that region.",
                k=s["n_early"]))
        if key == "elovich" and s["equilibrated"]:
            r.append(tr("Elovich rises logarithmically without limit, so it cannot "
                     "match the plateau in your data."))
        if key == "double_exponential":
            if s.get("two_stage"):
                r.append(tr("Your curve shows a distinct break between a fast and a "
                         "slow stage, which is the specific case this model exists "
                         "for."))
            else:
                r.append(tr("Your curve shows no clear two-stage break, so the second "
                         "exponential has little to explain."))
        if key in ("weber_morris",) and s.get("two_stage"):
            r.append(tr("A break in the q vs √t slope is visible in your data, the "
                     "multi-region analysis on the Diffusion tab is the right tool "
                     "for it."))
        if not s["monotonic"]:
            r.append(tr("Your uptake curve is not monotonic. Every kinetic model here "
                     "assumes uptake only increases, so check those points before "
                     "modelling."))
    return r


def _shape_summary(category, s, ctx) -> list[str]:
    """A short plain-language reading of what the raw data look like."""
    out = []
    if category == "isotherm":
        span = (tr("({d:.1f} decades)", d=s["decades"])
                if np.isfinite(s["decades"]) else "")
        out.append(tr(
            "You have {n} equilibrium points spanning C_e = {xlo} to {xhi} "
            "{span}, with q_e from {ylo} to {yhi}.",
            n=s["n"], xlo=fmt(s["x_min"]), xhi=fmt(s["x_max"]), span=span,
            ylo=fmt(s["y_min"]), yhi=fmt(s["y_max"])))
        if s["plateaus"]:
            out.append(tr("The isotherm **reaches a plateau**, the top third of the "
                       "concentration range adds little further uptake. Saturation "
                       "models (Langmuir, Sips, Tóth) can therefore give a capacity "
                       "that is measured rather than extrapolated."))
        elif s["still_rising"]:
            out.append(tr("The isotherm is **still rising steeply** at your highest "
                       "concentration. Nothing here determines a saturation "
                       "capacity, so treat any q_max as an extrapolation and prefer "
                       "models that do not assume a plateau."))
        else:
            out.append(tr("The isotherm is beginning to level off but has not fully "
                       "plateaued, so a fitted capacity is only moderately "
                       "constrained."))
        if np.isfinite(s.get("loglog_slope", np.nan)):
            sl = s["loglog_slope"]
            if sl < 0.5:
                verdict = tr("Well below 1, so adsorption is strongly "
                             "favourable and the surface is energetically "
                             "heterogeneous.")
            elif sl > 0.85:
                verdict = tr("Close to 1, so uptake is nearly proportional to "
                             "concentration. You may be in the linear "
                             "Henry's-law regime, where most isotherm models "
                             "become hard to distinguish.")
            else:
                verdict = tr("Between 0.5 and 1, the usual favourable range.")
            out.append(tr(
                "The overall log–log slope is {sl}, so the Freundlich 1/n is "
                "about {sl}. {verdict}", sl=fmt(sl), verdict=verdict))
        if s["is_linear"]:
            out.append(tr("**Caution:** your data are nearly a straight line through "
                       "the origin. In this regime almost every isotherm model will "
                       "fit well and they cannot be told apart; extend the "
                       "concentration range before claiming a mechanism."))
        if s.get("sigmoidal"):
            out.append(tr("The curve appears **sigmoidal** (uptake accelerates before "
                       "it saturates). Langmuir, Freundlich and Tóth are all "
                       "strictly concave and cannot reproduce that; Hill and BET can."))
    else:
        out.append(tr(
            "You have {n} time points from {tlo} to {thi}, reaching q = {q}.",
            n=s["n"], tlo=fmt(s["t_min"]), thi=fmt(s["t_max"]),
            q=fmt(s["q_max"])))
        if s["equilibrated"]:
            out.append(tr("The run **reaches equilibrium**; uptake is flat over the "
                       "final third: so q_e is directly measured and the models "
                       "that fit it are on solid ground."))
        elif s["still_rising"]:
            out.append(tr("Uptake is **still climbing** at your last time point. Every "
                       "model that fits q_e will be extrapolating, and because q_e "
                       "and the rate constant are correlated, both become "
                       "unreliable. Extend the contact time."))
        enough = (tr("That is enough to define the early, fast stage that "
                     "fixes the rate constant.")
                  if s["well_sampled_early"] else
                  tr("**That is too few.** Rate constants are determined "
                     "almost entirely by the early stage, so sample more "
                     "densely at short times."))
        out.append(tr(
            "{k} point(s) fall below half the final uptake. {enough}",
            k=s["n_early"], enough=enough))
        if s.get("two_stage"):
            out.append(tr(
                "The uptake rate against √t drops by a factor of {ratio} "
                "partway through, which indicates **two distinct stages**: "
                "typically fast external-surface adsorption followed by slower "
                "intraparticle diffusion. The Weber–Morris multi-region "
                "analysis and the double-exponential model are both worth "
                "running.", ratio=fmt(s.get("slope_ratio"))))
        if not s["monotonic"]:
            out.append(tr("**Your uptake curve decreases somewhere.** That breaks the "
                       "core assumption of every kinetic model here; check those "
                       "points for desorption or measurement error first."))
    return out
