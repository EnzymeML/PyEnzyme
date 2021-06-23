'''
File: kineticmodel.py
Project: models
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 9:55:38 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.tools.unitcreator import UnitCreator
from pyenzyme.enzymeml.core.functionalities import TypeChecker
from libsbml._libsbml import parseL3Formula
import json


class KineticModel(object):

    def __init__(self, equation, parameters, enzmldoc):

        '''
        Model class to define kinetic laws and store modeling parameters.

        Args:
            String equation: String describing mathematical formula of model
            Dict parameters: Dictionary of parameters from formula
        '''

        self.setEquation(equation)
        self.setParameters(parameters, enzmldoc)
        self.setEqObject(self.getEquation())

    def toJSON(self, d=False, enzmldoc=None):

        def transformAttr(self):
            d = dict()
            for key, item in self.__dict__.items():
                key = key.split('__')[-1]

                if 'eqObject' not in key:

                    if type(item) == dict and enzmldoc is not None:

                        item = {
                            k: (
                                it[0],
                                enzmldoc.getUnitDict()[it[1]].getName()
                            )
                            for k, it in item.items()
                            }

                    d[key] = item

            return d

        if d:
            return transformAttr(self)

        return json.dumps(
            self,
            default=transformAttr,
            indent=4
            )

    def __str__(self):
        return self.toJSON()

    def addToReaction(self, reaction):

        '''
        Adds kinetic law to SBML reaction.
        Only relevant for EnzymeML > SBML conversion.

        Args:
            Reaction (SBML) reaction: SBML reaciton class
        '''

        kl = reaction.createKineticLaw()

        for key, item in self.__parameters.items():

            local_param = kl.createLocalParameter()
            local_param.setId(key)
            local_param.setValue(item[0])
            local_param.setUnits(item[1])

        kl.setMath(self.__eqObject)

    def getEquation(self):
        return self.__equation

    def getParameters(self):
        return self.__parameters

    def getEqObject(self):
        return self.__eqObject

    def setEquation(self, equation):
        '''
        Args:
            String equation: mathematical description of kinetic law
        '''
        self.__equation = TypeChecker(equation, str)

    def setParameters(self, parameters, enzmldoc):
        '''
        Args:
            Dict parameters: Float parameters indexed by String names

        '''
        parameters = TypeChecker(parameters, dict)

        self.__parameters = dict()
        for paramName, (paramValue, paramUnit) in parameters.items():

            if paramUnit not in enzmldoc.getUnitDict().keys():
                paramUnit = UnitCreator().getUnit(paramUnit, enzmldoc)

            self.__parameters[paramName] = (
                    paramValue,
                    paramUnit
                )

    def setEqObject(self, equation):
        self.__eqObject = parseL3Formula(equation)

    def delEquation(self):
        del self.__equation

    def delParameters(self):
        del self.__parameters

    def delEqObject(self):
        del self.__eqObject
