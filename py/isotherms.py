"""
AdsorpFit - adsorption isotherm models.

Every model is declared once, as a ModelSpec carrying its equation, the
physical meaning and units of each parameter, sensible bounds, a data-driven
initial guess, the classical linearised form(s), the original citation, and a
function that turns the fitted numbers into prose.

Sign and unit conventions follow Tran et al. (2017) Water Research 120,
88-116, which is the standard correction of the unit errors that propagate
through much of the adsorption literature.

x = Ce, equilibrium liquid-phase concentration (mg/L unless noted)
y = qe, equilibrium solid-phase loading (mg/g)
"""

from __future__ import annotations

import numpy as np

from core import (ModelSpec, ParamSpec, LinearForm, R_GAS, fmt, issue,
                  terminal_slope_ratio)
from lang import tr

# --------------------------------------------------------------------------
# guess helpers
# --------------------------------------------------------------------------

def _qmax_guess(x, y):
    """Plateau estimate: a little above the highest observed loading."""
    return float(np.max(y)) * 1.15 + 1e-9


def _khalf_guess(x, y):
    """Affinity from the concentration at half the apparent plateau."""
    qm = _qmax_guess(x, y)
    target = qm / 2.0
    i = int(np.argmin(np.abs(y - target)))
    ce = float(x[i])
    return 1.0 / ce if ce > 0 else 1.0


def _kf_guess(x, y):
    """Freundlich KF from a log-log regression."""
    m = (x > 0) & (y > 0)
    if m.sum() < 2:
        return float(np.max(y)) if len(y) else 1.0
    b, a = np.polyfit(np.log(x[m]), np.log(y[m]), 1)
    return float(np.exp(a))


def _n_guess(x, y):
    m = (x > 0) & (y > 0)
    if m.sum() < 2:
        return 2.0
    b, _ = np.polyfit(np.log(x[m]), np.log(y[m]), 1)
    return float(np.clip(1.0 / b, 0.2, 10.0)) if b != 0 else 2.0


def _safe_pow(base, expo):
    base = np.clip(np.asarray(base, float), 1e-300, 1e300)
    return np.power(base, expo)


# --------------------------------------------------------------------------
# 2-parameter models
# --------------------------------------------------------------------------

def _langmuir(ce, qm, kl):
    ce = np.asarray(ce, float)
    return qm * kl * ce / (1.0 + kl * ce)


def _interp_langmuir(f, ctx):
    qm = f.params["qm"]; kl = f.params["KL"]
    out = [
        tr("The Langmuir monolayer capacity is q_max = {qm} mg/g. This is the "
        "loading the surface would reach if every adsorption site were occupied. "
        "It is an extrapolated ceiling rather than a measured value, so it is "
        "only trustworthy if your data actually approach a plateau.",
            qm=fmt(qm)),
        tr("The Langmuir affinity constant is K_L = {kl} L/mg. Physically it is "
        "the ratio of the adsorption to the desorption rate constant, so a larger "
        "K_L means the adsorbate is held more tightly and the isotherm rises more "
        "steeply at low concentration.",
            kl=fmt(kl)),
    ]
    # coverage check - is the plateau actually observed?
    q_max_obs = float(np.max(f.y))
    frac = q_max_obs / qm if qm > 0 else np.nan
    if np.isfinite(frac):
        if frac < 0.6:
            out.append(
                tr("Caution: your highest measured loading ({q_max_obs} mg/g) is only "
                "{v1:.0f}% of the fitted q_max. The plateau is far outside the "
                "measured range, so q_max here is an extrapolation with a large real "
                "uncertainty regardless of what the standard error says. Extend the "
                "concentration range before quoting this capacity.",
                    q_max_obs=fmt(q_max_obs), v1=frac * 100)
            )
        elif frac > 0.95:
            out.append(
                tr("Your data reach {v1:.0f}% of the fitted q_max, so the plateau is "
                "genuinely observed and this capacity is well constrained.",
                    v1=frac * 100)
            )
    # separation factor
    c0 = ctx.get("C0_list") or ctx.get("C0")
    if c0 is not None:
        c0arr = np.atleast_1d(np.asarray(c0, float))
        rl = 1.0 / (1.0 + kl * c0arr)
        f.derived["R_L"] = rl.tolist()
        lo, hi = float(np.min(rl)), float(np.max(rl))
        out.append(
            tr("The dimensionless separation factor R_L = 1/(1 + K_L·C_0) spans "
            "{lo}–{hi} over your initial concentrations. ",
                lo=fmt(lo), hi=fmt(hi))
            + (tr("All values fall in 0 < R_L < 1, which classifies the isotherm as "
               "favourable: the surface's affinity for the adsorbate is high enough "
               "that uptake is efficient at low residual concentration.")
               if 0 < lo and hi < 1 else
               tr("Values outside 0 < R_L < 1 indicate an unfavourable or irreversible "
               "classification and usually mean K_L or C_0 has a unit problem."))
        )
        if hi < 0.1:
            out.append(
                tr("R_L below about 0.1 is the 'strongly favourable' regime: the isotherm "
                "is close to rectangular, which is what you want for a practical "
                "adsorbent because it strips the solute down to very low residual levels.")
            )
    else:
        out.append(
            tr("To report the separation factor R_L, enter the initial concentrations "
            "C_0 in the experiment panel, R_L depends on C_0 and cannot be computed "
            "from the equilibrium data alone.")
        )
    return out


LANGMUIR = ModelSpec(
    key="langmuir", name="Langmuir", category="isotherm", family="2-parameter",
    func=_langmuir,
    equation=r"q_e = \frac{q_{max} K_L C_e}{1 + K_L C_e}",
    equation_plain="qe = qmax*KL*Ce / (1 + KL*Ce)",
    citation="Langmuir, I. (1918) J. Am. Chem. Soc. 40, 1361-1403.",
    year="1918",
    params=[
        ParamSpec("qm", "q_max", "mg g⁻¹",
                  "Maximum monolayer adsorption capacity, the loading at full "
                  "site occupancy. An extrapolated ceiling, not a measured maximum.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("KL", "K_L", "L mg⁻¹",
                  "Langmuir affinity constant; the ratio of adsorption to "
                  "desorption rate constants. Larger K_L = stronger binding and a "
                  "steeper rise at low Ce.",
                  lower=1e-12, guess_fn=_khalf_guess),
    ],
    assumptions=[
        "Adsorption is confined to a monolayer, with no stacking of adsorbate.",
        "All sites are energetically identical (a homogeneous surface).",
        "Adsorbed molecules do not interact with each other laterally.",
        "Each site holds exactly one molecule, and adsorption is reversible.",
    ],
    interpretation=_interp_langmuir,
    requires=[],
    linear_forms=[
        LinearForm("Type I (Hanes)", "Ce", "Ce/qe",
                   lambda x, y, c: (x, np.where(y > 0, x / np.where(y > 0, y, np.nan), np.nan)),
                   lambda s, i, c: {"qm": 1.0 / s if s else np.nan,
                                    "KL": (s / i) if i else np.nan},
                   note="Most commonly used; weights high-Ce points heavily."),
        LinearForm("Type II (Lineweaver-Burk)", "1/Ce", "1/qe",
                   lambda x, y, c: (np.where(x > 0, 1.0 / np.where(x > 0, x, np.nan), np.nan),
                                    np.where(y > 0, 1.0 / np.where(y > 0, y, np.nan), np.nan)),
                   lambda s, i, c: {"qm": 1.0 / i if i else np.nan,
                                    "KL": (i / s) if s else np.nan},
                   note="Badly distorts error structure; the double reciprocal "
                        "inflates the influence of the lowest-Ce point."),
        LinearForm("Type III (Eadie-Hofstee)", "qe/Ce", "qe",
                   lambda x, y, c: (np.where(x > 0, y / np.where(x > 0, x, np.nan), np.nan), y),
                   lambda s, i, c: {"qm": i, "KL": -1.0 / s if s else np.nan}),
        LinearForm("Type IV (Scatchard)", "qe", "qe/Ce",
                   lambda x, y, c: (y, np.where(x > 0, y / np.where(x > 0, x, np.nan), np.nan)),
                   lambda s, i, c: {"qm": -i / s if s else np.nan, "KL": -s}),
    ],
)


def _freundlich(ce, kf, n):
    return kf * _safe_pow(np.asarray(ce, float), 1.0 / n)


