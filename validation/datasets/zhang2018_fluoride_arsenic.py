# -*- coding: utf-8 -*-
"""Fluoride and arsenic on yak dung biochar, plain and iron-modified.

  Paper    Zhang, W., Fu, J., Zhang, C., Li, X., Zhang, S. (2018)
           Simultaneous removal of fluoride and arsenic in geothermal water
           in Tibet using modified yak dung biochar as an adsorbent.
           Royal Society Open Science 5, 181266.
           https://doi.org/10.1098/rsos.181266   (open access)

  Data     Deposited at Dryad, https://doi.org/10.5061/dryad.kv63501, and
           mirrored at Zenodo record 5001949. File "The experimental data.txt".
           Licence: CC0 1.0 (public domain dedication).

  Conditions
      dose 10 g/L, 30 mL in a 50 mL container, pH 5.0-6.0, 25 C
      isotherms  C0 = 5, 10, 15, 20, 30, 40 mg/L
      kinetics   As(V) C0 = 3.668 mg/L, F- C0 = 19.0 mg/L, 1/12 to 12 h

The deposited file gives residual concentrations rather than loadings, so q
is computed here from the authors' stated dose:

    q = (C0 - C) / 10 g/L

That reconstruction is checked against the paper's own tables in
validation/test_literature.py. Three of the four kinetic series reproduce
the published pseudo-second-order q_e to within 2%. The fourth, As(V) on
Fe-BC3, does not: the paper tabulates 1.069 mg/g while its own deposited
data never exceed 0.364 mg/g, which is the number the raw measurements
support. The series is included as measured.
"""

DOSE = 10.0                                   # g/L
C0_ISOTHERM = [5, 10, 15, 20, 30, 40]         # mg/L

# residual equilibrium concentrations, mg/L
CE_ISOTHERM = {
    ("As", "BC3"):    [3.970, 8.339, 12.80, 17.26, 26.01, 35.12],
    ("As", "Fe-BC3"): [0.0749, 0.5158, 1.837, 1.926, 3.328, 12.91],
    ("F", "BC3"):     [0.35, 0.84, 1.29, 2.08, 4.24, 6.88],
    ("F", "Fe-BC3"):  [0.18, 0.46, 0.83, 1.48, 3.67, 6.94],
}

# hours
T_KINETIC = [1/12, 1/6, 1/4, 1/3, 1/2, 2/3, 5/6,
             1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

C0_KINETIC = {"As": 3.668, "F": 19.0}         # mg/L

# residual concentrations through the run, mg/L
CT_KINETIC = {
    ("As", "BC3"): [3.509, 3.509, 3.436, 3.411, 3.402, 3.315, 3.274,
                    3.295, 3.238, 3.233, 3.158, 3.139, 3.067, 3.146,
                    3.126, 3.047, 3.026, 3.032, 2.926],
    ("As", "Fe-BC3"): [0.1911, 0.1111, 0.0971, 0.0951, 0.0640, 0.0623,
                       0.0787, 0.0460, 0.0414, 0.0388, 0.0376, 0.0355,
                       0.0335, 0.0320, 0.0301, 0.0295, 0.0229, 0.0203,
                       0.0262],
    ("F", "BC3"): [3.96, 3.35, 2.84, 2.44, 2.20, 2.15, 2.07, 2.10, 1.90,
                   1.84, 1.78, 1.80, 1.75, 1.77, 1.73, 1.72, 1.68, 1.68,
                   1.68],
    ("F", "Fe-BC3"): [3.43, 2.80, 2.06, 1.77, 1.48, 1.28, 1.22, 1.20,
                      1.20, 1.18, 1.22, 1.18, 1.17, 1.20, 1.14, 1.19,
                      1.12, 1.12, 1.18],
}

# what the paper reports, for the cross-check
PUBLISHED_LANGMUIR = {
    ("As", "BC3"): {"qm": 1.0497, "KL": 0.023},
    ("As", "Fe-BC3"): {"qm": 2.9257, "KL": 0.9617},
    ("F", "BC3"): {"qm": 4.851, "KL": 0.2932},
    ("F", "Fe-BC3"): {"qm": 3.928, "KL": 0.6698},
}
PUBLISHED_PSO_QE = {("As", "BC3"): 0.076, ("As", "Fe-BC3"): 1.069,
                    ("F", "BC3"): 1.737, ("F", "Fe-BC3"): 1.786}

CITATION = ("Zhang, W. et al. (2018) R. Soc. Open Sci. 5, 181266. "
            "Raw data: Dryad 10.5061/dryad.kv63501 (CC0).")


def qe(key):
    """Equilibrium loadings, mg/g, from the residual concentrations."""
    return [round((c0 - c) / DOSE, 4)
            for c0, c in zip(C0_ISOTHERM, CE_ISOTHERM[key])]


def qt(key):
    """Loadings through the kinetic run, mg/g."""
    c0 = C0_KINETIC[key[0]]
    return [round((c0 - c) / DOSE, 4) for c in CT_KINETIC[key]]
