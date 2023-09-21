# File: enzymemlreader.py
# Project: tools
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import os
import re
from typing import Dict, List, Tuple, Union, Optional
import libsbml
import xml.etree.ElementTree as ET
import pandas as pd
import tempfile

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
from pyenzyme.enzymeml.core.abstract_classes import (
    AbstractSpeciesFactory,
    AbstractSpecies,
)

from libsbml import SBMLReader
from libcombine import CombineArchive
from io import StringIO

# ! Factories


class ReactantFactory(AbstractSpeciesFactory):
    """Returns an un-initialized reactant species object"""

    enzymeml_part: str = "reactant_dict"

    def get_species(self, **kwargs) -> AbstractSpecies:
        reactant = Reactant(**kwargs)
        reactant._unit_id = kwargs["_unit_id"]
        return reactant


class ProteinFactory(AbstractSpeciesFactory):
    """Returns an un-initialized protein species object"""

    enzymeml_part: str = "protein_dict"

    def get_species(self, **kwargs) -> AbstractSpecies:
        protein = Protein(**kwargs)
        protein._unit_id = kwargs["_unit_id"]
        return protein


class ComplexFactory(AbstractSpeciesFactory):
    """Returns an un-initialized complex species object"""

    enzymeml_part: str = "complex_dict"

    def get_species(self, **kwargs) -> AbstractSpecies:
        complex = Complex(**kwargs)
        complex._unit_id = kwargs["_unit_id"]
        return complex


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
        "DIMER": ComplexFactory(),
    }

    return factory_mapping[entity]