def _interp_freundlich(f, ctx):
    kf = f.params["KF"]; n = f.params["n"]
    inv = 1.0 / n if n else np.nan
    out = [
        tr("K_F = {kf} (mg/g)(L/mg)^(1/n) measures the adsorption capacity, but "
        "note its units depend on n: so K_F values can only be compared between "
        "systems that have similar n. It is not a capacity in mg/g.",
            kf=fmt(kf)),
        tr("The heterogeneity exponent is n = {n} (1/n = {inv}).",
            n=fmt(n), inv=fmt(inv)),
    ]
    if inv < 1:
        out.append(
            tr("Because 1/n = {inv} is below 1, the isotherm is favourable and "
            "concave to the concentration axis: the first molecules bind to the "
            "strongest sites, and the surface's affinity falls as those sites fill. "
            "The smaller 1/n is, the more energetically heterogeneous the surface.",
                inv=fmt(inv))
        )
        if inv < 0.1:
            out.append(
                tr("1/n below ~0.1 describes an almost irreversible isotherm; uptake is "
                "nearly independent of concentration over your range. Check that this "
                "is not an artefact of too narrow a concentration window.")
            )
    elif abs(inv - 1) < 0.05:
        out.append(
            tr("With 1/n ≈ 1 the isotherm is effectively linear (Henry's law regime): "
            "loading is proportional to concentration, which means either the surface "
            "is homogeneous and far from saturation, or your concentration range is "
            "too low to probe site heterogeneity.")
        )
    else:
        out.append(
            tr("1/n = {inv} exceeds 1, giving an unfavourable, convex isotherm. "
            "This is the signature of cooperative adsorption, already-adsorbed "
            "molecules make further adsorption easier, as happens with surfactant "
            "hemimicelle formation or solute self-association on the surface. It is "
            "uncommon; check the data before claiming it.",
                inv=fmt(inv))
        )
    out.append(
        tr("The Freundlich model has no plateau: it predicts loading rising without "
        "limit as Ce increases. That is physically impossible at high concentration, "
        "so never extrapolate it beyond your measured range, and do not quote a "
        "'Freundlich capacity' as an adsorbent capacity.")
    )
    return out


FREUNDLICH = ModelSpec(
    key="freundlich", name="Freundlich", category="isotherm", family="2-parameter",
    func=_freundlich,
    equation=r"q_e = K_F\,C_e^{1/n}",
    equation_plain="qe = KF * Ce^(1/n)",
    citation="Freundlich, H.M.F. (1906) Z. Phys. Chem. 57, 385-470.",
    year="1906",
    params=[
        ParamSpec("KF", "K_F", "(mg g⁻¹)(L mg⁻¹)^(1/n)",
                  "Freundlich capacity factor. Its units depend on n, so it is "
                  "comparable only between systems with similar n.",
                  lower=1e-12, guess_fn=_kf_guess),
        ParamSpec("n", "n", "–",
                  "Heterogeneity index. 1/n < 1 is favourable adsorption on an "
                  "energetically heterogeneous surface; 1/n = 1 is linear; "
                  "1/n > 1 indicates cooperative adsorption.",
                  lower=1e-3, upper=50.0, guess_fn=_n_guess),
    ],
    assumptions=[
        "The surface is energetically heterogeneous, with an exponential "
        "distribution of site energies.",
        "Adsorption is multilayer and not limited to a fixed number of sites.",
        "The heat of adsorption falls logarithmically as coverage increases.",
    ],
    interpretation=_interp_freundlich,
    linear_forms=[
        LinearForm("log-log", "log Ce", "log qe",
                   lambda x, y, c: (np.where(x > 0, np.log10(np.where(x > 0, x, np.nan)), np.nan),
                                    np.where(y > 0, np.log10(np.where(y > 0, y, np.nan)), np.nan)),
                   lambda s, i, c: {"KF": 10 ** i, "n": 1.0 / s if s else np.nan}),
    ],
)


def _temkin(ce, at, bt, T=298.15):
    ce = np.asarray(ce, float)
    B = R_GAS * T / bt
    return B * np.log(np.clip(at * ce, 1e-300, None))


def _interp_temkin(f, ctx):
    at = f.params["AT"]; bt = f.params["bT"]
    T = ctx.get("T", 298.15)
    B = R_GAS * T / bt
    f.derived["B"] = B
    out = [
        tr("A_T = {at} L/g is the Temkin equilibrium binding constant, "
        "corresponding to the maximum binding energy.",
            at=fmt(at)),
        tr("b_T = {bt} J/mol is the Temkin constant related to the heat of "
        "adsorption, and B = RT/b_T = {B} J/mol is the Temkin heat constant.",
            bt=fmt(bt), B=fmt(B)),
        tr("The model's defining assumption is that the heat of adsorption of all "
        "molecules in the layer falls *linearly* with coverage, rather than "
        "logarithmically as Freundlich assumes, because of adsorbate–adsorbate "
        "repulsion. The fitted b_T = {bt} J/mol is the magnitude of that decline.",
            bt=fmt(bt)),
    ]
    b_kj = bt / 1000.0
    if b_kj < 8:
        out.append(
            tr("b_T = {b_kj} kJ/mol is below about 8 kJ/mol, which is usually read "
            "as physisorption; the interaction is weak, of the order of van der "
            "Waals or weak electrostatic attraction.",
                b_kj=fmt(b_kj))
        )
    elif b_kj < 16:
        out.append(
            tr("b_T = {b_kj} kJ/mol falls in the 8–16 kJ/mol window often assigned "
            "to ion exchange or strong electrostatic interaction.",
                b_kj=fmt(b_kj))
        )
    else:
        out.append(
            tr("b_T = {b_kj} kJ/mol exceeds ~16 kJ/mol, consistent with "
            "chemisorption involving genuine bond formation.",
                b_kj=fmt(b_kj))
        )
    out.append(
        tr("Treat these energy bands as rough guidance, not proof of mechanism. They "
        "were derived for specific systems and are quoted far more confidently in "
        "the literature than the underlying evidence supports.")
    )
    out.append(
        tr("The Temkin equation is undefined as Ce → 0 (it predicts qe → −∞), so it "
        "should only be used over the mid-coverage range and never extrapolated to "
        "dilute solution.")
    )
    return out


TEMKIN = ModelSpec(
    key="temkin", name="Temkin", category="isotherm", family="2-parameter",
    func=_temkin,
    equation=r"q_e = \frac{RT}{b_T}\ln\!\left(A_T C_e\right)",
    equation_plain="qe = (R*T/bT) * ln(AT*Ce)",
    citation="Temkin, M.J. & Pyzhev, V. (1940) Acta Physiochim. URSS 12, 217-222.",
    year="1940",
    requires=["T"],
    params=[
        ParamSpec("AT", "A_T", "L g⁻¹",
                  "Temkin equilibrium binding constant, corresponding to the "
                  "maximum binding energy.",
                  lower=1e-12, guess_fn=lambda x, y: 1.0 / max(float(np.min(x[x > 0])), 1e-6)
                  if np.any(x > 0) else 1.0),
        ParamSpec("bT", "b_T", "J mol⁻¹",
                  "Temkin constant related to the heat of adsorption; B = RT/b_T "
                  "is the Temkin heat constant (J/mol).",
                  lower=1e-6, guess=100.0),
    ],
    assumptions=[
        "The heat of adsorption of all molecules in the layer decreases linearly "
        "with surface coverage, because of adsorbate–adsorbate repulsion.",
        "Adsorption is characterised by a uniform distribution of binding energies "
        "up to a maximum.",
        "Valid only at intermediate coverage; it diverges as Ce → 0.",
    ],
    interpretation=_interp_temkin,
    linear_forms=[
        LinearForm("qe vs ln Ce", "ln Ce", "qe",
                   lambda x, y, c: (np.where(x > 0, np.log(np.where(x > 0, x, np.nan)), np.nan), y),
                   lambda s, i, c: {"bT": R_GAS * c.get("T", 298.15) / s if s else np.nan,
                                    "AT": np.exp(i / s) if s else np.nan}),
    ],
)


def _dubinin(ce, qs, kad, T=298.15):
    ce = np.asarray(ce, float)
    eps = R_GAS * T * np.log1p(1.0 / np.clip(ce, 1e-300, None))
    return qs * np.exp(-kad * eps ** 2)


def _interp_dr(f, ctx):
    qs = f.params["qs"]; kad = f.params["Kad"]
    E = 1.0 / np.sqrt(2.0 * kad) / 1000.0 if kad > 0 else np.nan   # kJ/mol
    f.derived["E_kJ_mol"] = E
    out = [
        tr("q_s = {qs} mg/g is the theoretical saturation capacity, which in the "
        "Dubinin–Radushkevich picture is the capacity for filling the *micropore "
        "volume* rather than for covering a surface as a monolayer. It is normally "
        "larger than the Langmuir q_max for the same data.",
            qs=fmt(qs)),
        tr("K_ad = {kad} mol²/J² is the activity coefficient related to the mean "
        "adsorption energy.",
            kad=fmt(kad)),
        tr("The mean free energy of adsorption is E = 1/√(2·K_ad) = {E} kJ/mol. "
        "This is the energy released when one mole of adsorbate is transferred to "
        "the surface from infinity in solution, and it is the parameter this model "
        "exists to deliver.",
            E=fmt(E)),
    ]
    if not np.isfinite(E):
        out.append(tr("E could not be computed because K_ad is not positive."))
    elif E < 8:
        out.append(
            tr("E = {E} kJ/mol is below 8 kJ/mol, which indicates **physisorption**, "
            "the adsorbate is held by van der Waals forces, hydrogen bonding or weak "
            "electrostatics. Such adsorption is typically fast, fully reversible, and "
            "the adsorbent should regenerate easily.",
                E=fmt(E))
        )
    elif E <= 16:
        out.append(
            tr("E = {E} kJ/mol lies in the 8–16 kJ/mol band, the classical signature "
            "of **ion exchange**: the adsorbate displaces a counter-ion from the "
            "surface rather than forming a covalent bond.",
                E=fmt(E))
        )
    else:
        out.append(
            tr("E = {E} kJ/mol is above 16 kJ/mol, pointing to **chemisorption**, "
            "genuine chemical bond formation between adsorbate and surface. Expect "
            "slow kinetics, poor reversibility and difficult regeneration.",
                E=fmt(E))
        )
    out.append(
        tr("One caveat that most papers skip: the Polanyi potential used here, "
        "ε = RT·ln(1 + 1/Ce), requires Ce in mol/L for E to come out in J/mol. "
        "AdsorpFit converts for you when you supply the molar mass; if you did not, "
        "the E value above inherits the units of your Ce and is not comparable with "
        "published values.")
    )
    return out


