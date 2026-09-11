"""
AdsorpFit - adsorption thermodynamics.

This module implements the van't Hoff analysis, the isosteric heat of
adsorption, the Arrhenius activation energy and the sticking probability.

A note on why this module is more opinionated than the others
-------------------------------------------------------------
The single most common error in the adsorption literature is feeding a
*dimensioned* equilibrium constant into

    dG0 = -R T ln K

A Langmuir K_L in L/mg is not dimensionless, so ln(K_L) is not defined, and
the dG0 that results depends on whether you happened to express
concentration in mg/L, g/L or mol/L.  Different unit choices for the same
experiment give dG0 values that differ by tens of kJ/mol - which is larger
than the effect being reported.

AdsorpFit therefore refuses to compute dG0 from a raw dimensioned constant.
It asks which route you want to use to obtain a genuinely dimensionless K0,
states the route in the output, and warns when a route is not defensible.

Routes implemented (after Lima et al. 2019, Tran & Bonilla-Petriciolet 2022,
Milonjic 2007, Zhou & Zhou 2014):

  langmuir_molar   K0 = K_L[L/mol] x 55.5[mol/L]          (recommended)
  kd_density       K0 = K_D[L/g]  x 1000[g/L]             (Milonjic route)
  kc_dimensionless K0 = (C_ads / C_solution) at equilibrium, already unitless
  redlich_peterson K0 = K_RP[L/g] x 1000[g/L]             (Tran 2023)
  freundlich       flagged as not thermodynamically defensible

References
  Lima, E.C. et al. (2019) J. Mol. Liq. 273, 425-434.
  Tran, H.N. & Bonilla-Petriciolet, A. (2022) Adsorpt. Sci. Technol. 2022, 5553212.
  Milonjic, S.K. (2007) J. Serb. Chem. Soc. 72, 1363-1367.
  Zhou, X. & Zhou, X. (2014) Chem. Eng. Commun. 201, 1459-1467.
"""

from __future__ import annotations

import numpy as np
from scipy import stats as sps

from core import R_GAS, WATER_MOLARITY, fmt


# --------------------------------------------------------------------------
# Making the equilibrium constant dimensionless
# --------------------------------------------------------------------------

K_ROUTES = {
    "langmuir_molar": {
        "label": "Langmuir K_L → molar → ×55.5 (recommended)",
        "needs": ["K_L (L/mg)", "molar mass (g/mol)"],
        "formula": r"K^\circ = K_L\,[\mathrm{L\,mol^{-1}}] \times 55.5\ \mathrm{mol\,L^{-1}}",
        "defensible": True,
        "note": "Converts K_L from L/mg to L/mol using the adsorbate molar mass, "
                "then multiplies by the molar concentration of pure water "
                "(55.5 mol/L), which is the standard state of the solvent. This "
                "is the route recommended by Lima et al. (2019) and is the one "
                "most reviewers will accept.",
    },
    "kd_density": {
        "label": "Distribution coefficient K_D × 1000 (Milonjić)",
        "needs": ["K_D = qe/Ce (L/g)"],
        "formula": r"K^\circ = K_D\,[\mathrm{L\,g^{-1}}] \times 1000\ \mathrm{g\,L^{-1}}",
        "defensible": True,
        "note": "Multiplies the distribution coefficient by the density of water "
                "(1000 g/L) to cancel units. Simple and widely used, but K_D is "
                "concentration-dependent unless the isotherm is linear, so it "
                "should be evaluated in the dilute limit (Ce → 0) rather than at "
                "an arbitrary concentration.",
    },
    "kc_dimensionless": {
        "label": "K_C from mass balance (already dimensionless)",
        "needs": ["qe, Ce, dose, volume"],
        "formula": r"K_C = \frac{C_{ads}}{C_e} = \frac{(C_0 - C_e)}{C_e}",
        "defensible": True,
        "note": "The ratio of adsorbed to residual solute concentration, both in "
                "the same units, so it is dimensionless by construction. It is "
                "legitimate but depends on the adsorbent dose, so ΔG° from this "
                "route is specific to the dose used.",
    },
    "redlich_peterson": {
        "label": "Redlich–Peterson K_RP × 1000 (Tran 2023)",
        "needs": ["K_RP (L/g)"],
        "formula": r"K^\circ = K_{RP}\,[\mathrm{L\,g^{-1}}] \times 1000\ \mathrm{g\,L^{-1}}",
        "defensible": True,
        "note": "K_RP already carries units of L/g, so the water-density "
                "conversion applies directly. Useful when Redlich–Peterson is the "
                "best-fitting isotherm.",
    },
    "freundlich": {
        "label": "Freundlich K_F (NOT recommended)",
        "needs": ["K_F"],
        "formula": r"K^\circ \approx K_F \quad\text{(dimensionally invalid)}",
        "defensible": False,
        "note": "K_F has units of (mg/g)(L/mg)^(1/n), which change with n. There "
                "is no unit conversion that makes it a proper thermodynamic "
                "equilibrium constant, because the Freundlich model has no "
                "well-defined standard state. Lima et al. (2019) and Tran & "
                "Bonilla-Petriciolet (2022) both identify this as an error. "
                "AdsorpFit computes it if you insist, but flags the result.",
    },
    "direct": {
        "label": "I already have dimensionless K° values",
        "needs": ["K° per temperature"],
        "formula": r"K^\circ \text{ supplied directly}",
        "defensible": True,
        "note": "You supply K° yourself. AdsorpFit performs no conversion and "
                "assumes you have made it dimensionless correctly.",
    },
}


