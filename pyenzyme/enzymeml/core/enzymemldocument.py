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

import os
import re
import json

from pydantic import Field, validator, PositiveInt
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass
from pathlib import Path

from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies

from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.creator import Creator
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.core.measurement import Measurement
from pyenzyme.enzymeml.core.measurementData import MeasurementData
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction
from pyenzyme.enzymeml.tools.unitcreator import UnitCreator
from pyenzyme.enzymeml.tools.enzymemlwriter import EnzymeMLWriter
from pyenzyme.enzymeml.databases.dataverse import toDataverseJSON
from pyenzyme.enzymeml.databases.dataverse import uploadToDataverse

import pyenzyme.enzymeml.tools.enzymemlreader as reader

from pyenzyme.enzymeml.core.ontology import EnzymeMLPart, SBOTerm
from pyenzyme.enzymeml.core.exceptions import SpeciesNotFoundError, IdentifierNameError
from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)

from texttable import Texttable


if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


class EnzymeMLDocument(object):

    name: str = Field(
        description="Title of the EnzymeML Document.",
        required=True
    )

    level: int = Field(
        default=3,
        description="SBML evel of the EnzymeML XML.",
        required=True,
        inclusiveMinimum=1,
        exclusiveMaximum=3
    )

    version: str = Field(
        default=2,
        description="SBML version of the EnzymeML XML.",
        required=True
    )

    pubmed_id: Optional[str] = Field(
        default=None,
        description="Pubmed ID reference.",
        required=False
    )

    url: Optional[str] = Field(
        default=None,
        description="Arbitrary type of URL that is related to the EnzymeML document.",
        required=False,
    )

    doi: Optional[str] = Field(
        default=None,
        description="Digital Object Identifier of the referenced publication or the EnzymeML document.",
        regex=r"/^10.\d{4,9}/[-._;()/:A-Z0-9]+$/i"
    )

    protein_dict: dict[str, Protein] = Field(
        default_factory=dict,
        description="Dictionary mapping from protein IDs to protein describing objects.",
        required=False
    )

    reactant_dict: dict[str, Reactant] = Field(
        default_factory=dict,
        description="Dictionary mapping from reactant IDs to reactant describing objects.",
        required=False
    )

    reaction_dict: dict[str, EnzymeReaction] = Field(
        default_factory=dict,
        description="Dictionary mapping from reaction IDs to reaction describing objects.",
        required=False
    )

    unit_dict: dict[str, UnitDef] = Field(
        default_factory=dict,
        description="Dictionary mapping from unit IDs to unit describing objects.",
        required=False
    )

    measurement_dict: dict[str, Measurement] = Field(
        default_factory=dict,
        description="Dictionary mapping from measurement IDs to measurement describing objects.",
        required=False
    )

    file_dict: dict[str, dict] = Field(
        default_factory=dict,
        description="Dictionary mapping from protein IDs to protein describing objects.",
        required=False
    )

    conc_dict: dict[str, tuple[float, str]] = Field(
        default_factory=dict,
        description="Dictionary mapping from concentration IDs to concentration describing objects.",
        required=False
    )

    # ! Validators
    @validator("pubmed_id")
    def add_identifier(cls, pubmed_id: str):
        """Adds an identifiers.org link in front of the pubmed ID if not given"""

        if pubmed_id.startswith("https://identifiers.org/pubmed:"):
            return pubmed_id
        else:
            return "https://identifiers.org/pubmed:" + pubmed_id

    # ! Imports and exports
    @staticmethod
    def fromFile(path: Path):
        """Initializes an EnzymeMLDocument from an OMEX container."

        Args:
            path (Path): Path to the OMEX container.

        Returns:
            EnzymeMLDocument: The intialized EnzymeML document.
        """

        return reader.EnzymeMLReader().readFromFile(path)

    def toFile(self, path: Path, verbose: PositiveInt = 1):
        """Saves an EnzymeML document to an OMEX container at the specified path

        Args:
            path (Path): Path where the document should be saved.
            verbose (PositiveInt, optional): Level of verbosity, in order to print a message and the resulting path. Defaults to 1.
        """

        EnzymeMLWriter().toFile(self, path, verbose=verbose)

    def toXMLString(self):
        """Generates an EnzymeML XML string"""

        return EnzymeMLWriter().toXMLString(self)

    def toDataverseJSON(self) -> str:
        """Generates a Dataverse compatible JSON representation of this EnzymeML document.

        Returns:
            String: JSON string representation of this EnzymeML document.
        """

        return json.dumps(toDataverseJSON(self), indent=4)

    # ! Utility methods
    @ staticmethod
    def _generateID(prefix: str, dictionary: dict) -> str:
        """Generates IDs complying to the [s|p|r|m|u|c]?[digit]+ schema.

        Args:
            prefix (str): Character denoting the type of species (p: Protein, s: Reactant, u: UnitDef, r: EnzymeReaction, m: Measurement, c: concentration).
            dictionary (dict): The dictionary from which the ID is generated and used to determine the number.

        Returns:
            str: Unique internal identifier.
        """

        if dictionary.keys():
            # fetch all keys and sort them
            number = max(list(dictionary.keys()), key=lambda id: int(id[1::]))
            return prefix + str(number + 1)

        return prefix + str(0)

    def validate(self) -> None:
        # TODO rework validation
        raise NotImplementedError(
            "Function not implemented yet."
        )

    def __str__(self) -> str:
        """
        Magic function return pretty string describing the object.

        Returns:
            string: Beautified summarization of object
        """

        fin_string: list[str]

        def generate_lines(dictionary: dict) -> None:
            """Breaks up a dictionary and generates a human readible line."""
            for element_id, element in dictionary.items():
                fin_string.append(
                    f"\tID: {element_id} \t Name: {element.name}")

        fin_string = ['>>> Units']
        generate_lines(self.unit_dict)

        fin_string.append('>>> Reactants')
        generate_lines(self.reactant_dict)

        fin_string.append('>>> Proteins')
        generate_lines(self.protein_dict)

        fin_string.append('>>> Reactions')
        generate_lines(self.reaction_dict)

        fin_string.append('>>> Measurements')
        fin_string.append(self.printMeasurements())

        return "\n".join(fin_string)

    def printMeasurements(self) -> str:
        """Prints all measurements as a human readable table"""

        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.set_cols_align(["l", "l", "l", "l"])

        # Initialize rows
        rows = [["ID", "Species", "Conc", "Unit"]]

        # Generate and append rows
        for measurementID, measurement in self._MeasurementDict.items():

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

        return f"\n{table.draw()}\n"

    # ! Getter methods
    def getUnitDef(self, unit_id: str) -> UnitDef:
        """Return UnitDef

        Args:
            unitID (string): Unit identifier

        Returns:
            UnitDef: Unit definition object
        """

        if re.match(r"u[\d]+", unit_id):
            return self.unit_dict[unit_id]
        else:
            raise IdentifierNameError(id=unit_id, prefix="u")

    @deprecated_getter("doi")
    def getDoi(self) -> Optional[str]:
        return self.doi

    @deprecated_getter("pubmed_id")
    def getPubmedID(self) -> Optional[str]:
        return self.pubmed_id

    @deprecated_getter("url")
    def getUrl(self) -> Optional[str]:
        return self.url

    def printReactions(self):
        """
        Prints reactions found in the object
        """

        print('>>> Reactions')
        for key, item in self._ReactionDict.items():
            print('    ID: %s \t Name: %s' % (key, item.getName()))

    def printUnits(self):
        """
        Prints units found in the object
        """

        print('>>> Units')
        for key, item in self._UnitDict.items():
            print('    ID: %s \t Name: %s' % (key, item.getName()))

    def printReactants(self):
        """
        Prints reactants found in the object
        """

        print('>>> Reactants')
        for key, item in self._ReactantDict.items():
            print('    ID: %s \t Name: %s' % (key, item.getName()))

    def printProteins(self):
        """
        Prints proteins found in the object
        """

        print('>>> Proteins')
        for key, item in self._ProteinDict.items():
            print('    ID: %s \t Name: %s' % (key, item.getName()))

    def getUnitString(self, unitID):
        return self._UnitDict[unitID].getName()

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

        return self._getSpecies(
            id_=id_,
            dictionary=self._ReactionDict,
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

        return self._getSpecies(
            id_=id_,
            dictionary=self._MeasurementDict,
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

        return self._getSpecies(
            id_=id_,
            dictionary=self._ReactantDict,
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

        return self._getSpecies(
            id_=id_,
            dictionary=self._ProteinDict,
            elementType="Protein",
            by_id=by_id
        )

    def getFile(self, id_):
        """
        Returns file object by ID

        Args:
            id_ (string): Unique Identifier of file to retrieve.

        Raises:
            KeyError: If ID is unfindable

        Returns:
            Dict: Dictionary containining the filename and content of the file.
        """

        return self._getSpecies(
            id_=id_,
            dictionary=self._FileDict,
            elementType="File",
            by_id=True
        )

    def _getSpecies(self, id_, dictionary, elementType="", by_id=True) -> AbstractSpecies:

        if by_id:
            try:
                return dictionary[id_]
            except KeyError:
                raise KeyError(
                    f"{elementType} {id_} not found in the EnzymeML document {self._name}"
                )

        else:
            name = id_
            for element in dictionary:
                if element.getName() == name:
                    return element

            raise ValueError(
                f"{elementType} {name} not found in the EnzymeML document {self._name}"
            )

    def getReactantList(self) -> list[Reactant]:
        """Returns a list of all reactants in the EnzymeML document."

        Returns:
            list[Reactant]: List of all reactants in the EnzymeML document.
        """
        return self._getSpeciesList(self.reactant_dict)

    def getProteinList(self) -> list[Protein]:
        """Returns a list of all proteins in the EnzymeML document."

        Returns:
            list[Protein]: List of all proteins in the EnzymeML document.
        """
        return self._getSpeciesList(self.protein_dict)

    def getReactionList(self) -> list[EnzymeReaction]:
        """Returns a list of all reactions in the EnzymeML document."

        Returns:
            list[EnzymeReaction]: List of all reactions in the EnzymeML document.
        """
        return self._getSpeciesList(self.reaction_dict)

    def getFilesList(self):
        """Returns a list of all files in the EnzymeML document."

        Returns:
            list[dict]: List of all files in the EnzymeML document.
        """
        return self._getSpeciesList(self.file_dict)

    @ staticmethod
    def _getSpeciesList(dictionary: dict) -> list:
        """Helper function to retrieve lists of dicitonary objects

        Args:
            dictionary (dict): Dictionary of corresponding elements

        Returns:
            list<Objects>: Returns all values in the dictionary
        """
        return list(dictionary.values())

    # ! Add methods
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

        return self._addSpecies(
            species=reactant,
            prefix="s",
            dictionary=self._ReactantDict,
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

        return self._addSpecies(
            species=protein,
            prefix="p",
            dictionary=self._ProteinDict,
            use_parser=use_parser,
            custom_id=custom_id
        )

    def _addSpecies(
        self,
        species,
        prefix,
        dictionary,
        use_parser=True,
        custom_id=None
    ):

        # Generate ID
        speciesID = custom_id or self._generateID(
            prefix=prefix, dictionary=dictionary
        )

        species.setId(speciesID)

        # Update unit to UnitDefID
        if use_parser:
            try:
                speciesUnit = self._convertUnit(species.getSubstanceUnits())
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
        reactionID = self._generateID("r", self._ReactionDict)
        reaction.setId(reactionID)

        if use_parser:
            # Reset temperature for SBML compliance to Kelvin
            reaction.setTemperature(reaction.getTemperature() + 273.15)
            reaction.setTempunit(
                self._convertUnit(reaction.getTempunit())
            )

        # Set model units
        if hasattr(reaction, '_EnzymeReaction_model'):
            model = reaction.getModel()

        # Finally add the reaction to the document
        self._ReactionDict[reactionID] = reaction

        return reactionID

    def addFile(self, filepath=None, fileHandle=None, description="Undefined"):
        """Adds any arbitrary file to the document. Please note, that if a filepath is given, any fileHandle will be ignored.

        Args:
            filepath (String, optional): Path to the file that is added to the document. Defaults to None.
            fileHandle (io.BufferedReader, optional): File handle that will be read to a bytes string. Defaults to None.

        Returns:
            String: Internal identifier for the file.
        """

        fileID = self._generateID("f", self._FileDict)

        if filepath:
            # Open file handle
            TypeChecker(filepath, str)
            fileHandle = open(filepath, "rb")
        elif filepath is None and fileHandle is None:
            raise ValueError(
                "Please specify either a file path or a file handle"
            )

        # Finally, add the file and close the handler
        self._FileDict[fileID] = {
            "name": os.path.basename(fileHandle.name),
            "content": fileHandle.read(),
            "description": description
        }

        fileHandle.close()

        return fileID

    def addMeasurement(self, measurement: Measurement) -> str:
        """Adds a measurement to an EnzymeMLDocument and validates consistency with already defined elements of the documentself.

        Args:
            measurement (Measurement): Collection of data and initial concentrations per reaction

        Returns:
            measurement_id (String): Assigned measurement identifier.
        """

        # Check consistency
        self._checkMeasurementConsistency(measurement)

        # Convert all measurement units to UnitDefs
        self._convertMeasurementUnits(measurement)

        # Finally generate the ID and add it to the dictionary
        measurement_id = self._generateID(
            prefix="m", dictionary=self.measurement_dict
        )
        measurement.id = measurement_id

        self.measurement_dict[measurement_id] = measurement

        return measurement_id

    def _convertMeasurementUnits(self, measurement: Measurement) -> None:
        """Converts string SI units to UnitDef objects and IDs

        Args:
            measurement (Measurement): Object defining a measurement
        """
        species_dict = measurement.species_dict
        measurement.global_time_unit = self._convertToUnitDef(
            measurement.global_time_unit
        )

        def update_unit(measurement_data: MeasurementData) -> None:
            """Helper function to update units"""
            unit = measurement_data.unit
            measurement_data.unit = self._convertToUnitDef(unit)
            self._convertReplicateUnits(measurement_data)

        # Perform update
        map(update_unit, species_dict["proteins"].values())
        map(update_unit, species_dict["reactants"].values())

    def _convertReplicateUnits(self, measurement_data: MeasurementData) -> None:
        """Converts replicate unit strings to unit definitions.

        Args:
            measurement_data (MeasurementData): Object holding measurement data for a species
        """
        for replicate in measurement_data.replicates:

            # Convert unit
            time_unit = self._convertToUnitDef(replicate.time_unit)
            data_unit = self._convertToUnitDef(replicate.data_unit)

            # Assign unit IDs
            replicate.data_unit = data_unit
            replicate.time_unit = time_unit

    def _checkMeasurementConsistency(self, measurement: Measurement) -> None:
        """Checks if the used species in the measurement are consistent with the EnzymeML document.

        Args:
            measurement (MeasurementData): Objech holding measurement data for a species.
        """

        map(self._checkSpecies, measurement.species_dict["reactants"])
        map(self._checkSpecies, measurement.species_dict["proteins"])

    def _checkSpecies(self, species_id):
        """Checks if a species is defined in the EnzymeML document.

        Args:
            species_id (str): Unique identifier of the species.

        Raises:
            SpeciesNotFoundError: Raised when a species is not defined in the EnzymeML document.
        """

        all_species = {**self.reactant_dict, **self.protein_dict}

        if species_id not in all_species.keys():

            # Retrieve species for ontology
            species = self._getSpecies(
                id_=species_id,
                dictionary=all_species
            )

            # Use the EnzymeMLPart Enum to derive the correct place
            sbo_term = SBOTerm(species.ontology).name
            enzymeml_part = EnzymeMLPart.fromSBOTerm(sbo_term)

            # Raise an error if the species is nowhere present
            raise SpeciesNotFoundError(
                species_id=species_id,
                enzymeml_part=enzymeml_part
            )

    def uploadToDataverse(
        self,
        baseURL,
        API_Token,
        dataverseName
    ):
        """Uploads an EnzymeML document to a Dataverse installation of choice.

        Args:
            baseURL (String): URL to a Dataverse installation
            API_Token (String): API Token given from your Dataverse installation for authentication.
            dataverseName (String): Name of the dataverse to upload the EnzymeML document. You can find the name in the link of your dataverse (e.g. https://dataverse.installation/dataverse/{dataverseName})

        Raises:
            AttributeError: Raised when neither a filename nor an EnzymeMLDocument object was provided.
            ValidationError: Raised when the validation fails.
        """
        uploadToDataverse(
            baseURL=baseURL,
            API_Token=API_Token,
            dataverseName=dataverseName,
            enzmldoc=self
        )

    def _convertToUnitDef(self, unit: Optional[str]) -> str:
        """Reads an SI unit string and converts it into a EnzymeML compatible UnitDef

        Args:
            unit (str): String representing the SI unit.

        Returns:
            str: Unique identifier of the UnitDef.
        """
        if unit is None:
            raise TypeError("No unit given.")
        elif unit in self._UnitDict.keys():
            return unit

        return UnitCreator().getUnit(unit, self)

    def get_created(self):
        """
        Returns date of creation

        Returns:
            string: Date of creation
        """

        return self._created

    def getModified(self):
        """
        Returns date of recent modification

        Returns:
            string: Date of recent modification
        """

        return self._modified

    def setCreated(self, date):
        """
        Sets date of creation

        Args:
            date (string): Date of creation
        """

        self._created = TypeChecker(date, str)

    def setModified(self, date):
        """
        Sets date of recent modification

        Args:
            date (string): Date of recent modification
        """

        self._modified = TypeChecker(date, str)

    def delCreated(self):
        del self._created

    def delModified(self):
        del self._modified

    def getCreator(self):
        return self._creator

    def setCreator(self, creators):
        """
        Sets creator information. Multiples are also allowed
        as a list of Creator classes

        Args:
            creators (string, list<string>): Single or multiple author classes
        """

        # Set hasCreatorFlag for Dataverse check
        self._hasCreator = True

        if type(creators) == list:
            self._creator = [
                TypeChecker(creator, Creator)
                for creator in creators
            ]
        else:
            self._creator = [TypeChecker(creators, Creator)]

    def delCreator(self):
        del self._creator
        self._hasCreator = False

    def hasCreator(self):
        return self._hasCreator

    def getVessel(self):
        return self._vessel

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

        self._vessel = TypeChecker(vessel, Vessel)

        return vessel.getId()

    def delVessel(self):
        del self._vessel

    def getName(self):
        """
        Returns name of EnzymeML document

        Returns:
            string: Name of document
        """

        return self._name

    def getLevel(self):
        return self._level

    def getVersion(self):
        return self._version

    def getProteinDict(self):
        """
        Return protein dictionary for manual access

        Returns:
            dict: Dictionary containing Protein objects describing proteins
        """

        return self._ProteinDict

    def getReactantDict(self):
        """
        Return reactant dictionary for manual access

        Returns:
            dict: Dictionary containing Reactant objects describing reactants
        """

        return self._ReactantDict

    def getReactionDict(self):
        """
        Return reaction dictionary for manual access

        Returns:
            dict: Dictionary containing EnzymeReaction
                  objects describing reactions
        """

        return self._ReactionDict

    def getMeasurementDict(self):
        """
        Return reaction dictionary for manual access

        Returns:
            dict: Dictionary containing EnzymeReaction
                  objects describing reactions
        """

        return self._MeasurementDict

    def getUnitDict(self):
        """
        Return unit dictionary for manual access

        Returns:
            dict: Dictionary containing UnitDef objects describing units
        """

        return self._UnitDict

    def getFileDict(self):
        """
        Return file dictionary for manual access

        Returns:
            dict: Dictionary containing File objects describing units
        """

        return self._FileDict

    def setName(self, value):
        """
        Sets name of the EnzymeML document

        Args:
            value (string): Name of the document
        """

        self._name = value

    def setLevel(self, level):
        """
        Sets SBML level of document

        Args:
            level (int): SBML level

        Raises:
            IndexError: If SBML level not in [1,3]
        """

        if 1 <= TypeChecker(level, int) <= 3:
            self._level = level
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

        self._version = TypeChecker(version, int)

    def setProteinDict(self, proteinDict):
        self._ProteinDict = TypeChecker(proteinDict, dict)

    def setReactantDict(self, reactantDict):
        self._ReactantDict = TypeChecker(reactantDict, dict)

    def setMeasurementDict(self, measurementDict):
        self._MeasurementDict = TypeChecker(measurementDict, dict)

    def setReactionDict(self, reactionDict):
        self._ReactionDict = TypeChecker(reactionDict, dict)

    def setUnitDict(self, unitDict):
        self._UnitDict = TypeChecker(unitDict, dict)

    def setFileDict(self, fileDict):
        self._FileDict = TypeChecker(fileDict, dict)

    def delName(self):
        del self._name

    def delLevel(self):
        del self._level

    def delVersion(self):
        del self._version

    def delProteinDict(self):
        del self._ProteinDict

    def delReactantDict(self):
        del self._ReactantDict

    def delReactionDict(self):
        del self._ReactionDict

    def delMeasurementDict(self):
        del self._MeasurementDict

    def delUnitDict(self):
        del self._UnitDict