DUBININ = ModelSpec(
    key="dubinin_radushkevich", name="Dubinin–Radushkevich", category="isotherm",
    family="2-parameter", func=_dubinin,
    equation=r"q_e = q_s \exp\!\left(-K_{ad}\,\varepsilon^2\right),\quad "
             r"\varepsilon = RT\ln\!\left(1 + \tfrac{1}{C_e}\right)",
    equation_plain="qe = qs*exp(-Kad*eps^2), eps = R*T*ln(1 + 1/Ce)",
    citation="Dubinin, M.M. & Radushkevich, L.V. (1947) Proc. Acad. Sci. USSR 55, 331-337.",
    year="1947",
    requires=["T"],
    params=[
        ParamSpec("qs", "q_s", "mg g⁻¹",
                  "Theoretical saturation capacity, micropore volume filling "
                  "capacity, generally larger than the Langmuir monolayer q_max.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("Kad", "K_ad", "mol² J⁻²",
                  "Constant related to the mean adsorption energy; "
                  "E = 1/√(2·K_ad) gives the mean free energy of adsorption.",
                  lower=1e-14, upper=1e-2, guess=1e-8),
    ],
    assumptions=[
        "Adsorption proceeds by pore filling rather than layer-by-layer coverage.",
        "The adsorption potential is temperature-invariant (the characteristic curve).",
        "Designed for microporous adsorbents; less appropriate for flat surfaces.",
        "Gives the mean free energy E, which is the model's main purpose.",
    ],
    interpretation=_interp_dr,
    linear_forms=[
        LinearForm("ln qe vs ε²", "ε² (J² mol⁻²)", "ln qe",
                   lambda x, y, c: (
                       (R_GAS * c.get("T", 298.15) * np.log1p(1.0 / np.clip(x, 1e-300, None))) ** 2,
                       np.where(y > 0, np.log(np.where(y > 0, y, np.nan)), np.nan)),
                   lambda s, i, c: {"qs": np.exp(i), "Kad": -s}),
    ],
)


def _jovanovic(ce, qm, kj):
    return qm * (1.0 - np.exp(-kj * np.clip(np.asarray(ce, float), 0, None)))


JOVANOVIC = ModelSpec(
    key="jovanovic", name="Jovanović", category="isotherm", family="2-parameter",
    func=_jovanovic,
    equation=r"q_e = q_{max}\left[1 - e^{-K_J C_e}\right]",
    equation_plain="qe = qmax*(1 - exp(-KJ*Ce))",
    citation="Jovanović, D.S. (1969) Kolloid-Z. Z. Polym. 235, 1203-1214.",
    year="1969",
    params=[
        ParamSpec("qm", "q_max", "mg g⁻¹",
                  "Maximum monolayer capacity, defined as in Langmuir.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("KJ", "K_J", "L mg⁻¹",
                  "Jovanović affinity constant.",
                  lower=1e-12, guess_fn=_khalf_guess),
    ],
    assumptions=[
        "Monolayer coverage as in Langmuir, but allowing for mechanical contact "
        "between adsorbing and desorbing molecules.",
        "Approaches the Langmuir result at low coverage and the same plateau at "
        "saturation, but rises more sharply in between.",
    ],
    interpretation=lambda f, c: [
        tr("q_max = {qm} mg/g and K_J = {KJ} L/mg.",
            qm=fmt(f.params['qm']), KJ=fmt(f.params['KJ'])),
        tr("Jovanović differs from Langmuir by allowing mechanical contact between "
        "arriving and departing molecules. It reduces to Langmuir at low coverage "
        "and shares the same plateau, so if Jovanović fits much better than "
        "Langmuir the difference is in the approach to saturation, not the capacity."),
    ],
)


def _halsey(ce, kh, nh):
    ce = np.clip(np.asarray(ce, float), 1e-300, None)
    return np.exp((np.log(kh) - np.log(ce)) / nh)


HALSEY = ModelSpec(
    key="halsey", name="Halsey", category="isotherm", family="2-parameter",
    func=_halsey,
    equation=r"\ln q_e = \frac{1}{n_H}\ln K_H - \frac{1}{n_H}\ln C_e",
    equation_plain="qe = exp((ln(KH) - ln(Ce))/nH)",
    citation="Halsey, G. (1948) J. Chem. Phys. 16, 931-937.",
    year="1948",
    params=[
        ParamSpec("KH", "K_H", "–", "Halsey constant.", lower=1e-12, guess=1.0),
        ParamSpec("nH", "n_H", "–",
                  "Halsey exponent; values far from unity indicate multilayer "
                  "adsorption on a heterogeneous surface.",
                  lower=-50, upper=50, guess=-2.0),
    ],
    assumptions=[
        "Describes multilayer adsorption at a relatively large distance from the surface.",
        "Suited to heteroporous solids; mathematically equivalent to Freundlich "
        "with n_H = -n, so the two always give the same R².",
    ],
    interpretation=lambda f, c: [
        tr("K_H = {KH}, n_H = {nH}.",
            KH=fmt(f.params['KH']), nH=fmt(f.params['nH'])),
        tr("The Halsey equation is algebraically the Freundlich equation rewritten, "
        "with n_H = −n. Its R² will therefore always equal the Freundlich R². "
        "Reporting both as independent evidence is double counting, a common "
        "error in the literature."),
        tr("Its stated purpose is different though: Halsey was derived for multilayer "
        "condensation at some distance from the surface, so a good fit is read as "
        "evidence of heteroporous multilayer adsorption."),
    ],
    linear_forms=[
        LinearForm("ln qe vs ln Ce", "ln Ce", "ln qe",
                   lambda x, y, c: (np.where(x > 0, np.log(np.where(x > 0, x, np.nan)), np.nan),
                                    np.where(y > 0, np.log(np.where(y > 0, y, np.nan)), np.nan)),
                   lambda s, i, c: {"nH": -1.0 / s if s else np.nan,
                                    "KH": np.exp(-i / s) if s else np.nan}),
    ],
)


def _harkins_jura(ce, A, B):
    ce = np.clip(np.asarray(ce, float), 1e-300, None)
    denom = B - np.log10(ce)
    denom = np.where(np.abs(denom) < 1e-12, np.nan, denom)
    val = A / denom
    return np.sqrt(np.clip(val, 0, None))


HARKINS_JURA = ModelSpec(
    key="harkins_jura", name="Harkins–Jura", category="isotherm", family="2-parameter",
    func=_harkins_jura,
    equation=r"\frac{1}{q_e^2} = \frac{B}{A} - \frac{1}{A}\log C_e",
    equation_plain="qe = sqrt(A / (B - log10(Ce)))",
    citation="Harkins, W.D. & Jura, G. (1944) J. Chem. Phys. 12, 112-113.",
    year="1944",
    params=[
        ParamSpec("A", "A", "–",
                  "Harkins–Jura constant, proportional to the surface area of the "
                  "adsorbent.", lower=1e-12, guess=10.0),
        ParamSpec("B", "B", "–", "Harkins–Jura isotherm constant.",
                  lower=-1e6, upper=1e6, guess=1.0),
    ],
    assumptions=[
        "Multilayer adsorption on a heterogeneous pore distribution.",
        "Assumes the existence of a condensed film on the adsorbent surface.",
    ],
    interpretation=lambda f, c: [
        tr("A = {A}, B = {B}.",
            A=fmt(f.params['A']), B=fmt(f.params['B'])),
        tr("The Harkins–Jura constant A is taken as proportional to the adsorbent's "
        "surface area, so a good fit is used as evidence for multilayer adsorption "
        "across a heterogeneous distribution of pores."),
        tr("This model is very often reported with a poor R². If yours fits badly, "
        "that is the normal result for solution-phase adsorption and is worth "
        "stating rather than omitting."),
    ],
)


def _bet_liquid(ce, qs, cb, Cs=1000.0):
    ce = np.asarray(ce, float)
    x = np.clip(ce / Cs, 0, 0.999999)
    return qs * cb * x / ((1.0 - x) * (1.0 + (cb - 1.0) * x))