def dimensionless_K(route: str, values: dict) -> dict:
    """Convert a fitted equilibrium constant into a dimensionless K°.

    ``values`` supplies whatever the chosen route needs:
        K_L    Langmuir constant in L/mg
        MW     adsorbate molar mass in g/mol
        K_D    distribution coefficient in L/g
        K_C    dimensionless mass-balance ratio
        K_RP   Redlich-Peterson constant in L/g
        K_F    Freundlich constant
        K0     already-dimensionless constant
    """
    info = K_ROUTES.get(route)
    if info is None:
        raise ValueError(f"Unknown K° route: {route}")

    warn = [] if info["defensible"] else [info["note"]]

    if route == "langmuir_molar":
        kl = float(values["K_L"])                 # L/mg
        mw = float(values["MW"])                  # g/mol
        kl_molar = kl * mw * 1000.0               # L/mg * g/mol * mg/g = L/mol
        k0 = kl_molar * WATER_MOLARITY
        detail = (f"K_L = {fmt(kl)} L/mg × {fmt(mw)} g/mol × 1000 mg/g "
                  f"= {fmt(kl_molar)} L/mol; × 55.5 mol/L → K° = {fmt(k0)}")
    elif route == "kd_density":
        kd = float(values["K_D"])
        k0 = kd * 1000.0
        detail = f"K_D = {fmt(kd)} L/g × 1000 g/L → K° = {fmt(k0)}"
    elif route == "kc_dimensionless":
        k0 = float(values["K_C"])
        detail = f"K_C = {fmt(k0)} (dimensionless by construction)"
    elif route == "redlich_peterson":
        krp = float(values["K_RP"])
        k0 = krp * 1000.0
        detail = f"K_RP = {fmt(krp)} L/g × 1000 g/L → K° = {fmt(k0)}"
    elif route == "freundlich":
        k0 = float(values["K_F"])
        detail = f"K_F = {fmt(k0)} used directly — dimensionally invalid"
    else:                                          # direct
        k0 = float(values["K0"])
        detail = f"K° = {fmt(k0)} supplied directly"

    if k0 <= 0:
        warn.append("K° is not positive, so ln K° is undefined and no "
                    "thermodynamic parameters can be computed.")
    elif k0 < 1:
        warn.append(
            f"K° = {fmt(k0)} is less than 1, so ln K° is negative and ΔG° will come "
            f"out positive — i.e. the analysis says adsorption is non-spontaneous "
            f"under standard-state conditions. That is a legitimate result, but if "
            f"your adsorbent clearly works, it usually means the K° conversion is "
            f"wrong rather than the thermodynamics."
        )

    return {"K0": k0, "route": route, "detail": detail,
            "defensible": info["defensible"], "warnings": warn}


