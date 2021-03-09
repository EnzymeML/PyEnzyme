'''
Created on 10.06.2020

@author: JR
'''
from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pyenzyme.enzymeml.models import KineticModel
from pyenzyme.enzymeml.tools.unitcreator import UnitCreator
from libsbml._libsbml import parseL3Formula
import json

def MichaelisMenten(vmax_val, vmax_unit, km_val, km_unit ,substrate_id, enzmldoc):
    
    equation = f"vmax_{substrate_id} * ( {substrate_id} / ({substrate_id} + km_{substrate_id}) )"
    
    vmax_unit = UnitCreator().getUnit(vmax_unit, enzmldoc)
    km_unit = UnitCreator().getUnit(km_unit, enzmldoc)
    
    parameters = {
        
        f"vmax_{substrate_id}": (vmax_val, vmax_unit),
        f"km_{substrate_id}": (km_val, km_unit)
        
    }
    
    return KineticModel(equation, parameters)