BET = ModelSpec(
    key="bet", name="BET (liquid phase)", category="isotherm", family="2-parameter",
    func=_bet_liquid,
    equation=r"q_e = \frac{q_s C_{BET} C_e}{(C_s - C_e)\left[1 + (C_{BET}-1)\frac{C_e}{C_s}\right]}",
    equation_plain="qe = qs*CBET*Ce / ((Cs - Ce)*(1 + (CBET-1)*Ce/Cs))",
    citation="Brunauer, S., Emmett, P.H. & Teller, E. (1938) J. Am. Chem. Soc. 60, 309-319.",
    year="1938",
    requires=["Cs"],
    params=[
        ParamSpec("qs", "q_s", "mg g⁻¹",
                  "Monolayer capacity: loading when the first layer is complete.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("cb", "C_BET", "–",
                  "BET constant; the ratio of the equilibrium constant for the "
                  "first layer to that for subsequent layers. Large C_BET means "
                  "the first layer is much more strongly bound than the rest.",
                  lower=1e-6, upper=1e8, guess=10.0),
    ],
    assumptions=[
        "Multilayer adsorption: molecules adsorb on top of already-adsorbed molecules.",
        "The first layer has a distinct adsorption energy; all higher layers have "
        "the energy of condensation of the bulk adsorbate.",
        "Requires the saturation concentration Cs, the solute's solubility limit.",
    ],
    interpretation=lambda f, c: [
        tr("Monolayer capacity q_s = {qs} mg/g; BET constant "
        "C_BET = {cb}.",
            qs=fmt(f.params['qs']), cb=fmt(f.params['cb'])),
        tr("C_BET is the ratio of the first-layer binding constant to the "
        "condensation constant of the higher layers. ")
        + (tr("A large C_BET here says the first layer is bound far more strongly "
           "than subsequent ones, so the isotherm shows a clear knee at monolayer "
           "completion (type II behaviour).")
           if f.params['cb'] > 50 else
           tr("A small C_BET means first-layer and multilayer energies are similar, so "
           "there is no sharp monolayer point and q_s is poorly defined.")),
        tr("The liquid-phase BET model needs the solubility limit Cs. If you left it "
        "at the default, q_s and C_BET are not physically meaningful; enter the "
        "real saturation concentration in the experiment panel."),
    ],
)


def _flory_huggins(c0_arr, kfh, nfh, C0=None):
    # theta/C0 = KFH * (1-theta)^nFH  -> returned as theta for given C0
    raise NotImplementedError


def _elovich_iso(ce, qm, ke, _iter=60):
    """Elovich isotherm, solved by fixed-point iteration.

    qe/qm = Ke*Ce*exp(-qe/qm) is implicit in qe; iterate theta until stable.
    """
    ce = np.asarray(ce, float)
    theta = np.full_like(ce, 0.3)
    for _ in range(_iter):
        new = np.clip(ke * ce * np.exp(-theta), 0, 50)
        theta = 0.5 * theta + 0.5 * new          # damped to keep it stable
    return qm * theta


ELOVICH_ISO = ModelSpec(
    key="elovich_isotherm", name="Elovich (isotherm)", category="isotherm",
    family="2-parameter", func=_elovich_iso,
    equation=r"\frac{q_e}{q_m} = K_E C_e \exp\!\left(-\frac{q_e}{q_m}\right)",
    equation_plain="qe/qm = KE*Ce*exp(-qe/qm)   (implicit)",
    citation="Elovich, S.Y. & Larinov, O.G. (1962) Izv. Akad. Nauk. SSSR, Otd. Khim. Nauk 2, 209-216.",
    year="1962",
    params=[
        ParamSpec("qm", "q_m", "mg g⁻¹", "Elovich maximum adsorption capacity.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("KE", "K_E", "L mg⁻¹", "Elovich equilibrium constant.",
                  lower=1e-12, guess_fn=_khalf_guess),
    ],
    assumptions=[
        "Adsorption sites increase exponentially with coverage, implying "
        "multilayer adsorption.",
        "Derived from a kinetic principle rather than an equilibrium one.",
    ],
    interpretation=lambda f, c: [
        tr("q_m = {qm} mg/g, K_E = {KE} L/mg.",
            qm=fmt(f.params['qm']), KE=fmt(f.params['KE'])),
        tr("The Elovich isotherm assumes the number of available sites grows "
        "exponentially with coverage, which implies multilayer adsorption. "
        "It is implicit in qe, so AdsorpFit solves it numerically at every point "
        "rather than using the usual ln(qe/Ce) linear plot."),
    ],
)


# --------------------------------------------------------------------------
# 3-parameter models
# --------------------------------------------------------------------------

def _sips(ce, qm, ks, ms):
    ce = np.clip(np.asarray(ce, float), 0, None)
    t = ks * _safe_pow(ce, ms)
    return qm * t / (1.0 + t)


def _interp_sips(f, ctx):
    qm = f.params["qm"]; ks = f.params["Ks"]; ms = f.params["ms"]
    out = [
        tr("q_max = {qm} mg/g is the saturation capacity. Because Sips has a real "
        "plateau (unlike Freundlich), this capacity is physically meaningful.",
            qm=fmt(qm)),
        tr("K_s = {ks} (L/mg)^m is the affinity constant and m_s = {ms} is the "
        "heterogeneity index.",
            ks=fmt(ks), ms=fmt(ms)),
        tr("Sips (Langmuir–Freundlich) is a hybrid: it behaves like Freundlich at low "
        "concentration and like Langmuir at high concentration, which fixes "
        "Freundlich's unbounded growth while keeping its ability to describe a "
        "heterogeneous surface."),
    ]
    if abs(ms - 1) < 0.05:
        out.append(
            tr("m_s = {ms} is essentially 1, at which point Sips reduces exactly to "
            "the Langmuir equation. The surface is behaving as energetically "
            "homogeneous, and the third parameter is buying you nothing; prefer "
            "Langmuir on parsimony grounds.",
                ms=fmt(ms))
        )
    elif ms < 1:
        out.append(
            tr("m_s = {ms} < 1 indicates a heterogeneous surface. The further m_s "
            "falls below 1, the broader the distribution of site energies. This is "
            "the usual result for activated carbons, biochars and most natural "
            "adsorbents.",
                ms=fmt(ms))
        )
    else:
        out.append(
            tr("m_s = {ms} > 1 implies positive cooperativity between adsorbed "
            "molecules. It is unusual: confirm it is not an artefact of a sparse "
            "high-concentration region.",
                ms=fmt(ms))
        )
    return out


SIPS = ModelSpec(
    key="sips", name="Sips (Langmuir–Freundlich)", category="isotherm",
    family="3-parameter", func=_sips,
    equation=r"q_e = \frac{q_{max}(K_s C_e)^{m_s}}{1 + (K_s C_e)^{m_s}}",
    equation_plain="qe = qmax*(Ks*Ce)^ms / (1 + (Ks*Ce)^ms)",
    citation="Sips, R. (1948) J. Chem. Phys. 16, 490-495.",
    year="1948",
    params=[
        ParamSpec("qm", "q_max", "mg g⁻¹",
                  "Saturation capacity: a genuine plateau, unlike Freundlich.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("Ks", "K_s", "(L mg⁻¹)^m", "Sips affinity constant.",
                  lower=1e-12, guess_fn=_khalf_guess),
        ParamSpec("ms", "m_s", "–",
                  "Heterogeneity index. m_s = 1 recovers Langmuir exactly; "
                  "m_s < 1 indicates a heterogeneous surface.",
                  lower=1e-3, upper=10.0, guess=1.0),
    ],
    assumptions=[
        "A hybrid of Langmuir and Freundlich: Freundlich-like at low Ce, "
        "Langmuir-like at high Ce.",
        "Reduces exactly to Langmuir when m_s = 1 and to Freundlich at low Ce.",
        "Describes localised adsorption without adsorbate–adsorbate interaction.",
    ],
    interpretation=_interp_sips,
)


def _toth(ce, qm, kt, nt):
    ce = np.clip(np.asarray(ce, float), 0, None)
    return qm * kt * ce / _safe_pow(1.0 + _safe_pow(kt * ce, nt), 1.0 / nt)


def _interp_toth(f, ctx):
    nt = f.params["nt"]
    out = [
        tr("q_max = {qm} mg/g, K_T = {KT} L/mg, "
        "n_T = {nt}.",
            qm=fmt(f.params['qm']), KT=fmt(f.params['KT']), nt=fmt(nt)),
        tr("Tóth was designed to fix Langmuir's poor behaviour at both ends of the "
        "concentration range simultaneously. It satisfies the Henry's law limit as "
        "Ce → 0 and saturates correctly at high Ce, which is why it usually "
        "outperforms Langmuir on wide-range data."),
    ]
    if abs(nt - 1) < 0.05:
        out.append(
            tr("n_T = {nt} ≈ 1 collapses Tóth to Langmuir. The surface is behaving "
            "homogeneously; the extra parameter is not earning its place.",
                nt=fmt(nt))
        )
    else:
        out.append(
            tr("n_T = {nt} departs from 1, and the size of that departure is the "
            "model's measure of surface heterogeneity, the further from 1, the more "
            "asymmetric the underlying distribution of site energies.",
                nt=fmt(nt))
        )
    return out


