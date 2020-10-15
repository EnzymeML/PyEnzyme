'''
Created on 10.06.2020

@author: JR
'''
from pyenzyme.enzymeml.core.functionalities import TypeChecker

class Reactant(object):

    def __init__(self, name, compartment_id, init_conc=0.0, substance_units='NAN', constant=False):
        
        '''
        Object describing an EnzymeML reactant.
        
        Args:
            String name: Systematic name of reactant
            String id_: Internal ID for reactant
            String metaid: MetaID for reactant
            String compartment: Compartment ID
            Float init_conc: Initial concentration value
            String substanceunits: Unit ID
            Boolean boundary: Has boundary condition boolean
            Boolean constant: Is constant in reaction boolean
        '''
        
        self.setName(name)
        self.setCompartment(compartment_id)
        self.setInitConc(init_conc)
        self.setSubstanceunits(substance_units)
        self.setBoundary(False)
        self.setConstant(constant)
        self.setSboterm("SBO:0000247")

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


    def getCompartment(self):
        return self.__compartment


    def getSubstanceunits(self):
        return self.__substanceunits


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


    def setSboterm(self, sboterm):
        self.__sboterm = TypeChecker(sboterm, str)


    def setCompartment(self, compartment_id):
        self.__compartment = TypeChecker(compartment_id, str)


    def setSubstanceunits(self, substance_unit):
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


    def delCompartment(self):
        del self.__compartment


    def delSubstanceunits(self):
        del self.__substanceunits


    def delBoundary(self):
        del self.__boundary


    def delConstant(self):
        del self.__constant

    _name = property(getName, setName, delName, "_name's docstring")
    _id = property(getId, setId, delId, "_id's docstring")
    _metaid = property(getMetaid, setMetaid, delMetaid, "_metaid's docstring")
    _sboterm = property(getSboterm, setSboterm, delSboterm, "_sboterm's docstring")
    _compartment = property(getCompartment, setCompartment, delCompartment, "_compartment's docstring")
    _substanceunits = property(getSubstanceunits, setSubstanceunits, delSubstanceunits, "_substanceunits's docstring")
    _boundary = property(getBoundary, setBoundary, delBoundary, "_boundary's docstring")
    _constant = property(getConstant, setConstant, delConstant, "_constant's docstring")
    _init_conc = property(getInitConc, setInitConc, delInitConc, "_init_conc's docstring")
    _inchi = property(getInchi, setInchi, delInchi, "_inchi's docstring")
    _smiles = property(getSmiles, setSmiles, delSmiles, "_smiles's docstring")

     
    
        
        