# --------------------------------------------------------------------------
# van't Hoff
# --------------------------------------------------------------------------

def vant_hoff(T: np.ndarray, K0: np.ndarray, nonlinear: bool = False) -> dict:
    """Van't Hoff analysis: ΔH°, ΔS° from ln K° vs 1/T, then ΔG° per T.

        ln K° = ΔS°/R − ΔH°/(RT)

    slope     = −ΔH°/R      →  ΔH° = −R·slope      (J/mol)
    intercept =  ΔS°/R      →  ΔS° =  R·intercept  (J/mol/K)

    ΔG° is reported two ways, because they are not identical and the
    difference is diagnostic:
        ΔG°(T) = −RT ln K°(T)        from each temperature directly
        ΔG°(T) = ΔH° − T·ΔS°         from the regression
    A large gap between them means the van't Hoff line is not straight, i.e.
    ΔH° is not constant over your temperature range.
    """
    T = np.asarray(T, float)
    K0 = np.asarray(K0, float)
    ok = np.isfinite(T) & np.isfinite(K0) & (K0 > 0) & (T > 0)
    T, K0 = T[ok], K0[ok]

    out = {"T": T.tolist(), "K0": K0.tolist(), "warnings": []}
    if T.size < 2:
        out["error"] = ("At least two temperatures with positive K° are needed "
                        "for a van't Hoff analysis.")
        return out
    if T.size < 3:
        out["warnings"].append(
            "Only two temperatures were supplied. A two-point van't Hoff line has "
            "zero residual degrees of freedom: ΔH° and ΔS° can be computed but "
            "have no uncertainty estimate and R² is meaningless (it is always 1). "
            "Three temperatures is the practical minimum; four or five is better."
        )

    invT = 1.0 / T
    lnK = np.log(K0)
    lr = sps.linregress(invT, lnK)

    dH = -R_GAS * lr.slope                      # J/mol
    dS = R_GAS * lr.intercept                   # J/mol/K
    dH_se = R_GAS * lr.stderr if np.isfinite(lr.stderr) else np.nan
    dS_se = R_GAS * lr.intercept_stderr if np.isfinite(lr.intercept_stderr) else np.nan

    dG_direct = -R_GAS * T * lnK                # J/mol, per temperature
    dG_from_fit = dH - T * dS

    out.update({
        "slope": lr.slope, "intercept": lr.intercept,
        "R2": lr.rvalue ** 2,
        "dH_J_mol": dH, "dH_kJ_mol": dH / 1000.0, "dH_se_kJ_mol": dH_se / 1000.0,
        "dS_J_mol_K": dS, "dS_se_J_mol_K": dS_se,
        "dG_direct_kJ_mol": (dG_direct / 1000.0).tolist(),
        "dG_from_fit_kJ_mol": (dG_from_fit / 1000.0).tolist(),
        "lnK": lnK.tolist(), "invT": invT.tolist(),
    })

    # diagnostic: how well does the line actually hold?
    gap = np.max(np.abs(dG_direct - dG_from_fit)) / 1000.0
    out["dG_gap_kJ_mol"] = float(gap)
    if gap > 1.0:
        out["warnings"].append(
            f"ΔG° computed directly from each K° and ΔG° computed from ΔH° − TΔS° "
            f"differ by up to {gap:.2f} kJ/mol. That gap means the van't Hoff plot "
            f"is curved: ΔH° is not constant across your temperature range, so a "
            f"single ΔH° value misrepresents the system. Consider the non-linear "
            f"van't Hoff form with a heat-capacity term, or report ΔH° as a range."
        )
    if out["R2"] < 0.95 and T.size >= 3:
        out["warnings"].append(
            f"The van't Hoff regression has R² = {out['R2']:.4f}. Below about 0.95 "
            f"the extracted ΔH° and ΔS° are not reliable — check for an outlying "
            f"temperature or a K° conversion that varies with temperature in a way "
            f"the model does not capture."
        )

    if nonlinear and T.size >= 4:
        out["nonlinear"] = _vant_hoff_cp(T, lnK)

    return out


