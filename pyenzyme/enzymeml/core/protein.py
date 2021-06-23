'''
File: protein.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 9:53:42 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase

import json
import re


class Protein(EnzymeMLBase):

    def __init__(
        self,
        name,
        sequence,
        vessel=None,
        init_conc=None,
        substanceunits=None,
        constant=True,
        ecnumber=None,
        uniprotid=None,
        organism=None,
        organismTaxId=None,
        uri=None,
        creatorId=None
    ):
        '''
        Object describing an EnzymeML protein.

        Args:
            String name: Systematic protein name
            String id_: Internal identifier
            String sequence: Protein amino acid sequence
            String vessel: Vessel Identifier
            Float init_conc: Initial protein concentration
            String substance_units: Unit definition
            Boolean boundary: boolean
            Boolean constant: boolean
            String uri: Custom unique identifier
            String creatorId: Identifier to credit Creator
        '''

        # Initialize base attributes
        super().__init__(
            uri,
            creatorId
        )

        self.setName(name)
        self.setSequence(sequence)
        self.setBoundary(False)
        self.setConstant(constant)
        self.setSboterm("SBO:0000252")

        if vessel is not None:
            self.setVessel(vessel)
        if init_conc is not None:
            self.setInitConc(init_conc)
        if substanceunits is not None:
            self.setSubstanceUnits(substanceunits)
        if ecnumber is not None:
            self.setEcnumber(ecnumber)
        if uniprotid is not None:
            self.setUniprotID(uniprotid)
        if organism is not None:
            self.setOrganism(organism)
        if organismTaxId:
            self.setOrganismTaxId(organismTaxId)

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

    def setOrganismTaxId(self, organismTaxId):
        self.__organismTaxId = TypeChecker(organismTaxId, str)

    def getOrganismTaxId(self):
        return self.__organismTaxId

    def delOrganismTaxId(self):
        del self.__organismTaxId

    def getEcnumber(self):
        return self.__ecnumber

    def getUniprotID(self):
        return self.__uniprotID

    def setEcnumber(self, ecnumber):
        ecnumber = TypeChecker(ecnumber, str)

        pattern = r"(\d+.)(\d+.)(\d+.)(\d+)"
        match = re.search(pattern, ecnumber)

        if match is not None:
            self.__ecnumber = "".join(match.groups())
        else:
            raise TypeError(
                f'EC number {ecnumber} is not valid. \
                Please provide with X.X.X.X pattern'
            )

    def setUniprotID(self, uniprotID):
        self.__uniprotID = TypeChecker(uniprotID, str)

    def delEcnumber(self):
        del self.__ecnumber

    def delUniprotID(self):
        del self.__uniprotID

    def getOrganism(self):
        return self.__organism

    def setOrganism(self, organism):
        self.__organism = TypeChecker(organism, str)

    def delOrganism(self):
        del self.__organism

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

    def getSequence(self):
        return self.__sequence

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

    def setSequence(self, sequence):
        sequence = TypeChecker(sequence, str)
        self.__sequence = sequence.replace(
            '\n', '').replace(' ', '').strip()

    def setSboterm(self, sboterm):
        self.__sboterm = TypeChecker(sboterm, str)

    def setVessel(self, vessel):
        self.__vessel = TypeChecker(vessel, str)

    def setSubstanceUnits(self, unit_id):
        self.__substanceunits = TypeChecker(unit_id, str)

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

    def delSequence(self):
        del self.__sequence

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
