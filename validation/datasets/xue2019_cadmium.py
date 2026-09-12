# -*- coding: utf-8 -*-
"""Cadmium(II) on a mesoporous ceramic functional nanomaterial.

  Paper    Xue, Z., Liu, N., Hu, H., Huang, J., Kianpoor Kalkhajeh, Y.,
           Wu, X., Xu, N., Fu, X., Zhan, L. (2019) Adsorption of Cd(II) in
           water by mesoporous ceramic functional nanomaterials.
           Royal Society Open Science 6, 182195.
           https://doi.org/10.1098/rsos.182195   (open access)

  Data     Deposited at Dryad, https://doi.org/10.5061/dryad.sg2637q, and
           mirrored at Zenodo record 4964670, in "Full Metadata.zip", file
           Data.xlsx, sheets "Contacting time" and "Cd(II) concentration".
           Licence: CC0 1.0.

  Conditions
      0.2 g adsorbent in 50 mL, so 4 g/L, pH 6, 25 C
      kinetics   C0 = 200 mg/L, 30 to 300 min
      isotherms  C0 = 50 to 1000 mg/L, 180 min

Values are the authors' own means over their replicates, with the standard
deviation of those replicates kept as the error bars. The dose and initial
concentration are not stated row by row in the file but follow from the
data: at 300 min the residual is 5.2 mg/L at 97.4% removal, which puts C0
at 200 mg/L, and (200 - 5.2) x 0.05 L / 0.2 g = 48.7 mg/g reproduces the
tabulated loading.

The isotherm is a deliberately awkward one. Its first three points sit at
almost the same residual concentration while the loading triples, because
removal is nearly complete there, and the last point rises above the
capacity the paper fits. It is a good test of whether a saturation model is
being asked to describe data that do not constrain a plateau.
"""

DOSE = 4.0                       # g/L, 0.2 g in 50 mL
C0_KINETIC = 200.0               # mg/L

# minutes, mean loading, and the standard deviation of the replicates
KINETIC_TIME = [30, 60, 90, 120, 150, 180, 240, 300]
KINETIC_Q = [44.29, 46.12, 46.74, 47.49, 48.54, 48.53, 48.52, 48.51]
KINETIC_SD = [0.27, 0.83, 1.54, 0.25, 0.56, 0.09, 0.16, 0.06]

# isotherm, means over replicates
C0_ISOTHERM = [50, 100, 150, 250, 300, 400, 500, 1000]
CE_ISOTHERM = [1.67, 1.094, 1.297, 33.863, 73.667, 155.85, 225.133, 572.467]
QE_ISOTHERM = [12.04, 24.67, 37.08, 53.83, 56.40, 60.84, 68.58, 106.55]
QE_SD = [0.18, 0.04, 0.06, 0.86, 1.29, 0.78, 3.64, 16.11]

# what the paper reports
PUBLISHED_LANGMUIR = {"qm": 97.09, "KL": 0.042, "R2": 0.9832}
PUBLISHED_FREUNDLICH = {"KF": 27.22, "inv_n": 0.187, "R2": 0.8383}

CITATION = ("Xue, Z. et al. (2019) R. Soc. Open Sci. 6, 182195. "
            "Raw data: Dryad 10.5061/dryad.sg2637q (CC0).")