def _vant_hoff_cp(T, lnK, T_ref=298.15):
    """Non-linear van't Hoff allowing a constant heat capacity change ΔCp.

        ln K°(T) = -ΔH°(Tr)/R · (1/T - 1/Tr) + ΔS°(Tr)/R
                   + ΔCp/R · [ln(T/Tr) + Tr/T - 1]
    """
    from scipy.optimize import curve_fit

    def f(Tv, dH, dS, dCp):
        return (-dH / R_GAS * (1.0 / Tv - 1.0 / T_ref) + dS / R_GAS
                + dCp / R_GAS * (np.log(Tv / T_ref) + T_ref / Tv - 1.0))

    try:
        p, cov = curve_fit(f, T, lnK, p0=[2e4, 50.0, 0.0], maxfev=20000)
        se = np.sqrt(np.diag(cov))
        pred = f(T, *p)
        ss = np.sum((lnK - pred) ** 2)
        sst = np.sum((lnK - lnK.mean()) ** 2)
        return {
            "T_ref": T_ref,
            "dH_kJ_mol": p[0] / 1000.0, "dH_se_kJ_mol": se[0] / 1000.0,
            "dS_J_mol_K": p[1], "dS_se_J_mol_K": se[1],
            "dCp_J_mol_K": p[2], "dCp_se_J_mol_K": se[2],
            "R2": 1.0 - ss / sst if sst > 0 else np.nan,
            "note": "ΔH° and ΔS° are reported at the reference temperature "
                    f"{T_ref} K. A non-zero ΔCp means the van't Hoff plot is "
                    "genuinely curved and ΔH° changes with temperature.",
        }
    except Exception as exc:
        return {"error": str(exc)}


