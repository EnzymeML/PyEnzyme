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
from pyenzyme.enzymeml.core.complex import Complex
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.measurement import Measurement
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction, ReactionElement
from pyenzyme.enzymeml.models.kineticmodel import KineticModel, KineticParameter
from pyenzyme.enzymeml.core.ontology import DataTypes, EnzymeMLPart, SBOTerm
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
    """Returns an un-initialized protein species object"""

    enzymeml_part: str = "protein_dict"

    def get_species(self, **kwargs) -> AbstractSpecies:
        return Protein(**kwargs)


class ComplexFactory(AbstractSpeciesFactory):
    """Returns an un-initialized complex species object"""

    enzymeml_part: str = "complex_dict"

    def get_species(self, **kwargs) -> AbstractSpecies:
        return Complex(**kwargs)


def species_factory_mapping(sbo_term: str) -> AbstractSpeciesFactory:
    """Maps from SBOTerms to the appropriate species using a factory"""

    # Get the enum entity for the mapping
    entity = EnzymeMLPart.entityFromSBOTerm(sbo_term)

    factory_mapping = {
        "PROTEIN": ProteinFactory(),
        "SMALL_MOLECULE": ReactantFactory(),
        "ION": ReactantFactory(),
        "RADICAL": ReactantFactory(),
        "MACROMOLECULAR_COMPLEX": ComplexFactory(),
        "PROTEIN_COMPLEX": ComplexFactory(),
        "DIMER": ComplexFactory()
    }

    return factory_mapping[entity]


