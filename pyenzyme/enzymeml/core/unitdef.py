'''
File: unitdef.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 15th 2021 7:48:57 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.core.functionalities import TypeChecker


class UnitDef(object):

    def __init__(
        self,
        name,
        id_,
        ontology
    ):

        '''
        Object describing an EnzymeML unit.

        Args:
            Tuple units: List of BaseUnits
            String name: Systematical name of unit
            String id_: Internal Identifier
            String metaid: Internal Meta Identifier
            String ontology: Link to ontology
        '''

        self.setUnits(list())
        self.setName(name)
        self.setId(id_)
        self.setOntology(ontology)

    def getFootprint(self):
        try:
            return self.__footprint
        except AttributeError:
            self.__footprint = sorted(self.__units)
            return self.__footprint

    def setFootprint(self, value):
        self.__footprint = TypeChecker(value, list)

    def delFootprint(self):
        del self.__footprint

    def addBaseUnit(self, kind, exponent, scale, multiplier):

        '''
        Adds defining base unit such as litre or grams to a unit definition

        Args:
            SBMLKind kind: SBML internal definition for Base Units
            Float exponent: Float value of exponent in Unit
            Integer scale: Integer value to define (m, mu etc)
            Float multiplier: FLoat value to multiply unit
        '''

        self.__units.append(

            (
                kind,
                TypeChecker(float(exponent), float),
                TypeChecker(scale, int),
                TypeChecker(float(multiplier), float)
              )
            )

    def getUnits(self):
        return self.__units

    def getName(self):
        return self.__name

    def getId(self):
        return self.__id

    def getMetaid(self):
        return self.__metaid

    def getOntology(self):
        return self.__ontology

    def setUnits(self, units):
        self.__units = TypeChecker(units, list)

    def setName(self, name):
        self.__name = TypeChecker(name, str)

    def setId(self, id_):
        self.__id = TypeChecker(id_, str)
        self.setMetaid("METAID_%s" % id_.upper())

    def setMetaid(self, metaid):
        self.__metaid = TypeChecker(metaid, str)

    def setOntology(self, ontology):
        self.__ontology = TypeChecker(ontology, str)

    def delUnits(self):
        del self.__units

    def delName(self):
        del self.__name

    def delId(self):
        del self.__id

    def delMetaid(self):
        del self.__metaid

    def delOntology(self):
        del self.__ontology