class EnzymeMLReader:
    def readFromFile(self, path: str) -> EnzymeMLDocument:
        """
        Reads EnzymeML document to an object layer EnzymeMLDocument class.

        Args:
            path (str): Path to .omex container or
                         folder destination for plain .xml
        """

        if not path.endswith(".omex"):
            raise TypeError(
                f"File {os.path.basename(path)} is not a valid OMEX archive"
            )

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
        self.enzmldoc = EnzymeMLDocument(
            name=model.getName(), level=model.getLevel(), version=model.getVersion()
        )

        # Add logs to the document
        self.enzmldoc.log = log

        # Fetch references
        self._getRefs(model, self.enzmldoc)

        # Fetch Creators
        self._getCreators(omex_desc=desc, enzmldoc=self.enzmldoc)

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
        self.enzmldoc._unit_dict = unitDict

        # Fetch Vessel
        vessel = self._getVessel(model, self.enzmldoc)
        self.enzmldoc.vessel_dict = vessel

        # Fetch Species
        protein_dict, reactant_dict, complex_dict = self._getSpecies(
            model, self.enzmldoc
        )

        self.enzmldoc.reactant_dict = reactant_dict
        self.enzmldoc.protein_dict = protein_dict
        self.enzmldoc.complex_dict = complex_dict

        # fetch global parameters
        self._getGlobalParameters(model, self.enzmldoc)

        # fetch reaction
        reaction_dict = self._getReactions(model, self.enzmldoc)
        self.enzmldoc.reaction_dict = reaction_dict

        # fetch Measurements
        measurement_dict = self._getData(model, self.enzmldoc)
        self.enzmldoc.measurement_dict = measurement_dict

        # fetch added files
        self._getFiles(self.enzmldoc)

        del self.path

        return self.enzmldoc

    @staticmethod
    def _sboterm_to_enum(sbo_term: int) -> Optional[SBOTerm]:
        try:
            sbo_string: str = libsbml.SBO.intToString(sbo_term)

            if len(sbo_string) == 0:
                return None

            return SBOTerm(sbo_string)

        except ValueError:
            return None

    def _getRefs(self, model, enzmldoc):

        if len(model.getAnnotationString()) == 0:
            return

        root = ET.fromstring(model.getAnnotationString())[0]

        for element in root:
            if "doi" in element.tag:
                enzmldoc.doi = element.text
            elif "pubmedID" in element.tag:
                enzmldoc.pubmedid = element.text
            elif "url" in element.tag:
                enzmldoc.url = element.text

    def _getCreators(self, omex_desc, enzmldoc) -> None:
        """Fetches all creators from an Combine archive's metadata.

        Args:
            omex_desc (OMEX obj): Combine metadata description.

        Returns:
            List[Creator]: Fetched list of creator objects.
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
                    mail=creator.getEmail(),
                ),
                log=False,
            )

    def _getUnits(self, model: libsbml.Model) -> Dict[str, UnitDef]:
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
            ontology = None  # TODO get unit ontology

            # Create unit definition
            unitdef = UnitDef(name=name, id=id, ontology=ontology, meta_id=meta_id)

            for baseunit in unit.getListOfUnits():
                # Construct unit definition with base units
                unitdef.addBaseUnit(
                    kind=baseunit.toXMLNode().getAttrValue("kind"),
                    exponent=baseunit.getExponentAsDouble(),
                    scale=baseunit.getScale(),
                    multiplier=baseunit.getMultiplier(),
                )

            # Finally add the unit definition
            unitDict[id] = unitdef

        return unitDict

    def _getVessel(
        self, model: libsbml.Model, enzmldoc: "EnzymeMLDocument"
    ) -> Dict[str, Vessel]:
        """Fetches all the vessels/compartments present in the SBML model.

        Args:
            model (libsbml.Model): The SBML model from which the vessels are fetched.

        Returns:
            Dict[str, Vessel]: Corresponding vessel dictionary that has been converted.
        """

        vessel_dict = {}
        compartments = model.getListOfCompartments()

        for compartment in compartments:
            name = compartment.getName()
            id = compartment.getId()

            # Set up dictionary for optional attributes
            params = {}

            if compartment.isSetVolume():
                params["volume"] = compartment.getSize()
                params["_unit_id"] = compartment.getUnits()
                params["unit"] = enzmldoc.getUnitString(params["_unit_id"])

            vessel = Vessel(name=name, id=id, **params)

            vessel._unit_id = params.get("_unit_id")
            vessel._enzmldoc = self.enzmldoc

            vessel_dict[vessel.id] = vessel

        return vessel_dict

    def _getSpecies(
        self, model: libsbml.Model, enzmldoc: "EnzymeMLDocument"
    ) -> Tuple[Dict[str, Protein], Dict[str, Reactant], Dict[str, Complex]]:

        # initialize dictionaries and get species
        protein_dict = {}
        reactant_dict = {}
        complex_dict = {}
        species_list = model.getListOfSpecies()

        for species in species_list:

            # Check if init conc is given
            init_conc = species.getInitialConcentration()
            unit_id = species.getSubstanceUnits()

            if repr(init_conc) == "nan":
                # Handle not existent init concs
                init_conc = None

            if unit_id:
                # Get unit string if given
                unit = enzmldoc.getUnitString(unit_id)
            else:
                unit = None

            # Get SBOTerm, but if there is none, give default
            ontology = self._sboterm_to_enum(species.getSBOTerm())

            # Parse annotations and construct a kwargs dictionary
            param_dict = self._parseSpeciesAnnotation(species.getAnnotationString())
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
                    "unit": unit,
                    # Some attributes need special care
                    "ecnumber": param_dict.get("e_cnumber"),
                    "uniprotid": param_dict.get("uniprot_id"),
                    "participants": param_dict.get("participant"),
                }
            )

            # Get species factory from ontology
            try:
                # Current version uses SBOTerms to distinguish between entities
                species_factory = species_factory_mapping(param_dict["ontology"])
            except ValueError:
                # Backwards compatibility to old documents that do not incorporate SBOTerms
                if param_dict["id"].startswith("s"):
                    species_factory = species_factory_mapping(
                        SBOTerm.SMALL_MOLECULE.value
                    )

                    # Remove ontology to get the default
                    param_dict.pop("ontology")

                elif param_dict["id"].startswith("p"):
                    species_factory = species_factory_mapping(SBOTerm.PROTEIN.value)

                    # Remove ontology to get the default
                    param_dict.pop("ontology")
                else:
                    raise ValueError(
                        f"ID {param_dict['id']} is not supported. Please use either of these 'p|s|c'"
                    )

            # Use factory to get the species class
            species = species_factory.get_species(**param_dict)
            species._enzmldoc = self.enzmldoc

            if species_factory.enzymeml_part == "protein_dict":
                protein_dict[species.id] = species
            elif species_factory.enzymeml_part == "reactant_dict":
                reactant_dict[species.id] = species
            elif species_factory.enzymeml_part == "complex_dict":
                complex_dict[species.id] = species

        return protein_dict, reactant_dict, complex_dict

    @staticmethod
    def _parseSpeciesAnnotation(annotationString):

        if len(annotationString) == 0:
            return dict()

        def camel_to_snake(name):
            name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
            return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

        speciesAnnot = ET.fromstring(annotationString)[0]

        # Initialize annotation dictionary
        param_dict = {}

        for enzymeMLAnnot in speciesAnnot:
            key = enzymeMLAnnot.tag.split("}")[-1]
            key = camel_to_snake(key)
            attribute = enzymeMLAnnot.text

            if key in param_dict:
                # Take care of list attributes
                try:
                    param_dict[key].append(attribute)
                except AttributeError:
                    param_dict[key] = [param_dict[key], attribute]

                continue

            param_dict[key] = attribute

        return param_dict

    def _getGlobalParameters(self, model: libsbml.Model, enzmldoc):
        """Fetches global parameters from the SBML model"""

        parameters = model.getListOfParameters()

        for parameter in parameters:
            parameter = self._parse_parameter(parameter, enzmldoc)
            parameter.is_global = True
            parameter._enzmldoc = self.enzmldoc

            enzmldoc.global_parameters[parameter.name] = parameter

    def _getReactions(
        self, model: libsbml.Model, enzmldoc: "EnzymeMLDocument"
    ) -> Dict[str, EnzymeReaction]:

        # Get SBML list of reactions
        reactionsList = model.getListOfReactions()

        # Initialize reaction dictionary
        reaction_dict = {}

        # parse annotations and filter replicates
        for reaction in reactionsList:

            # Fetch conditions
            if reaction.getAnnotationString():
                reactionAnnot = ET.fromstring(reaction.getAnnotationString())[0]
                conditions = self._parseConditions(reactionAnnot, enzmldoc)
            else:
                conditions = {}

            # Fetch Elements in SpeciesReference
            educts = self._getElements(
                reaction.getListOfReactants(), ontology=SBOTerm.SUBSTRATE
            )

            products = self._getElements(
                reaction.getListOfProducts(), ontology=SBOTerm.PRODUCT
            )

            modifiers = self._getElements(
                reaction.getListOfModifiers(), modifiers=True, ontology=SBOTerm.CATALYST
            )

            # Get the ontology
            ontology = self._sboterm_to_enum(reaction.getSBOTerm())

            if ontology is None:
                ontology = SBOTerm.BIOCHEMICAL_REACTION

            # Create object
            enzyme_reaction = EnzymeReaction(
                id=reaction.id,
                meta_id="META_" + reaction.id.upper(),
                name=reaction.name,
                reversible=reaction.reversible,
                educts=educts,
                products=products,
                modifiers=modifiers,
                ontology=ontology,
                **conditions,
            )

            # Check for kinetic model
            if reaction.getKineticLaw():
                # Check if model exists
                kinetic_law = reaction.getKineticLaw()
                kinetic_model = self._getKineticModel(kinetic_law, enzmldoc)
                enzyme_reaction.model = kinetic_model

                # Add global parameters
                for name, global_parameter in enzmldoc.global_parameters.items():
                    # Keep a reference to the global paremeter
                    if name in enzyme_reaction.model.equation:
                        enzyme_reaction.model.parameters.append(global_parameter)

            # Add reaction to reaction_dict
            enzyme_reaction._enzmldoc = self.enzmldoc
            reaction_dict[enzyme_reaction.id] = enzyme_reaction

        return reaction_dict

    @staticmethod
    def _parseConditions(
        reactionAnnot: ET.Element, enzmldoc: "EnzymeMLDocument"
    ) -> Dict[str, Union[str, float]]:
        """Exracts the conditions present in the SBML reaction annotations.
        Args:
            reactionAnnot (ET.Element): The reaction annotation element.
            enzmldoc (EnzymeMLDocument): The EnzymeMLDocument against which the data will be validated.
        Returns:
            Dict[str, Union[str, float]]: Mapping for the conditions.
        """

        # Get the conditions element
        conditions = reactionAnnot[0]
        condition_dict = {}

        for condition in conditions:
            # Sort all the conditions
            if "temperature" in condition.tag:

                # Get temperature conditions
                condition_dict["temperature"] = float(condition.attrib["value"])

                # Parse unit ID to Unit string
                condition_dict["_temperature_unit_id"] = condition.attrib["unit"]
                condition_dict["temperature_unit"] = enzmldoc.getUnitString(
                    condition_dict["_temperature_unit_id"]
                )

            elif "ph" in condition.tag:

                # Get the pH value
                condition_dict["ph"] = float(condition.attrib["value"])

        return condition_dict

    def _getElements(
        self,
        species_refs: List[libsbml.SpeciesReference],
        ontology: SBOTerm,
        modifiers: bool = False,
    ) -> List[ReactionElement]:
        """Extracts the speciesReference objects from the associated list and converts them to ReactionElements

        Args:
            species_refs (List[libsbml.SpeciesReference]): The species refrences for the reaction <-> Chemical reaction elements.
            modifiers (bool, optional): Used to override missing stoichiometry and constant for modifiers. Defaults to False.

        Returns:
            List[ReactionElement]: The list of reaction elements.
        """

        reaction_elements = []
        for species_ref in species_refs:

            species_id = species_ref.getSpecies()
            stoichiometry = 1.0 if modifiers else species_ref.getStoichiometry()
            constant = True if modifiers else species_ref.getConstant()
            sbo_term = libsbml.SBO.intToString(species_ref.getSBOTerm())

            if sbo_term:
                ontology = SBOTerm(sbo_term)

            reaction_elements.append(
                ReactionElement(
                    species_id=species_id,
                    stoichiometry=stoichiometry,
                    constant=constant,
                    ontology=ontology,
                )
            )

        return reaction_elements

    def _getKineticModel(
        self, kineticLaw: libsbml.KineticLaw, enzmldoc: "EnzymeMLDocument"
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
        ontology = self._sboterm_to_enum(kineticLaw.getSBOTerm())

        # Get local parameters
        parameters = []
        for local_param in kineticLaw.getListOfLocalParameters():

            parameter = self._parse_parameter(local_param, enzmldoc)

            if parameter.name in enzmldoc.global_parameters:
                parameters.append(enzmldoc.global_parameters[parameter.name])
            else:
                parameters.append(parameter)

        return KineticModel(
            name=name, equation=equation, parameters=parameters, ontology=ontology
        )

    def _parse_parameter(self, parameter, enzmldoc):
        """Parses a paramater and converts it to a KineticParameter instance"""

        # TODO refactor here

        value = parameter.getValue()
        unit_id = parameter.getUnits()

        annotation = parameter.getAnnotationString()
        param_dict = self._parseSpeciesAnnotation(annotation)

        if unit_id:
            param_dict["unit"] = enzmldoc.getUnitString(unit_id)

        if parameter.__class__.__name__ == "LocalParameter":
            constant = False
        else:
            constant = parameter.getConstant()

        if repr(parameter.getValue()) == "nan":
            value = None

        nu_param = KineticParameter(
            name=parameter.getId(),
            value=value,
            unit=param_dict.get("unit"),
            ontology=self._sboterm_to_enum(parameter.getSBOTerm()),
            initial_value=param_dict.get("initial_value"),
            upper=param_dict.get("upper_bound"),
            lower=param_dict.get("lower_bound"),
            stdev=param_dict.get("stdev"),
            constant=constant,
        )

        nu_param._enzmldoc = self.enzmldoc

        if unit_id:
            nu_param._unit_id = parameter.getUnits()

        return nu_param

    def _getData(
        self, model: libsbml.Model, enzmldoc: "EnzymeMLDocument"
    ) -> Dict[str, Measurement]:
        """Retrieves all available measurements found in the EnzymeML document.

        Args:
            model (libsbml.Model): The SBML model from which the measurements are feteched,

        Returns:
            Dict[str, Measurement]: Mapping from measurement ID to the associated object.
        """

        # Parse EnzymeML:format annotation
        reactions = model.getListOfReactions()
        annotation_string = reactions.getAnnotationString()

        # Guard clause for when there is no data
        if annotation_string == "":
            return {}

        # Parse annotation to an ElementTree
        data_annotation = ET.fromstring(annotation_string)[0]

        # Fetch measurements
        measurement_dict, measurement_files = self._parseListOfMeasurements(
            data_annotation, enzmldoc=enzmldoc
        )

        # Iterate over measurements and assign replicates
        for measurement_id, measurement_file in measurement_files.items():

            # Fetch list of files
            files = self._parseListOfFiles(data_annotation)

            # Fetch formats
            formats = self._parseListOfFormats(data_annotation)

            # Get file content
            fileInfo = files[measurement_file]
            file_content = self.archive.extractEntryToString(fileInfo["file"])
            csvFile = pd.read_csv(StringIO(file_content), header=None)

            # Get format data and extract time column
            measurement_format = formats[fileInfo["format"]]
            time, time_unit_id = [
                (csvFile.iloc[:, int(column["index"])].tolist(), column["unit"])
                for column in measurement_format
                if column["type"] == "time"
            ][0]

            measurement_dict[measurement_id]._global_time_unit_id = time_unit_id

            # Create replicate objects
            for format in measurement_format:

                if format["type"] != "time":

                    # Get time course data
                    data = csvFile.iloc[:, int(format["index"])].tolist()
                    reactant_id = format["species"]
                    replicate_id = format["replica"]
                    data_type = DataTypes(format["type"])
                    data_unit_id = format["unit"]
                    is_calculated = format["isCalculated"]

                    replicate = Replicate(
                        id=replicate_id,
                        species_id=reactant_id,
                        data_type=data_type,
                        measurement_id=measurement_id,
                        data_unit=enzmldoc._unit_dict[data_unit_id].name,
                        time_unit=enzmldoc._unit_dict[time_unit_id].name,
                        data=data,
                        time=time,
                        is_calculated=is_calculated,
                    )

                    replicate._data_unit_id = data_unit_id
                    replicate._time_unit_id = time_unit_id
                    replicate._enzmldoc = self.enzmldoc

                    measurement_dict[measurement_id].addReplicates(
                        replicate, log=False, enzmldoc=enzmldoc
                    )

        return measurement_dict

    def _parseListOfFiles(
        self, data_annotation: ET.Element
    ) -> Dict[str, Dict[str, str]]:
        """Extracts the list of files that are present in the annotation enzymeml:files.

        Args:
            data_annotation (ET.Element): ElementTree object containing the enzymeml:files annotation.

        Returns:
            Dict[str, Dict[str, str]]: Dictionary of all files present in the annotation.
        """

        return {
            file.attrib["id"]: {
                "file": file.attrib["file"],
                "format": file.attrib["format"],
                "id": file.attrib["id"],
            }
            for file in self._get_element(data_annotation, "files")
        }

    def _parseListOfFormats(self, data_annotation: ET.Element) -> Dict[str, List[dict]]:
        """Extracts the list of formats that areb present in the annotation enzymeml:formats.

        Args:
            data_annotation (ET.Element): ElementTree object containing the enzymeml:files annotation.

        Returns:
            Dict[str, List[dict]]: Dictionary of all the formats present in the annotation.
        """

        return {
            format.attrib["id"]: [column.attrib for column in format]
            for format in self._get_element(data_annotation, "formats")
        }

    def _parseListOfMeasurements(
        self, data_annotation: ET.Element, enzmldoc: "EnzymeMLDocument"
    ) -> Tuple[Dict[str, Measurement], dict]:
        """Extracts teh list of measurements that are present in the annotation enzymeml:measurements.

        Args:
            data_annotation (ET.Element): ElementTree object containing the enzymeml:measurements annotation.

        Returns:
            tuple[Dict[str, dict], Dict[str, Measurement]]: Two dictionaries returning the measurement objects and files.
        """

        measurements = self._get_element(data_annotation, "listOfMeasurements")

        if measurements is None:
            # There was a typo and it should be catched here
            measurements = self._get_element(data_annotation, "listOfMasurements")

        measurement_files = {
            measurement.attrib["id"]: measurement.attrib["file"]
            for measurement in measurements
            if measurement.attrib.get("file")
        }
        measurement_dict = {
            measurement.attrib["id"]: self._parseMeasurement(
                measurement, enzmldoc=enzmldoc
            )
            for measurement in measurements
        }

        return (measurement_dict, measurement_files)

    def _parseMeasurement(
        self, measurement: ET.Element, enzmldoc: "EnzymeMLDocument"
    ) -> Measurement:
        """Extracts individual initial concentrations of a measurement.

        Args:
            measurement (ET.Element): Measurement XML information

        Returns:
            Measurement: Initialized measurement object.
        """

        # Get conditions (temp, ph)
        temperature = measurement.attrib.get("temperature_value")
        temperature_unit = measurement.attrib.get("temperature_unit")
        ph = measurement.attrib.get("ph")

        # Get the unit string of temp if given
        if temperature_unit:
            temperature_unit = enzmldoc.getUnitString(temperature_unit)

        # initialize Measurement object
        measurement_object = Measurement(
            name=measurement.attrib["name"],
            temperature=temperature,
            temperature_unit=temperature_unit,
            ph=ph,
        )

        measurement_object.id = measurement.attrib["id"]
        temperature_unit_id = measurement.attrib.get("temperature_unit")
        measurement_object._temperature_unit_id = temperature_unit_id
        measurement_object._enzmldoc = self.enzmldoc

        for init_conc_element in measurement:

            params, unit_id = self._parse_init_conc_element(init_conc_element, enzmldoc)
            measurement_object.addData(**params, log=False)

            if params["reactant_id"]:
                meas_data = measurement_object.getReactant(params["reactant_id"])
            elif params["protein_id"]:
                meas_data = measurement_object.getProtein(params["protein_id"])
            else:
                raise ValueError("Neither 'reactant_id' nor 'protein_id' are defined")

            meas_data._unit_id = unit_id
            meas_data._enzmldoc = self.enzmldoc

        return measurement_object

    @staticmethod
    def _parse_init_conc_element(element: ET.Element, enzmldoc):
        """Parses initial concentration data of a measurement.

        Args:
            element (ET.Element): Element containing information about the initial concentration and species.

        Raises:
            KeyError: If there is neither a protein nor reactant ID.
        """

        value = float(element.attrib["value"])

        # Convert the unit ID to the corresponding SI string
        unit_id = element.attrib["unit"]
        unit = enzmldoc._unit_dict[unit_id].name

        reactant_id = None
        protein_id = None

        if "reactant" in element.attrib.keys():
            reactant_id = element.attrib["reactant"]
        elif "protein" in element.attrib.keys():
            protein_id = element.attrib["protein"]
        else:
            raise KeyError("Neither reactant or protein ID defined.")

        return {
            "init_conc": float(value),
            "unit": unit,
            "reactant_id": reactant_id,
            "protein_id": protein_id,
        }, unit_id

    @staticmethod
    def _get_element(tree: ET.Element, name: str):
        for element in tree.iter("*"):
            if name.lower() in element.tag.lower():
                return element

        return None

    def _getFiles(self, enzmldoc):
        """Extracts all added files fro the archive.

        Args:
            archive (CombineArchive): The OMEX archive to extract files from.
            enzmldoc (EnzymeMLDocument): The EnzymeMLDocument to add files to.
        """

        # Iterate over enries and extract files
        for file_location in self.archive.getAllLocations():
            file_location = str(file_location)

            if "./files/" in file_location:

                # Convert raw file to file_handle
                file_handle = tempfile.NamedTemporaryFile()
                file_handle.name = os.path.basename(file_location)

                # Write file to temporary file
                path = f"./{file_handle.name}"
                self.archive.extractEntry(file_location, path)

                with open(path, "rb") as f:
                    file_handle.write(f.read())
                    file_handle.seek(0)

                # Add the file to the EnzymeMLDocument
                enzmldoc.addFile(file_handle=file_handle)

                # Remove the temporary file
                os.remove(path)
