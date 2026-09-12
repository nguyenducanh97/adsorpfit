# -*- coding: utf-8 -*-
"""Korean translations of everything the Python layer writes.

Split by module so each table stays reviewable next to the code it
translates. Keyed by the English sentence; see py/lang.py.
"""

from ko_core import KO_CORE
from ko_advisor import KO_ADVISOR
from ko_kinetics import KO_KINETICS
from ko_thermo import KO_THERMO
from ko_isotherms import KO_ISOTHERMS
from ko_extra import KO_EXTRA
from ko_names import KO_NAMES
from ko_assumptions import KO_ASSUMPTIONS

KO = {}
for _table in (KO_CORE, KO_ADVISOR, KO_KINETICS, KO_THERMO,
               KO_ISOTHERMS, KO_EXTRA, KO_NAMES, KO_ASSUMPTIONS):
    KO.update(_table)