def interpret_thermo(res: dict, route_info: dict | None = None) -> list[str]:
    """Turn a van't Hoff result into prose."""
    if "error" in res:
        return [res["error"]]

    dH = res["dH_kJ_mol"]
    dS = res["dS_J_mol_K"]
    dG = res["dG_direct_kJ_mol"]
    T = res["T"]
    out = []

    if route_info:
        out.append(
            f"Equilibrium constant route: {K_ROUTES[route_info['route']]['label']}. "
            f"{route_info['detail']}. This choice is not cosmetic — a different "
            f"route gives a different ΔG°, so it must be stated explicitly in any "
            f"paper reporting these numbers."
        )

    # dG
    spont = all(g < 0 for g in dG)
    if spont:
        trend = "more negative" if dG[-1] < dG[0] else "less negative"
        out.append(
            f"ΔG° is negative at every temperature ({fmt(dG[0])} to {fmt(dG[-1])} "
            f"kJ/mol from {T[0]:.0f} to {T[-1]:.0f} K), so adsorption is "
            f"**spontaneous** and thermodynamically favourable across your whole "
            f"range. ΔG° becomes {trend} as temperature rises, meaning the driving "
            f"force {'increases' if dG[-1] < dG[0] else 'decreases'} with heating."
        )
    else:
        out.append(
            f"ΔG° is not negative at all temperatures ({fmt(min(dG))} to "
            f"{fmt(max(dG))} kJ/mol). A positive ΔG° means adsorption is "
            f"non-spontaneous under standard-state conditions at that temperature. "
            f"Before reporting this, check the K° conversion — a positive ΔG° for "
            f"an adsorbent that demonstrably removes the solute almost always "
            f"signals a units problem rather than real thermodynamics."
        )

    mag = float(np.mean(np.abs(dG)))
    if mag < 20:
        out.append(
            f"The magnitude of ΔG° (mean |ΔG°| ≈ {fmt(mag)} kJ/mol) lies in the "
            f"0–20 kJ/mol range conventionally assigned to **physisorption** — "
            f"the adsorbate is held by van der Waals forces, hydrogen bonding or "
            f"weak electrostatics."
        )
    elif mag <= 80:
        out.append(
            f"The magnitude of ΔG° (mean |ΔG°| ≈ {fmt(mag)} kJ/mol) falls in the "
            f"20–80 kJ/mol range usually taken to indicate a contribution from "
            f"**chemisorption** alongside physical interactions."
        )
    else:
        out.append(
            f"Mean |ΔG°| ≈ {fmt(mag)} kJ/mol exceeds 80 kJ/mol, which would imply "
            f"strong chemisorption. Values this large are unusual in aqueous "
            f"adsorption and are worth re-checking against the K° conversion."
        )

    # dH
    if dH > 0:
        out.append(
            f"ΔH° = {fmt(dH)} kJ/mol is **positive**, so adsorption is "
            f"**endothermic**: the system absorbs heat, and uptake improves as "
            f"temperature rises. This normally means the energy required to "
            f"dehydrate the adsorbate (strip its solvation shell) before it can "
            f"reach the surface exceeds the energy released on binding."
        )
    else:
        out.append(
            f"ΔH° = {fmt(dH)} kJ/mol is **negative**, so adsorption is "
            f"**exothermic**: heat is released on binding, and uptake falls as "
            f"temperature rises. Practically, this means running the process cold "
            f"gives higher capacity, and it makes thermal regeneration of the "
            f"adsorbent straightforward."
        )
    amag = abs(dH)
    if amag < 20:
        out.append(
            f"|ΔH°| = {fmt(amag)} kJ/mol is below ~20 kJ/mol, consistent with "
            f"**physisorption** (the enthalpy of physical adsorption is typically "
            f"2–40 kJ/mol, similar to a condensation enthalpy)."
        )
    elif amag < 40:
        out.append(
            f"|ΔH°| = {fmt(amag)} kJ/mol sits in the 20–40 kJ/mol transition zone, "
            f"where physical and chemical contributions are both plausible. Do not "
            f"claim a mechanism from this number alone — support it with the D–R "
            f"mean free energy E, spectroscopic evidence, or a reversibility test."
        )
    else:
        out.append(
            f"|ΔH°| = {fmt(amag)} kJ/mol exceeds 40 kJ/mol, which points to "
            f"**chemisorption** — bond formation rather than physical attraction. "
            f"Expect the process to be slow to reverse and the adsorbent hard to "
            f"regenerate without harsh conditions."
        )

    # dS
    if dS > 0:
        out.append(
            f"ΔS° = {fmt(dS)} J mol⁻¹ K⁻¹ is **positive**, indicating increased "
            f"randomness at the solid–liquid interface. This is the usual result in "
            f"aqueous systems and is counter-intuitive at first, because fixing a "
            f"molecule onto a surface should *lower* entropy. The resolution is "
            f"that the adsorbate and the surface are both hydrated: binding "
            f"releases several ordered water molecules per adsorbate molecule into "
            f"the bulk, and that gain outweighs the entropy lost by the adsorbate "
            f"itself. A positive ΔS° is therefore evidence of a desolvation-driven "
            f"process."
        )
    else:
        out.append(
            f"ΔS° = {fmt(dS)} J mol⁻¹ K⁻¹ is **negative**, indicating decreased "
            f"randomness at the interface: the adsorbate loses translational and "
            f"rotational freedom on binding, and that loss is not offset by "
            f"released solvation water. This is typical of adsorption onto a "
            f"well-ordered surface, or of large molecules that adopt a fixed "
            f"orientation on binding."
        )

    # driving force decomposition at the middle temperature
    Tm = float(np.mean(T))
    enth = dH
    entr = -Tm * dS / 1000.0
    if abs(enth) > abs(entr):
        out.append(
            f"Decomposing the driving force at {Tm:.0f} K: the enthalpy term "
            f"contributes {fmt(enth)} kJ/mol and the entropy term (−TΔS°) "
            f"contributes {fmt(entr)} kJ/mol. The process is **enthalpy-driven** — "
            f"the strength of the adsorbate–surface interaction, not the entropy "
            f"gain, is what makes it favourable."
        )
    else:
        out.append(
            f"Decomposing the driving force at {Tm:.0f} K: the enthalpy term "
            f"contributes {fmt(enth)} kJ/mol and the entropy term (−TΔS°) "
            f"contributes {fmt(entr)} kJ/mol. The process is **entropy-driven** — "
            f"it proceeds because of the disorder gained (largely released "
            f"solvation water), not because binding is energetically strong. This "
            f"is the common situation for endothermic adsorption, where a positive "
            f"ΔH° is overcome by a larger positive ΔS°."
        )

    out.extend(res.get("warnings", []))
    return out


