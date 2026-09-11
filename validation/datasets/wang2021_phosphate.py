# -*- coding: utf-8 -*-
"""Phosphate adsorption on metal-oxide-loaded Phragmites australis biochars.

Raw data from the authors' own deposited dataset, refit here and compared
against the parameters they published.

  Paper    Wang, P., Liu, X., Yu, B., Wu, X., Xu, J., Dong, F., Zheng, Y.
           (2021) A comparative study on phosphate removal from water using
           Phragmites australis biochars loaded with different metal oxides.
           Royal Society Open Science 8, 201789.
           https://doi.org/10.1098/rsos.201789   (open access)

  Data     Wang, P. (2021) Dataset of a comparative study on phosphate removal
           from water using phragmites australis biochars loaded with
           different metal oxides. Zenodo. https://doi.org/10.5281/zenodo.4711711
           File: PO4-P_adsorption_kinetis_and_isotherms_raw_data.xlsx
           Licence: CC0 1.0 (public domain dedication)

  Conditions
      isotherms  2 g/L biochar, 40 mL, pH 7.0, 25 C, 24 h
                 (Al-BC 168 h), C0 = 100-1500 mg/L PO4-P
      kinetics   2 g/L biochar, 500 mL, pH 7.0, 25 C, C0 = 20 mg/L PO4-P

The plain biochar (BC) adsorbs essentially nothing and its measured uptake is
partly negative, so it is kept deliberately: it is the case every diagnostic
in AdsorpFit should object to.
"""

# --- isotherms: Ce (mg/L), qe (mg/g), and the reported standard deviations ---
C0_ISOTHERM = [100, 200, 300, 400, 500, 600, 800, 1000, 1200, 1500]

ISOTHERMS = {
    "Al-BC": {
        "ce": [67.7, 144.5, 226.0, 306.9, 410.4, 475.2, 670.3, 827.3, 1022.0, 1292.0],
        "qe": [15.2, 25.4, 35.6, 40.9, 45.8, 52.1, 62.4, 69.7, 77.4, 84.8],
        "ce_sd": [2.6, 7.6, 12.8, 12.8, 7.2, 19.1, 16.9, 25.7, 32.6, 47.6],
        "qe_sd": [0.1, 1.0, 1.9, 1.3, 2.3, 2.4, 1.2, 0.1, 0.4, 1.8],
    },
    "Ca-BC": {
        "ce": [54.7, 116.3, 182.8, 254.4, 357.3, 428.7, 640.4, 810.3, 1019.0, 1302.0],
        "qe": [21.8, 39.6, 57.2, 67.1, 72.4, 75.4, 77.3, 78.2, 78.9, 79.5],
        "ce_sd": [2.0, 0.5, 4.2, 2.1, 1.9, 13.8, 15.7, 27.9, 29.4, 43.7],
        "qe_sd": [2.4, 2.5, 2.4, 6.2, 2.2, 0.3, 0.6, 1.2, 1.9, 0.1],
    },
    "Fe-BC": {
        "ce": [58.5, 132.4, 226.9, 315.9, 423.3, 497.9, 711.1, 880.0, 1089.0, 1373.0],
        "qe": [19.8, 31.5, 35.2, 36.4, 39.4, 40.7, 42.0, 43.3, 43.8, 44.4],
        "ce_sd": [0.7, 3.6, 9.8, 13.2, 2.6, 12.9, 11.3, 25.5, 37.0, 51.3],
        "qe_sd": [1.1, 1.0, 0.4, 1.4, 0.0, 0.7, 1.6, 0.0, 1.9, 3.7],
    },
    "La-BC": {
        "ce": [43.9, 137.6, 233.6, 323.3, 434.1, 511.0, 726.1, 897.4, 1108.0, 1392.0],
        "qe": [27.1, 28.9, 31.9, 32.7, 34.0, 34.2, 34.5, 34.6, 34.5, 34.7],
        "ce_sd": [2.6, 3.6, 3.0, 10.9, 3.8, 19.1, 10.8, 23.7, 36.5, 37.1],
        "qe_sd": [2.7, 1.0, 3.0, 0.3, 0.6, 2.4, 1.8, 0.9, 1.6, 3.4],
    },
    "Mg-BC": {
        "ce": [16.2, 67.2, 125.7, 200.7, 304.6, 412.8, 608.9, 789.3, 984.4, 1304.0],
        "qe": [41.1, 66.6, 81.3, 90.5, 96.2, 98.6, 101.6, 102.8, 103.4, 104.6],
        "ce_sd": [0.0, 0.5, 6.7, 2.9, 4.8, 7.2, 1.2, 6.0, 4.8, 7.2],
        "qe_sd": [0.0, 0.2, 3.4, 1.4, 2.4, 3.6, 0.6, 3.0, 2.4, 3.6],
    },
    "BC": {
        "ce": [97.8, 189.6, 282.5, 371.9, 492.2, 556.0, 765.3, 924.3, 1124.0, 1396.0],
        "qe": [-1.2, 0.1, 2.9, 3.2, 3.6, 4.5, 7.7, 8.4, 9.6, 10.8],
        "ce_sd": [1.0, 1.7, 1.0, 0.0, 2.4, 6.0, 1.2, 2.4, 0.0, 2.4],
        "qe_sd": [0.5, 0.8, 0.5, 0.0, 1.2, 3.0, 0.6, 1.2, 0.0, 1.2],
    },
}

