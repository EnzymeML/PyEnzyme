'''
File: enzymemldocument.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Thursday July 15th 2021 1:00:05 am
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.creator import Creator
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction
from pyenzyme.enzymeml.tools.unitcreator import UnitCreator
from pyenzyme.enzymeml.tools.enzymemlwriter import EnzymeMLWriter
from pyenzyme.enzymeml.tools.dataverse import toDataverseJSON

import pyenzyme.enzymeml.tools.enzymemlreader as reader


from texttable import Texttable

import json
import urllib


class EnzymeMLDocument(object):

    def __init__(
        self,
        name,
        level=3,
        version=2,
        doi=None,
        pubmedID=None,
        url=None
    ):
        """
        Class describing a complete EnzymeML document.

        Args:
            name (string): EnzymeML document name
            level (int, optional): SBML level. Defaults to 3.
            version (int, optional): SBML version. Defaults to 2.
        """

        self.setName(name)
        self.setLevel(level)
        self.setVersion(version)

        self.setProteinDict(dict())
        self.setReactantDict(dict())
        self.setReactionDict(dict())
        self.setMeasurementDict(dict())
        self.setUnitDict(dict())
        self.setConcDict(dict())

        if pubmedID:
            self.setPubmedID(pubmedID)
        if doi:
            self.setDoi(doi)
        if url:
            self.setUrl(url)

    @staticmethod
    def fromFile(path):
        TypeChecker(path, str)
        return reader.EnzymeMLReader().readFromFile(path)

    def toDataverseJSON(self):
        """Generates a Dataverse compatible JSON representation of this EnzymeML document.

        Returns:
            String: JSON string representation of this EnzymeML document.
        """
        return json.dumps(toDataverseJSON(self), indent=4)

    def addMeasurement(self, measurement):
        """Adds a measurement to an EnzymeMLDocument and validates consistency with already defined elements of the documentself.

        Args:
            measurement (Measurement): Collection of data and initial concentrations per reaction

        Returns:
            measurementID (String): Assigned measurement identifier.
        """

        # Check consistency
        self.__checkMeasurementConsistency(measurement)

        # Convert all measurement units to UnitDefs
        self.__convertMeasurementUnits(measurement)

        # Finally generate the ID and add it to the dictionary
        measurementID = self.__generateID(
            prefix="m", dictionary=self.__MeasurementDict
        )
        measurement.setId(measurementID)

        self.__MeasurementDict[measurementID] = measurement

        return measurementID

    def __convertMeasurementUnits(self, measurement):
        """Converts string SI units to UnitDef objects and IDs

        Args:
            measurement (Measurement): Object defining a measurement
        """
        speciesDict = measurement.getSpeciesDict()
        measurement.setGlobalTimeUnit(
            self.__convertUnit(measurement.getGlobalTimeUnit())
        )

        for data in speciesDict['proteins'].values():
            data.setUnit(
                self.__convertUnit(data.getUnit())
            )
            self.__convertReplicateUnits(data)

        for data in speciesDict['reactants'].values():
            data.setUnit(
                self.__convertUnit(data.getUnit())
            )
            self.__convertReplicateUnits(data)

    def __convertReplicateUnits(self, data):
        for replicate in data.getReplicates():
            replicate.setDataUnit(
                self.__convertUnit(replicate.getDataUnit())
            )
            replicate.setTimeUnit(
                self.__convertUnit(replicate.getTimeUnit())
            )

    def __checkMeasurementConsistency(self, measurement):

        speciesDict = measurement.getSpeciesDict()

        self.__checkSpecies(speciesDict["reactants"])
        self.__checkSpecies(speciesDict["proteins"])

    def __checkSpecies(self, measurementSpecies):

        for speciesID in measurementSpecies.keys():
            speciesType = "Reactant" if speciesID[0] == "s" else "Protein"
            speciesDict = self.__ReactantDict if speciesType == "Reactant" else self.__ProteinDict

            if speciesID not in speciesDict.keys():
                raise KeyError(
                    f"{speciesType} {speciesID} is not defined in the EnzymeMLDocument yet. Please define via the {speciesType} class and add it to the document via the add{speciesType} method.")

    @staticmethod
    def __generateID(prefix, dictionary):
        # fetch all keys and sort the
        if dictionary.keys():
            number = max([int(ID[1::]) for ID in dictionary]) + 1
            return prefix + str(number)

        else:
            return prefix + str(0)

    def __validField(self, log, enzml_obj, valid_key, valid):
        """Generates validation field and log

        Args:
            log (dict): Dictionary for logging validation results
            enzml_obj (dict): EnzymeML document JSON representation
            valid_key (string): Dict key to the respective validation object
            valid (dict): JSON validaton termplate representation
        """

        for key, item in valid[valid_key].items():
            importance = item['importance']

            if key in enzml_obj.keys():

                if importance == 'Mandatory':
                    log[key] = 'Valid'
                elif importance == 'Not supported':
                    log[key] = 'Not supported'

            else:
                if importance == 'Mandatory':
                    log[key] = 'Mandatory missing'
                    self.is_valid = False
                elif importance == 'Optional':
                    log[key] = 'Optional missing'
                elif importance == 'Not supported':
                    log[key] = 'Not supported'

    def validate(self, JSON=None, link=None, log=False):
        """
        Validate an EnzymeML file by using either a link
        to an existing file or a JSON schema.
        Please note that when a link is already given
        the JSON instance will be overriden.

        Args:
            JSON (dict/string, optional): JSON representation of an EnzymemL
                                          validation schema. Defaults to None.
            link (string, optional): Link to an existing JSON template.
                                     Defaults to None.
            log (Boolean, optional): Whether or not a log is returned.
                                     Defaults to False
        """

        # Convert EnzymeML document to JSON
        enzmldoc_json = self.toJSON(d=True)

        # Fetch validation template
        if link:
            response = urllib.request.urlopen(link)
            valid = json.loads(response.read())

        elif JSON:
            if type(JSON) == str:
                JSON = json.loads(JSON)
            valid = JSON

        else:
            raise FileNotFoundError(
                'Please provide either a JSON dict validation template or link'
            )

        # Initialize Log
        log = dict()
        self.is_valid = True

        # Validate general information
        log['EnzymeMLDocument'] = dict()

        self.__validField(
            log['EnzymeMLDocument'],
            enzmldoc_json,
            "EnzymeMLDocument",
            valid
        )

        # Validate Vessel
        log['Vessel'] = dict()

        self.__validField(
            log['Vessel'],
            enzmldoc_json['vessel'],
            "Vessel",
            valid
        )

        # Validate Reactants
        log['Reactant'] = dict()

        for reactant in enzmldoc_json['reactant']:
            log['Reactant'][reactant['id']] = dict()
            self.__validField(
                log['Reactant'][reactant['id']],
                reactant,
                "Reactant",
                valid
            )

        # Validate Proteins
        log['Protein'] = dict()

        for protein in enzmldoc_json['protein']:
            log['Protein'][protein['id']] = dict()

            self.__validField(
                log['Protein'][protein['id']],
                protein,
                "Protein",
                valid
            )

        # Validate Reactions
        log['EnzymeReaction'] = dict()
        for reaction in enzmldoc_json['reaction']:
            log['EnzymeReaction'][reaction['id']] = dict()

            self.__validField(
                log['EnzymeReaction'][reaction['id']],
                reaction,
                "EnzymeReaction",
                valid
            )

            # merge replicates and validate all of them
            def getRepls(reactionElement):
                return [repl for species in reaction[reactionElement]
                        for repl in species['replicates']
                        ]

            replicates = getRepls('educts') +\
                getRepls('products') +\
                getRepls('modifiers')

            log['EnzymeReaction'][reaction['id']]['replicates'] = dict()
            for replicate in replicates:
                log['EnzymeReaction'][reaction['id']
                                      ]['replicates'][replicate['replica']] = dict()

                self.__validField(
                    log['EnzymeReaction'][reaction['id']
                                          ]['replicates'][replicate['replica']],
                    replicate,
                    "Replicate",
                    valid
                )

        if log:
            return {'isvalid': self.is_valid, 'log': log}
        else:
            return self.is_valid

    def toFile(self, path):
        EnzymeMLWriter().toFile(self, path)

    def toXMLString(self):
        return EnzymeMLWriter().toXMLString(self)

    def toJSON(self, d=False, only_reactions=False):
        """
        Converts complete EnzymeMLDocument to
        a JSON-formatted string or dictionary.

        Args:
            only_reactions (bool, optional): Returns only reactions including
                                             Reactant/Protein info.
                                             Defaults to False.
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

            # create JSON file with correct names
            enzmldoc_dict = dict()
            kwds = ['ProteinDict', 'ReactantDict', 'ReactionDict']

            if only_reactions:
                kwds = ['ReactionDict']

            # iterate over attributes and call toJSON
            for key, item in self.__dict__.items():

                key = key.split('__')[-1]

                # GET SINGLE ATTRIBUTES
                if type(item) == str or type(item) == int:
                    # store basic meta information
                    enzmldoc_dict[key.lower()] = item

                # Get Creator
                elif key.lower() == "creator":
                    enzmldoc_dict[key.lower()] = [
                        creator.toJSON(d=True, enzmldoc=self)
                        for creator in item
                    ]

                # GET VESSEL/Creator
                elif key == 'vessel':
                    # add vessel to the dictionary
                    enzmldoc_dict[key.lower()] = item.toJSON(
                        d=True,
                        enzmldoc=self
                    )

                # GET DICTIONARIES
                elif type(item) == dict and key in kwds:

                    # store dictionaries and transform IDs
                    cleanedElementKey = key.replace('Dict', '').lower()
                    enzmldoc_dict[cleanedElementKey] = list()

                    # iterate over entries and use toJSON method
                    for elem in item.values():
                        jsonElem = elem.toJSON(d=True, enzmldoc=self)

                        # Add JSON object to element array
                        enzmldoc_dict[cleanedElementKey].append(jsonElem)

            return enzmldoc_dict

        if d:
            return transformAttr(self)

        return json.dumps(
            self,
            default=transformAttr,
            indent=4
        )

    def __str__(self):
        """
        Magic function return pretty string describing the object.

        Returns:
            string: Beautified summarization of object
        """

        fin_string = ['>>> Units']
        for key, item in self.__UnitDict.items():
            fin_string.append('\tID: %s \t Name: %s' % (key, item.getName()))

        fin_string.append('>>> Reactants')
        for key, item in self.__ReactantDict.items():
            fin_string.append('\tID: %s \t Name: %s' % (key, item.getName()))

        fin_string.append('>>> Proteins')
        for key, item in self.__ProteinDict.items():
            fin_string.append('\tID: %s \t Name: %s' % (key, item.getName()))

        fin_string.append('>>> Reactions')
        for key, item in self.__ReactionDict.items():
            fin_string.append('\tID: %s \t Name: %s' % (key, item.getName()))

        fin_string.append('>>> Measurements')
        fin_string.append(self.printMeasurements())

        return "\n".join(fin_string)

    def addConc(self, tup):
        """
        Adds initial concentration to ConcDict. Only internal usage!

        Args:
            tup (float, string): Value and unit of initial concentration
        """

        # Generate the ID
        concID = self.__generateID(prefix="c", dictionary=self.__ConcDict)

        # Add it to the dicitionary
        self.__ConcDict[concID] = tup

        return concID

    def getUnitDef(self, unitID):
        """Return UnitDef

        Args:
            unitID (string): Unit identifier

        Returns:
            UnitDef: Unit definition object
        """
        assert isinstance(unitID, str)
        return self.__UnitDict[unitID]

    def getDoi(self):
        """
        Return DOI

        Returns:
            string: DOI Identifier
        """

        return self.__doi

    def getPubmedID(self):
        """
        Returns PubmedID

        Returns:
            string: PubMed ID
        """

        return self.__pubmedID

    def getUrl(self):
        """
        Return URL

        Returns:
            string: Arbitrary URL
        """

        return self.__url

    def setDoi(self, doi):
        """
        Sets DOI of EnzymeML document. Adds Identifiers.org URI if not given.

        Args:
            doi (string): EnzymeML document or publication DOI
        """

        if "https://identifiers.org/doi:" in TypeChecker(doi, str):
            self.__doi = doi
        else:
            self.__doi = "https://identifiers.org/doi:" + doi

    def setPubmedID(self, pubmedID):
        """
        Sets PubMedID of EnzymeML document.
        Add Identifiers.org URI if not given

        Args:
            pubmedID (string): EnzymeML document ot publication PubMedID
        """

        if "https://identifiers.org/pubmed:" in pubmedID:
            self.__pubmedID = TypeChecker(pubmedID, str)
        else:
            self.__pubmedID = "https://identifiers.org/pubmed:" + \
                TypeChecker(pubmedID, str)

    def setUrl(self, url):
        """
        Sets arbitrary URL of EnzymeML document

        Args:
            url (string): Arbitraty URL
        """

        self.__url = TypeChecker(url, str)

    def delDoi(self):
        del self.__doi

    def delPubmedID(self):
        del self.__pubmedID

    def delUrl(self):
        del self.__url

    def getConcDict(self):
        return self.__ConcDict

    def setConcDict(self, value):
        self.__ConcDict = value

    def delConcDict(self):
        del self.__ConcDict

    def printReactions(self):
        """
        Prints reactions found in the object
        """

        print('>>> Reactions')
        for key, item in self.__ReactionDict.items():
            print('    ID: %s \t Name: %s' % (key, item.getName()))

    def printUnits(self):
        """
        Prints units found in the object
        """

        print('>>> Units')
        for key, item in self.__UnitDict.items():
            print('    ID: %s \t Name: %s' % (key, item.getName()))

    def printReactants(self):
        """
        Prints reactants found in the object
        """

        print('>>> Reactants')
        for key, item in self.__ReactantDict.items():
            print('    ID: %s \t Name: %s' % (key, item.getName()))

    def printProteins(self):
        """
        Prints proteins found in the object
        """

        print('>>> Proteins')
        for key, item in self.__ProteinDict.items():
            print('    ID: %s \t Name: %s' % (key, item.getName()))

    def printMeasurements(self):

        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.set_cols_align(["l", "l", "l", "l"])

        # Initialize rows
        rows = [["ID", "Species", "Conc", "Unit"]]

        # Generate and append rows
        for measurementID, measurement in self.__MeasurementDict.items():

            speciesDict = measurement.getSpeciesDict()
            proteins = speciesDict['proteins']
            reactants = speciesDict['reactants']

            # succesively add rows with schema
            # [ measID, speciesID, initConc, unit ]

            for speciesID, species in {**proteins, **reactants}.items():
                rows.append(
                    [
                        measurementID,
                        speciesID,
                        species.getInitConc(),
                        self.getUnitString(species.getUnit())
                    ]
                )

        # Add empty row for better readablity
        rows.append([" "] * 4)

        table.add_rows(rows)
        return "\n" + table.draw() + "\n"

    def getUnitString(self, unitID):
        return self.__UnitDict[unitID].getName()

    def getReaction(self, id_, by_id=True):
        """
        Returns reaction object by ID or name

        Args:
            id_ (string): Unique Identifier of reaction to retrieve
            by_id (bool, optional): If set False id_ has to be reactions name.
                                    Defaults to True.

        Raises:
            KeyError: If ID is unfindable
            KeyError: If Name is unfindable

        Returns:
            EnzymeReaction: Object describing a reaction
        """

        return self.__getElement(
            id_=id_,
            dictionary=self.__ReactionDict,
            elementType="Reaction",
            by_id=by_id
        )

    def getMeasurement(self, id_, by_id=True):
        """
        Returns reaction object by ID or name

        Args:
            id_ (string): Unique Identifier of measurement to retrieve
            by_id (bool, optional): If set False id_ has to be reactions name.
                                    Defaults to True.

        Raises:
            KeyError: If ID is unfindable
            KeyError: If Name is unfindable

        Returns:
            EnzymeReaction: Object describing a reaction
        """

        return self.__getElement(
            id_=id_,
            dictionary=self.__MeasurementDict,
            elementType="Measurement",
            by_id=by_id
        )

    def getReactant(self, id_, by_id=True):
        """
        Returns reactant object by ID or name

        Args:
            id_ (string): Unique Identifier of reactant to retrieve
            by_id (bool, optional): If set False id_ has to be reactants name.
                                    Defaults to True.

        Raises:
            KeyError: If ID is unfindable
            KeyError: If Name is unfindable

        Returns:
            Reactant: Object describing a reactant
        """

        return self.__getElement(
            id_=id_,
            dictionary=self.__ReactantDict,
            elementType="Reactant",
            by_id=by_id
        )

    def getProtein(self, id_, by_id=True):
        """
        Returns protein object by ID or name

        Args:
            id_ (string): Unique Identifier of protein to retrieve
            by_id (bool, optional): If set False id_ has to be protein name.
                                    Defaults to True.

        Raises:
            KeyError: If ID is unfindable
            KeyError: If Name is unfindable

        Returns:
            Protein: Object describing a protein
        """

        return self.__getElement(
            id_=id_,
            dictionary=self.__ProteinDict,
            elementType="Protein",
            by_id=by_id
        )

    def __getElement(self, id_, dictionary, elementType, by_id=True):

        if by_id:
            try:
                return dictionary[id_]
            except KeyError:
                raise KeyError(
                    f"{elementType} {id_} not found in the EnzymeML document {self.__name}"
                )

        else:
            name = id_
            for element in dictionary:
                if element.getName() == name:
                    return element

            raise ValueError(
                f"{elementType} {name} not found in the EnzymeML document {self.__name}"
            )

    def getReactantList(self):
        """Returns a list of all Reactant objects

        Returns:
            list<Reactant>: List of Reactant objects in the document
        """
        return self.__getSpeciesList(self.__ReactantDict)

    def getProteinList(self):
        """Returns a list of all Protein objects

        Returns:
            list<Protein>: List of Protein objects in the document
        """
        return self.__getSpeciesList(self.__ReactantDict)

    def getReactionList(self):
        """Returns a list of all Reaction objects

        Returns:
            list<Reaction>: List of Reaction objects in the document
        """
        return self.__getSpeciesList(self.__ReactionDict)

    @staticmethod
    def __getSpeciesList(dictionary):
        """Helper function to retrieve lists of dicitonary objects

        Args:
            dictionary (dict): Dictionary of corresponding elements

        Returns:
            list<Objects>: Returns all values in the dictionary
        """
        return list(dictionary.values())

    def addReactant(self, reactant, use_parser=True, custom_id=None):
        """
        Adds Reactant object to EnzymeMLDocument object.
        Automatically assigns ID and converts units.

        Args:
            reactant (Reactant): Object describing reactant
            use_parser (bool, optional): If set True, will use
                                         internal unit parser.
                                         Defaults to True.
            custom_id (str, optional): Assigns custom ID instead of automatic.
                                       Defaults to 'NULL'.

        Returns:
            string: Internal identifier for the reactant.
                    Use it for other objects!
        """

        # Assert correct type
        TypeChecker(reactant, Reactant)

        return self.__addSpecies(
            species=reactant,
            prefix="s",
            dictionary=self.__ReactantDict,
            use_parser=use_parser,
            custom_id=custom_id
        )

    def addProtein(self, protein, use_parser=True, custom_id=None):
        """
        Adds Protein object to EnzymeMLDocument object.
        Automatically assigns ID and converts units.

        Args:
            protein (Protein): Object describing g
            use_parser (bool, optional): If set True, will use
                                         internal unit parser.
                                         Defaults to True.
            custom_id (str, optional): Assigns custom ID instead of automatic.
                                       Defaults to 'NULL'.

        Returns:
            string: Internal identifier for the protein.
                    Use it for other objects!
        """

        TypeChecker(protein, Protein)

        return self.__addSpecies(
            species=protein,
            prefix="p",
            dictionary=self.__ProteinDict,
            use_parser=use_parser,
            custom_id=custom_id
        )

    def __addSpecies(
        self,
        species,
        prefix,
        dictionary,
        use_parser=True,
        custom_id=None
    ):

        # Generate ID
        if custom_id:
            speciesID = custom_id
        else:
            speciesID = self.__generateID(prefix=prefix, dictionary=dictionary)

        species.setId(speciesID)

        # Update unit to UnitDefID
        if use_parser:
            try:
                speciesUnit = self.__convertUnit(species.getSubstanceUnits())
                species.setSubstanceUnits(speciesUnit)
            except AttributeError:
                pass

        # Add species to dictionary
        dictionary[speciesID] = species

        return speciesID

    def addReaction(self, reaction, use_parser=True):
        """
        Adds EnzymeReaction object to EnzymeMLDocument object.
        Automatically assigns ID and converts units.

        Args:
            reaction (EnzymeReaction): Object describing reaction
            use_parser (bool, optional): If set True, will use
                                         internal unit parser.
                                         Defaults to True.

        Returns:
            string: Internal identifier for the reaction.
            Use it for other objects!
        """

        TypeChecker(reaction, EnzymeReaction)

        # Generate ID
        reactionID = self.__generateID("r", self.__ReactionDict)
        reaction.setId(reactionID)

        if use_parser:
            # Reset temperature for SBML compliance to Kelvin
            reaction.setTemperature(reaction.getTemperature() + 273.15)
            reaction.setTempunit(
                self.__convertUnit(reaction.getTempunit())
            )

        # Set model units
        if hasattr(reaction, '_EnzymeReaction__model'):
            model = reaction.getModel()

        # Finally add the reaction to the document
        self.__ReactionDict[reactionID] = reaction

        return reactionID

    def __convertUnit(self, unit):
        if unit in self.__UnitDict.keys():
            return unit
        else:
            return UnitCreator().getUnit(unit, self)

    def get_created(self):
        """
        Returns date of creation

        Returns:
            string: Date of creation
        """

        return self.__created

    def getModified(self):
        """
        Returns date of recent modification

        Returns:
            string: Date of recent modification
        """

        return self.__modified

    def setCreated(self, date):
        """
        Sets date of creation

        Args:
            date (string): Date of creation
        """

        self.__created = TypeChecker(date, str)

    def setModified(self, date):
        """
        Sets date of recent modification

        Args:
            date (string): Date of recent modification
        """

        self.__modified = TypeChecker(date, str)

    def delCreated(self):
        del self.__created

    def delModified(self):
        del self.__modified

    def getCreator(self):
        return self.__creator

    def setCreator(self, creators):
        """
        Sets creator information. Multiples are also allowed
        as a list of Creator classes

        Args:
            creators (string, list<string>): Single or multiple author classes
        """

        if type(creators) == list:
            self.__creator = [
                TypeChecker(creator, Creator)
                for creator in creators
            ]
        else:
            self.__creator = [TypeChecker(creators, Creator)]

    def delCreator(self):
        del self.__creator

    def getVessel(self):
        return self.__vessel

    def setVessel(self, vessel, use_parser=True):
        """
        Sets vessel information

        Args:
            vessel (Vessel): Object describing a vessel
            use_parser (bool, optional): If set True, will use
                                         internal unit parser.
                                         Defaults to True.

        Returns:
            string : Internal identifier for Vessel object.
                     Use it for other objetcs!
        """

        # Automatically set unit
        if use_parser:

            vessel.setUnit(

                UnitCreator().getUnit(vessel.getUnit(), self)

            )

            # TODO Automatic ID assignment
            vessel.setId('v0')

        self.__vessel = TypeChecker(vessel, Vessel)

        return vessel.getId()

    def delVessel(self):
        del self.__vessel

    def getName(self):
        """
        Returns name of EnzymeML document

        Returns:
            string: Name of document
        """

        return self.__name

    def getLevel(self):
        return self.__level

    def getVersion(self):
        return self.__version

    def getProteinDict(self):
        """
        Return protein dictionary for manual access

        Returns:
            dict: Dictionary containing Protein objects describing proteins
        """

        return self.__ProteinDict

    def getReactantDict(self):
        """
        Return reactant dictionary for manual access

        Returns:
            dict: Dictionary containing Reactant objects describing reactants
        """

        return self.__ReactantDict

    def getReactionDict(self):
        """
        Return reaction dictionary for manual access

        Returns:
            dict: Dictionary containing EnzymeReaction
                  objects describing reactions
        """

        return self.__ReactionDict

    def getMeasurementDict(self):
        """
        Return reaction dictionary for manual access

        Returns:
            dict: Dictionary containing EnzymeReaction
                  objects describing reactions
        """

        return self.__MeasurementDict

    def getUnitDict(self):
        """
        Return unit dictionary for manual access

        Returns:
            dict: Dictionary containing UnitDef objects describing units
        """

        return self.__UnitDict

    def setName(self, value):
        """
        Sets name of the EnzymeML document

        Args:
            value (string): Name of the document
        """

        self.__name = value

    def setLevel(self, level):
        """
        Sets SBML level of document

        Args:
            level (int): SBML level

        Raises:
            IndexError: If SBML level not in [1,3]
        """

        if 1 <= TypeChecker(level, int) <= 3:
            self.__level = level
        else:
            raise IndexError(
                "Level out of bounds. SBML level is defined from 1 to 3."
            )

    def setVersion(self, version):
        """
        Sets SBML version

        Args:
            version (string): SBML level
        """

        self.__version = TypeChecker(version, int)

    def setProteinDict(self, proteinDict):
        self.__ProteinDict = TypeChecker(proteinDict, dict)

    def setReactantDict(self, reactantDict):
        self.__ReactantDict = TypeChecker(reactantDict, dict)

    def setMeasurementDict(self, measurementDict):
        self.__MeasurementDict = TypeChecker(measurementDict, dict)

    def setReactionDict(self, reactionDict):
        self.__ReactionDict = TypeChecker(reactionDict, dict)

    def setUnitDict(self, unitDict):
        self.__UnitDict = TypeChecker(unitDict, dict)

    def delName(self):
        del self.__name

    def delLevel(self):
        del self.__level

    def delVersion(self):
        del self.__version

    def delProteinDict(self):
        del self.__ProteinDict

    def delReactantDict(self):
        del self.__ReactantDict

    def delReactionDict(self):
        del self.__ReactionDict

    def delMeasurementDict(self):
        del self.__MeasurementDict

    def delUnitDict(self):
        del self.__UnitDict
