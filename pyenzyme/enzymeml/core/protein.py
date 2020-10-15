'''
Created on 09.06.2020

@author: JR
'''

from pyenzyme.enzymeml.core.functionalities import TypeChecker


class Protein(object):

    def __init__(self, name, sequence, compartment_id, init_conc, substance_units, constant=True):
        
        '''
        Object describing an EnzymeML protein.
        
        Args:
            String name: Systematic protein name
            String id_: Internal identifier
            String sequence: Protein amino acid sequence
            String compartment_id: Vessel Identifier
            Float init_conc: Initial protein concentration
            String substance_units: Unit definition
            Boolean boundary: boolean
            Boolean constant: boolean
        '''

        self.setName(name)
        self.setSequence(sequence)
        self.setCompartment(compartment_id)
        self.setInitConc(init_conc)
        self.setSubstanceUnits(substance_units)
        self.setBoundary(False)
        self.setConstant(constant)
        self.setSboterm("SBO:0000252")

    def getEcnumber(self):
        return self.__ecnumber


    def getUniprotID(self):
        return self.__uniprotID


    def setEcnumber(self, ecnumber):
        self.__ecnumber = TypeChecker(ecnumber, str) 


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


    def getCompartment(self):
        return self.__compartment


    def getSubstanceUnits(self):
        return self.__substance_units


    def getBoundary(self):
        return self.__boundary


    def getConstant(self):
        return self.__constant


    def setName(self, name):
        self.__name = TypeChecker(name, str)


    def setId(self, id_):
        self.__id = TypeChecker(id_, str)
        self.setMetaid("METAID_" + id_.upper())


    def setMetaid(self, metaid):
        self.__metaid = TypeChecker(metaid, str)


    def setSequence(self, sequence):
        self.__sequence = TypeChecker(sequence, str)


    def setSboterm(self, sboterm):
        self.__sboterm = TypeChecker(sboterm, str)


    def setCompartment(self, compartment_id):
        self.__compartment = TypeChecker(compartment_id, str)


    def setSubstanceUnits(self, unit_id):
        self.__substance_units = TypeChecker(unit_id, str)


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


    def delCompartment(self):
        del self.__compartment


    def delSubstanceUnits(self):
        del self.__substance_units


    def delBoundary(self):
        del self.__boundary


    def delConstant(self):
        del self.__constant

    _name = property(getName, setName, delName, "_name's docstring")
    _id = property(getId, setId, delId, "_id's docstring")
    _metaid = property(getMetaid, setMetaid, delMetaid, "_metaid's docstring")
    _sequence = property(getSequence, setSequence, delSequence, "_sequence's docstring")
    _sboterm = property(getSboterm, setSboterm, delSboterm, "_sboterm's docstring")
    _compartment = property(getCompartment, setCompartment, delCompartment, "_compartment's docstring")
    _substance_units = property(getSubstanceUnits, setSubstanceUnits, delSubstanceUnits, "_substance_units's docstring")
    _boundary = property(getBoundary, setBoundary, delBoundary, "_boundary's docstring")
    _constant = property(getConstant, setConstant, delConstant, "_constant's docstring")
    _init_conc = property(getInitConc, setInitConc, delInitConc, "_init_conc's docstring")
    _organism = property(getOrganism, setOrganism, delOrganism, "_organism's docstring")
    _ecnumber = property(getEcnumber, setEcnumber, delEcnumber, "_ecnumber's docstring")
    _uniprotID = property(getUniprotID, setUniprotID, delUniprotID, "_uniprotID's docstring")
    
    
        
        