# AdsorpFit

*A product of [SWAT Lab](http://www.swatlab.or.kr/), Sungkyunkwan University, and UTOP.*

Browser-based fitting of adsorption **kinetics**, **isotherm** and **thermodynamic**
data. 34 models, non-linear least squares, publication-quality figure export in
nine formats, and an interpretation of every fitted parameter written out in
plain language. English and Korean interface.

Everything runs locally. The Python scientific stack (NumPy, SciPy, Matplotlib)
is loaded into the browser through WebAssembly, so unpublished data never leaves
the machine: there is no server and no upload.

**Live site:** https://nguyenducanh97.github.io/adsorpfit/

---

## What it does

| | |
|---|---|
| **Kinetics** | 13 models: PFO, PSO, Elovich, Avrami, mixed 1,2-order, pseudo-*n*th-order, Ritchie, fractal-like PFO, Weber–Morris, film diffusion, Bangham, Crank homogeneous surface diffusion, double exponential |
| **Isotherms** | 21 models across 2-, 3- and 4-parameter families: Langmuir, Freundlich, Temkin, Dubinin–Radushkevich, Jovanović, Halsey, Harkins–Jura, BET, Elovich, Sips, Tóth, Redlich–Peterson, Khan, Radke–Prausnitz, Hill, Koble–Corrigan, Brouers–Sotolongo, Vieth–Sladek, Fritz–Schlünder, Baudu, Marczewski–Jaroniec |
| **Thermodynamics** | van't Hoff (ΔG°, ΔH°, ΔS°) with six documented routes to a dimensionless K°, non-linear van't Hoff with ΔC*p*, isosteric heat vs. loading, Arrhenius *E*a, sticking probability |
| **Diagnostics** | Weber–Morris multi-region segmentation with automatic breakpoint search, Boyd plot with a statistical test on the intercept |
| **Statistics** | R², adjusted R², RMSE, SSE, χ², reduced χ², ARE, HYBRID, MPSD, EABS, MAE, Δ*q*, AIC, AICc, BIC, parameter standard errors, 95 % confidence intervals, *t* and *p* values, Akaike weights |
| **Figures** | Full control of fonts, sizes, colours, markers, line styles, ticks, grid, legend, axis ranges, log scales, annotations, canvas size; export as PNG, TIFF, PDF, SVG, EPS, PS, JPEG, WebP, BMP at up to 1200 dpi |
| **Tables** | CSV, TSV, XLSX, Markdown, LaTeX, HTML, JSON; plus curve data and a complete HTML report |
| **Model advisor** | Reads the shape of your raw data, does it plateau? is it linear, sigmoidal? did the kinetics equilibrate?, then screens every model and sorts them into recommended / usable / not advised, each with a reason |
| **Domain checking** | Every model is tested against its own range of validity before and after fitting, so a model cannot be reported from data it mathematically cannot describe |
| **Layout** | Drag the divider between the columns; drag a panel by its header grip to move it within a column or across to the other one; drag the dotted handle along a panel's bottom edge to set its height; collapse with the chevron; blow one panel up over the window with the focus button (Esc returns). All of it persists, with `Reset layout` in the toolbar. |
| **Workspace** | English and Korean, light / dark / system theme, three background-motion levels, three layout arrangements, two densities, and named projects saved in the browser with export and import |

---

## Four design decisions worth knowing about

**Non-linear regression is the default, and linearised fits are shown only for
comparison.** Linearising an adsorption model moves the error onto a transformed
variable, which silently re-weights the data. The pseudo-second-order Type 1 plot
(*t*/*q*t against *t*) is the clearest case: *t* appears on both axes, which
manufactures a correlation and produces a high R² even for data the model does
not describe. That is a large part of why PSO appears to fit nearly every
published dataset. AdsorpFit fits the untransformed equation, then shows the
linear plot alongside it and tells you when the two disagree.

**Models are ranked on AICc, not R².** R² cannot decrease when a parameter is
added, so ranking a two-parameter Langmuir against a four-parameter
Fritz–Schlünder by R² is guaranteed to favour the latter whether or not the extra
parameters mean anything. AdsorpFit reports Akaike weights, so when two models
are genuinely indistinguishable (Δ < 2) it says so rather than declaring a winner.

**ΔG° requires a dimensionless K°, and the route must be stated.** −RT ln K is
undefined for a K with units. A Langmuir K_L in L mg⁻¹ is not dimensionless, and
different unit choices for the same experiment give ΔG° values differing by tens
of kJ mol⁻¹: larger than the effect being reported. AdsorpFit makes you choose a
conversion route explicitly, prints the arithmetic it used, and marks the
Freundlich route as not defensible because K_F has no well-defined standard
state. See Lima et al. (2019) *J. Mol. Liq.* **273**, 425–434 and Tran &
Bonilla-Petriciolet (2022).

**A model is only reported where it is mathematically defined.** Several of
these equations are unbounded below. Temkin contains ln(A_T·C_e) and diverges
to −∞ as C_e → 0; Harkins–Jura has 1/(B − log C_e) and blows up at C_e = 10^B;
liquid-phase BET has (C_s − C_e) in its denominator. Least squares has no
objection to a negative loading, so a fit can reach R² = 0.96 while predicting
q_e = −14 mg/g at your lowest point, not hypothetical, this is what prompted
the check. AdsorpFit tests each model's domain against your data before
fitting, tests the fitted parameters against it afterwards, and blocks the
result rather than quietly reporting it.

---

## Checks it runs on your behalf

- Whether a model predicts negative or undefined values anywhere in your
  measured range, and the concentration at which it breaks down.
- A parameter whose standard error exceeds the parameter itself; the data do not
  determine it, whatever R² says.
- *q*e,cal against *q*e,exp. A kinetic fit whose calculated equilibrium capacity
  disagrees with the measured one is wrong even at R² = 0.999. This catches more
  bad fits than R² does.
- A fitted *q*max far above the highest measured loading, making it an
  extrapolation rather than a measurement.
- A three- or four-parameter model that has collapsed onto a simpler one, Sips
  with *m* = 1 is Langmuir; Redlich–Peterson with *g* = 1 is Langmuir; Tóth with
  *n* = 1 is Langmuir.
- A parameter pinned against a physical bound.
- A model outside its own domain of validity (Baudu requires 0 < 1+*x*+*y* < 1;
  Koble–Corrigan requires *n* ≥ 1).
- A linearised fit flattering itself relative to the same parameters tested
  against the raw data.
- A van't Hoff plot whose curvature means ΔH° is not constant over your
  temperature range.
- K° < 1 in the thermodynamics, which for a working adsorbent nearly always means
  the conversion is wrong rather than the chemistry.

---

## Example datasets

The eight built-in examples are **real measured data**, not synthetic curves.
They come from:

> Wang, P., Liu, X., Yu, B., Wu, X., Xu, J., Dong, F. & Zheng, Y. (2021)
> A comparative study on phosphate removal from water using *Phragmites
> australis* biochars loaded with different metal oxides.
> *Royal Society Open Science* **8**, 201789.
> <https://doi.org/10.1098/rsos.201789> (open access)
>
> Raw data: Wang, P. (2021) Zenodo. <https://doi.org/10.5281/zenodo.4711711>,
> released under **CC0 1.0** (public domain dedication).

They were chosen to span behaviours rather than to flatter the tool: two
isotherms that saturate cleanly, one that never plateaus, one failing adsorbent
with negative measured uptake, and four kinetic runs ranging from a clean
approach to equilibrium to one that finished before the first measurement.
Each preset carries its citation in the interface.

---

## Validation

Four independent test suites plus a project audit, all runnable offline:

```bash
python validation/test_recovery.py
python validation/test_published.py
python validation/test_domain.py
python validation/test_literature.py
python tools/audit.py
python tools/notation.py
python tools/csscheck.py css/style.css
```

**`test_recovery.py`: synthetic parameter recovery.** Each of the 34 models
generates data from known parameters with 1.5 % Gaussian noise; the engine must
refit to within the noise floor (RMSE ≤ 1.6 σ). All 34 pass. The suite separately
reports which models are *structurally non-identifiable*, Crank's *D* and *r*
appear only as *D*/*r*², Khan's *q*max and *b*K only as their product at low
*C*e: and verifies that the identifiable combination is recovered (to 2–4 %)
even when the individual parameters are not. That is a property of those models,
not a defect in the fitter, and the app says so rather than hiding it.

**`test_published.py`: cross-check against the literature.** Verifies the
derived-quantity relationships against papers that publish both the input
constant and the quantity derived from it, which is where unit errors actually
occur: *E* = 1/√(2K_ad) against a published *E* of 1581.14 J mol⁻¹; *B* = RT/b_T
against 14.678; *h* = k₂q*e*² against 33.67 mg g⁻¹ min⁻¹; ΔG° = −RT ln K° against
−1.6765 kJ mol⁻¹. It also round-trips published parameter sets through the full
fitting engine (recovery exact to 10⁻⁶), and confirms the diagnostics fire on
three genuinely defective fits that were published as they stand, a negative
Langmuir *q*max, a *q*e,cal 235 % away from *q*e,exp, and a ΔG° near zero caused
by an unconverted K. 16/16 pass.

**`test_domain.py`: domain and validity regression tests.** Twenty checks
pinning the failure modes above: Temkin blocked on dilute data but allowed on
mid-range data, BET blocked above C_s, Harkins–Jura past its singularity, Baudu
outside 0 < 1+x+y < 1, saturation models warned about on non-saturating data,
kinetic models warned about on runs that never equilibrated, Weber–Morris with
a negative boundary-layer intercept, and too few points for the parameter
count. 20/20 pass.

**`test_literature.py` — refit of published raw data.** The strongest of the
four, and the one the others could not be: real measurements from a paper,
refitted here, checked against the numbers that paper reports. Wang et al.
(2021) deposited their raw data openly, giving six adsorbents with ten isotherm
points and twelve kinetic points each.

Across twenty isotherm comparisons and twenty kinetic ones, **every fitted
capacity lands within 0.5 % of the published value and every q_e within 0.05 %**,
with our R² equal to or slightly better than theirs in all ten isotherm cases.
Rate constants agree to the precision the paper prints; in the two places they
differ, our optimum has the lower residual sum of squares, on a dataset whose
entire signal (0.09 mg/g) sits inside the measurement scatter (0.02 mg/g).

It also checks that the diagnostics fire on the three cases the authors
themselves describe: Al-BC not reaching equilibrium in 72 h, Al-BC's isotherm
not plateauing, and the unmodified biochar recording negative uptake. 44/44 pass.

Writing it found a real defect: the isotherm plateau test still used the
tail-rise measure that the kinetics test had already outgrown, and it missed
Al-BC. On the terminal-slope measure the four isotherms that do plateau score
0.02 to 0.13 and the one that does not scores 0.48, so both checks now use it.

**`tools/audit.py` — project audit.** Translation coverage in both directions,
keys referenced but undefined, model metadata completeness, preset integrity and
attribution, missing asset references, cache-busting consistency, leftover
debugging statements, credentials in shipped files, unexpected third-party
hosts, and basic accessibility. Currently 0 errors, 0 warnings.

**`tools/notation.py` — symbol formatting.** Reads the live model objects
rather than grepping source, so variable names cannot be mistaken for prose,
and checks that all 91 parameter symbols convert to valid LaTeX. The symbols
had accumulated in four notations as the library grew (ASCII underscores,
Unicode subscripts, bare letters, Greek), and all four rendered literally in
the tables: "q_max" appeared exactly as typed. Symbols and units are now
rendered with KaTeX, and prose is normalised at render time so both notations
produce the same markup.

**A limitation, stated plainly.** Most adsorption papers still show raw
(*t*, *q*t) and (*C*e, *q*e) data only as figures, with the numbers in
supplementary files that subscription journals do not expose. Of roughly a dozen
papers checked, one had its raw data openly deposited, which is why the
literature suite rests on a single study (albeit six adsorbents and forty
comparisons). More datasets in `validation/datasets/` would strengthen it
further; the format is one small Python module per study.

---

## Running it locally

The app fetches its Python modules over HTTP, so opening `index.html` straight
from disk will not work: the browser blocks it. Serve the folder instead:

```bash
python -m http.server 8777
```

Then open <http://localhost:8777>.

---

## Publishing to GitHub Pages

```bash
git remote add origin https://github.com/nguyenducanh97/adsorpfit.git
git branch -M main
git push -u origin main
```

**When you update the site**, bump `APP_VERSION` in `index.html` and the `?v=`
query on every local `<script>` and `<link>`. Without that, browsers and the
GitHub Pages CDN keep serving the previously cached JavaScript and CSS, and your
changes will not appear.

Then in the repository: **Settings → Pages → Source: Deploy from a branch →
Branch: `main`, folder: `/ (root)` → Save**. The site appears at
`https://nguyenducanh97.github.io/adsorpfit/` after a minute or two.

---

## Project layout

```
adsorpfit/
├── index.html              app shell
├── assets/                 SWAT, SKKU and U-TOP marks: source PNGs plus the
│                           light variants used by the dark theme
├── tools/make_marks.py     regenerates the light variants and css/marks.css
├── css/
│   ├── marks.css           the logos inlined as data URIs, one variant per
│   │                       theme, both transparent (generated, do not edit)
│   └── style.css           styling, water background, light and dark themes
├── js/
│   ├── i18n.js             English / Korean dictionary and switching
│   ├── prefs.js            theme, motion, layout, density + project storage
│   ├── layout.js           column splitter, panel drag/collapse, plot resize
│   ├── water.js            animated caustics and waves
│   ├── plot.js             figure engine, one style object drives both the
│   │                       Plotly preview and the Matplotlib export
│   └── app.js              application controller
├── py/
│   ├── core.py             model specification framework, fitting, statistics
│   ├── isotherms.py        21 isotherm models with interpretation logic
│   ├── kinetics.py         13 kinetic models with interpretation logic
│   ├── thermo.py           van't Hoff, K° conversion, isosteric heat, Arrhenius
│   ├── advisor.py          reads the data's shape and recommends models
│   └── bridge.py           JSON boundary between JavaScript and Python
└── validation/
    ├── test_recovery.py    synthetic parameter recovery, all 34 models
    ├── test_published.py   cross-validation against published values
    └── test_domain.py      domain and validity regression tests
```

### A note on the Korean translation

The interface, the guide, the model names and the parameter descriptions are
translated. The automatically generated interpretation paragraphs are still
English: they are composed in Python with fitted numbers interpolated into
them, so translating them means maintaining a parallel set of sentence
templates in the Python layer, a separate piece of work, not a `t()` call.
The Korean strings would also benefit from a native-speaker review before you
publish.

Each model is declared once, in a single `ModelSpec` carrying its equation, the
physical meaning and units of every parameter, its bounds, a data-driven initial
guess, its classical linearised forms, the original citation, and the function
that turns the fitted numbers into prose. Adding a model means adding one
`ModelSpec`: the picker, the fitting, the tables, the figures, the export and
the interpretation all follow from it.

---

## Citing the models

Every model card in the app carries its primary citation, reachable from the **?**
button beside the model name. Cite the original source: Lagergren 1898, Langmuir
1918, Freundlich 1906, Ho & McKay 1999, not a recent paper that happens to use
the model.

Key methodological references behind the design:

- Tran, H.N. et al. (2017) Mistakes and inconsistencies regarding adsorption of
  contaminants from aqueous solutions: a critical review. *Water Research* **120**, 88–116.
- Wang, J. & Guo, X. (2020) Adsorption kinetic models: physical meanings,
  applications, and solving methods. *J. Hazard. Mater.* **390**, 122156.
- Al-Ghouti, M.A. & Da'ana, D.A. (2020) Guidelines for the use and interpretation
  of adsorption isotherm models: a review. *J. Hazard. Mater.* **393**, 122383.
- Lima, E.C. et al. (2019) A critical review of the estimation of the
  thermodynamic parameters on adsorption equilibria. *J. Mol. Liq.* **273**, 425–434.
- Tran, H.N. & Bonilla-Petriciolet, A. (2022) Improper estimation of thermodynamic
  parameters in adsorption studies. *Adsorpt. Sci. Technol.* **2022**, 5553212.
- El-Khaiary, M.I. (2008) Least-squares regression of adsorption equilibrium
  data: comparing the options. *J. Hazard. Mater.* **158**, 73–87.
- Simonin, J.-P. (2016) On the comparison of pseudo-first order and pseudo-second
  order rate laws. *Chem. Eng. J.* **300**, 254–263.
- Burnham, K.P. & Anderson, D.R. (2002) *Model Selection and Multimodel Inference*,
  2nd ed. Springer. (AICc, Akaike weights, and the Δ thresholds.)

---

## Licence

MIT. Use it, modify it, publish with it.
