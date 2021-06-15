'''
File: reactant.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 15th 2021 8:40:52 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase

import json


class Reactant(EnzymeMLBase):

    def __init__(
        self,
        name,
        vessel,
        init_conc=0.0,
        substanceunits='NAN',
        constant=False,
        smiles=None,
        inchi=None,
        uri=None,
        creatorId=None
    ):

        '''
        Object describing an EnzymeML reactant.

        Args:
            String name: Systematic name of reactant
            String id_: Internal ID for reactant
            String metaid: MetaID for reactant
            String vessel: Vessel ID
            Float init_conc: Initial concentration value
            String substanceunits: Unit ID
            Boolean boundary: Has boundary condition boolean
            Boolean constant: Is constant in reaction boolean
            String uri: Custom unique identifier
            String creatorId: Identifier to credit Creator
        '''

        # Initialize base attributes
        super().__init__(
            uri,
            creatorId
        )

        self.setName(name)
        self.setVessel(vessel)
        self.setInitConc(init_conc)
        self.setSubstanceUnits(substanceunits)
        self.setBoundary(False)
        self.setConstant(constant)
        self.setSboterm("SBO:0000247")

        if inchi is not None:
            self.setInchi(inchi)
        if smiles is not None:
            self.setSmiles(smiles)

    def toJSON(self, d=False, enzmldoc=False):

        def transformAttr(self):
            d = dict()
            for key, item in self.__dict__.items():

                if enzmldoc is not False:

                    if 'unit' in key:
                        if item:
                            item = enzmldoc.getUnitDict()[item].getName()
                        if not item:
                            item = "nan"

                if str(item) != "nan":
                    d[key.split('__')[-1]] = item

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

    def getInchi(self):
        return self.__inchi

    def getSmiles(self):
        return self.__smiles

    def setInchi(self, inchi):
        self.__inchi = TypeChecker(inchi, str)

    def setSmiles(self, smiles):
        self.__smiles = TypeChecker(smiles, str)

    def delInchi(self):
        del self.__inchi

    def delSmiles(self):
        del self.__smiles

    def getInitConc(self):
        return self.__init_conc

    def setInitConc(self, init_conc):
        self.__init_conc = TypeChecker(init_conc, float)

    def delInitConc(self):
        del self.__init_conc

    def getName(self):
        return self.__name

    def getId(self):
        return self.__id

    def getMetaid(self):
        return self.__metaid

    def getSboterm(self):
        return self.__sboterm

    def getVessel(self):
        return self.__vessel

    def getSubstanceUnits(self):
        return self.__substanceunits

    def getBoundary(self):
        return self.__boundary

    def getConstant(self):
        return self.__constant

    def setName(self, name):
        self.__name = TypeChecker(name, str).lower()

    def setId(self, id_):
        self.__id = TypeChecker(id_, str)
        self.setMetaid("METAID_" + id_.upper())

    def setMetaid(self, metaid):
        self.__metaid = TypeChecker(metaid, str)

    def setSboterm(self, sboterm):
        self.__sboterm = TypeChecker(sboterm, str)

    def setVessel(self, vessel):
        self.__vessel = TypeChecker(vessel, str)

    def setSubstanceUnits(self, substance_unit):
        self.__substanceunits = TypeChecker(substance_unit, str)

    def setBoundary(self, boundary):
        self.__boundary = TypeChecker(boundary, bool)

    def setConstant(self, constant):
        self.__constant = TypeChecker(constant, bool)

    def delName(self):
        del self.__name

    def delId(self):
        del self.__id

    def delMetaid(self):
        del self.__metaid

    def delSboterm(self):
        del self.__sboterm

    def delVessel(self):
        del self.__vessel

    def delSubstanceUnits(self):
        del self.__substanceunits

    def delBoundary(self):
        del self.__boundary

    def delConstant(self):
        del self.__constant
