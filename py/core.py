"""
AdsorpFit - core model specification framework, fitting engine and statistics.

Everything numerical in AdsorpFit flows through this module. It defines:

  * ParamSpec / ModelSpec   - declarative description of a model, its
                              parameters, units, physical meaning and bounds
  * fit_model()             - bounded non-linear least squares (SciPy TRF)
                              with a covariance-based uncertainty estimate
  * fit_linear()            - the classical linearised fit, kept as an option
  * statistics()            - the full error-function battery used in the
                              adsorption literature
  * rank_models()           - information-criterion based model selection

Design notes
------------
Non-linear regression is the default because linearising an adsorption model
distorts the error structure: least squares assumes the residuals are
independent and identically distributed on the *fitted* variable, and a
transform such as t/qt or 1/qe re-weights the points so that the fit is
dominated by whichever end of the data the transform happens to inflate.
The linear route is still implemented, because reviewers frequently ask for
it, but it is reported alongside the non-linear result so the two can be
compared directly.

References for the statistical treatment:
  Tran, H.N. et al. (2017) Water Research 120, 88-116.
  El-Khaiary, M.I. (2008) J. Hazard. Mater. 158, 73-87.
  Wang, J. & Guo, X. (2020) J. Hazard. Mater. 390, 122156.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np
from scipy.optimize import least_squares, curve_fit
from scipy import stats as sps

R_GAS = 8.314462618          # J / (mol K)
WATER_MOLARITY = 55.5        # mol / L, pure water at ~298 K


# --------------------------------------------------------------------------
# Declarative model description
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# Symbol formatting
# --------------------------------------------------------------------------

_GREEK = {
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma",
    "Δ": r"\Delta", "ε": r"\varepsilon", "θ": r"\theta",
    "ν": r"\nu", "σ": r"\sigma", "χ": r"\chi",
    "φ": r"\phi", "λ": r"\lambda", "ρ": r"\rho",
}
_SUBDIGIT = {"₀": "0", "₁": "1", "₂": "2", "₃": "3",
             "₄": "4", "₅": "5", "₆": "6", "₇": "7",
             "₈": "8", "₉": "9"}


def symbol_to_tex(sym: str) -> str:
    """Turn a parameter symbol into LaTeX for display.

    The symbols were written in four different notations as the model library
    grew: ASCII underscores (q_max), Unicode subscripts (k1 with a subscript
    one), bare letters (n, A, g) and Greek characters. They all rendered
    literally in the tables, so "q_max" appeared as typed. This normalises
    them to one form.

    A single-letter subscript stays italic, because it is a variable
    (K_L, n_T). A longer one is an abbreviation and is set upright
    (q_max, k_id, K_RP), which is the convention in the physical sciences.
    """
    s = sym or ""
    prime = ""
    while s.endswith("′") or s.endswith("'"):
        prime += "'"
        s = s[:-1]
    for u, d in _SUBDIGIT.items():
        if u in s:
            s = s.replace(u, "_" + d)

    if s in _GREEK:
        return _GREEK[s] + prime

    if "_" in s:
        base, sub = s.split("_", 1)
        base = _GREEK.get(base, base)
        parts = []
        for piece in sub.split(","):
            piece = piece.strip()
            upright = not ((len(piece) == 1 and piece.isalpha()) or piece.isdigit())
            parts.append(r"\mathrm{%s}" % piece if upright else piece)
        return "%s_{%s}%s" % (base, ",".join(parts), prime)

    return _GREEK.get(s, s) + prime


def issue(level: str, code: str, text: str) -> dict:
    """One applicability or validity finding.

    level is one of:
        "block"  the model cannot legitimately be applied to these data
        "warn"   it can be applied but the result needs a stated caveat
        "info"   worth knowing, not a defect
    """
    return {"level": level, "code": code, "text": text}


@dataclass
class ParamSpec:
    """One fitted parameter of a model."""

    key: str
    symbol: str                  # LaTeX-ish symbol for display, e.g. "q_m"
    unit: str                    # e.g. "mg g^-1"; "-" for dimensionless
    meaning: str                 # plain-language physical meaning
    lower: float = 0.0
    upper: float = np.inf
    guess: float = 1.0
    # optional callable(x, y) -> float producing a data-driven initial guess
    guess_fn: Callable | None = None
    # if set, the parameter is constrained to this range for physical reasons
    physical_note: str = ""
    # explicit LaTeX for display; derived from `symbol` when left blank
    tex: str = ""

    @property
    def symbol_tex(self) -> str:
        return self.tex or symbol_to_tex(self.symbol)

    def initial(self, x: np.ndarray, y: np.ndarray) -> float:
        if self.guess_fn is not None:
            try:
                g = float(self.guess_fn(x, y))
                if np.isfinite(g) and self.lower < g < self.upper:
                    return g
            except Exception:
                pass
        return float(np.clip(self.guess, self.lower + 1e-12,
                             self.upper if np.isfinite(self.upper) else 1e12))


@dataclass
class LinearForm:
    """Classical linearised form of a model, y* = a + b x*."""

    name: str                                     # e.g. "Type I"
    x_label: str
    y_label: str
    # transform(x, y, aux) -> (x_star, y_star); may return NaN for invalid pts
    transform: Callable
    # recover(slope, intercept, aux) -> dict of model parameters
    recover: Callable
    note: str = ""


@dataclass
class ModelSpec:
    """Full declarative description of one adsorption model."""

    key: str
    name: str
    category: str                                 # kinetics | isotherm | thermo
    func: Callable                                # func(x, *params) -> y
    params: list[ParamSpec]
    equation: str                                 # LaTeX body, no delimiters
    equation_plain: str                           # ASCII fallback
    citation: str
    year: str = ""
    assumptions: list[str] = field(default_factory=list)
    interpretation: Callable | None = None        # (fit, ctx) -> list[str]
    linear_forms: list[LinearForm] = field(default_factory=list)
    # models that need experimental context beyond (x, y)
    requires: list[str] = field(default_factory=list)
    family: str = ""                              # e.g. "2-parameter"
    notes: str = ""
    # domain(x, y, ctx) -> [issue]  : is this model applicable to these DATA,
    # judged before any fitting (e.g. Temkin cannot describe dilute data).
    domain: Callable | None = None
    # validity(params, x, y, ctx) -> [issue] : are the FITTED parameters inside
    # the model's own domain of definition over the measured range?
    validity: Callable | None = None
    # the range of x over which the model is mathematically defined, given the
    # fitted parameters: valid_range(params, ctx) -> (lo, hi) or None
    valid_range: Callable | None = None

    @property
    def n_params(self) -> int:
        return len(self.params)

    def p0(self, x, y) -> np.ndarray:
        return np.array([p.initial(x, y) for p in self.params], float)

    def bounds(self):
        return (np.array([p.lower for p in self.params], float),
                np.array([p.upper for p in self.params], float))


# --------------------------------------------------------------------------
# Error functions / goodness of fit
# --------------------------------------------------------------------------

def statistics(y_obs: np.ndarray, y_cal: np.ndarray, n_params: int) -> dict:
    """Return the full error-function battery used in adsorption papers.

    All quantities follow the definitions collected by Tran et al. (2017)
    and El-Khaiary (2008).  ``n_params`` is needed for the degree-of-freedom
    corrections (adjusted R^2, reduced chi^2, AIC/BIC).
    """
    y_obs = np.asarray(y_obs, float)
    y_cal = np.asarray(y_cal, float)
    n = y_obs.size
    resid = y_obs - y_cal
    dof = max(n - n_params, 1)

    sse = float(np.sum(resid ** 2))
    sst = float(np.sum((y_obs - y_obs.mean()) ** 2))
    mse = sse / n
    rmse = math.sqrt(mse)

    r2 = 1.0 - sse / sst if sst > 0 else np.nan
    # adjusted R^2 penalises extra parameters; the correct denominator is
    # n - p (not n - p - 1) when p already counts the model's own constant.
    adj_r2 = 1.0 - (1.0 - r2) * (n - 1) / dof if sst > 0 and dof > 0 else np.nan

    with np.errstate(divide="ignore", invalid="ignore"):
        safe = np.where(np.abs(y_cal) > 1e-12, y_cal, np.nan)
        rel = resid / safe
        chi2 = float(np.nansum(resid ** 2 / safe))
        are = 100.0 / n * float(np.nansum(np.abs(rel)))
        hybrid = 100.0 / dof * float(np.nansum(resid ** 2 / safe))
        mpsd = 100.0 * math.sqrt(float(np.nansum(rel ** 2)) / dof)
        ssre = float(np.nansum(rel ** 2))

    eabs = float(np.sum(np.abs(resid)))
    mae = eabs / n
    # standard deviation of relative errors (Delta q, %)
    with np.errstate(divide="ignore", invalid="ignore"):
        dq = 100.0 * math.sqrt(
            float(np.nansum(((y_obs - y_cal) / np.where(y_obs != 0, y_obs, np.nan)) ** 2)) / dof
        )

    # Information criteria (Gaussian likelihood, variance profiled out)
    if sse > 0:
        aic = n * math.log(sse / n) + 2 * n_params
        # small-sample correction; guard the pole at n = p + 1
        denom = n - n_params - 1
        aicc = aic + (2 * n_params * (n_params + 1) / denom) if denom > 0 else np.inf
        bic = n * math.log(sse / n) + n_params * math.log(n)
    else:
        aic = aicc = bic = -np.inf

    return {
        "n": n, "n_params": n_params, "dof": dof,
        "SSE": sse, "MSE": mse, "RMSE": rmse,
        "R2": r2, "adj_R2": adj_r2,
        "chi2": chi2, "chi2_red": chi2 / dof,
        "ARE": are, "HYBRID": hybrid, "MPSD": mpsd, "SSRE": ssre,
        "EABS": eabs, "MAE": mae, "delta_q": dq,
        "AIC": aic, "AICc": aicc, "BIC": bic,
    }


# --------------------------------------------------------------------------
# Fit result container
# --------------------------------------------------------------------------

@dataclass
class FitResult:
    model_key: str
    model_name: str
    method: str                      # "nonlinear" | "linear:<form>"
    success: bool
    params: dict                     # key -> value
    stderr: dict                     # key -> 1 sigma standard error
    ci95: dict                       # key -> (low, high)
    tvalue: dict                     # key -> parameter / stderr
    pvalue: dict
    stats: dict
    x: np.ndarray
    y: np.ndarray
    y_cal: np.ndarray
    residuals: np.ndarray
    message: str = ""
    derived: dict = field(default_factory=dict)   # e.g. R_L, E, h
    warnings: list = field(default_factory=list)
    issues: list = field(default_factory=list)    # applicability / validity findings

    def curve(self, n: int = 300, x_min=None, x_max=None):
        """Dense smooth curve for plotting."""
        lo = float(np.min(self.x)) if x_min is None else x_min
        hi = float(np.max(self.x)) if x_max is None else x_max
        lo = min(lo, 0.0) if lo > 0 else lo
        xs = np.linspace(lo, hi, n)
        return xs, self._fn(xs)

    _fn: Callable | None = None


# --------------------------------------------------------------------------
# The fitting engines
# --------------------------------------------------------------------------

def fit_model(spec: ModelSpec,
              x: Sequence[float],
              y: Sequence[float],
              ctx: dict | None = None,
              weights: str = "none",
              p0: Sequence[float] | None = None,
              n_restarts: int = 6,
              loss: str = "linear",
              max_nfev: int = 20000) -> FitResult:
    """Bounded non-linear least squares fit of ``spec`` to (x, y).

    ``weights`` selects the residual weighting:
        "none"      ordinary least squares            w_i = 1
        "relative"  minimise relative error           w_i = 1 / y_i
        "sqrt"      Poisson-like                      w_i = 1 / sqrt(y_i)

    Multi-start is used because several adsorption models (Toth, Baudu,
    Fritz-Schlunder, Avrami) have shallow, strongly correlated optima and a
    single start from a naive guess lands in a local minimum often enough to
    matter.
    """
    ctx = ctx or {}
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]

    if x.size < spec.n_params:
        return _failed(spec, x, y,
                       f"Need at least {spec.n_params} points to fit "
                       f"{spec.n_params} parameters; got {x.size}.")

    if weights == "relative":
        w = 1.0 / np.where(np.abs(y) > 1e-12, np.abs(y), 1e-12)
    elif weights == "sqrt":
        w = 1.0 / np.sqrt(np.where(np.abs(y) > 1e-12, np.abs(y), 1e-12))
    else:
        w = np.ones_like(y)

    def model_fn(xv, theta):
        return spec.func(xv, *theta, **_ctx_kwargs(spec, ctx))

    def resid(theta):
        try:
            pred = model_fn(x, theta)
        except Exception:
            return np.full_like(y, 1e6)
        pred = np.asarray(pred, float)
        bad = ~np.isfinite(pred)
        if bad.any():
            pred = np.where(bad, 1e6, pred)
        return (pred - y) * w

    lo, hi = spec.bounds()
    starts = []
    base = np.asarray(p0, float) if p0 is not None else spec.p0(x, y)
    starts.append(np.clip(base, lo + 1e-12, hi))
    rng = np.random.default_rng(12345)
    for _ in range(max(0, n_restarts - 1)):
        # log-uniform jitter around the base guess, respecting bounds
        jit = base * np.exp(rng.normal(0.0, 1.1, size=base.size))
        hi_c = np.where(np.isfinite(hi), hi, base * 1e6 + 1e6)
        starts.append(np.clip(jit, lo + 1e-12, hi_c))

    best = None
    msgs = []
    for s in starts:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                sol = least_squares(resid, s, bounds=(lo, hi), loss=loss,
                                    max_nfev=max_nfev, x_scale="jac")
            if best is None or sol.cost < best.cost:
                best = sol
        except Exception as exc:                       # pragma: no cover
            msgs.append(str(exc))
            continue

    if best is None:
        return _failed(spec, x, y, "Optimiser failed from every start. "
                                   + ("; ".join(msgs[:2])))

    theta = best.x
    y_cal = np.asarray(model_fn(x, theta), float)
    st = statistics(y, y_cal, spec.n_params)

    # Covariance from the Gauss-Newton approximation J^T J, scaled by the
    # residual variance.  This is the same estimator curve_fit reports.
    stderr = _stderr_from_jac(best.jac, best.fun, x.size, spec.n_params)

    params = {p.key: float(v) for p, v in zip(spec.params, theta)}
    se = {p.key: float(s) for p, s in zip(spec.params, stderr)}
    tcrit = sps.t.ppf(0.975, st["dof"])
    ci = {k: (params[k] - tcrit * se[k], params[k] + tcrit * se[k])
          if np.isfinite(se[k]) else (np.nan, np.nan) for k in params}
    tval = {k: (params[k] / se[k] if se[k] > 0 else np.nan) for k in params}
    pval = {k: (float(2 * (1 - sps.t.cdf(abs(tval[k]), st["dof"])))
                if np.isfinite(tval[k]) else np.nan) for k in params}

    warns = []
    for p in spec.params:
        v = params[p.key]
        if np.isfinite(se[p.key]) and se[p.key] > abs(v):
            warns.append(
                f"{p.symbol} is not resolved by these data: its standard error "
                f"({se[p.key]:.3g}) exceeds the estimate itself ({v:.3g}). "
                f"Treat this parameter as indeterminate."
            )
        if np.isfinite(p.upper) and abs(v - p.upper) < 1e-6 * max(1.0, abs(p.upper)):
            warns.append(f"{p.symbol} hit its upper bound ({p.upper:g}) - "
                         f"the optimum lies outside the physically allowed range.")
        if abs(v - p.lower) < 1e-9 and p.lower == 0.0:
            warns.append(f"{p.symbol} collapsed to zero, which usually means "
                         f"this model term is not supported by the data.")

    issues = list(check_domain(spec, x, y, ctx))
    specific = []
    if spec.validity is not None:
        try:
            specific = list(spec.validity(params, x, y, ctx) or [])
        except Exception:
            specific = []
    issues.extend(specific)
    # The generic negative-prediction check is a safety net. When a model has
    # already explained the same failure in its own terms, saying it twice just
    # dilutes the message.
    explained = any(i["code"].endswith("_threshold") or i["code"] == "baudu_domain"
                    for i in specific)
    for i in _physical_prediction_check(spec, params, x, y, y_cal, ctx):
        if i["code"] == "negative_prediction" and explained:
            continue
        issues.append(i)

    res = FitResult(
        model_key=spec.key, model_name=spec.name, method="nonlinear",
        success=True, params=params, stderr=se, ci95=ci,
        tvalue=tval, pvalue=pval, stats=st,
        x=x, y=y, y_cal=y_cal, residuals=y - y_cal,
        message=f"converged in {best.nfev} function evaluations",
        warnings=warns, issues=issues,
    )
    res._fn = lambda xv: np.asarray(model_fn(np.asarray(xv, float), theta), float)
    return res


def fit_linear(spec: ModelSpec, form: LinearForm,
               x: Sequence[float], y: Sequence[float],
               ctx: dict | None = None) -> FitResult:
    """Classical linearised fit: ordinary least squares on transformed axes.

    Reported for comparison only.  The R^2 returned is the R^2 *of the
    transformed variables*, which is what the literature quotes and is
    exactly why linearised fits look deceptively good.  The error battery is
    additionally recomputed on the original q scale so the two can be
    compared honestly.
    """
    ctx = ctx or {}
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    with np.errstate(all="ignore"):
        xs, ys = form.transform(x, y, ctx)
    xs = np.asarray(xs, float)
    ys = np.asarray(ys, float)
    ok = np.isfinite(xs) & np.isfinite(ys)
    if ok.sum() < 2:
        return _failed(spec, x, y, "Linearisation produced fewer than two "
                                   "valid points (log or reciprocal of a "
                                   "non-positive value).")

    # A transform can collapse the x axis to a single value (the Scatchard
    # form of Langmuir does exactly that on flat data), and SciPy raises
    # rather than returning a degenerate line. Catch it here: one unusable
    # linearisation must not take down the whole request.
    if np.ptp(xs[ok]) == 0:
        return _failed(spec, x, y,
                       f"The {form.name} transform maps every point to the same "
                       f"x value, so no line can be fitted through them. This "
                       f"happens when the data are flat; the non-linear fit is "
                       f"unaffected.")
    try:
        lr = sps.linregress(xs[ok], ys[ok])
    except Exception as exc:
        return _failed(spec, x, y,
                       f"The {form.name} linearisation could not be fitted: {exc}")
    try:
        params = form.recover(lr.slope, lr.intercept, ctx)
    except Exception as exc:
        return _failed(spec, x, y, f"Could not recover parameters: {exc}")

    theta = [params.get(p.key, np.nan) for p in spec.params]
    try:
        y_cal = np.asarray(spec.func(x, *theta, **_ctx_kwargs(spec, ctx)), float)
    except Exception:
        y_cal = np.full_like(y, np.nan)

    st = statistics(y, y_cal, spec.n_params)
    st["R2_linear"] = lr.rvalue ** 2
    st["slope"] = lr.slope
    st["intercept"] = lr.intercept
    st["slope_se"] = lr.stderr
    st["intercept_se"] = lr.intercept_stderr
    st["n_points_used"] = int(ok.sum())

    warns = []
    if ok.sum() < xs.size:
        warns.append(
            f"{xs.size - ok.sum()} of {xs.size} points were discarded by the "
            f"{form.name} linearisation (the transform is undefined for them). "
            f"The non-linear fit uses all points."
        )
    if np.isfinite(st["R2"]) and np.isfinite(st["R2_linear"]) \
            and st["R2_linear"] - st["R2"] > 0.05:
        warns.append(
            f"The linear plot reports R^2 = {st['R2_linear']:.4f}, but the "
            f"same parameters reproduce the raw q data with only R^2 = "
            f"{st['R2']:.4f}. The linearisation is flattering the fit."
        )

    res = FitResult(
        model_key=spec.key, model_name=spec.name,
        method=f"linear:{form.name}", success=True,
        params={p.key: float(v) for p, v in zip(spec.params, theta)},
        stderr={p.key: np.nan for p in spec.params},
        ci95={p.key: (np.nan, np.nan) for p in spec.params},
        tvalue={p.key: np.nan for p in spec.params},
        pvalue={p.key: np.nan for p in spec.params},
        stats=st, x=x, y=y, y_cal=y_cal, residuals=y - y_cal,
        message=f"{form.name}: {form.y_label} vs {form.x_label}",
        warnings=warns,
    )
    res.derived["linear_x"] = xs
    res.derived["linear_y"] = ys
    res.derived["linear_mask"] = ok
    res._fn = lambda xv: np.asarray(
        spec.func(np.asarray(xv, float), *theta, **_ctx_kwargs(spec, ctx)), float)
    return res


# --------------------------------------------------------------------------
# Model selection
# --------------------------------------------------------------------------

def rank_models(results: Sequence[FitResult], criterion: str = "AICc") -> list[dict]:
    """Rank fitted models and compute Akaike weights.

    Akaike weights give the probability that each candidate is the best
    approximating model *within the set tested* - which is the honest way to
    compare a 2-parameter model against a 4-parameter one.  Comparing raw
    R^2 across models of different parameter count, as most papers do,
    always favours the model with more parameters.
    """
    ok = [r for r in results if r.success and np.isfinite(r.stats.get(criterion, np.nan))]
    if not ok:
        return []
    vals = np.array([r.stats[criterion] for r in ok], float)
    best = vals.min()
    delta = vals - best
    if criterion in ("AIC", "AICc", "BIC"):
        wl = np.exp(-0.5 * delta)
        weights = wl / wl.sum()
    else:
        weights = np.full(delta.size, np.nan)

    order = np.argsort(delta)
    out = []
    for rank, i in enumerate(order, start=1):
        r = ok[i]
        out.append({
            "rank": rank,
            "model_key": r.model_key,
            "model_name": r.model_name,
            "criterion": criterion,
            "value": float(vals[i]),
            "delta": float(delta[i]),
            "weight": float(weights[i]),
            "R2": r.stats["R2"],
            "adj_R2": r.stats["adj_R2"],
            "RMSE": r.stats["RMSE"],
            "n_params": r.stats["n_params"],
            "evidence": ("best model in this set" if rank == 1
                         else _evidence_phrase(float(delta[i]))),
        })
    return out


def _evidence_phrase(delta: float) -> str:
    """Burnham & Anderson's rule of thumb for Delta-AIC."""
    if delta < 2:
        return "substantial support - indistinguishable from the best model"
    if delta < 4:
        return "strong support"
    if delta < 7:
        return "considerably less support"
    if delta < 10:
        return "weak support"
    return "essentially no support"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def terminal_slope_ratio(x, y):
    """How steeply is the curve still climbing at the end, relative to overall?

    Measuring the rise over the last few points is unreliable: with only two
    or three points in the window, even a curve that is plainly still growing
    (q proportional to sqrt(t), say) shows a small rise and looks settled.
    Comparing the final slope against the mean slope is the honest test,
    because at true equilibrium the final slope goes to zero whatever the
    sampling.  Returns ~0 at equilibrium and ~1 for a straight line.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    o = np.argsort(x)
    x, y = x[o], y[o]
    if x.size < 4 or x[-1] <= x[0]:
        return 0.0
    mean_slope = (y[-1] - y[0]) / (x[-1] - x[0])
    if abs(mean_slope) < 1e-12:
        return 0.0
    # slope over the final quarter of the measured range
    cut = x[0] + 0.75 * (x[-1] - x[0])
    m = x >= cut
    if m.sum() < 2:
        m = np.zeros_like(x, bool)
        m[-3:] = True
    xs, ys = x[m], y[m]
    if xs[-1] <= xs[0]:
        return 0.0
    final_slope = float(np.polyfit(xs, ys, 1)[0])
    return float(abs(final_slope / mean_slope))


def check_domain(spec: ModelSpec, x, y, ctx: dict | None = None) -> list[dict]:
    """Applicability of a model to a dataset, judged before fitting.

    Two layers: generic checks that apply to every model, then the model's
    own ``domain`` hook.  This is what stops a model being fitted to data it
    cannot represent - the failure mode that produces a respectable-looking
    R^2 alongside physically impossible predictions.
    """
    ctx = ctx or {}
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    out: list[dict] = []

    n = x.size
    p = spec.n_params
    if n < p:
        out.append(issue("block", "too_few_points",
                         f"{n} data points cannot determine {p} parameters."))
    elif n < p + 2:
        out.append(issue("warn", "few_points",
                         f"Only {n} points for {p} parameters leaves {n - p} "
                         f"degrees of freedom. The fit will look excellent "
                         f"because it is nearly interpolating, and the "
                         f"confidence intervals will be very wide."))

    if np.any(y < 0):
        out.append(issue("warn", "negative_y",
                         f"{int(np.sum(y < 0))} of your q values are negative. "
                         f"A negative uptake usually means the measured "
                         f"equilibrium concentration exceeded the initial one - "
                         f"check for desorption, evaporation or a calibration "
                         f"offset before modelling."))
    if np.any(x < 0):
        out.append(issue("block", "negative_x",
                         "Negative concentrations or times cannot be modelled."))

    if len(np.unique(x)) < len(x):
        out.append(issue("info", "duplicate_x",
                         "Some x values are repeated. That is fine for replicate "
                         "measurements, but each replicate is weighted as an "
                         "independent point."))

    if spec.domain is not None:
        try:
            out.extend(spec.domain(x, y, ctx) or [])
        except Exception:
            pass
    return out


def _physical_prediction_check(spec, params, x, y, y_cal, ctx) -> list[dict]:
    """Does the fitted model predict impossible values where you measured?

    A model can reach a high R^2 while predicting a negative loading at one
    end of the range - the Temkin equation on dilute data is the standard
    example, because it diverges to -infinity as Ce -> 0.  Nothing in the
    least-squares objective forbids this, so it has to be checked separately.
    """
    out = []
    y_cal = np.asarray(y_cal, float)
    neg = np.asarray(y_cal < 0).sum()
    if neg and np.all(np.asarray(y) >= 0):
        worst = float(np.min(y_cal))
        where = np.asarray(x)[np.argmin(y_cal)]
        rng = spec.valid_range(params, ctx) if spec.valid_range else None
        extra = ""
        if rng is not None:
            lo, hi = rng
            if lo is not None and np.isfinite(lo):
                extra = (f" With these parameters the model is only defined for "
                         f"x > {fmt(lo)}; ")
                below = int(np.sum(np.asarray(x) < lo))
                if below:
                    extra += f"{below} of your {len(x)} points lie below that."
            elif hi is not None and np.isfinite(hi):
                extra = (f" With these parameters the model is only defined for "
                         f"x < {fmt(hi)}.")
        out.append(issue(
            "block", "negative_prediction",
            f"This model predicts a NEGATIVE q of {fmt(worst)} at x = {fmt(where)}, "
            f"which is physically impossible ({neg} of {len(x)} fitted points are "
            f"affected).{extra} The fit statistics are therefore meaningless no "
            f"matter how good R² looks - do not report these parameters."))

    nonfinite = int(np.sum(~np.isfinite(y_cal)))
    if nonfinite:
        out.append(issue("block", "nonfinite_prediction",
                         f"The model is undefined at {nonfinite} of your data "
                         f"points, so those points contributed nothing to the fit."))
    return out


def _ctx_kwargs(spec: ModelSpec, ctx: dict) -> dict:
    """Pass only the context values this model actually declares."""
    return {k: ctx[k] for k in spec.requires if k in ctx}


def _stderr_from_jac(jac, fun, n, p) -> np.ndarray:
    """1-sigma parameter standard errors from the least-squares Jacobian."""
    try:
        _, s, VT = np.linalg.svd(jac, full_matrices=False)
        tol = np.finfo(float).eps * max(jac.shape) * (s[0] if s.size else 0.0)
        s = s[s > tol]
        VT = VT[:s.size]
        pcov = np.dot(VT.T / s ** 2, VT)
        dof = max(n - p, 1)
        s_sq = float(np.sum(fun ** 2)) / dof
        pcov = pcov * s_sq
        se = np.sqrt(np.diag(pcov))
        out = np.full(p, np.nan)
        out[:se.size] = se
        return out
    except Exception:
        return np.full(p, np.nan)


def _failed(spec: ModelSpec, x, y, msg: str) -> FitResult:
    nan = {p.key: np.nan for p in spec.params}
    return FitResult(
        model_key=spec.key, model_name=spec.name, method="nonlinear",
        success=False, params=dict(nan), stderr=dict(nan),
        ci95={k: (np.nan, np.nan) for k in nan},
        tvalue=dict(nan), pvalue=dict(nan),
        stats=statistics(y, np.full_like(y, np.nan), spec.n_params)
        if len(y) else {},
        x=np.asarray(x, float), y=np.asarray(y, float),
        y_cal=np.full_like(np.asarray(y, float), np.nan),
        residuals=np.full_like(np.asarray(y, float), np.nan),
        message=msg,
    )


def fmt(value: float, sig: int = 4) -> str:
    """Format a number the way a journal table would."""
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "n.d."
    a = abs(value)
    if a == 0:
        return "0"
    if a >= 1e5 or a < 1e-3:
        return f"{value:.{sig - 1}e}"
    return f"{value:.{max(0, sig - 1 - int(math.floor(math.log10(a))))}f}"