# --------------------------------------------------------------------------
# Isosteric heat of adsorption
# --------------------------------------------------------------------------

def isosteric_heat(T_list, Ce_at_q, q_values) -> dict:
    """Isosteric heat from the Clausius–Clapeyron relation at constant loading.

        ln C_e = ΔH_iso/(R T) + constant        (at fixed q_e)

    ``Ce_at_q`` is an array of shape (n_loadings, n_temperatures) giving the
    equilibrium concentration required to reach each loading at each
    temperature - normally obtained by interpolating the fitted isotherms.

    This is the most physically informative thermodynamic quantity available
    from an isotherm series, because it shows how the binding enthalpy varies
    with coverage - which a single van't Hoff ΔH° cannot.
    """
    T = np.asarray(T_list, float)
    Ce = np.asarray(Ce_at_q, float)
    q = np.asarray(q_values, float)
    invT = 1.0 / T

    rows = []
    for i, qi in enumerate(q):
        y = Ce[i]
        ok = np.isfinite(y) & (y > 0)
        if ok.sum() < 2:
            rows.append({"q": float(qi), "dH_iso_kJ_mol": np.nan, "R2": np.nan})
            continue
        lr = sps.linregress(invT[ok], np.log(y[ok]))
        rows.append({
            "q": float(qi),
            "dH_iso_kJ_mol": R_GAS * lr.slope / 1000.0,
            "se_kJ_mol": R_GAS * lr.stderr / 1000.0 if np.isfinite(lr.stderr) else np.nan,
            "R2": lr.rvalue ** 2,
            "n_points": int(ok.sum()),
        })

    valid = [r for r in rows if np.isfinite(r["dH_iso_kJ_mol"])]
    trend = ""
    if len(valid) >= 3:
        qs = np.array([r["q"] for r in valid])
        hs = np.array([r["dH_iso_kJ_mol"] for r in valid])
        sl = sps.linregress(qs, hs).slope
        if abs(sl) < 1e-3 * max(1.0, float(np.mean(np.abs(hs)))):
            trend = ("The isosteric heat is essentially constant with loading, "
                     "which is the signature of an energetically **homogeneous** "
                     "surface — every site binds with the same enthalpy. This is "
                     "the assumption Langmuir makes, so a constant ΔH_iso supports "
                     "a Langmuir description.")
        elif sl > 0:
            trend = ("|ΔH_iso| decreases as loading increases (the values become "
                     "less negative). This is the classic **heterogeneous surface** "
                     "result: the highest-energy sites are occupied first, so each "
                     "additional molecule binds more weakly than the last. It "
                     "supports Freundlich, Sips or Tóth over Langmuir.")
        else:
            trend = ("|ΔH_iso| increases with loading, meaning later molecules bind "
                     "*more* strongly than earlier ones. That indicates "
                     "**cooperative adsorption** — adsorbed molecules attract "
                     "further adsorbate, as in surface aggregation or hemimicelle "
                     "formation. Cross-check it against a Hill coefficient above 1.")

    return {"rows": rows, "trend": trend,
            "note": "ΔH_iso is obtained at constant loading, so unlike the van't "
                    "Hoff ΔH° it resolves how the binding enthalpy changes as the "
                    "surface fills. Its variation with coverage is direct evidence "
                    "about surface heterogeneity."}