# --- kinetics: t (h), qt (mg/g) ---------------------------------------------
KIN_TIME = [0.5, 1, 1.5, 2, 3, 4, 6, 8, 12, 24, 48, 72]

KINETICS = {
    "Al-BC": {
        "qt": [1.81, 2.34, 2.52, 2.86, 2.88, 3.45, 3.78, 4.05, 5.23, 6.55, 8.34, 9.25],
        "sd": [0.30, 0.43, 0.36, 0.22, 0.14, 0.15, 0.20, 0.24, 0.47, 0.37, 0.48, 0.01],
    },
    "Ca-BC": {
        "qt": [6.83, 7.10, 7.23, 7.75, 8.84, 9.31, 9.56, 9.62, 9.76, 9.79, 9.82, 9.83],
        "sd": [0.29, 0.08, 0.15, 0.12, 0.21, 0.04, 0.04, 0.06, 0.05, 0.06, 0.01, 0.01],
    },
    "Fe-BC": {
        "qt": [5.87, 6.09, 6.33, 6.49, 6.96, 7.18, 7.57, 8.06, 8.50, 8.82, 8.75, 8.75],
        "sd": [0.45, 0.32, 0.16, 0.22, 0.37, 0.30, 0.31, 0.06, 0.07, 0.16, 0.19, 0.02],
    },
    "La-BC": {
        "qt": [9.82, 9.87, 9.88, 9.87, 9.87, 9.88, 9.91, 9.89, 9.88, 9.91, 9.90, 9.91],
        "sd": [0.04, 0.02, 0.03, 0.02, 0.02, 0.02, 0.01, 0.02, 0.04, 0.01, 0.01, 0.02],
    },
    "Mg-BC": {
        "qt": [1.51, 1.98, 2.63, 7.38, 8.53, 8.93, 9.28, 9.54, 9.56, 9.86, 9.73, 9.82],
        "sd": [0.02, 0.04, 0.03, 0.01, 0.03, 0.04, 0.00, 0.03, 0.02, 0.02, 0.01, 0.01],
    },
    "BC": {
        "qt": [-0.33, -0.15, 0.01, -0.22, -0.34, -0.27, -0.37, -0.21, -0.46, -0.43,
               -0.65, -0.77],
        "sd": [0.06, 0.09, 0.55, 0.18, 0.28, 0.25, 0.33, 0.32, 0.14, 0.09, 0.08, 0.02],
    },
}

# --- what the authors reported (table 3 and table 4 of the paper) ------------
# Their Langmuir-Freundlich is the Sips equation; kL, kF and kLF are as printed.
PUBLISHED_ISOTHERM = {
    "Al-BC": {"langmuir": {"qm": 122.2, "KL": 1.64e-3, "R2": 0.990},
              "sips": {"qm": 219.9, "R2": 0.998}},
    "Ca-BC": {"langmuir": {"qm": 91.6, "KL": 8.13e-3, "R2": 0.947},
              "sips": {"qm": 81.5, "R2": 0.992}},
    "Fe-BC": {"langmuir": {"qm": 46.6, "KL": 13.49e-3, "R2": 0.988},
              "sips": {"qm": 46.6, "R2": 0.986}},
    "La-BC": {"langmuir": {"qm": 34.7, "KL": 67.66e-3, "R2": 0.838},
              "sips": {"qm": 38.9, "R2": 0.920}},
    "Mg-BC": {"langmuir": {"qm": 106.3, "KL": 30.21e-3, "R2": 0.979},
              "sips": {"qm": 112.5, "R2": 0.993}},
}

PUBLISHED_KINETIC = {
    "Al-BC": {"pfo": {"qe": 8.17, "k1": 0.11, "R2": 0.808},
              "pso": {"qe": 9.25, "k2": 0.02, "R2": 0.885}},
    "Ca-BC": {"pfo": {"qe": 9.35, "k1": 1.63, "R2": 0.503},
              "pso": {"qe": 9.84, "k2": 0.31, "R2": 0.843}},
    "Fe-BC": {"pfo": {"qe": 7.88, "k1": 1.75, "R2": 0.333},
              "pso": {"qe": 8.42, "k2": 0.32, "R2": 0.757}},
    "La-BC": {"pfo": {"qe": 9.89, "k1": 9.81, "R2": 0.617},
              "pso": {"qe": 9.90, "k2": 24.00, "R2": 0.817}},
    "Mg-BC": {"pfo": {"qe": 9.94, "k1": 0.44, "R2": 0.890},
              "pso": {"qe": 10.92, "k2": 0.05, "R2": 0.818}},
}

CITATION = ("Wang, P. et al. (2021) R. Soc. Open Sci. 8, 201789. "
            "Data: Zenodo 10.5281/zenodo.4711711 (CC0).")
