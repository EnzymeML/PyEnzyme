# @Author: Jan Range
# @Date:   2021-03-18 22:33:21
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-03-23 22:09:22
'''
File: /enzymereaction.py
Project: EnzymeML
Created Date: November 10th 2020
Author: Jan Range
-----
Last Modified: Friday December 11th 2020 4:05:57 pm
Modified By: the developer formerly known as Jan Range at <range.jan@web.de>
-----
Copyright (c) 2020 Institute Of Biochemistry and Technical Biochemistry Stuttgart
'''


from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pyenzyme.enzymeml.models.kineticmodel import KineticModel
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.tools.unitcreator import UnitCreator
import pandas as pd
import json
from copy import deepcopy


class EnzymeReaction(object):

    def __init__(self, temperature, tempunit, ph, name, reversible, educts=None, products=None, modifiers=None):
        """
        Class describing an enzymatic reaction, including assay conditions as well as equation

        Args:
            temperature (float): Temperature reaction was executed at
            tempunit (string): Temperature unit
            ph (float): pH value [0,14]
            name (string): Name of reaction
            reversible (bool): Whether or not reaction is reversible
            educts (list<(id, stoich, constant, replicates, initiConcs)>, optional): List of tuples describing participant. Defaults to None.
            products (list<(id, stoich, constant, replicates, initiConcs)>, optional): List of tuples describing participant. Defaults to None.
            modifiers (list<(id, stoich, constant, replicates, initiConcs)>, optional): List of tuples describing participant. Defaults to None.
        """

        
        self.setTemperature(temperature)
        self.setTempunit(tempunit)
        self.setPh(ph)
        self.setName(name)
        self.setReversible(reversible)
        self.setEducts(educts)
        self.setProducts(products)
        self.setModifiers(modifiers)
     
    def toJSON(self, d=False, enzmldoc=False):
        """
        Converts complete EnzymeMLDocument to a JSON-formatted string or dictionary.

        Args:
            only_reactions (bool, optional): Returns only reactions including Reactant/Protein info. Defaults to False.
            d (bool, optional): Returns dictionary instead of JSON. Defaults to False.
        Returns:
            string: JSON-formatted string
            dict: Object serialized as dictionary
        """

        def transformAttr(self):
            """
            Serialization function

            Returns:
                dict: Object serialized as dictionary
            """

            d = dict()
            for key, item in self.__dict__.items():
                
                if 'KineticModel' not in key:
                
                    if 'model' in key:
                        d['model'] = item.toJSON(d=True, enzmldoc=enzmldoc)
                    
                    elif type(item) == list:
                        nu_lst = [
                            
                            {
                                'species': tup[0],
                                'stoich': tup[1],
                                'constant': tup[2],
                                'replicates': [ repl.toJSON(d=True, enzmldoc=enzmldoc) for repl in tup[3] ],
                                'init_conc': tup[4]
                                
                            }
                            for tup in item
                        ]
                        
                        d[key.split('__')[-1]] = nu_lst
                        
                    else:
                        d[key.split('__')[-1]] = item
            
            return d
        
        if d: return transformAttr(self)
        
        return json.dumps(
            self, 
            default=transformAttr, 
            indent=4
            )
    
    def __str__(self):
        """
        Returns object as JSON-formatted string

        Returns:
            string: JSON-formatted string
        """

        return self.toJSON() 
        
    def __setInitConc(self, conc, reactant, enzmldoc):
        """
        INTERNAL. Sets initial concentrations of reactant.

        Args:
            conc (float): Concentration value
            reactant (string): Reactant ID
            enzmldoc (EnzymeMLDocument): To add and check IDs

        Returns:
            string: initConc ID
        """

        conc_tup = (conc, enzmldoc.getReactant(reactant).getSubstanceUnits())
        
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
        """
        Exports replicated data for given IDs as Pandas.Dataframe objec

        Args:
            ids (string or list<string>): Single or multiple IDs to retrieve replicate data

        Returns:
            Pandas.DataFrame: Raw replicate data
        """

        ids = deepcopy(ids)
        if type(ids) == str:
            ids = [ids]
        
        
        repls = []
        all_tups = self.__educts + self.__products + self.__modifiers
        
        
        for tup in all_tups:
            if tup[0].split('_')[0] in ids:
                
                repls += [ repl.getData() for repl in tup[3] ]
                ids.remove(tup[0].split('_')[0])
        
        if len(ids) > 0:
            
            print('\nCould not find ', ids, '\n' )
        return pd.DataFrame( repls ).T
    
    def getEduct(self, id_, index=False):
        """
        Returns tuple describing reaction element.

        Args:
            id_ (string): Reactant/Modifier ID
            index (bool, optional): If set True, returns index of internal list of elements. Defaults to False.

        Raises:
            KeyError: If reactant ID unfindable

        Returns:
            Tuple: (ID, stoich, constant, replicated, initConcs)
        """

        for i, tup in enumerate(self.__educts):
            if tup[0] == id_:
                if index:
                    return i
                else:
                    return tup
            
        raise KeyError( "Reactant %s not defined in educts" % id_ )
    
    def getProduct(self, id_, index=False):
        """

        Args:
            id_ (string): Reactant/Modifier ID
            index (bool, optional): If set True, returns index of internal list of elements. Defaults to False.

        Raises:
            KeyError: If reactant ID unfindable

        Returns:
            Tuple: (ID, stoich, constant, replicated, initConcs)
        """

        for i, tup in enumerate(self.__products):
            if tup[0] == id_:
                if index:
                    return i
                else:
                    return tup
            
            
        raise KeyError( "Reactant %s not defined in products" % id_ )
    
    def getModifier(self, id_, index=False):
        """

        Args:
            id_ (string): Reactant/Modifier ID
            index (bool, optional): If set True, returns index of internal list of elements. Defaults to False.

        Raises:
            KeyError: If reactant ID unfindable

        Returns:
            Tuple: (ID, stoich, constant, replicated, initConcs)
        """

        for i, tup in enumerate(self.__modifiers):
            if tup[0] == id_:
                if index:
                    return i
                else:
                    return tup
            
        raise KeyError( "Reactant/Protein %s not defined in modifiers" % id_ )
        
    def addReplicate(self, replicate, enzmldoc, by_id=True):
        """
        Adds Replicate object to EnzymeReaction object. Destination is inherited automatically based on ID.

        Args:
            replicate (Replicate): Replicate object describing experimental data
            enzmldoc (EnzymeMLDocument): Checks and adds IDs

        Raises:
            AttributeError: If no experimental data has been added
            AttributeError: If reactant/protein ID unfindable in reaction

        Returns:
            int: 1 for success
        """

        # Turn initial cocncentrations to IDs
        try:
            init_conc_tup = ( replicate.getInitConc(), enzmldoc.getReactant( replicate.getReactant() ).getSubstanceUnits() )
            inv_conc = { item: key for key, item in enzmldoc.getConcDict().items() }
            replicate.setInitConc( inv_conc[ init_conc_tup ] )
            
        except KeyError:
            index = 0
            init_conc_tup = ( replicate.getInitConc(), enzmldoc.getReactant( replicate.getReactant(), by_id=by_id ).getSubstanceUnits() )
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
        
        def getName(name, by_id):
            # Helper function
            if by_id:
                return enzmldoc.getReactant( name, by_id ).getId()
            else:
                return enzmldoc.getReactant( name, by_id ).getName()
            
        def checkUnits(replicate, enzmldoc):
            # Checks if units are given as ID or need to be added 
            # to the document
            
            time_unit = replicate.getTimeUnit()
            data_unit = replicate.getDataUnit()
            
            # Check if units are already given as an ID
            def isID(string):
                if string[0] == "u":
                    try:
                        int(string[1::])
                        return 1
                    except ValueError:
                        return 0
                else:
                    return 0
                
            # perform checks
            if isID(time_unit): 
                replicate.setTimeUnit( enzmldoc.getUnitDict()[time_unit].getId() )
            else:
                replicate.setTimeUnit( UnitCreator().getUnit(time_unit, enzmldoc) )
                
            if isID(data_unit):
                replicate.setDataUnit( enzmldoc.getUnitDict()[data_unit].getId() )
            else:
                replicate.setDataUnit( UnitCreator().getUnit(data_unit, enzmldoc) )
            
            return replicate
        
        for i in range(len(self.__educts)):
            if getName(self.__educts[i][0], by_id) == replicate.getReactant():
                self.__educts[i][3].append( checkUnits(replicate, enzmldoc) )
                return 1
            
        for i in range(len(self.__products)):
            if getName(self.__products[i][0], by_id) == replicate.getReactant():
                self.__products[i][3].append( checkUnits(replicate, enzmldoc) )
                return 1
            
        for i in range(len(self.__modifiers)):
            if getName(self.__products[i][0], by_id) == replicate.getReactant():
                self.__modifiers[i][3].append( checkUnits(replicate, enzmldoc) )
                return 1
            
        raise AttributeError( "Replicate's reactant %s not defined in reaction" % (replicate.getReactant()) )
        
    def addEduct(self, id_, stoichiometry, constant, enzmldoc, replicates=[], init_concs=[]):
        """
        Adds element to EnzymeReaction object. Replicates as well as initial concentrations are optional.

        Args:
            id_ (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            constant (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs
            replicates (list, optional): List of Replicate objects. Defaults to [].
            init_concs (list, optional): List of InitConcs. Defaults to [].

        Raises:
            KeyError: If Reactant/Protein hasnt been defined yet
        """

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
        """
        Adds element to EnzymeReaction object. Replicates as well as initial concentrations are optional.

        Args:
            id_ (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            constant (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs
            replicates (list, optional): List of Replicate objects. Defaults to [].
            init_concs (list, optional): List of InitConcs. Defaults to [].

        Raises:
            KeyError: If Reactant/Protein hasnt been defined yet
        """

        
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
        """
        Adds element to EnzymeReaction object. Replicates as well as initial concentrations are optional.

        Args:
            id_ (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            constant (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs
            replicates (list, optional): List of Replicate objects. Defaults to [].
            init_concs (list, optional): List of InitConcs. Defaults to [].

        Raises:
            KeyError: If Reactant/Protein hasnt been defined yet
        """

        
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
        """
        Returns temperature value

        Returns:
            float: Temperature value
        """

        return self.__temperature


    def getTempunit(self):
        """
        Returns temperature unit

        Returns:
            string: Temperature unit
        """

        return self.__tempunit


    def getPh(self):
        """
        Returns pH value

        Returns:
            float: pH Value
        """

        return self.__ph


    def getName(self):
        """
        Returns name of reaction

        Returns:
            string: Reaction name
        """

        return self.__name


    def getReversible(self):
        """
        Returns if reaction is reversible or not

        Returns:
            bool: Is reversible
        """

        return self.__reversible


    def getId(self):
        """
        Returns ID of reaction

        Returns:
            string: Reaction ID
        """

        return self.__id


    def getMetaid(self):
        """
        Returns Meta-ID of reaction

        Returns:
            string: Meta-ID of reaction
        """

        return self.__metaid


    def getModel(self):
        """
        Returns kinetic model of reaction

        Returns:
            KineticModel: Object describing a kinetic model
        """

        return self.__model


    def getEducts(self):
        """
        Returns list of tuples (ID, stoich, constant, replicates, initCncs)

        Returns:
            list: List of tuples.
        """

        return self.__educts


    def getProducts(self):
        """
        Returns list of tuples (ID, stoich, constant, replicates, initCncs)

        Returns:
            list: List of tuples.
        """

        return self.__products


    def getModifiers(self):
        """
        Returns list of tuples (ID, stoich, constant, replicates, initCncs)

        Returns:
            list: List of tuples.
        """

        return self.__modifiers


    def setTemperature(self, temperature):
        """
        Sets temperature value

        Args:
            temperature (float): temperature
        """

        self.__temperature = TypeChecker(float(temperature), float)


    def setTempunit(self, tempunit):
        """
        Sets temperature unit

        Args:
            tempunit (string): temperature unit
        """

        self.__tempunit = TypeChecker(tempunit, str)


    def setPh(self, ph):
        """
        Sets pH value of reaction

        Args:
            ph (float): pH value

        Raises:
            ValueError: If pH value out of bounds [0,14]
        """

        if 0 <= TypeChecker(float(ph), float) <= 14:
            self.__ph = ph
            
        else:
            raise ValueError( "pH out of bounds [0-14]" )


    def setName(self, name):
        """
        Sets name of reaction

        Args:
            name (string): Name of reaction
        """

        self.__name = TypeChecker(name, str)


    def setReversible(self, reversible):
        """
        Sets if reaction if reversible or not

        Args:
            reversible (bool): Is reversible
        """

        self.__reversible = TypeChecker(reversible, bool)


    def setId(self, id_):
        """
        Sets internal ID

        Args:
            id_ (string): Internal ID
        """

        self.__id = TypeChecker(id_, str)
        self.setMetaid("METAID_" + id_.upper())


    def setMetaid(self, metaID):
        """
        Sets Meta-ID

        Args:
            metaID (string): Meta-ID
        """

        self.__metaid = TypeChecker(metaID, str)


    def setModel(self, model):
        """
        Sets model of reaction

        Args:
            model (string): KineticModel object describing kinetics of enzyme
        """

        self.__model = TypeChecker(model, KineticModel)


    def setEducts(self, educts):
        """
        INTERNAL. USE addXXX instead!
        """

        if educts == None: 
            self.__educts = []
        else:
            self.__educts = TypeChecker(educts, list)


    def setProducts(self, products):
        """
        INTERNAL. USE addXXX instead!
        """

        if products == None:
            self.__products = list()
        else:
            self.__products = TypeChecker(products, list)


    def setModifiers(self, modifiers):
        """
        INTERNAL. USE addXXX instead!
        """

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

    
        