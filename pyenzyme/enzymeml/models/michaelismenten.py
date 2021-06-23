'''
File: michaelismenten.py
Project: models
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 10:16:22 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.models import KineticModel
from pyenzyme.enzymeml.tools.unitcreator import UnitCreator


def MichaelisMenten(
    vmax_val,
    vmax_unit,
    km_val,
    km_unit,
    substrate_id,
    enzmldoc
):

    equation = f"vmax_{substrate_id} * ( {substrate_id} / ({substrate_id} + km_{substrate_id}) )"

    vmax_unit = UnitCreator().getUnit(vmax_unit, enzmldoc)
    km_unit = UnitCreator().getUnit(km_unit, enzmldoc)

    parameters = {

        f"vmax_{substrate_id}": (vmax_val, vmax_unit),
        f"km_{substrate_id}": (km_val, km_unit)

    }

    return KineticModel(equation, parameters)
