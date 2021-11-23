'''
File: enzymemlreader.py
Project: tools
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 7:18:49 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

import os
import re
from typing import Union, Optional
import libsbml
import xml.etree.ElementTree as ET
import pandas as pd

from pyenzyme.enzymeml.core.creator import Creator
from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.measurement import Measurement
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction, ReactionElement
from pyenzyme.enzymeml.models.kineticmodel import KineticModel, KineticParameter
from pyenzyme.enzymeml.core.ontology import EnzymeMLPart, SBOTerm
from pyenzyme.enzymeml.core.abstract_classes import AbstractSpeciesFactory, AbstractSpecies

from libsbml import SBMLReader
from enum import Enum
from libcombine import CombineArchive
from io import StringIO, BytesIO

# ! Factories


class ReactantFactory(AbstractSpeciesFactory):
    """Returns an un-initialized reactant species object"""

    enzymeml_part: str = "reactant_dict"

    def get_species(self, **kwargs) -> AbstractSpecies:
        return Reactant(**kwargs)


class ProteinFactory(AbstractSpeciesFactory):
    """Returns an un-initialized reactant species object"""

    enzymeml_part: str = "protein_dict"

    def get_species(self, **kwargs) -> AbstractSpecies:
        return Protein(**kwargs)


def species_factory_mapping(sbo_term: str) -> AbstractSpeciesFactory:
    """Maps from SBOTerms to the appropriate species using a factory"""

    # Get the enum entity for the mapping
    entity = EnzymeMLPart.entityFromSBOTerm(sbo_term)

    factory_mapping = {
        "PROTEIN": ProteinFactory(),
        "SMALL_MOLECULE": ReactantFactory(),
        "ION": ReactantFactory(),
        "RADICAL": ReactantFactory()
    }

    return factory_mapping[entity]


class EnzymeMLReader():

    def readFromFile(
        self,
        path: str
    ) -> EnzymeMLDocument:
        '''
        Reads EnzymeML document to an object layer EnzymeMLDocument class.

        Args:
            String path: Path to .omex container or
                         folder destination for plain .xml
        '''

        # Read omex archive
        self.path = path
        self.archive = CombineArchive()
        self.archive.initializeFromArchive(self.path)

        sbmlfile = self.archive.getEntry(0)
        content = self.archive.extractEntryToString(sbmlfile.getLocation())
        desc = self.archive.getMetadataForLocation(sbmlfile.getLocation())

        # Read experiment file (sbml)
        reader = SBMLReader()
        document = reader.readSBMLFromString(content)
        document.getErrorLog().printErrors()
        model = document.getModel()

        # Initialize EnzymeMLDocument object
        enzmldoc = EnzymeMLDocument(
            name=model.getName(),
            level=model.getLevel(),
            version=model.getVersion()
        )

        # Fetch references
        self._getRefs(model, enzmldoc)

        # Fetch Creators
        self._getCreators(omex_desc=desc, enzmldoc=enzmldoc)

        # try:
        #     # TODO extract VCard
        #     model_hist = model.getModelHistory()
        #     enzmldoc.setCreated(
        #         model_hist.getCreatedDate().getDateAsString()
        #     )

        #     enzmldoc.setModified(
        #         model_hist.getModifiedDate().getDateAsString()
        #     )

        # Fetch units
        unitDict = self._getUnits(model)
        enzmldoc.unit_dict = unitDict

        # Fetch Vessel
        vessel = self._getVessel(model, enzmldoc)
        enzmldoc.vessel_dict = vessel

        # Fetch Species
        protein_dict, reactant_dict = self._getSpecies(model, enzmldoc)
        enzmldoc.reactant_dict = reactant_dict
        enzmldoc.protein_dict = protein_dict

        # fetch reaction
        reaction_dict = self._getReactions(model, enzmldoc)
        enzmldoc.setReactionDict(reaction_dict)

        # fetch Measurements
        measurementDict = self._getData(model)
        enzmldoc.setMeasurementDict(measurementDict)

        # fetch added files
        self._getFiles(enzmldoc)

        del self.path

        return enzmldoc

    @staticmethod
    def _sboterm_to_enum(sbo_term: int) -> Optional[Enum]:
        try:
            return SBOTerm(
                libsbml.SBO_intToString(sbo_term)
            )
        except ValueError:
            return None

    def _getRefs(self, model, enzmldoc):

        if len(model.getAnnotationString()) == 0:
            return

        root = ET.fromstring(model.getAnnotationString())[0]

        for element in root:
            if "doi" in element.tag:
                enzmldoc.doi = element.text
            elif 'pubmedID' in element.tag:
                enzmldoc.pubmed_id = element.text
            elif 'url' in element.tag:
                enzmldoc.setUrl(element.text)

    def _getCreators(self, omex_desc, enzmldoc) -> None:
        """Fetches all creators from an Combine archive's metadata.

        Args:
            omex_desc (OMEX obj): Combine metadata description.

        Returns:
            list[Creator]: Fetched list of creator objects.
        """

        # Get the number of creators to iterate
        numCreators = omex_desc.getNumCreators()

        for i in range(numCreators):
            # Fetch creator information
            creator = omex_desc.getCreator(i)

            enzmldoc.addCreator(
                Creator(
                    family_name=creator.getFamilyName(),
                    given_name=creator.getGivenName(),
                    mail=creator.getEmail()
                )
            )

    def _getUnits(self, model: libsbml.Model) -> dict[str, UnitDef]:
        """Fetches all the units present in the SBML model.^

        Args:
            model (libsbml.Model): The SBML model from which the units are fetched.

        Returns:
            [type]: [description]
        """

        unitDict = {}
        unitdef_list = model.getListOfUnitDefinitions()

        for unit in unitdef_list:

            # Get infos from the SBML model
            name = unit.getName()
            id_ = unit.getId()
            metaid = unit.getMetaId()
            ontology = "NONE"  # TODO get unit ontology

            # Create unit definition
            unitdef = UnitDef(
                name=name,
                id=id_,
                ontology=ontology,
                meta_id=metaid
            )

            for baseunit in unit.getListOfUnits():
                # Construct unit definition with base units
                unitdef.addBaseUnit(
                    kind=baseunit.toXMLNode().getAttrValue('kind'),
                    exponent=baseunit.getExponentAsDouble(),
                    scale=baseunit.getScale(),
                    multiplier=baseunit.getMultiplier()
                )

            # Finally add the unit definition
            unitDict[id_] = unitdef

        return unitDict

    def _getVessel(self, model: libsbml.Model, enzmldoc: 'EnzymeMLDocument') -> dict[str, Vessel]:
        """Fetches all the vessels/compartments present in the SBML model.

        Args:
            model (libsbml.Model): The SBML model from which the vessels are fetched.

        Returns:
            dict[str, Vessel]: Corresponding vessel dictionary that has been converted.
        """

        vessel_dict = {}
        compartments = model.getListOfCompartments()

        for compartment in compartments:
            name = compartment.getName()
            id = compartment.getId()
            volume = compartment.getSize()
            unit_id = compartment.getUnits()

            vessel = Vessel(
                name=name,
                id=id,
                volume=volume,
                unit=enzmldoc.getUnitString(unit_id),
                _unit_id=unit_id
            )

            vessel_dict[vessel.id] = vessel

        return vessel_dict

    def _getSpecies(
        self,
        model: libsbml.Model,
        enzmldoc: 'EnzymeMLDocument'
    ) -> tuple[dict[str, Protein], dict[str, Reactant]]:

        # initialize dictionaries and get species
        protein_dict = {}
        reactant_dict = {}
        species_list = model.getListOfSpecies()

        for species in species_list:

            # Parse annotations and construct a kwargs dictionary
            param_dict = self._parseSpeciesAnnotation(
                species.getAnnotationString())
            param_dict.update(
                {
                    "id": species.getId(),
                    "meta_id": species.getMetaId(),
                    "vessel_id": species.getCompartment(),
                    "name": species.getName(),
                    "init_conc": species.getInitialConcentration(),
                    "_unit_id": species.getSubstanceUnits(),
                    "unit": enzmldoc.getUnitString(species.getSubstanceUnits()),
                    "constant": species.getConstant(),
                    "ontology": self._sboterm_to_enum(species.getSBOTerm())
                }
            )

            # Get scpecies factory from ontology
            species_factory = species_factory_mapping(param_dict["ontology"])
            species = species_factory.get_species(**param_dict)

            if species_factory.enzymeml_part == 'protein_dict':
                protein_dict[species.id] = species
            elif species_factory.enzymeml_part == 'reactant_dict':
                reactant_dict[species.id] = species

        return protein_dict, reactant_dict

    @staticmethod
    def _parseSpeciesAnnotation(annotationString):

        if len(annotationString) == 0:
            return dict()

        def camel_to_snake(name):
            name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

        speciesAnnot = ET.fromstring(
            annotationString
        )[0]

        # Initialize annotation dictionary
        param_dict = {}

        for enzymeMLAnnot in speciesAnnot:
            key = enzymeMLAnnot.tag.split('}')[-1].lower()
            key = camel_to_snake(key)

            attribute = enzymeMLAnnot.text

            param_dict[key] = attribute

        return param_dict

    def _getReactions(self, model: libsbml.Model, enzmldoc: 'EnzymeMLDocument') -> dict[str, EnzymeReaction]:

        # Get SBML list of reactions
        reactionsList = model.getListOfReactions()

        # Initialize reaction dictionary
        reaction_dict = {}

        # parse annotations and filter replicates
        for reaction in reactionsList:

            # Fetch conditions
            reactionAnnot = ET.fromstring(reaction.getAnnotationString())[0]
            conditions = self._parseConditions(reactionAnnot, enzmldoc)

            # Fetch Elements in SpeciesReference
            educts = self._getElements(
                reaction.getListOfReactants(),
            )

            products = self._getElements(
                reaction.getListOfProducts(),
            )

            modifiers = self._getElements(
                reaction.getListOfModifiers(),
                modifiers=True
            )

            # Create object
            enzyme_reaction = EnzymeReaction(
                id=reaction.getId(),
                meta_id='META_' + reaction.getId().upper(),
                name=reaction.getName(),
                reversible=reaction.getReversible(),
                educts=educts,
                products=products,
                modifiers=modifiers,
                ontology=self._sboterm_to_enum(reaction.getSBOTerm()),
                ** conditions
            )

            # Check for kinetic model
            if reaction.hasKineticLaw():
                # Check if model exists
                kinetic_law = reaction.getKineticLaw()
                kinetic_model = self._getKineticModel(kinetic_law, enzmldoc)
                enzyme_reaction.model = kinetic_model

            # Add reaction to reaction_dict
            reaction_dict[enzyme_reaction.id] = enzyme_reaction

        return reaction_dict

    @staticmethod
    def _parseConditions(
        reactionAnnot: ET.Element,
        enzmldoc: 'EnzymeMLDocument'
    ) -> dict[str, Union[str, float]]:
        """Exracts the conditions present in the SBML reaction annotations.

        Args:
            reactionAnnot (ET.Element): The reaction annotation element.
            enzmldoc (EnzymeMLDocument): The EnzymeMLDocument against which the data will be validated.

        Returns:
            dict[str, Union[str, float]]: Mapping for the conditions.
        """

        # Get the conditions element
        conditions = reactionAnnot[0]
        condition_dict = {}

        for condition in conditions:
            # Sort all the conditions
            if 'temperature' in condition.tag:

                # Get temperature conditions
                condition_dict['temperature'] = float(
                    condition.attrib['value']
                )

                # Parse unit ID to Unit string
                condition_dict['_temperature_unit_id'] = condition.attrib['unit']
                condition_dict['temperature_unit'] = enzmldoc.getUnitString(
                    condition_dict['temperature_unit_id']
                )

            elif 'ph' in condition.tag:

                # Get the pH value
                condition_dict['ph'] = float(condition.attrib['value'])

        return condition_dict

    def _getElements(
        self,
        species_refs: list[libsbml.SpeciesReference],
        modifiers: bool = False
    ) -> list[ReactionElement]:
        """Extracts the speciesReference objects from the associated list and converts them to ReactionElements

        Args:
            species_refs (list[libsbml.SpeciesReference]): The species refrences for the reaction <-> Chemical reaction elements.
            modifiers (bool, optional): Used to override missing stoichiometry and constant for modifiers. Defaults to False.

        Returns:
            list[ReactionElement]: The list of reaction elements.
        """

        reaction_elements = []
        for species_ref in species_refs:

            species_id = species_ref.getSpecies()
            stoichiometry = 1.0 if modifiers else species_ref.getStoichiometry()
            constant = True if modifiers else species_ref.getConstant()
            ontology = SBOTerm(
                libsbml.SBO_intToString(species_ref.getSBOTerm())
            )

            reaction_elements.append(
                ReactionElement(
                    species_id=species_id,
                    stoichiometry=stoichiometry,
                    constant=constant,
                    ontology=ontology
                )
            )

        return reaction_elements

    def _getKineticModel(
        self,
        kineticLaw: libsbml.KineticLaw,
        enzmldoc: 'EnzymeMLDocument'
    ) -> KineticModel:
        """Extracts a kinetic rate law from the SBML data model.

        Args:
            kineticLaw (libsbml.KineticLaw): The kinetic law to be extracted.
            enzmldoc (EnzymeMLDocument): The EnzymeMLDocument to which the kinetic law will be added.

        Returns:
            KineticModel: Teh resulting kinetic model.
        """

        # Extract metadata
        name = kineticLaw.getName()
        equation = kineticLaw.getFormula()
        ontology = SBOTerm(
            libsbml.SBO_intToString(kineticLaw.getSBOTerm())
        )

        # Get parameters
        parameters = [
            KineticParameter(
                name=localParam.getId(),
                value=localParam.getValue(),
                _unit_id=localParam.getUnits(),
                unit=enzmldoc.getUnitString(localParam.getUnits()),
                ontology=self._sboterm_to_enum(localParam.getSBOTerm())
            )
            for localParam in kineticLaw.getListOfLocalParameters()
        ]

        return KineticModel(
            name=name,
            equation=equation,
            parameters=parameters,
            ontology=ontology
        )

    @staticmethod
    def _parseListOfFiles(dataAnnot):
        # _getReplicates helper function
        # reads file anntations to dict
        fileAnnot = dataAnnot[1]
        return {
            file.attrib['id']:
            {
                'file': file.attrib['file'],
                'format': file.attrib['format'],
                'id': file.attrib['id']

            } for file in fileAnnot
        }

    @ staticmethod
    def _parseListOfFormats(dataAnnot):
        # _getReplicates helper function
        # reads format anntations to dict
        formatAnnot = dataAnnot[0]
        formats = {}

        for format in formatAnnot:
            formatID = format.attrib['id']
            format = [
                column.attrib
                for column in format
            ]

            formats[formatID] = format

        return formats

    def _parseListOfMeasurements(self, dataAnnot):
        # _getReplicates helper function
        # reads measurement anntations to
        # tuple list
        listOfMeasurements = dataAnnot[2]
        measurementFiles = {
            measurement.attrib['id']:
            measurement.attrib['file']
            for measurement in listOfMeasurements
        }
        measurementDict = {
            measurement.attrib['id']:
            self._parseMeasurement(measurement)
            for measurement in listOfMeasurements
        }

        return measurementDict, measurementFiles

    @ staticmethod
    def _parseMeasurement(measurement):
        """Extracts individual initial concentrations of a measurement.

        Args:
            measurement (XMLNode): Measurement XML information
        """

        # initialize Measurement object
        measurementObject = Measurement(
            name=measurement.attrib['name']
        )

        measurementObject.setId(
            measurement.attrib['id']
        )

        for initConc in measurement:
            value = float(initConc.attrib['value'])
            unit = initConc.attrib['unit']

            reactantID = None
            proteinID = None

            if 'reactant' in initConc.attrib.keys():
                reactantID = initConc.attrib['reactant']
            elif 'protein' in initConc.attrib.keys():
                proteinID = initConc.attrib['protein']
            else:
                raise KeyError(
                    "Neither reactant or protein ID defined."
                )

            measurementObject.addData(
                initConc=float(value),
                unit=unit,
                reactantID=reactantID,
                proteinID=proteinID,
            )

        return measurementObject

    def _getData(self, model):

        # Parse EnzymeML:format annotation
        reactions = model.getListOfReactions()
        dataAnnot = ET.fromstring(reactions.getAnnotationString())[0]

        # Fetch list of files
        files = self._parseListOfFiles(dataAnnot)

        # Fetch formats
        formats = self._parseListOfFormats(dataAnnot)

        # Fetch measurements
        measurementDict, measurementFiles = self._parseListOfMeasurements(
            dataAnnot
        )

        # Initialize replicates dictionary
        replicates = {}

        # Iterate over measurements and assign replicates
        for measurementID, measurementFile in measurementFiles.items():

            # Get file content
            fileInfo = files[measurementFile]
            fileContent = self.archive.extractEntryToString(fileInfo['file'])
            csvFile = pd.read_csv(
                StringIO(fileContent),
                header=None
            )

            # Get format data and extract time column
            measurementFormat = formats[fileInfo['format']]
            timeValues, timeUnitID = [
                (
                    csvFile.iloc[:, int(column['index'])],
                    column['unit']
                )
                for column in measurementFormat
                if column['type'] == 'time'
            ][0]

            # Create replicate objects
            for format in measurementFormat:

                if format['type'] != 'time':

                    # Get time course data
                    replicateValues = csvFile.iloc[:, int(format['index'])]
                    replicateReactant = format['species']
                    replicateID = format['replica']
                    replicateType = format['type']
                    replicateUnitID = format['unit']

                    replicate = Replicate(
                        replica=replicateID,
                        reactant=replicateReactant,
                        type_=replicateType,
                        measurement=measurementID,
                        data_unit=replicateUnitID,
                        time_unit=timeUnitID,
                        data=replicateValues.values.tolist(),
                        time=timeValues
                    )

                    measurementDict[measurementID].addReplicates(
                        replicate
                    )

        return measurementDict

    def _getFiles(self, enzmldoc):
        """Extracts all added files fro the archive.

        Args:
            archive (CombineArchive): The OMEX archive to extract files from.
            enzmldoc (EnzymeMLDocument): The EnzymeMLDocument to add files to.
        """

        # Iterate over enries and extract files
        for fileLocation in self.archive.getAllLocations():
            fileLocation = str(fileLocation)
            if "./files/" in fileLocation:

                # Convert raw file to fileHandle
                fileHandle = BytesIO(
                    str.encode(self.archive.extractEntryToString(fileLocation))
                )

                # Set name of file to the one that is given within the EnzymeMLDocument
                fileHandle.name = os.path.basename(fileLocation)

                # Add the file to the EnzymeMLDocument
                enzmldoc.addFile(fileHandle=fileHandle)