# --------------------------------------------------------------------------
# Activation energy and sticking probability
# --------------------------------------------------------------------------

def arrhenius(T_list, k_list) -> dict:
    """Activation energy from rate constants measured at several temperatures.

        ln k = ln A − E_a/(R T)
    """
    T = np.asarray(T_list, float)
    k = np.asarray(k_list, float)
    ok = np.isfinite(T) & np.isfinite(k) & (k > 0)
    if ok.sum() < 2:
        return {"error": "Need at least two positive rate constants at different "
                         "temperatures."}
    lr = sps.linregress(1.0 / T[ok], np.log(k[ok]))
    Ea = -R_GAS * lr.slope / 1000.0            # kJ/mol
    A = float(np.exp(lr.intercept))

    if Ea < 0:
        note = (f"E_a = {fmt(Ea)} kJ/mol is negative, meaning the rate *decreases* "
                f"with temperature. For a single elementary step this is "
                f"impossible; it usually means the apparent rate constant lumps "
                f"together an exothermic pre-equilibrium with the rate-determining "
                f"step, or that the kinetic model does not describe the data at "
                f"every temperature.")
    elif Ea < 40:
        note = (f"E_a = {fmt(Ea)} kJ/mol is below about 40 kJ/mol, which indicates a "
                f"**diffusion-controlled, physical** process. Physisorption has a "
                f"low energy barrier, so the rate is limited by how fast adsorbate "
                f"reaches the surface rather than by the binding event itself.")
    else:
        note = (f"E_a = {fmt(Ea)} kJ/mol exceeds 40 kJ/mol, the conventional "
                f"threshold for a **chemically controlled** process. The rate is "
                f"limited by bond formation at the surface, which is consistent "
                f"with chemisorption.")

    return {"Ea_kJ_mol": Ea, "A": A, "R2": lr.rvalue ** 2,
            "se_kJ_mol": R_GAS * lr.stderr / 1000.0 if np.isfinite(lr.stderr) else np.nan,
            "interpretation": note,
            "invT": (1.0 / T[ok]).tolist(), "lnk": np.log(k[ok]).tolist()}


def sticking_probability(T_list, theta_list) -> dict:
    """Sticking probability S* and its activation energy.

        ln(1 − θ) = ln S* + E_a/(R T)

    where θ = 1 − Ce/C0 is the surface coverage.  S* is interpreted as the
    probability that an adsorbate molecule striking the surface sticks to it.
    """
    T = np.asarray(T_list, float)
    th = np.asarray(theta_list, float)
    ok = np.isfinite(T) & np.isfinite(th) & (th < 1) & (th >= 0)
    if ok.sum() < 2:
        return {"error": "Need at least two valid (T, θ) pairs with θ < 1."}
    lr = sps.linregress(1.0 / T[ok], np.log(1.0 - th[ok]))
    Ea = R_GAS * lr.slope / 1000.0
    S = float(np.exp(lr.intercept))

    if 0 < S < 1:
        note = (f"S* = {fmt(S)} lies between 0 and 1, the range in which the "
                f"sticking-probability model is valid. It is read as the fraction "
                f"of molecular collisions with the surface that result in "
                f"adsorption — here about {S * 100:.1f}% of encounters stick.")
    elif S > 1:
        note = (f"S* = {fmt(S)} exceeds 1, which is outside the model's valid range "
                f"(a probability cannot exceed unity). The usual cause is that "
                f"coverage θ was computed at a concentration where the surface is "
                f"far from saturated. Treat this result as uninterpretable.")
    else:
        note = f"S* = {fmt(S)} is not positive, so the model does not apply here."

    return {"S_star": S, "Ea_kJ_mol": Ea, "R2": lr.rvalue ** 2,
            "interpretation": note,
            "invT": (1.0 / T[ok]).tolist(),
            "ln1mtheta": np.log(1.0 - th[ok]).tolist()}
