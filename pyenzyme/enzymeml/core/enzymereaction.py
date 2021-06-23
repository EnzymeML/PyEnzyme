'''
File: enzymereaction.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 9:06:54 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pyenzyme.enzymeml.models.kineticmodel import KineticModel
from pyenzyme.enzymeml.tools.unitcreator import UnitCreator
from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase

import pandas as pd
import json
import re

from copy import deepcopy


class EnzymeReaction(EnzymeMLBase):

    def __init__(
        self,
        temperature,
        tempunit,
        ph,
        name,
        reversible,
        educts=None,
        products=None,
        modifiers=None,
        uri=None,
        creatorId=None
    ):

        """
        Class describing an enzymatic reaction, including
        assay conditions as well as equation

        Args:
            temperature (float): Temperature reaction was executed at
            tempunit (string): Temperature unit
            ph (float): pH value [0,14]
            name (string): Name of reaction
            reversible (bool): Whether or not reaction is reversible
            educts (list<(id, stoich, constant, replicates, initiConcs)>, optional):
                List of tuples describing participant. Defaults to None.
            products (list<(id, stoich, constant, replicates, initiConcs)>, optional):
                List of tuples describing participant. Defaults to None.
            modifiers (list<(id, stoich, constant, replicates, initiConcs)>, optional):
                List of tuples describing participant. Defaults to None.
            String uri: Custom unique identifier
            String creatorId: Identifier to credit Creator
        """

        # Initialize base attributes
        super().__init__(
            uri,
            creatorId
        )

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
        Converts complete EnzymeMLDocument to a
        JSON-formatted string or dictionary.

        Args:
            only_reactions (bool, optional): Returns only reactions including
                                             Reactant/Protein info. Defaults
                                             to False.
            d (bool, optional): Returns dictionary instead of JSON.
                                Defaults to False.
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

                        def getInitConc(elementTuple):
                            return [
                                (val, enzmldoc.getUnitDict()[unit].getName())
                                if enzmldoc else
                                (val, unit)
                                for val, unit in elementTuple[4]
                                ]

                        nu_lst = [

                            {
                                'species': elementTuple[0],
                                'stoich': elementTuple[1],
                                'constant': elementTuple[2],
                                'replicates': [
                                    repl.toJSON(d=True, enzmldoc=enzmldoc)
                                    for repl in elementTuple[3]
                                    ],
                                'init_conc': getInitConc(elementTuple)

                            }
                            for elementTuple in item
                        ]

                        d[key.split('__')[-1]] = nu_lst

                    elif 'unit' in key and enzmldoc is not False and item:
                        unitDef = enzmldoc.getUnitDict()[item]
                        d[key.split('__')[-1]] = unitDef.getName()

                    else:
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
        """
        Returns object as JSON-formatted string

        Returns:
            string: JSON-formatted string
        """

        return self.toJSON()

    def __setInitConc(self, concValue, concUnit, enzmldoc):
        """
        INTERNAL. Sets initial concentrations of reactant.

        Args:
            conc (float): Concentration value
            reactant (string): Reactant ID
            enzmldoc (EnzymeMLDocument): To add and check IDs
            conc_unit (boolean): If none, uses the reactants unit

        Returns:
            string: initConc ID
        """

        # check if unit is an ID
        regex = r"u[\d]+"
        regex = re.compile(regex)

        if regex.search(concUnit) is None:
            # Create new ID for unit
            concUnit = UnitCreator().getUnit(concUnit, enzmldoc)

        # Check if initConc already defined
        concTuple = (concValue, concUnit)

        if concTuple not in enzmldoc.getConcDict().values():

            index = 0
            while True:
                concID = f"c{index}"
                if concID not in enzmldoc.getConcDict().keys():
                    enzmldoc.getConcDict()[concID] = concTuple
                    return concTuple
                index += 1

        else:
            return [
                item for key, item in enzmldoc.getConcDict().items()
                if concTuple == item
                ][0]

    def exportReplicates(self, ids):
        """
        Exports replicated data for given IDs as Pandas.Dataframe objec

        Args:
            ids (string or list<string>): Single or multiple IDs to retrieve
                                          replicate data

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

                repls += [repl.getData() for repl in tup[3]]
                ids.remove(tup[0].split('_')[0])

        if len(ids) > 0:

            print('\nCould not find ', ids, '\n')

        return pd.DataFrame(repls).T

    def getEduct(self, id_, index=False):
        """
        Returns tuple describing reaction element.

        Args:
            id_ (string): Reactant/Modifier ID
            index (bool, optional): If set True, returns index of internal
                                    list of elements. Defaults to False.

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

        raise KeyError("Reactant %s not defined in educts" % id_)

    def getProduct(self, id_, index=False):
        """

        Args:
            id_ (string): Reactant/Modifier ID
            index (bool, optional): If set True, returns index of internal
                                    list of elements. Defaults to False.

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

        raise KeyError("Reactant %s not defined in products" % id_)

    def getModifier(self, id_, index=False):
        """

        Args:
            id_ (string): Reactant/Modifier ID
            index (bool, optional): If set True, returns index of internal
                                    list of elements. Defaults to False.

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

        raise KeyError("Reactant/Protein %s not defined in modifiers" % id_)

    def addInitConc(self, elem_id, conc_val, conc_unit, enzmldoc):

        def __parseAdd(fun, d, elem_id, conc_val, conc_unit, enzmldoc):

            try:
                tup_id = fun(elem_id, index=True)
                elem, stoich, constant, replicates, initConc = d[tup_id]

                nu_initConc = list(set(
                    initConc + [
                        self.__setInitConc(
                            concValue=conc_val,
                            concUnit=conc_unit,
                            enzmldoc=enzmldoc
                            )
                        ]
                    )
                )

                d[tup_id] = (elem, stoich, constant, replicates, nu_initConc)

                return 1

            except KeyError:

                return 0

        # check for all elements
        if __parseAdd(
            self.getEduct,
            self.__educts,
            elem_id,
            conc_val,
            conc_unit,
            enzmldoc
        ):
            return 1

        elif __parseAdd(
            self.getProduct,
            self.__products,
            elem_id,
            conc_val,
            conc_unit,
            enzmldoc
        ):
            return 1

        elif __parseAdd(
            self.getModifier,
            self.__modifiers,
            elem_id,
            conc_val,
            conc_unit,
            enzmldoc
        ):
            return 1

        else:
            raise KeyError(
                f"Reactant/Protein {elem_id} not defined in reaction!"
                )

    def addReplicate(self, replicate, enzmldoc, by_id=True):
        """
        Adds Replicate object to EnzymeReaction object.
        Destination is inherited automatically based on ID.

        Args:
            replicate (Replicate): Replicate object describing
                                   experimental data
            enzmldoc (EnzymeMLDocument): Checks and adds IDs

        Raises:
            AttributeError: If no experimental data has been added
            AttributeError: If reactant/protein ID unfindable in reaction

        Returns:
            int: 1 for success
        """

        # Helper functions BEGIN

        def getName(name, by_id):
            if by_id:
                return enzmldoc.getReactant(name, by_id).getId()
            else:
                return enzmldoc.getReactant(name, by_id).getName()

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
                unitID = enzmldoc.getUnitDict()[time_unit].getId()
                replicate.setTimeUnit(unitID)
            else:
                unitID = UnitCreator().getUnit(time_unit, enzmldoc)
                replicate.setTimeUnit(unitID)

            if isID(data_unit):
                unitID = enzmldoc.getUnitDict()[data_unit].getId()
                replicate.setDataUnit(unitID)
            else:
                unitID = UnitCreator().getUnit(data_unit, enzmldoc)
                replicate.setDataUnit(unitID)

            return replicate

        def checkExistingReactant(elementList):

            reactantID = replicate.getReactant()

            for elementIndex in range(len(elementList)):

                if getName(elementList[elementIndex][0], by_id) == reactantID:

                    # Add replicate object
                    elementList[elementIndex][3].append(
                        checkUnits(replicate, enzmldoc)
                    )

                    # Add initial concentration
                    initConcTuple = enzmldoc.getConcDict()[
                            replicate.getInitConc()
                        ]

                    if initConcTuple not in elementList[elementIndex][4]:
                        elementList[elementIndex][4].append(
                            initConcTuple
                        )

                    return 1

        # Helper functions END

        # Add Replicates section
        # Turn initial cocncentrations to IDs

        try:
            if replicate.getDataUnit() in enzmldoc.getUnitDict().keys():
                # Check if the unit is already an index defined in teh document
                init_conc_tup = (
                    replicate.getInitConc(),
                    replicate.getDataUnit()
                )

            else:
                # If not, create a new one
                init_conc_tup = (
                    replicate.getInitConc(),
                    UnitCreator().getUnit(replicate.getDataUnit(), enzmldoc)
                )

            inv_conc = {
                item: key
                for key, item in enzmldoc.getConcDict().items()
            }

            replicate.setInitConc(inv_conc[init_conc_tup])

        except KeyError:
            index = 0

            init_conc_tup = (
                replicate.getInitConc(),
                UnitCreator().getUnit(replicate.getDataUnit(), enzmldoc)
            )

            while True:
                id_ = "c%i" % index

                if id_ not in enzmldoc.getConcDict().keys():
                    enzmldoc.getConcDict()[id_] = init_conc_tup
                    replicate.setInitConc(id_)
                    break

                else:
                    index += 1

        try:
            replicate.getData()
        except AttributeError:
            raise AttributeError(
                "Replicate has no series data. \
                Add data via replicate.setData( pandas.Series )"
                )

        if checkExistingReactant(self.__educts):
            return 1

        elif checkExistingReactant(self.__products):
            return 1

        elif checkExistingReactant(self.__modifiers):
            return 1

        else:
            raise AttributeError(
                f"Replicate's reactant {replicate.getReactant()}\
                     not defined in reaction"
                )

    def __addElement(
        self,
        speciesID,
        stoichiometry,
        isConstant,
        elementList,
        enzmldoc,
        replicates=[],
        initConcs=[]
    ):

        # Check if type of ID is correct
        speciesID = TypeChecker(speciesID, str)
        stoichiometry = TypeChecker(float(stoichiometry), float)
        isConstant = TypeChecker(isConstant, bool)
        replicates = TypeChecker(replicates, list)
        initConcs = TypeChecker(initConcs, list)

        # Check if species is part of document already
        if speciesID not in enzmldoc.getReactantDict().keys():
            if speciesID not in enzmldoc.getProteinDict().keys():
                raise KeyError(
                    f"Reactant/Protein with id {speciesID} is not defined yet"
                )

        # Add intial concentrations
        initConcs = [
            self.__setInitConc(
                concValue=value,
                concUnit=unit,
                enzmldoc=enzmldoc
            )
            for value, unit in initConcs
        ]

        # Add altogether to the element list
        elementList.append(
            (
                speciesID,
                stoichiometry,
                isConstant,
                replicates,
                initConcs
            )
        )

    def addEduct(
        self,
        speciesID,
        stoichiometry,
        isConstant,
        enzmldoc,
        replicates=[],
        initConcs=[]
    ):
        """
        Adds element to EnzymeReaction object. Replicates as well
        as initial concentrations are optional.

        Args:
            speciesID (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            isConstant (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs
            replicates (list, optional): Replicate object list. Defaults to [].
            initConcs (list, optional): List of InitConcs. Defaults to [].

        Raises:
            KeyError: If Reactant/Protein hasnt been defined yet
        """

        self.__addElement(
            speciesID=speciesID,
            stoichiometry=stoichiometry,
            isConstant=isConstant,
            replicates=replicates,
            initConcs=initConcs,
            elementList=self.__educts,
            enzmldoc=enzmldoc
        )

    def addProduct(
        self,
        speciesID,
        stoichiometry,
        isConstant,
        enzmldoc,
        replicates=[],
        initConcs=[]
    ):
        """
        Adds element to EnzymeReaction object. Replicates as well
        as initial concentrations are optional.

        Args:
            speciesID (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            isConstant (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs
            replicates (list, optional): Replicate object list. Defaults to [].
            initConcs (list, optional): List of InitConcs. Defaults to [].

        Raises:
            KeyError: If Reactant/Protein hasnt been defined yet
        """

        self.__addElement(
            speciesID=speciesID,
            stoichiometry=stoichiometry,
            isConstant=isConstant,
            replicates=replicates,
            initConcs=initConcs,
            elementList=self.__products,
            enzmldoc=enzmldoc
        )

    def addModifier(
        self,
        speciesID,
        stoichiometry,
        isConstant,
        enzmldoc,
        replicates=[],
        initConcs=[]
    ):
        """
        Adds element to EnzymeReaction object. Replicates as well
        as initial concentrations are optional.

        Args:
            speciesID (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            isConstant (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs
            replicates (list, optional): Replicate object list. Defaults to [].
            initConcs (list, optional): List of InitConcs. Defaults to [].

        Raises:
            KeyError: If Reactant/Protein hasnt been defined yet
        """

        self.__addElement(
            speciesID=speciesID,
            stoichiometry=stoichiometry,
            isConstant=isConstant,
            replicates=replicates,
            initConcs=initConcs,
            elementList=self.__modifiers,
            enzmldoc=enzmldoc
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
            raise ValueError(
                "pH out of bounds [0-14]"
            )

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

        if educts is None:
            self.__educts = []
        else:
            self.__educts = TypeChecker(educts, list)

    def setProducts(self, products):
        """
        INTERNAL. USE addXXX instead!
        """

        if products is None:
            self.__products = list()
        else:
            self.__products = TypeChecker(products, list)

    def setModifiers(self, modifiers):
        """
        INTERNAL. USE addXXX instead!
        """

        if modifiers is None:
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