class EnzymeMLReader:

    def readFromFile(
        self,
        path: str
    ) -> EnzymeMLDocument:
        '''
        Reads EnzymeML document to an object layer EnzymeMLDocument class.

        Args:
            path (str): Path to .omex container or
                         folder destination for plain .xml
        '''

        # Read omex archive
        self.path = path
        self.archive = CombineArchive()
        self.archive.initializeFromArchive(self.path)

        content = self.archive.extractEntryToString("./experiment.xml")
        desc = self.archive.getMetadataForLocation("./experiment.xml")

        # Get previous logs
        log = self.archive.extractEntryToString("./history.log")

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

        # Add logs to the document
        enzmldoc.log = log

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
        enzmldoc.reaction_dict = reaction_dict

        # fetch Measurements
        measurement_dict = self._getData(model, enzmldoc)
        enzmldoc.measurement_dict = measurement_dict

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
                enzmldoc.pubmedid = element.text
            elif 'url' in element.tag:
                enzmldoc.url = element.text

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
            name = unit.name
            id = unit.id
            meta_id = unit.meta_id
            ontology = "NONE"  # TODO get unit ontology

            # Create unit definition
            unitdef = UnitDef(
                name=name,
                id=id,
                ontology=ontology,
                meta_id=meta_id
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
            unitDict[id] = unitdef

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
            )

            vessel._unit_id = unit_id

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

            # Check if init conc is given
            init_conc = species.getInitialConcentration()
            unit_id = species.getSubstanceUnits()

            if repr(species.getInitialConcentration()) == "nan":
                init_conc, unit_id, unit = None, None, None
            else:
                unit = enzmldoc.getUnitString(unit_id)

            # Get SBOTerm, but if there is none, give default
            try:
                ontology = self._sboterm_to_enum(species.getSBOTerm())
            except ValueError:
                ontology = None

            # Parse annotations and construct a kwargs dictionary
            param_dict = self._parseSpeciesAnnotation(
                species.getAnnotationString())
            param_dict.update(
                {
                    "id": species.getId(),
                    "meta_id": species.getMetaId(),
                    "vessel_id": species.getCompartment(),
                    "name": species.getName(),
                    "constant": species.getConstant(),
                    "ontology": ontology,
                    "init_conc": init_conc,
                    "_unit_id": unit_id,
                    "unit": unit
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
                reaction.getListOfReactants(), ontology=SBOTerm.SUBSTRATE
            )

            products = self._getElements(
                reaction.getListOfProducts(), ontology=SBOTerm.PRODUCT
            )

            modifiers = self._getElements(
                reaction.getListOfModifiers(),
                modifiers=True, ontology=SBOTerm.CATALYST
            )

            # Create object
            enzyme_reaction = EnzymeReaction(
                id=reaction.id,
                meta_id='META_' + reaction.id.upper(),
                name=reaction.name,
                reversible=reaction.reversible,
                educts=educts,
                products=products,
                modifiers=modifiers,
                ontology=self._sboterm_to_enum(reaction.getSBOTerm()),
                **conditions
            )

            # Check for kinetic model
            if reaction.getKineticLaw():
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
                    condition_dict['_temperature_unit_id']
                )

            elif 'ph' in condition.tag:

                # Get the pH value
                condition_dict['ph'] = float(condition.attrib['value'])

        return condition_dict

    def _getElements(
        self,
        species_refs: list[libsbml.SpeciesReference],
        ontology: SBOTerm,
        modifiers: bool = False,
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
            sbo_term = libsbml.SBO_intToString(species_ref.getSBOTerm())

            if sbo_term:
                ontology = SBOTerm(sbo_term)

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

    def _getData(self, model: libsbml.Model, enzmldoc: 'EnzymeMLDocument') -> dict[str, Measurement]:
        """Retrieves all available measurements found in the EnzymeML document.

        Args:
            model (libsbml.Model): The SBML model from which the measurements are feteched,

        Returns:
            dict[str, Measurement]: Mapping from measurement ID to the associated object.
        """

        # Parse EnzymeML:format annotation
        reactions = model.getListOfReactions()
        data_annotation = ET.fromstring(reactions.getAnnotationString())[0]

        # Fetch list of files
        files = self._parseListOfFiles(data_annotation)

        # Fetch formats
        formats = self._parseListOfFormats(data_annotation)

        # Fetch measurements
        measurement_dict, measurement_files = self._parseListOfMeasurements(
            data_annotation, enzmldoc=enzmldoc
        )

        # Iterate over measurements and assign replicates
        for measurement_id, measurement_file in measurement_files.items():

            # Get file content
            fileInfo = files[measurement_file]
            file_content = self.archive.extractEntryToString(fileInfo['file'])
            csvFile = pd.read_csv(
                StringIO(file_content)
            )

            # Get format data and extract time column
            measurement_format = formats[fileInfo['format']]
            time, time_unit_id = [
                (
                    csvFile.iloc[:, int(column['index'])].tolist(),
                    column['unit']
                )
                for column in measurement_format
                if column['type'] == 'time'
            ][0]

            measurement_dict[measurement_id]._global_time_unit_id = time_unit_id

            # Create replicate objects
            for format in measurement_format:

                if format['type'] != 'time':

                    # Get time course data
                    data = csvFile.iloc[:, int(format['index'])].tolist()
                    reactant_id = format['species']
                    replicate_id = format['replica']
                    data_type = DataTypes(format['type'])
                    data_unit_id = format['unit']
                    is_calculated = format['isCalculated']

                    replicate = Replicate(
                        id=replicate_id,
                        species_id=reactant_id,
                        data_type=data_type,
                        measurement_id=measurement_id,
                        data_unit=enzmldoc.unit_dict[data_unit_id].name,
                        time_unit=enzmldoc.unit_dict[time_unit_id].name,
                        data=data,
                        time=time,
                        is_calculated=is_calculated
                    )

                    replicate._data_unit_id = data_unit_id
                    replicate._time_unit_id = time_unit_id

                    measurement_dict[measurement_id].addReplicates(
                        replicate, log=False, enzmldoc=enzmldoc
                    )

        return measurement_dict

    @ staticmethod
    def _parseListOfFiles(data_annotation: ET.Element) -> dict[str, dict[str, str]]:
        """Extracts the list of files that are present in the annotation enzymeml:files.

        Args:
            data_annotation (ET.Element): ElementTree object containing the enzymeml:files annotation.

        Returns:
            dict[str, dict[str, str]]: Dictionary of all files present in the annotation.
        """

        return {
            file.attrib['id']:
            {
                'file': file.attrib['file'],
                'format': file.attrib['format'],
                'id': file.attrib['id']

            } for file in data_annotation[1]
        }

    @ staticmethod
    def _parseListOfFormats(data_annotation: ET.Element) -> dict[str, list[dict]]:
        """Extracts the list of formats that areb present in the annotation enzymeml:formats.

        Args:
            data_annotation (ET.Element): ElementTree object containing the enzymeml:files annotation.

        Returns:
            dict[str, list[dict]]: Dictionary of all the formats present in the annotation.
        """

        return {
            format.attrib['id']: [
                column.attrib
                for column in format
            ]
            for format in data_annotation[0]
        }

    def _parseListOfMeasurements(self, data_annotation: ET.Element, enzmldoc: 'EnzymeMLDocument') -> tuple[dict[str, Measurement], dict]:
        """Extracts teh list of measurements that are present in the annotation enzymeml:measurements.

        Args:
            data_annotation (ET.Element): ElementTree object containing the enzymeml:measurements annotation.

        Returns:
            tuple[dict[str, dict], dict[str, Measurement]]: Two dictionaries returning the measurement objects and files.
        """

        measurements = data_annotation[2]
        measurement_files = {
            measurement.attrib['id']:
            measurement.attrib['file']
            for measurement in measurements
        }
        measurement_dict = {
            measurement.attrib['id']:
            self._parseMeasurement(measurement, enzmldoc=enzmldoc)
            for measurement in measurements
        }

        return (measurement_dict, measurement_files)

    def _parseMeasurement(self, measurement: ET.Element, enzmldoc: 'EnzymeMLDocument') -> Measurement:
        """Extracts individual initial concentrations of a measurement.

        Args:
            measurement (ET.Element): Measurement XML information

        Returns:
            Measurement: Initialized measurement object.
        """

        # Get conditions (temp, ph)
        temperature = measurement.attrib.get('temperature_value')
        temperature_unit = measurement.attrib.get('temperature_unit')
        ph = measurement.attrib.get('ph')

        # Get the unit string of temp if given
        if temperature_unit:
            temperature_unit = enzmldoc.getUnitString(temperature_unit)

        # initialize Measurement object
        measurement_object = Measurement(
            name=measurement.attrib['name'],
            temperature=temperature,
            temperature_unit=temperature_unit,
            ph=ph
        )

        measurement_object.id = measurement.attrib['id']
        temperature_unit_id = measurement.attrib.get('temperature_unit')
        measurement_object._temperature_unit_id = temperature_unit_id

        for init_conc_element in measurement:

            params, unit_id = self._parse_init_conc_element(
                init_conc_element, enzmldoc)
            measurement_object.addData(**params, log=False)

            if params["reactant_id"]:
                meas_data = measurement_object.getReactant(
                    params["reactant_id"]
                )
            elif params["protein_id"]:
                meas_data = measurement_object.getProtein(
                    params["protein_id"]
                )
            else:
                raise ValueError(
                    "Neither 'reactant_id' nor 'protein_id' are defined"
                )

            meas_data._unit_id = unit_id

        return measurement_object

    @ staticmethod
    def _parse_init_conc_element(element: ET.Element, enzmldoc):
        """Parses initial concentration data of a measurement.

        Args:
            element (ET.Element): Element containing information about the initial concentration and species.

        Raises:
            KeyError: If there is neither a protein nor reactant ID.
        """

        value = float(element.attrib['value'])

        # Convert the unit ID to the corresponding SI string
        unit_id = element.attrib['unit']
        unit = enzmldoc.unit_dict[unit_id].name

        reactant_id = None
        protein_id = None

        if 'reactant' in element.attrib.keys():
            reactant_id = element.attrib['reactant']
        elif 'protein' in element.attrib.keys():
            protein_id = element.attrib['protein']
        else:
            raise KeyError(
                "Neither reactant or protein ID defined."
            )

        return {
            "init_conc": float(value),
            "unit": unit,
            "reactant_id": reactant_id,
            "protein_id": protein_id
        }, unit_id

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