TOTH = ModelSpec(
    key="toth", name="Tóth", category="isotherm", family="3-parameter",
    func=_toth,
    equation=r"q_e = \frac{q_{max} K_T C_e}{\left[1 + (K_T C_e)^{n_T}\right]^{1/n_T}}",
    equation_plain="qe = qmax*KT*Ce / (1 + (KT*Ce)^nT)^(1/nT)",
    citation="Tóth, J. (1971) Acta Chim. Acad. Sci. Hung. 69, 311-328.",
    year="1971",
    params=[
        ParamSpec("qm", "q_max", "mg g⁻¹", "Tóth saturation capacity.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("KT", "K_T", "L mg⁻¹", "Tóth affinity constant.",
                  lower=1e-12, guess_fn=_khalf_guess),
        ParamSpec("nt", "n_T", "–",
                  "Heterogeneity parameter. n_T = 1 reduces Tóth to Langmuir; "
                  "the departure from 1 measures surface heterogeneity.",
                  lower=1e-3, upper=10.0, guess=1.0),
    ],
    assumptions=[
        "Derived from potential theory for heterogeneous adsorption.",
        "Obeys the Henry's law limit as Ce → 0 and saturates at high Ce, the "
        "main advantage over Langmuir and Freundlich respectively.",
        "Assumes an asymmetric quasi-Gaussian distribution of site energies, with "
        "most sites having energies below the mean.",
    ],
    interpretation=_interp_toth,
)


def _redlich_peterson(ce, krp, arp, g):
    ce = np.clip(np.asarray(ce, float), 0, None)
    return krp * ce / (1.0 + arp * _safe_pow(ce, g))


def _interp_rp(f, ctx):
    g = f.params["g"]; krp = f.params["KRP"]; arp = f.params["aRP"]
    out = [
        tr("K_RP = {krp} L/g, a_RP = {arp} (L/mg)^g, g = {g}.",
            krp=fmt(krp), arp=fmt(arp), g=fmt(g)),
        tr("Redlich–Peterson is a three-parameter compromise that combines features of "
        "Langmuir and Freundlich; the numerator is Langmuir-like and the "
        "denominator's exponent g controls how the model interpolates between them."),
    ]
    if abs(g - 1) < 0.05:
        out.append(
            tr("g = {g} ≈ 1 reduces Redlich–Peterson exactly to the Langmuir "
            "equation, with q_max = K_RP/a_RP = {v1} mg/g "
            "and K_L = a_RP = {arp} L/mg. Report Langmuir instead: it gives the "
            "same fit with one fewer parameter.",
                g=fmt(g), v1=fmt(krp / arp) if arp else 'n.d.', arp=fmt(arp))
        )
        if arp:
            f.derived["qmax_equiv"] = krp / arp
    elif g < 0.2:
        out.append(
            tr("g = {g} is close to 0, where the model approaches Henry's law "
            "(linear partitioning). Your data are probably confined to the dilute, "
            "pre-saturation region.",
                g=fmt(g))
        )
    else:
        out.append(
            tr("g = {g} lies between 0 and 1, so the isotherm is genuinely "
            "intermediate between Langmuir and Freundlich behaviour, neither "
            "two-parameter model alone would capture it.",
                g=fmt(g))
        )
    out.append(
        tr("Note that Redlich–Peterson has no plateau unless g = 1, so K_RP is not a "
        "capacity. Papers that quote K_RP in mg/g as an adsorption capacity are "
        "making a unit error.")
    )
    return out


REDLICH_PETERSON = ModelSpec(
    key="redlich_peterson", name="Redlich–Peterson", category="isotherm",
    family="3-parameter", func=_redlich_peterson,
    equation=r"q_e = \frac{K_{RP} C_e}{1 + a_{RP} C_e^{\,g}}",
    equation_plain="qe = KRP*Ce / (1 + aRP*Ce^g)",
    citation="Redlich, O. & Peterson, D.L. (1959) J. Phys. Chem. 63, 1024-1026.",
    year="1959",
    params=[
        ParamSpec("KRP", "K_RP", "L g⁻¹",
                  "Redlich–Peterson constant. Not a capacity: it has units of "
                  "L/g, not mg/g.", lower=1e-12,
                  guess_fn=lambda x, y: _kf_guess(x, y)),
        ParamSpec("aRP", "a_RP", "(L mg⁻¹)^g",
                  "Redlich–Peterson affinity constant.",
                  lower=1e-12, guess_fn=_khalf_guess),
        ParamSpec("g", "g", "–",
                  "Exponent between 0 and 1. g = 1 gives Langmuir exactly; "
                  "g → 0 gives Henry's law.",
                  lower=0.0, upper=1.0, guess=0.9),
    ],
    assumptions=[
        "An empirical hybrid of Langmuir and Freundlich.",
        "Applies over a wide concentration range and to both homogeneous and "
        "heterogeneous systems.",
        "Reduces to Langmuir at g = 1 and to Henry's law at g = 0.",
    ],
    interpretation=_interp_rp,
)


def _khan(ce, qm, bk, ak):
    ce = np.clip(np.asarray(ce, float), 0, None)
    return qm * bk * ce / _safe_pow(1.0 + bk * ce, ak)


KHAN = ModelSpec(
    key="khan", name="Khan", category="isotherm", family="3-parameter",
    func=_khan,
    equation=r"q_e = \frac{q_{max} b_K C_e}{(1 + b_K C_e)^{a_K}}",
    equation_plain="qe = qmax*bK*Ce / (1 + bK*Ce)^aK",
    citation="Khan, A.R., Al-Waheab, I.R. & Al-Haddad, A. (1996) Environ. Technol. 17, 13-23.",
    year="1996",
    params=[
        ParamSpec("qm", "q_max", "mg g⁻¹", "Khan maximum adsorption capacity.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("bK", "b_K", "L mg⁻¹", "Khan affinity constant.",
                  lower=1e-12, guess_fn=_khalf_guess),
        ParamSpec("ak", "a_K", "–",
                  "Khan exponent. a_K = 1 recovers Langmuir; a_K < 1 gives "
                  "Freundlich-like behaviour at high concentration.",
                  lower=1e-3, upper=10.0, guess=1.0),
    ],
    assumptions=[
        "A general model for pure solutions, intended for multi-component systems.",
        "Reduces to Langmuir at a_K = 1 and to Freundlich at high Ce with a_K < 1.",
    ],
    interpretation=lambda f, c: [
        tr("q_max = {qm} mg/g, b_K = {bK} L/mg, "
        "a_K = {ak}.",
            qm=fmt(f.params['qm']), bK=fmt(f.params['bK']), ak=fmt(f.params['ak'])),
        (tr("a_K ≈ 1, so Khan has collapsed to Langmuir; use Langmuir instead.")
         if abs(f.params['ak'] - 1) < 0.05 else
         tr("a_K = {ak} departs from 1, so the isotherm is "
         "Freundlich-like at the high-concentration end. Khan was formulated for "
         "multicomponent systems, so a strong Khan fit is sometimes taken as a "
         "hint that more than one solute species is competing for sites.",
             ak=fmt(f.params['ak']))),
    ],
)


def _radke_prausnitz(ce, qm, krp, mrp):
    ce = np.clip(np.asarray(ce, float), 0, None)
    return qm * krp * ce / _safe_pow(1.0 + krp * ce, mrp)


RADKE_PRAUSNITZ = ModelSpec(
    key="radke_prausnitz", name="Radke–Prausnitz", category="isotherm",
    family="3-parameter", func=_radke_prausnitz,
    equation=r"q_e = \frac{q_{max} K_{RP} C_e}{(1 + K_{RP} C_e)^{m_{RP}}}",
    equation_plain="qe = qmax*KRP*Ce / (1 + KRP*Ce)^mRP",
    citation="Radke, C.J. & Prausnitz, J.M. (1972) Ind. Eng. Chem. Fundam. 11, 445-451.",
    year="1972",
    params=[
        ParamSpec("qm", "q_max", "mg g⁻¹", "Radke–Prausnitz maximum capacity.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("KRP", "K_RP", "L mg⁻¹", "Radke–Prausnitz affinity constant.",
                  lower=1e-12, guess_fn=_khalf_guess),
        ParamSpec("mrp", "m_RP", "–",
                  "Radke–Prausnitz exponent; m_RP = 1 gives Langmuir, "
                  "m_RP = 0 gives Henry's law.",
                  lower=0.0, upper=10.0, guess=1.0),
    ],
    assumptions=[
        "Performs particularly well at dilute concentrations, its original purpose.",
        "Reduces to Langmuir at m_RP = 1, to Freundlich at intermediate values, "
        "and to Henry's law at m_RP = 0.",
    ],
    interpretation=lambda f, c: [
        tr("q_max = {qm} mg/g, K_RP = {KRP} L/mg, "
        "m_RP = {mrp}.",
            qm=fmt(f.params['qm']), KRP=fmt(f.params['KRP']), mrp=fmt(f.params['mrp'])),
        tr("Radke–Prausnitz was built for dilute solutions, so it is the model to "
        "prefer when your data cluster at low Ce and you care about behaviour near "
        "the origin rather than near saturation."),
    ],
)


