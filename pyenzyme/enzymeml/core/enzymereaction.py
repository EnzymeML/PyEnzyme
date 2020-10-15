'''
Created on 09.06.2020

@author: JR
'''
from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pyenzyme.enzymeml.models.kineticmodel import KineticModel
from pyenzyme.enzymeml.core.replicate import Replicate
import pandas as pd


class EnzymeReaction(object):

    def __init__(self, temperature, tempunit, ph, name, reversible, educts=None, products=None, modifiers=None):
        '''
        Class to describe an enzyme reaction, its molecules/proteins, data and models
        
        Args:
            temperature: Numerical value for temperature
            tempunit: Unit for temperature
            ph: pH value [0-14]
            name: Enzyme Reaction Name
            reversible: Is Reversible bool
            id_: Internal identifier
            educts: List of tuples ( Reactant ID, Stoichiometry, Constant?, List Of Replicates )
            products: List of tuples ( Reactant ID, Stoichiometry, Constant?, List Of Replicates )
            modifiers: List of tuples ( Reactant ID, Stoichiometry, Constant?, List Of Replicates )
        '''
        
        self.setTemperature(temperature)
        self.setTempunit(tempunit)
        self.setPh(ph)
        self.setName(name)
        self.setReversible(reversible)
        self.setEducts(educts)
        self.setProducts(products)
        self.setModifiers(modifiers)
        
    def __setInitConc(self, conc, reactant, enzmldoc):
        
        conc_tup = (conc, enzmldoc.getReactant(reactant).getSubstanceunits())
        
        if conc_tup not in enzmldoc.getConcDict().values():
            
            index = 0
            while True:
                id_ = "c%i" % index
                if id_ not in enzmldoc.getConcDict().keys():
                    enzmldoc.getConcDict()[ id_ ] = conc_tup
                    return id_
                index += 1
                
        else:
            
            return [ key for key, item in enzmldoc.getConcDict().items() if conc_tup == item ][0]
        
    def exportReplicates(self, ids):
        
        '''
        Returns replicate data of given ID(s) as a pandas DataFrame.
        
        Args:
            String/ListStr ids: Single or multiple IDs of reactants/proteins
        '''
        
        if type(ids) == str:
            ids = [ids]
        
        repls = []
        all_tups = self.__educts + self.__products + self.__modifiers
        
        
        for tup in all_tups:
            if tup[0].split('_')[0] in ids:
                repls += [ repl.getData() for repl in tup[3] ]
                ids.remove(tup[0])
        
        if len(ids) > 0:
            
            print('\nCould not find ', ids, '\n' )
        
        return pd.DataFrame( repls ).T
    
    def getEduct(self, id_):
        
        '''
        Returns educt tuple ( ID, Stoichiometry, IsConstant, Replicates )
        
        Args:
            String id_: Reactant internal ID
        '''
        
        for tup in self.__educts:
            if tup[0] == id_:
                return tup
            
        raise KeyError( "Reactant %s not defined in educts" % id_ )
    
    def getProduct(self, id_):
        
        '''
        Returns product tuple ( ID, Stoichiometry, IsConstant, Replicates )
        
        Args:
            String id_: Reactant internal ID
        '''
        
        for tup in self.__products:
            if tup[0] == id_:
                return tup
            
        raise KeyError( "Reactant %s not defined in products" % id_ )
    
    def getModifier(self, id_):
        
        '''
        Returns modifier tuple ( ID, Stoichiometry, IsConstant, Replicates )
        
        Args:
            String id_: Reactant/Protein internal ID
        '''
        
        for tup in self.__modifiers:
            if tup[0] == id_:
                return tup
            
        raise KeyError( "Reactant/Protein %s not defined in modifiers" % id_ )
        
    def addReplicate(self, replicate, enzmldoc):
        
        '''
        Adds replicate to EnzymeReaction object by pre-defined Replicate object ID. 
        If no time course data was given and error is raised.
        
        Args:
            Replicate replicate: Object describing an EnzymeML replicate.
        '''
        
        # Turn initial cocncentrations to IDs
        try:
            init_conc_tup = ( replicate.getInitConc(), enzmldoc.getReactant( replicate.getReactant() ).getSubstanceunits() )
            inv_conc = { item: key for key, item in enzmldoc.getConcDict().items() }
            replicate.setInitConc( inv_conc[ init_conc_tup ] )
            
        except KeyError:
            index = 0
            init_conc_tup = ( replicate.getInitConc(), enzmldoc.getReactant( replicate.getReactant() ).getSubstanceunits() )
            while True:
                id_ = "c%i" % index
                
                if id_ not in enzmldoc.getConcDict().keys():
                    enzmldoc.getConcDict()[ id_ ] = init_conc_tup
                    replicate.setInitConc(id_)
                    break
                    
                else:
                    index += 1
        
        try:
            replicate.getData()
        except AttributeError:
            raise AttributeError( "Replicate has no series data. Add data via replicate.setData( pandas.Series )" )
        
        for i in range(len(self.__educts)):
            if self.__educts[i][0] == replicate.getReactant():
                self.__educts[i][3].append(replicate)
                return 1
            
        for i in range(len(self.__products)):
            if self.__products[i][0] == replicate.getReactant():
                self.__products[i][3].append(replicate)
                return 1
            
        for i in range(len(self.__modifiers)):
            if self.__modifiers[i][0] == replicate.getReactant():
                self.__modifiers[i][3].append(replicate)
                return 1
            
        raise AttributeError( "Replicate's reactant %s not defined in reaction" % (replicate.getReactant()) )
        
    def addEduct(self, id_, stoichiometry, constant, enzmldoc, replicates=[], init_concs=[]):
        
        '''
        Adds educt to EnzymeReaction object. Replicates are not mandatory can be left empty if no data is given.
        EnzymeMLDocument has to be given to check for un-defined entities. These should be added to the document before
        a reaction is constructed.
        
        Args:
            String id_: Reactant internal ID
            Float stoichiometry: Can also be given as an integer 
            Boolean constant: Sets if reactant is either constant or not
            EnzymeMLDocument enzmldoc: Object describing an entire EnzymeML file
            Replicate replicates: Single or multiple Replicate instances
        '''
        
        id_ = TypeChecker(id_, str)
        
        if id_ not in list(enzmldoc.getReactantDict().keys()):
            raise KeyError( "Reactant with id %s is not defined yet" % id_ )
        
        stoichiometry = TypeChecker( float(stoichiometry) , float)
        constant = TypeChecker(constant, bool)
        
        if type(replicates) == list and len(replicates) > 0:
            replicates = replicates
        elif type(replicates) == list and len(replicates) == 0:
            replicates = []
        elif type(replicates) == Replicate:
            replicates = [replicates]
            
        # replace concentrations with identifiers
        init_concs = [ self.__setInitConc(conc, id_, enzmldoc) for conc in init_concs ]
        
        self.__educts.append(
            
            (
                id_,
                stoichiometry,
                constant,
                replicates,
                init_concs
                )
            
            )
        
    def addProduct(self, id_, stoichiometry, constant, enzmldoc, replicates=[], init_concs=[]):
        
        '''
        Adds product to EnzymeReaction object. Replicates are not mandatory can be left empty if no data is given.
        EnzymeMLDocument has to be given to check for un-defined entities. These should be added to the document before
        a reaction is constructed.
        
        Args:
            String id_: Reactant internal ID
            Float stoichiometry: Can also be given as an integer 
            Boolean constant: Sets if reactant is either constant or not
            EnzymeMLDocument enzmldoc: Object describing an entire EnzymeML file
            Replicate replicates: Single or multiple Replicate instances
        '''
        
        id_ = TypeChecker(id_, str)
        
        if id_ not in list(enzmldoc.getReactantDict().keys()):
            raise KeyError( "Reactant with id %s is not defined yet" % id_ )
        
        stoichiometry = TypeChecker( float(stoichiometry) , float)
        constant = TypeChecker(constant, bool)
        
        if type(replicates) == list and len(replicates) > 0:
            replicates = replicates
        elif type(replicates) == list and len(replicates) == 0:
            replicates = []
        elif type(replicates) == Replicate:
            replicates = [replicates]
        
        # replace concentrations with identifiers
        init_concs = [ self.__setInitConc(conc, id_, enzmldoc) for conc in init_concs ]
        
        self.__products.append(
            
            (
                id_,
                stoichiometry,
                constant,
                replicates,
                init_concs
                )
            
            )
        
    def addModifier(self, id_, stoichiometry, constant, enzmldoc, replicates=[], init_concs=[]):
        
        '''
        Adds product to EnzymeReaction object. Replicates are not mandatory can be left empty if no data is given.
        EnzymeMLDocument has to be given to check for un-defined entities. These should be added to the document before
        a reaction is constructed.
        
        Args:
            String id_: Reactant internal ID
            Float stoichiometry: Can also be given as an integer 
            Boolean constant: Sets if reactant is either constant or not
            EnzymeMLDocument enzmldoc: Object describing an entire EnzymeML file
            Replicate replicates: Single or multiple Replicate instances
        '''
        
        id_ = TypeChecker(id_, str)
        
        if id_ not in list(enzmldoc.getReactantDict().keys()) + list(enzmldoc.getProteinDict().keys()) :
            raise KeyError( "Reactant/Protein with id %s is not defined yet" % id_ )
        
        stoichiometry = TypeChecker( float(stoichiometry) , float)
        constant = TypeChecker(constant, bool)
        
        if type(replicates) == list and len(replicates) > 0:
            replicates = replicates
        elif type(replicates) == list and len(replicates) == 0:
            replicates = []
        elif type(replicates) == Replicate:
            replicates = [replicates]
            
        # replace concentrations with identifiers
        init_concs = [ self.__setInitConc(conc, id_, enzmldoc) for conc in init_concs ]
        
        self.__modifiers.append(
            
            (
                id_,
                stoichiometry,
                constant,
                replicates,
                init_concs
                )
            
            )
    
    def getTemperature(self):
        return self.__temperature


    def getTempunit(self):
        return self.__tempunit


    def getPh(self):
        return self.__ph


    def getName(self):
        return self.__name


    def getReversible(self):
        return self.__reversible


    def getId(self):
        return self.__id


    def getMetaid(self):
        return self.__metaid


    def getModel(self):
        return self.__model


    def getEducts(self):
        return self.__educts


    def getProducts(self):
        return self.__products


    def getModifiers(self):
        return self.__modifiers


    def setTemperature(self, temperature):
        self.__temperature = TypeChecker(float(temperature), float)


    def setTempunit(self, tempunit):
        self.__tempunit = TypeChecker(tempunit, str)


    def setPh(self, ph):
        
        if 0 <= TypeChecker(float(ph), float) <= 14:
            self.__ph = ph
            
        else:
            raise ValueError( "pH out of bounds [0-14]" )


    def setName(self, name):
        self.__name = TypeChecker(name, str)


    def setReversible(self, reversible):
        self.__reversible = TypeChecker(reversible, bool)


    def setId(self, id_):
        self.__id = TypeChecker(id_, str)
        self.setMetaid("METAID_" + id_.upper())


    def setMetaid(self, metaID):
        self.__metaid = TypeChecker(metaID, str)


    def setModel(self, model):
        self.__model = TypeChecker(model, KineticModel)


    def setEducts(self, educts):
        if educts == None: 
            self.__educts = []
        else:
            self.__educts = TypeChecker(educts, list)


    def setProducts(self, products):
        if products == None:
            self.__products = list()
        else:
            self.__products = TypeChecker(products, list)


    def setModifiers(self, modifiers):
        if modifiers == None:
            self.__modifiers = list()
        else:
            self.__modifiers = TypeChecker(modifiers, list)


    def delTemperature(self):
        del self.__temperature


    def delTempunit(self):
        del self.__tempunit


    def delPh(self):
        del self.__ph


    def delName(self):
        del self.__name


    def delReversible(self):
        del self.__reversible


    def delId(self):
        del self.__id


    def delMetaid(self):
        del self.__metaid


    def delModel(self):
        del self.__model


    def delEducts(self):
        del self.__educts


    def delProducts(self):
        del self.__products


    def delModifiers(self):
        del self.__modifiers

    _temperature = property(getTemperature, setTemperature, delTemperature, "_temperature's docstring")
    _tempunit = property(getTempunit, setTempunit, delTempunit, "_tempunit's docstring")
    _ph = property(getPh, setPh, delPh, "_ph's docstring")
    _name = property(getName, setName, delName, "_name's docstring")
    _reversible = property(getReversible, setReversible, delReversible, "_reversible's docstring")
    _id = property(getId, setId, delId, "_id's docstring")
    _metaid = property(getMetaid, setMetaid, delMetaid, "_metaid's docstring")
    _model = property(getModel, setModel, delModel, "_model's docstring")
    _educts = property(getEducts, setEducts, delEducts, "_educts's docstring")
    _products = property(getProducts, setProducts, delProducts, "_products's docstring")
    _modifiers = property(getModifiers, setModifiers, delModifiers, "_modifiers's docstring")

    
        