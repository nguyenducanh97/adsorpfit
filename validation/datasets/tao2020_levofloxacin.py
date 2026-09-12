# -*- coding: utf-8 -*-
"""Levofloxacin hydrochloride on a cellulose nanocrystal / graphene oxide composite.

  Paper    Tao, J., Yang, J., Ma, C., Li, J., Du, K., Wei, Z., Chen, C.,
           Wang, Z., Zhao, C., Deng, X. (2020) Cellulose nanocrystals/graphene
           oxide composite for the adsorption and removal of levofloxacin
           hydrochloride antibiotic from aqueous solution.
           Royal Society Open Science 7, 200857.
           https://doi.org/10.1098/rsos.200857   (open access)

  Data     Deposited at Dryad, https://doi.org/10.5061/dryad.47d7wm39s, and
           mirrored at Zenodo record 4069308. Files "Adsorption_isotherm.xlsx"
           and "Adsorption_kinetics.xlsx". Licence: CC0 1.0.

The isotherm file holds three unlabelled pairs of Ce and qe columns. The
paper measured isotherms at 293.15, 303.15 and 313.15 K, and fitting the
three pairs in the order they appear reproduces the paper's own Sips
capacities of 17.29, 19.34 and 23.29 mg/g exactly, which is what fixes the
mapping: the columns run from the coldest to the warmest.

That makes this the one dataset here with isotherms at three temperatures,
so it is also the worked thermodynamic example. Levofloxacin hydrochloride
is C18H20FN3O4 . HCl, 397.83 g/mol, which the van 't Hoff analysis needs to
turn the Langmuir constant into a dimensionless one.
"""

MW = 397.83                      # g/mol, levofloxacin hydrochloride

TEMPERATURES = [293.15, 303.15, 313.15]

# Ce (mg/L) and qe (mg/g) at each temperature, in the deposited order
ISOTHERMS = {
    293.15: {
        "ce": [2.7066, 3.6314, 4.982, 6.754, 9.0965, 11.988, 14.8644],
        "qe": [1.2934, 5.3686, 9.018, 11.246, 13.1035, 15.012, 17.1356],
    },
    303.15: {
        "ce": [2.5066, 3.4314, 4.782, 6.554, 8.8965, 11.7888, 14.6644],
        "qe": [2.5456, 6.6188, 11.2682, 13.4962, 15.6537, 17.2622, 19.3858],
    },
    313.15: {
        "ce": [2.9066, 3.8314, 5.182, 6.954, 9.2965, 12.188, 15.0644],
        "qe": [3.3292, 8.1044, 12.7588, 15.9818, 18.6392, 20.7478, 22.8714],
    },
}

# minutes, and mg/g
KINETIC_TIME = [3, 5, 10, 20, 40, 60, 90, 120, 150, 180, 240, 360, 540, 720, 1080]
KINETIC_Q = [0.686, 0.998, 1.238, 1.445, 3.786, 5.593, 6.086, 6.591, 7.223,
             7.675, 8.075, 8.394, 8.772, 8.901, 9.195]

# the paper's Sips capacity at each temperature, for the cross-check
PUBLISHED_SIPS_QMAX = {293.15: 17.29, 303.15: 19.34, 313.15: 23.29}

CITATION = ("Tao, J. et al. (2020) R. Soc. Open Sci. 7, 200857. "
            "Raw data: Dryad 10.5061/dryad.47d7wm39s (CC0).")