def _hill(ce, qsh, kd, nh):
    ce = np.clip(np.asarray(ce, float), 0, None)
    cn = _safe_pow(ce, nh)
    return qsh * cn / (kd + cn)


def _interp_hill(f, ctx):
    nh = f.params["nH"]
    out = [
        tr("q_SH = {qsh} mg/g is the Hill saturation capacity and "
        "K_D = {KD} is the Hill dissociation constant.",
            qsh=fmt(f.params['qsh']), KD=fmt(f.params['KD'])),
        tr("The Hill coefficient is n_H = {nh}. This is the model's whole point: "
        "it quantifies cooperativity between binding sites, an idea imported from "
        "ligand binding to macromolecules.",
            nh=fmt(nh)),
    ]
    if nh > 1.05:
        out.append(
            tr("n_H = {nh} > 1 means **positive cooperativity**: binding of the "
            "first molecules increases the affinity of the remaining sites. The "
            "isotherm is sigmoidal rather than concave.",
                nh=fmt(nh))
        )
    elif nh < 0.95:
        out.append(
            tr("n_H = {nh} < 1 means **negative cooperativity**: each bound "
            "molecule makes subsequent binding harder, which is the behaviour "
            "expected on a heterogeneous surface where the best sites fill first.",
                nh=fmt(nh))
        )
    else:
        out.append(
            tr("n_H ≈ 1 means **non-cooperative** binding, sites act independently, "
            "and Hill reduces to the Langmuir form.")
        )
    return out


HILL = ModelSpec(
    key="hill", name="Hill", category="isotherm", family="3-parameter",
    func=_hill,
    equation=r"q_e = \frac{q_{SH} C_e^{\,n_H}}{K_D + C_e^{\,n_H}}",
    equation_plain="qe = qSH*Ce^nH / (KD + Ce^nH)",
    citation="Hill, A.V. (1910) J. Physiol. 40, iv-vii.",
    year="1910",
    params=[
        ParamSpec("qsh", "q_SH", "mg g⁻¹", "Hill saturation capacity.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("KD", "K_D", "–", "Hill dissociation constant.",
                  lower=1e-12, guess=1.0),
        ParamSpec("nH", "n_H", "–",
                  "Hill cooperativity coefficient. n_H > 1 positive cooperativity; "
                  "n_H = 1 independent sites; n_H < 1 negative cooperativity.",
                  lower=1e-3, upper=20.0, guess=1.0),
    ],
    assumptions=[
        "Derived for binding of a ligand to a homogeneous substrate.",
        "Explicitly models cooperativity, whether bound molecules help or hinder "
        "further binding at the remaining sites.",
        "Can produce sigmoidal isotherms, which Langmuir and Freundlich cannot.",
    ],
    interpretation=_interp_hill,
)


def _koble_corrigan(ce, A, B, n):
    ce = np.clip(np.asarray(ce, float), 0, None)
    cn = _safe_pow(ce, n)
    return A * cn / (1.0 + B * cn)


KOBLE_CORRIGAN = ModelSpec(
    key="koble_corrigan", name="Koble–Corrigan", category="isotherm",
    family="3-parameter", func=_koble_corrigan,
    equation=r"q_e = \frac{A\,C_e^{\,n}}{1 + B\,C_e^{\,n}}",
    equation_plain="qe = A*Ce^n / (1 + B*Ce^n)",
    citation="Koble, R.A. & Corrigan, T.E. (1952) Ind. Eng. Chem. 44, 383-387.",
    year="1952",
    params=[
        ParamSpec("A", "A", "(mg g⁻¹)(L mg⁻¹)^n", "Koble–Corrigan capacity constant.",
                  lower=1e-12, guess_fn=_kf_guess),
        ParamSpec("B", "B", "(L mg⁻¹)^n", "Koble–Corrigan affinity constant.",
                  lower=1e-12, guess_fn=_khalf_guess),
        ParamSpec("n", "n", "–",
                  "Koble–Corrigan exponent; n = 1 reduces the model to Langmuir.",
                  lower=1e-3, upper=10.0, guess=1.0),
    ],
    assumptions=[
        "An empirical combination of the Langmuir and Freundlich forms.",
        "n must be ≥ 1 for the model to be thermodynamically consistent; n < 1 "
        "means the data are better described by another model.",
        "Saturation capacity is A/B.",
    ],
    interpretation=lambda f, c: [
        tr("A = {A}, B = {B}, n = {n}. "
        "The implied saturation capacity is A/B = "
        "{v1} mg/g.",
            A=fmt(f.params['A']), B=fmt(f.params['B']), n=fmt(f.params['n']), v1=fmt(f.params['A'] / f.params['B']) if f.params['B'] else 'n.d.'),
        (tr("n ≈ 1, so Koble–Corrigan has reduced to Langmuir.")
         if abs(f.params['n'] - 1) < 0.05 else
         (tr("n > 1 as required for thermodynamic consistency; the model is "
          "describing a heterogeneous surface.")
          if f.params['n'] > 1 else
          tr("n < 1 here. Koble and Corrigan noted that n below 1 makes the model "
          "thermodynamically inconsistent, so this fit should not be reported as "
          "evidence of anything: another model describes these data better."))),
    ],
)


def _brouers_sotolongo(ce, qm, kbs, alpha):
    ce = np.clip(np.asarray(ce, float), 0, None)
    return qm * (1.0 - np.exp(-kbs * _safe_pow(ce, alpha)))


BROUERS_SOTOLONGO = ModelSpec(
    key="brouers_sotolongo", name="Brouers–Sotolongo (deformed Weibull)",
    category="isotherm", family="3-parameter", func=_brouers_sotolongo,
    equation=r"q_e = q_{max}\left[1 - \exp\!\left(-K_{BS} C_e^{\,\alpha}\right)\right]",
    equation_plain="qe = qmax*(1 - exp(-KBS*Ce^alpha))",
    citation="Brouers, F. et al. (2005) J. Hazard. Mater. 138, 591-597.",
    year="2005",
    params=[
        ParamSpec("qm", "q_max", "mg g⁻¹", "Brouers–Sotolongo maximum capacity.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("KBS", "K_BS", "(L mg⁻¹)^α", "Brouers–Sotolongo constant.",
                  lower=1e-12, guess_fn=_khalf_guess),
        ParamSpec("alpha", "α", "–",
                  "Fractal/heterogeneity exponent; α = 1 recovers Jovanović. "
                  "Smaller α means a broader distribution of site energies.",
                  lower=1e-3, upper=10.0, guess=1.0),
    ],
    assumptions=[
        "Derived from a statistical distribution of adsorption energies "
        "(a deformed exponential / Weibull form).",
        "α characterises the width of the site-energy distribution.",
        "Reduces to the Jovanović isotherm when α = 1.",
    ],
    interpretation=lambda f, c: [
        tr("q_max = {qm} mg/g, K_BS = {KBS}, "
        "α = {alpha}.",
            qm=fmt(f.params['qm']), KBS=fmt(f.params['KBS']), alpha=fmt(f.params['alpha'])),
        tr("α is the fractal exponent describing the width of the site-energy "
        "distribution. ")
        + (tr("α ≈ 1 recovers the Jovanović isotherm, a narrow, near-uniform energy "
           "distribution.")
           if abs(f.params['alpha'] - 1) < 0.05 else
           tr("α = {alpha} indicates a broad distribution of site "
           "energies; the further α is from 1, the more heterogeneous the surface.",
               alpha=fmt(f.params['alpha']))),
    ],
)


def _fritz_schlunder_3(ce, qm, K, a, b=None):
    raise NotImplementedError


def _vieth_sladek(ce, kvs, qm, b):
    ce = np.clip(np.asarray(ce, float), 0, None)
    return kvs * ce + qm * b * ce / (1.0 + b * ce)


VIETH_SLADEK = ModelSpec(
    key="vieth_sladek", name="Vieth–Sladek", category="isotherm",
    family="3-parameter", func=_vieth_sladek,
    equation=r"q_e = k_{VS} C_e + \frac{q_{max} b\,C_e}{1 + b\,C_e}",
    equation_plain="qe = kVS*Ce + qmax*b*Ce/(1 + b*Ce)",
    citation="Vieth, W.R. & Sladek, K.J. (1965) J. Colloid Sci. 20, 1014-1033.",
    year="1965",
    params=[
        ParamSpec("kVS", "k_VS", "L g⁻¹",
                  "Henry's law constant for the linearly dissolved fraction.",
                  lower=0.0, guess=0.1),
        ParamSpec("qm", "q_max", "mg g⁻¹",
                  "Langmuir-type capacity for the site-bound fraction.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("b", "b", "L mg⁻¹", "Langmuir affinity of the bound fraction.",
                  lower=1e-12, guess_fn=_khalf_guess),
    ],
    assumptions=[
        "Two populations of adsorbate coexist: one dissolved into the solid "
        "following Henry's law, one bound to discrete sites following Langmuir.",
        "Originally derived for gas diffusion in polymers; used for adsorbents "
        "with both a dissolution and a site-binding mechanism.",
    ],
    interpretation=lambda f, c: [
        tr("Henry constant k_VS = {kVS} L/g; Langmuir part "
        "q_max = {qm} mg/g, b = {b} L/mg.",
            kVS=fmt(f.params['kVS']), qm=fmt(f.params['qm']), b=fmt(f.params['b'])),
        tr("Vieth–Sladek splits uptake into a linear 'dissolution' term and a "
        "saturable site-binding term. A large k_VS relative to the Langmuir term "
        "says partitioning into the bulk of the solid dominates; a small one says "
        "surface site binding does."),
    ],
)


