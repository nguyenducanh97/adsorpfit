"""
AdsorpFit - adsorption kinetic models.

x = t, contact time (min unless noted)
y = qt, loading at time t (mg/g)

The models are grouped the way Wang & Guo (2020) classify them:

  * adsorption reaction models  - PFO, PSO, Elovich, nth-order, Ritchie,
                                  mixed 1,2-order, Avrami
  * diffusion models            - Weber-Morris, Boyd, film diffusion,
                                  Crank/homogeneous surface diffusion,
                                  Vermeulen, Bangham
  * empirical models            - fractional power, double exponential

References:
  Wang, J. & Guo, X. (2020) J. Hazard. Mater. 390, 122156.
  Tran, H.N. et al. (2017) Water Research 120, 88-116.
  Simonin, J.-P. (2016) Chem. Eng. J. 300, 254-263.
"""

from __future__ import annotations

import numpy as np

from core import ModelSpec, ParamSpec, LinearForm, R_GAS, fmt, issue


# --------------------------------------------------------------------------
# guess helpers
# --------------------------------------------------------------------------

def _qe_guess(t, q):
    """Equilibrium loading: mean of the plateau region (last third of data)."""
    if len(q) == 0:
        return 1.0
    k = max(1, len(q) // 3)
    return float(np.mean(np.sort(q)[-k:])) * 1.02 + 1e-9


def _k1_guess(t, q):
    """PFO rate constant from the time to reach ~63% of equilibrium."""
    qe = _qe_guess(t, q)
    target = 0.632 * qe
    i = int(np.argmin(np.abs(q - target)))
    tau = float(t[i])
    return 1.0 / tau if tau > 0 else 0.05


def _k2_guess(t, q):
    qe = _qe_guess(t, q)
    k1 = _k1_guess(t, q)
    return k1 / qe if qe > 0 else 0.01


def _safe_pow(base, expo):
    base = np.clip(np.asarray(base, float), 1e-300, 1e300)
    return np.power(base, expo)


# --------------------------------------------------------------------------
# Adsorption reaction models
# --------------------------------------------------------------------------

def _pfo(t, qe, k1):
    t = np.clip(np.asarray(t, float), 0, None)
    return qe * (1.0 - np.exp(-k1 * t))


def _interp_pfo(f, ctx):
    qe = f.params["qe"]; k1 = f.params["k1"]
    t_half = np.log(2.0) / k1 if k1 > 0 else np.nan
    t95 = np.log(20.0) / k1 if k1 > 0 else np.nan
    f.derived["t_half"] = t_half
    f.derived["t_95"] = t95
    out = [
        f"The calculated equilibrium capacity is q_e,cal = {fmt(qe)} mg/g and the "
        f"pseudo-first-order rate constant is k₁ = {fmt(k1)} min⁻¹.",
        f"k₁ sets the timescale of uptake: the half-time is t₁/₂ = ln2/k₁ = "
        f"{fmt(t_half)} min, and 95% of equilibrium is reached at about "
        f"{fmt(t95)} min. Those numbers, not k₁ itself, are what a column or "
        f"batch reactor design actually needs.",
        "Lagergren's model assumes the rate of uptake is proportional to the number "
        "of *unoccupied* sites, (q_e − q_t). Mechanistically that corresponds to "
        "adsorption controlled by physisorption onto a surface where the driving "
        "force is simply the remaining free capacity; it does not imply a "
        "first-order chemical reaction.",
    ]
    q_obs = float(np.max(f.y))
    if q_obs > 0:
        diff = 100.0 * abs(qe - q_obs) / q_obs
        if diff > 15:
            out.append(
                f"Consistency warning: the fitted q_e,cal ({fmt(qe)} mg/g) differs from "
                f"your highest measured loading ({fmt(q_obs)} mg/g) by {diff:.0f}%. "
                f"A PFO fit whose q_e,cal disagrees badly with q_e,exp is the "
                f"classic sign that the model is wrong for these data, no matter "
                f"how good R² looks. Compare q_e,cal against q_e,exp for every "
                f"kinetic model you report: this check catches more bad fits than "
                f"R² does."
            )
        else:
            out.append(
                f"q_e,cal ({fmt(qe)} mg/g) agrees with the observed plateau "
                f"({fmt(q_obs)} mg/g) to within {diff:.0f}%, which supports the model."
            )
    out.append(
        "PFO is generally the better description of the *early* stage of "
        "adsorption and tends to underpredict the approach to equilibrium. If it "
        "fits your first few points but drifts later, that pattern is expected "
        "rather than surprising."
    )
    return out


PFO = ModelSpec(
    key="pfo", name="Pseudo-first-order (Lagergren)", category="kinetics",
    family="reaction model", func=_pfo,
    equation=r"q_t = q_e\left(1 - e^{-k_1 t}\right)",
    equation_plain="qt = qe*(1 - exp(-k1*t))",
    citation="Lagergren, S. (1898) Kungliga Svenska Vetenskapsakademiens Handlingar 24, 1-39.",
    year="1898",
    params=[
        ParamSpec("qe", "q_e,cal", "mg g⁻¹",
                  "Calculated equilibrium capacity. Compare it against the "
                  "experimental q_e: disagreement condemns the fit.",
                  lower=1e-12, guess_fn=_qe_guess),
        ParamSpec("k1", "k₁", "min⁻¹",
                  "Pseudo-first-order rate constant. Sets the uptake timescale: "
                  "t₁/₂ = ln2/k₁.", lower=1e-12, guess_fn=_k1_guess),
    ],
    assumptions=[
        "The uptake rate is proportional to the number of unoccupied sites, "
        "d q_t/dt = k₁(q_e − q_t).",
        "Usually describes the initial, fast stage of adsorption best.",
        "Applies when adsorption is not limited by intraparticle diffusion.",
        "Does NOT mean the process is a first-order chemical reaction.",
    ],
    interpretation=_interp_pfo,
    linear_forms=[
        LinearForm("ln(qe−qt) vs t", "t", "ln(qe − qt)",
                   lambda x, y, c: (
                       x,
                       np.log(np.where(c.get("qe_exp", np.max(y) * 1.02) - y > 0,
                                       c.get("qe_exp", np.max(y) * 1.02) - y, np.nan))),
                   lambda s, i, c: {"qe": np.exp(i), "k1": -s},
                   note="Requires q_e to be assumed in advance, which is the "
                        "model's weakest point: the answer depends on a value "
                        "you had to guess."),
    ],
)


def _pso(t, qe, k2):
    t = np.clip(np.asarray(t, float), 0, None)
    return (k2 * qe * qe * t) / (1.0 + k2 * qe * t)


def _interp_pso(f, ctx):
    qe = f.params["qe"]; k2 = f.params["k2"]
    h = k2 * qe ** 2
    t_half = 1.0 / (k2 * qe) if (k2 > 0 and qe > 0) else np.nan
    f.derived["h_initial_rate"] = h
    f.derived["t_half"] = t_half
    out = [
        f"q_e,cal = {fmt(qe)} mg/g and k₂ = {fmt(k2)} g mg⁻¹ min⁻¹.",
        f"The initial adsorption rate is h = k₂·q_e² = {fmt(h)} mg g⁻¹ min⁻¹, the "
        f"slope of uptake at t = 0, and the most directly comparable number between "
        f"experiments. The half-time is t₁/₂ = 1/(k₂q_e) = {fmt(t_half)} min.",
        "The pseudo-second-order model assumes the rate depends on the *square* of "
        "the number of free sites, d q_t/dt = k₂(q_e − q_t)². It is conventionally "
        "read as evidence that chemisorption, meaning valency forces through sharing or "
        "exchange of electrons: controls the rate.",
    ]
    q_obs = float(np.max(f.y))
    if q_obs > 0:
        diff = 100.0 * abs(qe - q_obs) / q_obs
        out.append(
            f"q_e,cal vs q_e,exp: {fmt(qe)} vs {fmt(q_obs)} mg/g ({diff:.0f}% apart)."
            + (" Good agreement." if diff <= 10 else
               " This gap is large enough to question the fit.")
        )
    out.append(
        "Two cautions that the literature routinely omits. First, PSO fits almost "
        "every batch dataset well, because its algebraic form happens to match the "
        "shape of a saturating curve, so a high R² for PSO is weak evidence of "
        "chemisorption, not strong evidence. Second, k₂ is not a true constant: it "
        "varies systematically with initial concentration, adsorbent dose and "
        "particle size, so k₂ values are only comparable between experiments run "
        "under identical conditions."
    )
    c0 = ctx.get("C0")
    if c0:
        out.append(
            f"Because your data were collected at C₀ = {c0} mg/L, the k₂ reported here "
            f"belongs to that concentration only. To claim a concentration-independent "
            f"mechanism you would need k₂ measured across several C₀ values and shown "
            f"to be constant: which it usually is not."
        )
    return out


PSO = ModelSpec(
    key="pso", name="Pseudo-second-order (Ho & McKay)", category="kinetics",
    family="reaction model", func=_pso,
    equation=r"q_t = \frac{k_2 q_e^2 t}{1 + k_2 q_e t}",
    equation_plain="qt = k2*qe^2*t / (1 + k2*qe*t)",
    citation="Ho, Y.S. & McKay, G. (1999) Process Biochem. 34, 451-465.",
    year="1999",
    params=[
        ParamSpec("qe", "q_e,cal", "mg g⁻¹", "Calculated equilibrium capacity.",
                  lower=1e-12, guess_fn=_qe_guess),
        ParamSpec("k2", "k₂", "g mg⁻¹ min⁻¹",
                  "Pseudo-second-order rate constant. Not a true constant: it "
                  "varies with C₀, dose and particle size.",
                  lower=1e-14, guess_fn=_k2_guess),
    ],
    assumptions=[
        "The uptake rate is proportional to the square of the number of "
        "unoccupied sites, d q_t/dt = k₂(q_e − q_t)².",
        "Conventionally interpreted as rate-limiting chemisorption.",
        "Describes the whole uptake curve including the approach to equilibrium.",
        "k₂ depends on experimental conditions, so it is not transferable.",
    ],
    interpretation=_interp_pso,
    linear_forms=[
        LinearForm("Type 1: t/qt vs t", "t", "t/qt",
                   lambda x, y, c: (x, np.where(y > 0, x / np.where(y > 0, y, np.nan), np.nan)),
                   lambda s, i, c: {"qe": 1.0 / s if s else np.nan,
                                    "k2": (s ** 2 / i) if i else np.nan},
                   note="By far the most used form: and the reason PSO appears to "
                        "fit everything. Plotting t/qt against t builds a spurious "
                        "correlation because t appears on both axes, so R² is high "
                        "even for data the model does not describe."),
        LinearForm("Type 2: 1/qt vs 1/t", "1/t", "1/qt",
                   lambda x, y, c: (np.where(x > 0, 1.0 / np.where(x > 0, x, np.nan), np.nan),
                                    np.where(y > 0, 1.0 / np.where(y > 0, y, np.nan), np.nan)),
                   lambda s, i, c: {"qe": 1.0 / i if i else np.nan,
                                    "k2": (i ** 2 / s) if s else np.nan}),
        LinearForm("Type 4: qt/t vs qt", "qt", "qt/t",
                   lambda x, y, c: (y, np.where(x > 0, y / np.where(x > 0, x, np.nan), np.nan)),
                   lambda s, i, c: {"qe": -i / s if s else np.nan,
                                    "k2": (s ** 2 / i) if i else np.nan}),
    ],
)


def _elovich(t, alpha, beta):
    t = np.clip(np.asarray(t, float), 0, None)
    return (1.0 / beta) * np.log1p(alpha * beta * t)


def _interp_elovich(f, ctx):
    a = f.params["alpha"]; b = f.params["beta"]
    out = [
        f"α = {fmt(a)} mg g⁻¹ min⁻¹ is the initial adsorption rate, the uptake rate "
        f"when the surface is still bare.",
        f"β = {fmt(b)} g mg⁻¹ is the desorption constant, related to the extent of "
        f"surface coverage and the activation energy for chemisorption. 1/β = "
        f"{fmt(1.0 / b if b else np.nan)} mg/g indicates how much the surface can "
        f"take up before the rate falls off appreciably.",
        "The Elovich equation assumes the activation energy for adsorption rises "
        "*linearly* with coverage. That is the behaviour of a genuinely "
        "heterogeneous surface undergoing chemisorption: the strongest sites are "
        "consumed first, so each additional molecule faces a higher barrier.",
        "A good Elovich fit is one of the more specific pieces of evidence for a "
        "heterogeneous surface, because the model has no plateau and cannot mimic a "
        "simple saturating curve the way PSO can.",
    ]
    if a * b > 0:
        out.append(
            f"The product αβ = {fmt(a * b)} min⁻¹ sets where the logarithmic regime "
            f"begins; the usual simplification q_t = (1/β)ln(αβ) + (1/β)ln t requires "
            f"αβt ≫ 1, which holds here for t ≫ {fmt(1.0 / (a * b))} min. AdsorpFit "
            f"fits the exact form q_t = (1/β)ln(1 + αβt) instead, so it stays valid "
            f"at short times too."
        )
    return out


ELOVICH = ModelSpec(
    key="elovich", name="Elovich", category="kinetics", family="reaction model",
    func=_elovich,
    equation=r"q_t = \frac{1}{\beta}\ln\!\left(1 + \alpha\beta t\right)",
    equation_plain="qt = (1/beta)*ln(1 + alpha*beta*t)",
    citation="Roginsky, S. & Zeldovich, Y.B. (1934) Acta Physicochim. URSS 1, 554-594; "
             "Chien, S.H. & Clayton, W.R. (1980) Soil Sci. Soc. Am. J. 44, 265-268.",
    year="1934",
    params=[
        ParamSpec("alpha", "α", "mg g⁻¹ min⁻¹",
                  "Initial adsorption rate on the bare surface.",
                  lower=1e-14, guess_fn=lambda t, q: (
                      float(q[1] - q[0]) / float(t[1] - t[0])
                      if len(t) > 1 and t[1] != t[0] else 1.0)),
        ParamSpec("beta", "β", "g mg⁻¹",
                  "Desorption constant; related to surface coverage and the "
                  "activation energy for chemisorption.",
                  lower=1e-12, guess_fn=lambda t, q: 1.0 / _qe_guess(t, q)),
    ],
    assumptions=[
        "The activation energy for adsorption increases linearly with coverage.",
        "The adsorbent surface is energetically heterogeneous.",
        "Describes chemisorption; has no equilibrium plateau, so it cannot be "
        "used to estimate q_e.",
        "Assumes the desorption rate is negligible.",
    ],
    interpretation=_interp_elovich,
    linear_forms=[
        LinearForm("qt vs ln t", "ln t", "qt",
                   lambda x, y, c: (np.where(x > 0, np.log(np.where(x > 0, x, np.nan)), np.nan), y),
                   lambda s, i, c: {"beta": 1.0 / s if s else np.nan,
                                    "alpha": (np.exp(i / s) * s) if s else np.nan},
                   note="Valid only when αβt ≫ 1; it discards the t = 0 point."),
    ],
)


def _avrami(t, qe, kav, nav):
    t = np.clip(np.asarray(t, float), 0, None)
    return qe * (1.0 - np.exp(-_safe_pow(kav * t, nav)))


def _interp_avrami(f, ctx):
    n = f.params["nav"]
    out = [
        f"q_e = {fmt(f.params['qe'])} mg/g, k_AV = {fmt(f.params['kav'])} min⁻¹, "
        f"n_AV = {fmt(n)}.",
        "The Avrami equation comes from nucleation-and-growth theory and was "
        "adapted to adsorption to allow a *fractional* reaction order. Its value is "
        "that n_AV is not forced to 1 or 2; it is fitted, so the data choose.",
        f"n_AV = {fmt(n)} is the fractional kinetic order. It reflects possible "
        f"changes in the adsorption mechanism as the process advances, rather than "
        f"a single elementary step.",
    ]
    if abs(n - 1) < 0.1:
        out.append("n_AV ≈ 1 makes Avrami equivalent to pseudo-first-order.")
    elif abs(n - 2) < 0.15:
        out.append("n_AV ≈ 2 puts the kinetics close to second-order behaviour.")
    elif n < 1:
        out.append(
            f"n_AV = {fmt(n)} below 1 indicates the rate decays faster than "
            f"first-order at early times: often read as a broad distribution of "
            f"site reactivities, or as diffusion beginning to limit the rate."
        )
    else:
        out.append(
            f"n_AV = {fmt(n)} between 1 and 2 sits between first- and second-order "
            f"behaviour, which is the common outcome and is the main argument for "
            f"fitting Avrami rather than forcing PFO or PSO."
        )
    return out


AVRAMI = ModelSpec(
    key="avrami", name="Avrami (fractional order)", category="kinetics",
    family="reaction model", func=_avrami,
    equation=r"q_t = q_e\left[1 - \exp\!\left(-(k_{AV}t)^{n_{AV}}\right)\right]",
    equation_plain="qt = qe*(1 - exp(-(kAV*t)^nAV))",
    citation="Avrami, M. (1940) J. Chem. Phys. 8, 212-224; "
             "Lopes, E.C.N. et al. (2003) J. Colloid Interface Sci. 263, 542-547.",
    year="1940",
    params=[
        ParamSpec("qe", "q_e", "mg g⁻¹", "Equilibrium capacity.",
                  lower=1e-12, guess_fn=_qe_guess),
        ParamSpec("kav", "k_AV", "min⁻¹", "Avrami kinetic constant.",
                  lower=1e-12, guess_fn=_k1_guess),
        ParamSpec("nav", "n_AV", "–",
                  "Fractional kinetic order; reflects changes in mechanism as "
                  "adsorption proceeds. n = 1 gives pseudo-first-order.",
                  lower=1e-3, upper=10.0, guess=1.0),
    ],
    assumptions=[
        "Adapted from nucleation and crystal-growth theory.",
        "Allows a fractional reaction order rather than forcing 1 or 2.",
        "n_AV is interpreted as reflecting possible changes in the adsorption "
        "mechanism over the course of the process.",
    ],
    interpretation=_interp_avrami,
)


def _mixed_12(t, qe, k, f2):
    t = np.clip(np.asarray(t, float), 0, None)
    e = np.exp(-k * t)
    return qe * (1.0 - e) / (1.0 - f2 * e)


MIXED_12 = ModelSpec(
    key="mixed_1_2", name="Mixed 1,2-order (MOE)", category="kinetics",
    family="reaction model", func=_mixed_12,
    equation=r"q_t = q_e\,\frac{1 - e^{-kt}}{1 - f_2 e^{-kt}}",
    equation_plain="qt = qe*(1 - exp(-k*t)) / (1 - f2*exp(-k*t))",
    citation="Marczewski, A.W. (2010) Langmuir 26, 15229-15238.",
    year="2010",
    params=[
        ParamSpec("qe", "q_e", "mg g⁻¹", "Equilibrium capacity.",
                  lower=1e-12, guess_fn=_qe_guess),
        ParamSpec("k", "k_MOE", "min⁻¹", "Mixed-order rate coefficient.",
                  lower=1e-12, guess_fn=_k1_guess),
        ParamSpec("f2", "f₂", "–",
                  "Second-order fraction. f₂ = 0 gives pure pseudo-first-order; "
                  "f₂ → 1 gives pure pseudo-second-order.",
                  lower=0.0, upper=0.9999, guess=0.5),
    ],
    assumptions=[
        "Interpolates continuously between PFO and PSO rather than forcing a "
        "choice between them.",
        "f₂ is the fraction of the process behaving as second order.",
    ],
    interpretation=lambda f, c: [
        f"q_e = {fmt(f.params['qe'])} mg/g, k = {fmt(f.params['k'])} min⁻¹, "
        f"f₂ = {fmt(f.params['f2'])}.",
        f"f₂ is the headline number: it is the fraction of the uptake behaving as "
        f"second order. f₂ = {fmt(f.params['f2'])} means the process is "
        + ("essentially pure pseudo-first-order; report PFO instead."
           if f.params['f2'] < 0.1 else
           "essentially pure pseudo-second-order; report PSO instead."
           if f.params['f2'] > 0.9 else
           f"genuinely mixed, roughly {f.params['f2'] * 100:.0f}% second-order in "
           f"character. This is the case where MOE earns its extra parameter: "
           f"neither PFO nor PSO alone is right."),
        "MOE sidesteps the PFO-vs-PSO argument that dominates the adsorption "
        "literature by letting the data decide the balance rather than forcing an "
        "either/or.",
    ],
)


def _nth_order(t, qe, kn, n):
    t = np.clip(np.asarray(t, float), 0, None)
    n = float(n)
    if abs(n - 1.0) < 1e-6:
        return qe * (1.0 - np.exp(-kn * t))
    inner = _safe_pow(qe, 1.0 - n) + (n - 1.0) * kn * t
    inner = np.clip(inner, 1e-300, None)
    return qe - _safe_pow(inner, 1.0 / (1.0 - n))


NTH_ORDER = ModelSpec(
    key="nth_order", name="Pseudo-nth-order", category="kinetics",
    family="reaction model", func=_nth_order,
    equation=r"q_t = q_e - \left[q_e^{\,1-n} + (n-1)k_n t\right]^{\frac{1}{1-n}}",
    equation_plain="qt = qe - [qe^(1-n) + (n-1)*kn*t]^(1/(1-n))",
    citation="Özer, A. (2007) J. Hazard. Mater. 141, 753-761.",
    year="2007",
    params=[
        ParamSpec("qe", "q_e", "mg g⁻¹", "Equilibrium capacity.",
                  lower=1e-12, guess_fn=_qe_guess),
        ParamSpec("kn", "k_n", "varies with n", "nth-order rate constant.",
                  lower=1e-14, guess_fn=_k2_guess),
        ParamSpec("n", "n", "–",
                  "Fitted reaction order. n = 1 gives PFO, n = 2 gives PSO; "
                  "letting n float tests whether either is justified.",
                  lower=0.1, upper=6.0, guess=2.0),
    ],
    assumptions=[
        "Generalises PFO and PSO by letting the order n be fitted.",
        "d q_t/dt = k_n (q_e − q_t)ⁿ.",
        "A fitted n far from 1 or 2 means neither standard model is appropriate.",
    ],
    interpretation=lambda f, c: [
        f"q_e = {fmt(f.params['qe'])} mg/g, k_n = {fmt(f.params['kn'])}, "
        f"n = {fmt(f.params['n'])}.",
        f"The fitted order n = {fmt(f.params['n'])} is the result that matters. "
        + ("It is close to 1, so pseudo-first-order is justified for these data."
           if abs(f.params['n'] - 1) < 0.2 else
           "It is close to 2, so pseudo-second-order is justified."
           if abs(f.params['n'] - 2) < 0.25 else
           f"It is far from both 1 and 2, which means neither PFO nor PSO is the "
           f"right description: forcing one of them onto these data would give a "
           f"rate constant with no physical meaning."),
        "Note that k_n's units depend on n, so k_n from this fit cannot be compared "
        "with a k₁ or k₂ from PFO/PSO.",
    ],
)


def _ritchie(t, qe, kr, n):
    t = np.clip(np.asarray(t, float), 0, None)
    n = float(n)
    if abs(n - 1.0) < 1e-6:
        return qe * (1.0 - np.exp(-kr * t))
    return qe * (1.0 - _safe_pow(1.0 + (n - 1.0) * kr * t, 1.0 / (1.0 - n)))


RITCHIE = ModelSpec(
    key="ritchie", name="Ritchie nth-order", category="kinetics",
    family="reaction model", func=_ritchie,
    equation=r"q_t = q_e\left[1 - \left(1 + (n-1)k_R t\right)^{\frac{1}{1-n}}\right]",
    equation_plain="qt = qe*(1 - (1 + (n-1)*kR*t)^(1/(1-n)))",
    citation="Ritchie, A.G. (1977) J. Chem. Soc. Faraday Trans. 1 73, 1650-1653.",
    year="1977",
    params=[
        ParamSpec("qe", "q_e", "mg g⁻¹", "Equilibrium capacity.",
                  lower=1e-12, guess_fn=_qe_guess),
        ParamSpec("kR", "k_R", "min⁻¹", "Ritchie rate constant.",
                  lower=1e-12, guess_fn=_k1_guess),
        ParamSpec("n", "n", "–",
                  "Number of surface sites occupied by one adsorbate molecule. "
                  "n = 1 means one site per molecule; n = 2 means bidentate binding.",
                  lower=0.1, upper=6.0, guess=2.0),
    ],
    assumptions=[
        "Derived from the fraction of surface sites occupied, not from a "
        "concentration-driven rate law.",
        "n has a concrete meaning here: the number of sites occupied by one "
        "adsorbate molecule.",
        "Assumes the rate depends only on the fraction of vacant sites.",
    ],
    interpretation=lambda f, c: [
        f"q_e = {fmt(f.params['qe'])} mg/g, k_R = {fmt(f.params['kR'])} min⁻¹, "
        f"n = {fmt(f.params['n'])}.",
        f"Unlike the empirical nth-order model, Ritchie's n has a physical "
        f"referent: the number of surface sites occupied by a single adsorbate "
        f"molecule. n = {fmt(f.params['n'])} therefore suggests "
        + ("monodentate binding: one molecule per site."
           if abs(f.params['n'] - 1) < 0.25 else
           "bidentate binding: each molecule occupies two sites, which is common "
           "for chelating metal complexes and carboxylate groups."
           if abs(f.params['n'] - 2) < 0.4 else
           f"roughly {f.params['n']:.1f} sites per molecule, a non-integer value "
           f"that usually means the site picture is an oversimplification here."),
    ],
)


# --------------------------------------------------------------------------
# Diffusion models
# --------------------------------------------------------------------------

def _weber_morris(t, kid, C):
    t = np.clip(np.asarray(t, float), 0, None)
    return kid * np.sqrt(t) + C


def _interp_wm(f, ctx):
    kid = f.params["kid"]; C = f.params["C"]
    out = [
        f"k_id = {fmt(kid)} mg g⁻¹ min⁻⁰·⁵ is the intraparticle diffusion rate "
        f"constant, and C = {fmt(C)} mg/g is the intercept.",
        "The intercept C is the informative parameter here, and it is what the "
        "Weber–Morris plot is actually for. C is proportional to the thickness of "
        "the boundary layer surrounding the particle.",
    ]
    if abs(C) < 0.05 * max(1.0, float(np.max(f.y))):
        out.append(
            f"C = {fmt(C)} mg/g is essentially zero, so the line passes through the "
            f"origin. That is the specific condition under which intraparticle "
            f"diffusion is the **sole** rate-limiting step, external film diffusion "
            f"contributes nothing measurable."
        )
    else:
        out.append(
            f"C = {fmt(C)} mg/g is significantly greater than zero, so the plot does "
            f"NOT pass through the origin. Intraparticle diffusion is therefore "
            f"involved but is **not the only** rate-controlling step: film (boundary "
            f"layer) diffusion contributes as well. The larger C is, the greater the "
            f"boundary-layer contribution."
        )
    out.append(
        "Important methodological point: a single straight line fitted through all "
        "your q_t vs √t points is almost always the wrong analysis. The standard "
        "interpretation requires you to identify *multiple linear regions*"
        "typically an initial fast external surface adsorption stage, a second "
        "gradual stage where intraparticle diffusion is rate-limiting, and a final "
        "plateau as equilibrium is approached. Use the multi-region tool in "
        "AdsorpFit to segment the plot; each segment gets its own k_id and C, and "
        "their relative slopes tell you which step controls the rate."
    )
    return out


WEBER_MORRIS = ModelSpec(
    key="weber_morris", name="Weber–Morris (intraparticle diffusion)",
    category="kinetics", family="diffusion model", func=_weber_morris,
    equation=r"q_t = k_{id}\sqrt{t} + C",
    equation_plain="qt = kid*sqrt(t) + C",
    citation="Weber, W.J. & Morris, J.C. (1963) J. Sanit. Eng. Div. ASCE 89, 31-60.",
    year="1963",
    params=[
        ParamSpec("kid", "k_id", "mg g⁻¹ min⁻⁰·⁵",
                  "Intraparticle diffusion rate constant, the slope.",
                  lower=0.0, guess_fn=lambda t, q: float(np.max(q)) / max(np.sqrt(np.max(t)), 1e-9)),
        ParamSpec("C", "C", "mg g⁻¹",
                  "Intercept, proportional to boundary-layer thickness. "
                  "C = 0 means intraparticle diffusion alone controls the rate.",
                  lower=-1e6, upper=1e6, guess=0.0),
    ],
    assumptions=[
        "Uptake varies with the square root of time when intraparticle diffusion "
        "controls the rate.",
        "Should be analysed as multiple linear segments, not one line.",
        "An intercept C = 0 is the diagnostic for intraparticle diffusion being "
        "the sole rate-limiting step.",
    ],
    interpretation=_interp_wm,
    linear_forms=[
        LinearForm("qt vs √t", "√t", "qt",
                   lambda x, y, c: (np.sqrt(np.clip(x, 0, None)), y),
                   lambda s, i, c: {"kid": s, "C": i},
                   note="This model IS linear, so the linear and non-linear fits "
                        "agree exactly."),
    ],
)


def _film_diffusion(t, qe, kfd):
    t = np.clip(np.asarray(t, float), 0, None)
    return qe * (1.0 - np.exp(-kfd * t))


FILM_DIFFUSION = ModelSpec(
    key="film_diffusion", name="Liquid film diffusion (Boyd–Adamson)",
    category="kinetics", family="diffusion model", func=_film_diffusion,
    equation=r"\ln\!\left(1 - \frac{q_t}{q_e}\right) = -k_{fd}\,t",
    equation_plain="qt = qe*(1 - exp(-kfd*t))",
    citation="Boyd, G.E., Adamson, A.W. & Myers, L.S. (1947) J. Am. Chem. Soc. 69, 2836-2848.",
    year="1947",
    params=[
        ParamSpec("qe", "q_e", "mg g⁻¹", "Equilibrium capacity.",
                  lower=1e-12, guess_fn=_qe_guess),
        ParamSpec("kfd", "k_fd", "min⁻¹",
                  "Film diffusion rate constant, set by transport across the "
                  "liquid film surrounding the particle.",
                  lower=1e-12, guess_fn=_k1_guess),
    ],
    assumptions=[
        "The rate is controlled by diffusion of adsorbate across the stagnant "
        "liquid film around the adsorbent particle.",
        "Diagnostic: a plot of ln(1 − F) vs t is linear and passes through the "
        "origin if film diffusion controls.",
        "Mathematically identical to pseudo-first-order; the difference is "
        "interpretive, not algebraic.",
    ],
    interpretation=lambda f, c: [
        f"q_e = {fmt(f.params['qe'])} mg/g and k_fd = {fmt(f.params['kfd'])} min⁻¹.",
        "Be aware that the film-diffusion equation is *algebraically identical* to "
        "pseudo-first-order. It will always give exactly the same R², SSE and "
        "curve. What differs is the claim you attach to it: PFO says the rate "
        "depends on free sites, film diffusion says the rate depends on transport "
        "through the boundary layer. Fitting quality cannot distinguish them.",
        "What can distinguish them is experiment: film diffusion is sensitive to "
        "stirring speed, PFO site-limited kinetics is not. If your rate constant "
        "changes when you change the agitation rate, film diffusion is real. The "
        "Boyd plot in the diffusion panel makes the same test graphically"
        "a straight line through the origin indicates particle diffusion control, "
        "while a non-zero intercept points to film diffusion.",
    ],
)


def _bangham_q(t, k0, alpha, qe_ref=1.0):
    t = np.clip(np.asarray(t, float), 1e-12, None)
    return k0 * _safe_pow(t, alpha)


BANGHAM = ModelSpec(
    key="bangham", name="Bangham (pore diffusion)", category="kinetics",
    family="diffusion model", func=_bangham_q,
    equation=r"\log\log\!\left(\frac{C_0}{C_0 - q_t m}\right) = "
             r"\log\!\left(\frac{k_0 m}{2.303\,V}\right) + \alpha\log t",
    equation_plain="qt = k0 * t^alpha   (power-law form used for fitting)",
    citation="Bangham, D.H. & Burt, F.P. (1924) Proc. R. Soc. Lond. A 105, 481-488.",
    year="1924",
    params=[
        ParamSpec("k0", "k₀", "mg g⁻¹ min⁻ᵅ", "Bangham rate constant.",
                  lower=1e-14, guess_fn=lambda t, q: float(np.max(q)) /
                  max(float(np.max(t)) ** 0.5, 1e-9)),
        ParamSpec("alpha", "α", "–",
                  "Bangham exponent; α < 1 is the signature of pore-diffusion "
                  "control.", lower=1e-3, upper=3.0, guess=0.5),
    ],
    assumptions=[
        "Pore diffusion is the rate-controlling step.",
        "A linear double-log Bangham plot supports pore diffusion control; "
        "curvature argues against it.",
        "AdsorpFit fits the equivalent power-law form q_t = k₀tᵅ directly, which "
        "avoids the double logarithm's severe error distortion.",
    ],
    interpretation=lambda f, c: [
        f"k₀ = {fmt(f.params['k0'])} and α = {fmt(f.params['alpha'])}.",
        f"α = {fmt(f.params['alpha'])} is the diagnostic. "
        + (f"Being below 1, it is consistent with diffusion into the pore network "
           f"controlling the rate: uptake slows progressively as the adsorbate "
           f"must travel further into the particle."
           if f.params['alpha'] < 1 else
           f"α ≥ 1 means uptake is not decelerating the way pore diffusion "
           f"requires, which argues against pore-diffusion control."),
        ("α ≈ 0.5 specifically recovers the Weber–Morris √t dependence, meaning "
         "classical intraparticle diffusion."
         if abs(f.params['alpha'] - 0.5) < 0.08 else ""),
    ],
)


def _double_exponential(t, qe, a1, k1, k2):
    t = np.clip(np.asarray(t, float), 0, None)
    return qe - a1 * np.exp(-k1 * t) - (qe - a1) * np.exp(-k2 * t)


DOUBLE_EXP = ModelSpec(
    key="double_exponential", name="Double exponential", category="kinetics",
    family="empirical model", func=_double_exponential,
    equation=r"q_t = q_e - a_1 e^{-k_{D1}t} - (q_e - a_1) e^{-k_{D2}t}",
    equation_plain="qt = qe - a1*exp(-kD1*t) - (qe-a1)*exp(-kD2*t)",
    citation="Wilczak, A. & Keinath, T.M. (1993) Water Environ. Res. 65, 238-244.",
    year="1993",
    params=[
        ParamSpec("qe", "q_e", "mg g⁻¹", "Equilibrium capacity.",
                  lower=1e-12, guess_fn=_qe_guess),
        ParamSpec("a1", "a₁", "mg g⁻¹",
                  "Capacity attributable to the fast step.",
                  lower=0.0, guess_fn=lambda t, q: _qe_guess(t, q) * 0.6),
        ParamSpec("k1", "k_D1", "min⁻¹", "Rate constant of the fast step.",
                  lower=1e-12, guess_fn=lambda t, q: _k1_guess(t, q) * 5),
        ParamSpec("k2", "k_D2", "min⁻¹", "Rate constant of the slow step.",
                  lower=1e-14, guess_fn=lambda t, q: _k1_guess(t, q) * 0.2),
    ],
    assumptions=[
        "Adsorption proceeds in two parallel or sequential steps with distinct "
        "rate constants: typically a fast external surface step and a slow "
        "internal diffusion step.",
        "Appropriate when the uptake curve shows a clear two-stage shape that a "
        "single exponential cannot follow.",
    ],
    interpretation=lambda f, c: [
        f"q_e = {fmt(f.params['qe'])} mg/g. Fast step: a₁ = {fmt(f.params['a1'])} mg/g "
        f"at k_D1 = {fmt(f.params['k1'])} min⁻¹. Slow step: "
        f"{fmt(f.params['qe'] - f.params['a1'])} mg/g at k_D2 = "
        f"{fmt(f.params['k2'])} min⁻¹.",
        f"The two rate constants differ by a factor of "
        f"{fmt(f.params['k1'] / f.params['k2']) if f.params['k2'] else 'n.d.'}. "
        + ("That separation is large enough for the two steps to be genuinely "
           "distinguishable: usually fast adsorption on the external surface "
           "followed by slow diffusion into the interior."
           if f.params['k2'] and f.params['k1'] / f.params['k2'] > 5 else
           "That separation is small, so the two exponentials are not well "
           "distinguished and the extra parameters are probably not justified. "
           "Check the standard errors before reporting both steps."),
        f"The fast step accounts for "
        f"{100 * f.params['a1'] / f.params['qe'] if f.params['qe'] else float('nan'):.0f}% "
        f"of the total uptake.",
    ],
)


def _fractal_pfo(t, qe, k1, h):
    t = np.clip(np.asarray(t, float), 0, None)
    if abs(1.0 - h) < 1e-9:
        return qe * (1.0 - np.exp(-k1 * np.log1p(t)))
    return qe * (1.0 - np.exp(-k1 * _safe_pow(t, 1.0 - h) / (1.0 - h)))


FRACTAL_PFO = ModelSpec(
    key="fractal_pfo", name="Fractal-like pseudo-first-order", category="kinetics",
    family="reaction model", func=_fractal_pfo,
    equation=r"q_t = q_e\left[1 - \exp\!\left(-\frac{k_1' t^{1-h}}{1-h}\right)\right]",
    equation_plain="qt = qe*(1 - exp(-k1*t^(1-h)/(1-h)))",
    citation="Kopelman, R. (1988) Science 241, 1620-1626; "
             "Haerifar, M. & Azizian, S. (2012) J. Phys. Chem. C 116, 13111-13119.",
    year="2012",
    params=[
        ParamSpec("qe", "q_e", "mg g⁻¹", "Equilibrium capacity.",
                  lower=1e-12, guess_fn=_qe_guess),
        ParamSpec("k1", "k₁′", "min^(h−1)", "Fractal-like rate coefficient.",
                  lower=1e-12, guess_fn=_k1_guess),
        ParamSpec("h", "h", "–",
                  "Fractal (heterogeneity) exponent. h = 0 recovers classical PFO; "
                  "h > 0 means the effective rate constant decays with time.",
                  lower=0.0, upper=0.99, guess=0.2),
    ],
    assumptions=[
        "The rate 'constant' is not constant: on a fractal or energetically "
        "disordered surface it decays as a power of time, k(t) = k′t^(−h).",
        "h = 0 recovers classical pseudo-first-order kinetics.",
        "Physically motivated for rough, porous or geometrically disordered "
        "adsorbents where reactant and site cannot mix freely.",
    ],
    interpretation=lambda f, c: [
        f"q_e = {fmt(f.params['qe'])} mg/g, k₁′ = {fmt(f.params['k1'])}, "
        f"h = {fmt(f.params['h'])}.",
        f"The fractal exponent h = {fmt(f.params['h'])} is the point of this model. "
        + ("h ≈ 0 means the rate constant really is constant and classical PFO is "
           "adequate; the fractal correction is unnecessary here."
           if f.params['h'] < 0.05 else
           f"h > 0 means the effective rate constant decays with time as t^(−h). "
           f"This is what happens on a geometrically disordered or fractal surface: "
           f"the adsorbate and the remaining free sites become progressively "
           f"segregated, so the encounter rate falls even though sites remain "
           f"available. A larger h means stronger disorder."),
    ],
)


# --------------------------------------------------------------------------
# Diagnostic transforms (not fitted models, but plotted)
# --------------------------------------------------------------------------

def boyd_bt(F: np.ndarray) -> np.ndarray:
    """Boyd's B·t from fractional attainment F = qt/qe.

    Uses Reichenberg's two-branch approximation, which is the standard
    treatment: the series solution converges differently above and below
    F ≈ 0.85.
    """
    F = np.clip(np.asarray(F, float), 1e-9, 1 - 1e-9)
    bt = np.empty_like(F)
    hi = F > 0.85
    bt[hi] = -0.4977 - np.log(1.0 - F[hi])
    lo = ~hi
    inner = np.clip(np.pi - (np.pi ** 2 * F[lo]) / 3.0, 0, None)
    bt[lo] = (np.sqrt(np.pi) - np.sqrt(inner)) ** 2
    return bt


def crank_qt(t, qe, D, r):
    """Homogeneous surface diffusion (Crank's spherical solution).

    qt/qe = 1 - (6/pi^2) * sum_{n=1..inf} (1/n^2) exp(-n^2 pi^2 D t / r^2)
    Truncated at 60 terms, which is convergent to machine precision for all
    but the very shortest times.
    """
    t = np.clip(np.asarray(t, float), 0, None)
    total = np.zeros_like(t, dtype=float)
    for n in range(1, 61):
        total += (1.0 / n ** 2) * np.exp(-(n ** 2) * np.pi ** 2 * D * t / (r ** 2))
    return qe * (1.0 - (6.0 / np.pi ** 2) * total)


CRANK = ModelSpec(
    key="crank", name="Homogeneous surface diffusion (Crank)", category="kinetics",
    family="diffusion model", func=crank_qt,
    equation=r"\frac{q_t}{q_e} = 1 - \frac{6}{\pi^2}\sum_{n=1}^{\infty}"
             r"\frac{1}{n^2}\exp\!\left(\frac{-n^2\pi^2 D t}{r^2}\right)",
    equation_plain="qt/qe = 1 - (6/pi^2)*sum(1/n^2 * exp(-n^2*pi^2*D*t/r^2))",
    citation="Crank, J. (1975) The Mathematics of Diffusion, 2nd ed., Oxford.",
    year="1975",
    params=[
        ParamSpec("qe", "q_e", "mg g⁻¹", "Equilibrium capacity.",
                  lower=1e-12, guess_fn=_qe_guess),
        ParamSpec("D", "D", "cm² min⁻¹",
                  "Effective intraparticle diffusion coefficient, the physical "
                  "quantity this model exists to deliver.",
                  lower=1e-20, upper=1e-2, guess=1e-8),
        ParamSpec("r", "r", "cm",
                  "Adsorbent particle radius. Fix this to your measured value "
                  "rather than fitting it, or D and r trade off against each other.",
                  lower=1e-6, upper=1.0, guess=0.05),
    ],
    assumptions=[
        "Spherical, homogeneous particles of uniform radius r.",
        "Diffusion within the particle follows Fick's law with a constant D.",
        "Surface concentration reaches equilibrium instantaneously (no film "
        "resistance).",
        "D and r are strongly correlated, fix r at its measured value.",
    ],
    interpretation=lambda f, c: [
        f"q_e = {fmt(f.params['qe'])} mg/g, D = {fmt(f.params['D'])} cm²/min, "
        f"r = {fmt(f.params['r'])} cm.",
        f"D is the effective intraparticle diffusion coefficient and is the only "
        f"parameter here with transferable physical meaning. "
        + ("Values around 10⁻¹¹–10⁻¹³ cm²/s indicate strongly hindered pore "
           "diffusion typical of microporous adsorbents; values near the "
           "free-solution value (~10⁻⁵ cm²/s) mean the pore network offers little "
           "resistance."),
        "Because D appears only as D/r², it is perfectly correlated with the "
        "particle radius. If you fitted r rather than fixing it at a measured "
        "value, neither number is meaningful on its own, only the ratio is.",
    ],
)


# --------------------------------------------------------------------------
# Domain of applicability
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


def _reaches_equilibrium(x, y, ctx):
    """Models that fit q_e need the data to actually approach equilibrium."""
    y = np.asarray(y, float)
    if y.size < 4:
        return []
    span = float(np.max(y) - np.min(y))
    if span <= 0:
        return []
    ratio = terminal_slope_ratio(x, y)
    k = max(2, y.size // 3)
    tail = y[-k:]
    rise = (float(np.max(tail)) - float(np.min(tail))) / span
    if ratio > 0.15 or rise > 0.25:
        return [issue(
            "warn", "no_equilibrium",
            f"Uptake is still climbing at your last time point: the slope over "
            f"the final quarter of the run is {ratio * 100:.0f}% of the average "
            f"slope, and the last third accounts for {rise * 100:.0f}% of the "
            f"total change in q_t. At equilibrium both would be near zero. "
            f"Any q_e this model reports is an extrapolation beyond the "
            f"measured window, and the rate constant is correlated with it, so "
            f"both numbers are soft. Run the experiment longer if q_e matters.")]
    return []


def _early_resolution(x, y, ctx):
    """Rate constants are set by the early part of the curve."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if y.size < 4:
        return []
    q_end = float(np.max(y))
    if q_end <= 0:
        return []
    early = int(np.sum(y < 0.5 * q_end))
    if early < 2:
        return [issue(
            "warn", "sparse_early",
            f"Only {early} point(s) were measured before half the final uptake was "
            f"reached. The rate constant is determined almost entirely by that "
            f"early region, so with this sampling it is poorly constrained however "
            f"tight the confidence interval looks. Add earlier time points.")]
    return []


def _elovich_domain(x, y, ctx):
    out = _early_resolution(x, y, ctx)
    y = np.asarray(y, float)
    if y.size >= 4:
        span = float(np.max(y) - np.min(y))
        if span > 0:
            if terminal_slope_ratio(x, y) < 0.05:
                out.append(issue(
                    "warn", "elovich_plateau",
                    "Your data have clearly reached a plateau. The Elovich equation "
                    "has no equilibrium plateau: it rises logarithmically without "
                    "limit: so it cannot reproduce the flat region and will "
                    "systematically overshoot at long times. It suits data still in "
                    "the rising, chemisorption-controlled stage."))
    return out


def _weber_morris_validity(p, x, y, ctx):
    """A negative intercept implies a negative loading at short times."""
    C, kid = p.get("C", 0.0), p.get("kid", 0.0)
    out = []
    if C < 0 and kid > 0:
        t_zero = (C / kid) ** 2
        out.append(issue(
            "warn", "wm_negative_intercept",
            f"The fitted intercept C = {fmt(C)} mg/g is negative, so the line "
            f"predicts a negative loading for all t below {fmt(t_zero)} min. C is "
            f"meant to be proportional to boundary-layer thickness and cannot be "
            f"negative physically. This is the usual sign that a single straight "
            f"line has been forced through what are really two or three distinct "
            f"diffusion stages; use the multi-region analysis on the Diffusion "
            f"tab instead of this single-line fit."))
    return out


def _weber_morris_domain(x, y, ctx):
    return [issue(
        "info", "wm_single_line",
        "Fitted here as one straight line over all points. That is almost never "
        "the right analysis: the standard interpretation requires identifying "
        "separate linear regions. The Diffusion tab does that segmentation and is "
        "what you should report.")]


def _double_exp_validity(p, x, y, ctx):
    qe, a1 = p.get("qe", 0.0), p.get("a1", 0.0)
    if a1 > qe:
        return [issue(
            "warn", "de_amplitude",
            f"The fast-step amplitude a₁ = {fmt(a1)} mg/g exceeds the total "
            f"capacity q_e = {fmt(qe)} mg/g, which makes the slow step's amplitude "
            f"negative: i.e. the model is describing desorption in the second "
            f"stage. That is rarely intended; the two exponentials are probably "
            f"not separable in these data.")]
    k1, k2 = p.get("k1", 0.0), p.get("k2", 0.0)
    if k2 > 0 and 0.2 < k1 / k2 < 5:
        return [issue(
            "warn", "de_unseparated",
            f"The two rate constants differ by only a factor of {fmt(k1 / k2)}. "
            f"Two exponentials that close together are not distinguishable from a "
            f"single one: the extra two parameters are fitting noise. Prefer the "
            f"pseudo-first-order model unless the standard errors say otherwise.")]
    return []


def _crank_domain(x, y, ctx):
    out = _reaches_equilibrium(x, y, ctx)
    if not ctx.get("particle_radius"):
        out.append(issue(
            "warn", "crank_radius",
            "D and r enter this model only as D/r², so they cannot be determined "
            "separately. Enter your measured particle radius in the experiment "
            "panel and treat D as the single fitted quantity; otherwise neither "
            "number means anything on its own."))
    return out


def _bangham_domain(x, y, ctx):
    if np.any(np.asarray(x) <= 0):
        return [issue("info", "bangham_t0",
                      "The Bangham power law is undefined at t = 0; that point is "
                      "handled by clamping and contributes little to the fit.")]
    return []


for _m in (PFO, PSO, AVRAMI, MIXED_12, NTH_ORDER, RITCHIE, FRACTAL_PFO,
           FILM_DIFFUSION):
    _m.domain = (lambda x, y, ctx: _reaches_equilibrium(x, y, ctx)
                 + _early_resolution(x, y, ctx))

ELOVICH.domain = _elovich_domain
WEBER_MORRIS.domain = _weber_morris_domain
WEBER_MORRIS.validity = _weber_morris_validity
DOUBLE_EXP.domain = _reaches_equilibrium
DOUBLE_EXP.validity = _double_exp_validity
CRANK.domain = _crank_domain
BANGHAM.domain = _bangham_domain


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------

KINETIC_MODELS = {
    m.key: m for m in [
        PFO, PSO, ELOVICH, AVRAMI, MIXED_12, NTH_ORDER, RITCHIE, FRACTAL_PFO,
        WEBER_MORRIS, FILM_DIFFUSION, BANGHAM, CRANK, DOUBLE_EXP,
    ]
}