# --------------------------------------------------------------------------
# 4-parameter models
# --------------------------------------------------------------------------

def _fritz_schlunder_4(ce, A, B, alpha, beta):
    ce = np.clip(np.asarray(ce, float), 0, None)
    return A * _safe_pow(ce, alpha) / (1.0 + B * _safe_pow(ce, beta))


FRITZ_SCHLUNDER = ModelSpec(
    key="fritz_schlunder", name="Fritz–Schlünder (IV)", category="isotherm",
    family="4-parameter", func=_fritz_schlunder_4,
    equation=r"q_e = \frac{A\,C_e^{\,\alpha}}{1 + B\,C_e^{\,\beta}}",
    equation_plain="qe = A*Ce^alpha / (1 + B*Ce^beta)",
    citation="Fritz, W. & Schlünder, E.U. (1974) Chem. Eng. Sci. 29, 1279-1282.",
    year="1974",
    params=[
        ParamSpec("A", "A", "–", "Fritz–Schlünder capacity parameter.",
                  lower=1e-12, guess_fn=_kf_guess),
        ParamSpec("B", "B", "–", "Fritz–Schlünder affinity parameter.",
                  lower=1e-12, guess_fn=_khalf_guess),
        ParamSpec("alpha", "α", "–",
                  "Numerator exponent; must satisfy α ≤ 1 for consistency.",
                  lower=1e-3, upper=5.0, guess=0.8),
        ParamSpec("beta", "β", "–",
                  "Denominator exponent; α = β reduces the model to "
                  "Langmuir–Freundlich (Sips).",
                  lower=1e-3, upper=5.0, guess=0.8),
    ],
    assumptions=[
        "A flexible empirical equation with no single mechanistic derivation.",
        "Reduces to Langmuir when α = β = 1 and to Sips when α = β.",
        "Its flexibility means it almost always fits well, which makes a good "
        "fit weak evidence for anything mechanistic.",
    ],
    interpretation=lambda f, c: [
        tr("A = {A}, B = {B}, "
        "α = {alpha}, β = {beta}.",
            A=fmt(f.params['A']), B=fmt(f.params['B']), alpha=fmt(f.params['alpha']), beta=fmt(f.params['beta'])),
        (tr("α ≈ β, which means Fritz–Schlünder has reduced to the Sips equation. "
         "Fit Sips instead and save two parameters.")
         if abs(f.params['alpha'] - f.params['beta']) < 0.05 else
         tr("α and β differ, so the model is using its full flexibility to bend the "
         "isotherm's low- and high-concentration ends independently.")),
        tr("Be careful how you present this result. With four adjustable parameters "
        "Fritz–Schlünder will fit almost any monotonic dataset, so a high R² is "
        "close to guaranteed and carries little mechanistic information. Compare it "
        "to simpler models on AICc, not on R²."),
    ],
)


def _baudu(ce, qm, b0, x, y_):
    ce = np.clip(np.asarray(ce, float), 1e-300, None)
    return qm * b0 * _safe_pow(ce, 1.0 + x + y_) / (1.0 + b0 * _safe_pow(ce, 1.0 + x))


BAUDU = ModelSpec(
    key="baudu", name="Baudu", category="isotherm", family="4-parameter",
    func=_baudu,
    equation=r"q_e = \frac{q_{max} b_0 C_e^{\,1+x+y}}{1 + b_0 C_e^{\,1+x}}",
    equation_plain="qe = qmax*b0*Ce^(1+x+y) / (1 + b0*Ce^(1+x))",
    citation="Baudu, M. (1990) PhD thesis, Université de Rennes; "
             "see Limousin, G. et al. (2007) Appl. Geochem. 22, 249-275.",
    year="1990",
    params=[
        ParamSpec("qm", "q_max", "mg g⁻¹", "Baudu maximum adsorption capacity.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("b0", "b_0", "L mg⁻¹", "Baudu equilibrium constant.",
                  lower=1e-12, guess_fn=_khalf_guess),
        ParamSpec("x", "x", "–", "Baudu parameter; x + y < 0 is required.",
                  lower=-1.0, upper=1.0, guess=-0.1),
        ParamSpec("y", "y", "–", "Baudu parameter; 1 + x + y must lie in (0, 1).",
                  lower=-1.0, upper=1.0, guess=-0.1),
    ],
    assumptions=[
        "An extension of Langmuir in which the affinity b_0 is itself allowed to "
        "vary with coverage.",
        "Valid only over a restricted range: 1 + x + y and 1 + x must both stay "
        "between 0 and 1.",
    ],
    interpretation=lambda f, c: [
        tr("q_max = {qm} mg/g, b_0 = {b0} L/mg, "
        "x = {x}, y = {y}.",
            qm=fmt(f.params['qm']), b0=fmt(f.params['b0']), x=fmt(f.params['x']), y=fmt(f.params['y'])),
        tr("Baudu generalises Langmuir by letting the affinity constant itself depend "
        "on coverage: which is why it captures isotherms that Langmuir's fixed "
        "affinity cannot."),
        (tr("Validity check passed: 1 + x + y = "
         "{v2} and 1 + x = "
         "{v1} both lie in (0, 1), as the model requires.",
            v2=fmt(1 + f.params['x'] + f.params['y']), v1=fmt(1 + f.params['x']))
         if 0 < 1 + f.params['x'] + f.params['y'] < 1
         and 0 < 1 + f.params['x'] < 1 else
         tr("Validity check FAILED: the Baudu model requires both 1 + x + y and 1 + x "
         "to lie between 0 and 1. Your fitted values fall outside that range, so "
         "these parameters are outside the model's domain of applicability and "
         "should not be reported.")),
    ],
)


def _marczewski_jaroniec(ce, qm, K, m, n):
    ce = np.clip(np.asarray(ce, float), 0, None)
    t = _safe_pow(K * ce, n)
    return qm * _safe_pow(t / (1.0 + t), m / n)


MARCZEWSKI_JARONIEC = ModelSpec(
    key="marczewski_jaroniec", name="Marczewski–Jaroniec", category="isotherm",
    family="4-parameter", func=_marczewski_jaroniec,
    equation=r"q_e = q_{max}\left[\frac{(K C_e)^n}{1 + (K C_e)^n}\right]^{m/n}",
    equation_plain="qe = qmax*[ (K*Ce)^n / (1 + (K*Ce)^n) ]^(m/n)",
    citation="Marczewski, A.W. & Jaroniec, M. (1983) Monatsh. Chem. 114, 711-715.",
    year="1983",
    params=[
        ParamSpec("qm", "q_max", "mg g⁻¹", "Marczewski–Jaroniec capacity.",
                  lower=1e-12, guess_fn=_qmax_guess),
        ParamSpec("K", "K", "L mg⁻¹", "Affinity constant.",
                  lower=1e-12, guess_fn=_khalf_guess),
        ParamSpec("m", "m", "–",
                  "Controls the spread of the site-energy distribution at its "
                  "low-energy end.", lower=1e-3, upper=1.0, guess=0.8),
        ParamSpec("n", "n", "–",
                  "Controls the spread at the high-energy end; m = n gives Sips, "
                  "m = n = 1 gives Langmuir.",
                  lower=1e-3, upper=1.0, guess=0.8),
    ],
    assumptions=[
        "Derived from a generalised (quasi-Gaussian) distribution of adsorption "
        "energies, with m and n controlling each tail independently.",
        "Reduces to Langmuir–Freundlich (Sips) when m = n, and to Langmuir when "
        "m = n = 1.",
    ],
    interpretation=lambda f, c: [
        tr("q_max = {qm} mg/g, K = {K} L/mg, "
        "m = {m}, n = {n}.",
            qm=fmt(f.params['qm']), K=fmt(f.params['K']), m=fmt(f.params['m']), n=fmt(f.params['n'])),
        tr("m and n independently shape the two tails of the underlying site-energy "
        "distribution: this is the model's advantage over Sips, which forces both "
        "tails to share one exponent."),
        (tr("m ≈ n, so the distribution is symmetric and the model has reduced to "
         "Sips. Use Sips instead.")
         if abs(f.params['m'] - f.params['n']) < 0.05 else
         tr("m ≠ n, so the site-energy distribution is asymmetric: ")
         + (tr("the low-energy tail is broader.") if f.params['m'] < f.params['n']
            else tr("the high-energy tail is broader."))),
    ],
)


# --------------------------------------------------------------------------
# Domain of applicability
#
# Attached after the specs are built so each rule sits next to the others and
# can be read as a single audit of where these models break down.  Several of
# these equations are unbounded below and will happily return a negative
# loading; least squares has no objection, so the check has to be explicit.
# --------------------------------------------------------------------------

def _temkin_domain(x, y, ctx):
    """Temkin diverges to -inf as Ce -> 0, so dilute data are out of bounds."""
    out = []
    lo, hi = float(np.min(x)), float(np.max(x))
    if lo <= 0:
        return [issue("block", "temkin_zero",
                      tr("The Temkin equation contains ln(A_T·C_e) and is undefined "
                      "at C_e = 0."))]
    if hi / lo > 100:
        out.append(issue(
            "warn", "temkin_wide_range",
            tr("Your concentrations span {v1:.0f}-fold ({lo} to {hi}). "
            "Temkin is a mid-coverage approximation; it has no plateau at high "
            "C_e and diverges to −∞ as C_e → 0, so over a range this wide it is "
            "likely to misrepresent at least one end.",
                v1=hi / lo, lo=fmt(lo), hi=fmt(hi))))
    return out


def _temkin_valid_range(p, ctx):
    at = p.get("AT", 0.0)
    return (1.0 / at, np.inf) if at > 0 else (None, None)


def _temkin_validity(p, x, y, ctx):
    at = p.get("AT", 0.0)
    if at <= 0:
        return []
    c_min = 1.0 / at
    below = int(np.sum(np.asarray(x) < c_min))
    if below:
        return [issue(
            "block", "temkin_below_threshold",
            tr("With the fitted A_T = {at} L/g, the Temkin equation predicts a "
            "negative q_e for any C_e below 1/A_T = {c_min} mg/L. "
            "{below} of your {v1} points fall in that region, so the model is "
            "being extrapolated outside its own domain. Either drop the dilute "
            "points and refit over the mid-coverage range Temkin was derived for, "
            "or use a model that is bounded below, Langmuir, Sips or Tóth all "
            "behave correctly as C_e → 0.",
                at=fmt(at), c_min=fmt(c_min), below=below, v1=len(x)))]
    margin = c_min / float(np.min(x))
    if margin > 0.5:
        return [issue(
            "warn", "temkin_near_threshold",
            tr("Your lowest point (C_e = {v1}) sits close to the "
            "threshold 1/A_T = {c_min} below which Temkin turns negative. "
            "The fit is valid, but do not extrapolate it to lower concentrations.",
                v1=fmt(float(np.min(x))), c_min=fmt(c_min)))]
    return []


def _harkins_jura_valid_range(p, ctx):
    b = p.get("B", None)
    return (None, 10.0 ** b) if b is not None and np.isfinite(b) else (None, None)


def _harkins_jura_validity(p, x, y, ctx):
    b = p.get("B", np.nan)
    if not np.isfinite(b):
        return []
    c_max = 10.0 ** b
    above = int(np.sum(np.asarray(x) >= c_max))
    if above:
        return [issue(
            "block", "hj_above_threshold",
            tr("The Harkins–Jura equation contains 1/(B − log C_e) and is undefined "
            "once C_e reaches 10^B = {c_max} mg/L. {above} of your "
            "{v1} points are at or beyond that, where the model has no value "
            "to return. Those points cannot constrain the fit, so the reported "
            "statistics describe only the remaining ones.",
                c_max=fmt(c_max), above=above, v1=len(x)))]
    return []


def _bet_domain(x, y, ctx):
    cs = ctx.get("Cs")
    hi = float(np.max(x))
    if not cs:
        return [issue(
            "warn", "bet_no_cs",
            tr("The liquid-phase BET model needs the adsorbate's saturation "
            "concentration C_s (its solubility limit). Without it a placeholder is "
            "used and neither q_s nor C_BET means anything. Enter C_s in the "
            "experiment panel."))]
    if hi >= float(cs):
        return [issue(
            "block", "bet_above_cs",
            tr("Your highest C_e ({hi} mg/L) is at or above the saturation "
            "concentration C_s = {cs} mg/L. BET contains (C_s − C_e) "
            "in its denominator and diverges there; the solution would be "
            "supersaturated, which is outside the model's physical premise.",
                hi=fmt(hi), cs=fmt(float(cs))))]
    if hi / float(cs) < 0.05:
        return [issue(
            "warn", "bet_far_from_cs",
            tr("Your data reach only {v1:.1f}% of the saturation "
            "concentration. BET describes multilayer build-up, which only becomes "
            "significant as C_e approaches C_s, so there is little multilayer "
            "behaviour here for the model to detect.",
                v1=100 * hi / float(cs)))]
    return []


def _needs_positive_x(name):
    def f(x, y, ctx):
        if np.any(np.asarray(x) <= 0):
            return [issue("block", "nonpositive_x",
                          tr("The {name} equation is logarithmic in C_e and is "
                          "undefined at C_e = 0.",
                              name=name))]
        return []
    return f


def _plateau_domain(x, y, ctx):
    """Saturating models need the data to actually approach saturation.

    Judged on the terminal slope as well as the rise over the last few
    points, for the same reason as the kinetics check: with ten points the
    tail measure alone is noisy, and on real data it missed a case the
    authors themselves described as not having reached saturation. Across the
    Wang (2021) phosphate series the four isotherms that do plateau score
    0.02 to 0.13 on the slope ratio while the one that does not scores 0.48,
    so the threshold sits comfortably between them.
    """
    y = np.asarray(y, float)
    if y.size < 4:
        return []
    span = float(np.max(y) - np.min(y))
    if span <= 0:
        return []
    ratio = terminal_slope_ratio(x, y)
    k = max(1, y.size // 3)
    tail = y[-k:]
    rise = (float(np.max(tail)) - float(np.min(tail))) / span
    if ratio > 0.25 or rise > 0.25:
        return [issue(
            "warn", "no_plateau",
            tr("Your isotherm is still rising at the highest concentration: the "
            "slope over the final quarter of the range is {v2:.0f}% of "
            "the average slope, and the top third of the data accounts for "
            "{v1:.0f}% of the total change in q_e. At saturation both "
            "would be near zero. A capacity fitted to data that never plateau is "
            "an extrapolation rather than a measurement, so extend the "
            "concentration range if q_max is the number you want to report.",
                v2=ratio * 100, v1=rise * 100))]
    return []


def _baudu_validity(p, x, y, ctx):
    a, b = 1.0 + p.get("x", 0) + p.get("y", 0), 1.0 + p.get("x", 0)
    if not (0 < a < 1 and 0 < b < 1):
        return [issue(
            "block", "baudu_domain",
            tr("The Baudu model requires both 1+x+y and 1+x to lie strictly between "
            "0 and 1. The fit gives 1+x+y = {a} and 1+x = {b}, so these "
            "parameters are outside the model's stated domain of applicability "
            "and should not be reported.",
                a=fmt(a), b=fmt(b)))]
    return []


def _koble_validity(p, x, y, ctx):
    n = p.get("n", 1.0)
    if n < 1:
        return [issue(
            "warn", "koble_n_lt_1",
            tr("Koble and Corrigan noted that n must be at least 1 for the model to "
            "be thermodynamically consistent. The fit gives n = {n}, below "
            "that limit, which means another model describes these data better.",
                n=fmt(n)))]
    return []


def _dr_domain(x, y, ctx):
    if not ctx.get("MW"):
        return [issue(
            "info", "dr_units",
            tr("The Polanyi potential ε = RT·ln(1 + 1/C_e) requires C_e in mol/L for "
            "the mean free energy E to come out in J/mol. Enter the adsorbate "
            "molar mass and AdsorpFit will convert; without it, E carries the units "
            "of your C_e and is not comparable with published values."))]
    return []


LANGMUIR.domain = _plateau_domain
JOVANOVIC.domain = _plateau_domain
SIPS.domain = _plateau_domain
TOTH.domain = _plateau_domain
KHAN.domain = _plateau_domain
RADKE_PRAUSNITZ.domain = _plateau_domain
HILL.domain = _plateau_domain
BROUERS_SOTOLONGO.domain = _plateau_domain
MARCZEWSKI_JARONIEC.domain = _plateau_domain

TEMKIN.domain = _temkin_domain
TEMKIN.valid_range = _temkin_valid_range
TEMKIN.validity = _temkin_validity

HARKINS_JURA.valid_range = _harkins_jura_valid_range
HARKINS_JURA.validity = _harkins_jura_validity

BET.domain = _bet_domain
FREUNDLICH.domain = _needs_positive_x("Freundlich")
HALSEY.domain = _needs_positive_x("Halsey")
HARKINS_JURA.domain = _needs_positive_x("Harkins–Jura")
DUBININ.domain = _dr_domain
BAUDU.validity = _baudu_validity
KOBLE_CORRIGAN.validity = _koble_validity


# --------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------

ISOTHERM_MODELS = {
    m.key: m for m in [
        LANGMUIR, FREUNDLICH, TEMKIN, DUBININ, JOVANOVIC, HALSEY,
        HARKINS_JURA, BET, ELOVICH_ISO,
        SIPS, TOTH, REDLICH_PETERSON, KHAN, RADKE_PRAUSNITZ, HILL,
        KOBLE_CORRIGAN, BROUERS_SOTOLONGO, VIETH_SLADEK,
        FRITZ_SCHLUNDER, BAUDU, MARCZEWSKI_JARONIEC,
    ]
}
