# File: enzymemlwriter.py
# Project: tools
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import pandas as pd
import os
import shutil
import libsbml
import tempfile
import logging
import warnings

from libsbml import (
    SBMLDocument,
    XMLNode,
    XMLTriple,
    XMLAttributes,
    XMLNamespaces,
    SBMLWriter,
)

from typing import Dict, List, Callable, Optional
from libcombine import CombineArchive, OmexDescription, KnownFormats, VCard

from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.measurement import Measurement
from pyenzyme.enzymeml.core.measurementData import MeasurementData
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction, ReactionElement
from pyenzyme.enzymeml.models.kineticmodel import KineticModel, KineticParameter

# Initialize the logger
logger = logging.getLogger("pyenzyme")


class EnzymeMLWriter:
    def __init__(self):
        self.namespace = "http://sbml.org/enzymeml/version2"

    def toFile(self, enzmldoc, path: str, name: Optional[str] = None):
        """
        Writes EnzymeMLDocument object to an .omex container

        Args:
            enzmldoc (String): Previously created instance of an EnzymeML document
            path (String): EnzymeML file is written to this destination
            name (String): Name of the target EnzymeML file. Defaults to 'None' and thus uses the doc name.

        """

        self.path = os.path.normpath(path)
        self.enzmldoc = enzmldoc  # TODO replace all static enzmldocs with self.enzmldoc

        try:
            os.makedirs(os.path.join(self.path, "data"))
        except FileExistsError:
            pass

        doc = SBMLDocument()
        doc.setLevelAndVersion(3, 2)

        model = doc.createModel()
        model.setName(enzmldoc.name)
        model.setId(enzmldoc.name)

        # Convert the SBML model to EnzymeML
        self.convertEnzymeMLToSBML(model, enzmldoc)

        # Add data
        paths = self._addData(model, enzmldoc.measurement_dict)

        # Write to EnzymeML
        writer = SBMLWriter()
        writer.writeSBMLToFile(doc, os.path.join(self.path, "experiment.xml"))

        # Validate the SBML document
        self._validate_sbml_doc(document=doc)

        # Write to OMEX
        self._createArchive(enzmldoc, paths, name)

        shutil.rmtree(os.path.join(self.path, "data"), ignore_errors=True)

        os.remove(os.path.join(self.path, "experiment.xml"))

    def toXMLString(self, enzmldoc):
        """
        Converts EnzymeMLDocument to XML string.

        Args:
            EnzymeMLDocument enzmldoc: Previously created instance of an
                                       EnzymeML document
        """
        doc = SBMLDocument()
        doc.setLevelAndVersion(3, 2)

        model = doc.createModel()
        model.setName(enzmldoc.name)
        model.setId(enzmldoc.name)

        self.path = None
        self.enzmldoc = enzmldoc

        # Convert the SBML model to EnzymeML
        self.convertEnzymeMLToSBML(model, enzmldoc)

        # Add data
        self._addData(model, enzmldoc.measurement_dict)

        # Write to EnzymeML
        writer = SBMLWriter()
        return writer.writeToString(doc)

    def toSBML(self, enzmldoc):
        """
        Returns libSBML model.

        Args:
            EnzymeMLDocument enzmldoc: Previously created instance of an
                                       EnzymeML document
        """

        doc = SBMLDocument()
        doc.setLevelAndVersion(3, 2)

        model = doc.createModel()
        model.setName(enzmldoc.name)
        model.setId(enzmldoc.name)

        # Convert the SBML model to EnzymeML
        self.convertEnzymeMLToSBML(model, enzmldoc)

        return doc

    def convertEnzymeMLToSBML(self, model: libsbml.Model, enzmldoc):
        """Manages the conversion of EnzymeML to SBML.

        Args:
            model (libsbml.Model): The blank SBML model, where the EnzymeML document is converted to.
            enzmldoc (EnzymeMLDocument): The EnzymeML document to be converted.
        """

        self._addRefs(model, enzmldoc)
        self._addVessel(model, enzmldoc.vessel_dict)
        self._addProteins(model, enzmldoc.protein_dict)
        self._addComplex(model, enzmldoc.complex_dict)
        self._addReactants(model, enzmldoc.reactant_dict)
        self._addGlobalParameters(model, enzmldoc.global_parameters)
        self._addReactions(model, enzmldoc.reaction_dict)
        self._addUnits(model, enzmldoc._unit_dict)

    def _createArchive(self, enzmldoc, listofPaths, name: str = None):

        archive = CombineArchive()

        # add experiment file to archive
        archive.addFile(
            f"{self.path}/experiment.xml",
            "./experiment.xml",
            KnownFormats.lookupFormat("sbml"),
            True,
        )

        # add logs to teh Archive
        history_path = f"{self.path}/history.log"
        try:
            with open(history_path, "wb") as f:
                f.write(enzmldoc.log.getvalue().encode("utf-8", "replace"))

                self.addFileToArchive(
                    archive=archive,
                    file_path=history_path,
                    target_path="./history.log",
                    format=KnownFormats.lookupFormat("txt"),
                    description="History of the EnzymeML document",
                )
        except Exception as e:
            logging.error("couldn't write history")

        # add metadata to the experiment file
        location = "./experiment.xml"
        description = OmexDescription()
        description.setAbout(location)
        description.setDescription("EnzymeML model")
        description.setCreated(OmexDescription.getCurrentDateAndTime())

        for creat in enzmldoc.creator_dict.values():
            creator = VCard()
            creator.setFamilyName(creat.family_name)
            creator.setGivenName(creat.given_name)
            creator.setEmail(creat.mail)
            description.addCreator(creator)

        archive.addMetadata(".", description)
        archive.addMetadata(location, description)

        # Add CSV files to archive
        for csvPath, file_path in listofPaths.items():

            self.addFileToArchive(
                archive=archive,
                file_path=csvPath,
                target_path=file_path,
                format=KnownFormats.lookupFormat("csv"),
                description="Time course data",
            )

        # Add files from fileDict
        tmpFolder = None
        if enzmldoc.file_dict:
            # create temporary directory for files
            tmpFolder = tempfile.mkdtemp()

            for fileDict in enzmldoc.file_dict.values():

                file_handler = fileDict["handler"]
                file_name = fileDict["name"]
                fileDescription = fileDict["description"]
                tmpPath = os.path.join(tmpFolder, file_name)

                # Write file locally and add it to the document
                with open(tmpPath, "wb") as fileHandle:
                    fileHandle.write(file_handler.read())

                self.addFileToArchive(
                    archive=archive,
                    file_path=tmpPath,
                    target_path=f"./files/{file_name}",
                    format=KnownFormats.guessFormat(file_name),
                    description=fileDescription,
                )

        if name:
            out_file = f"{name.replace(' ', '_')}.omex"
        else:
            out_file = f"{enzmldoc.name.replace(' ', '_')}.omex"

        out_path = os.path.join(self.path, out_file)

        try:
            os.remove(out_path)
        except FileNotFoundError:
            pass

        archive.writeToFile(out_path)

        # Remove temporary directory
        if tmpFolder is not None:
            shutil.rmtree(tmpFolder, ignore_errors=True)

        # Remove unused
        os.remove(f"{self.path}/history.log")

        print(f"\nArchive was written to {out_path}\n")

    @staticmethod
    def addFileToArchive(archive, file_path, target_path, format, description):

        # Add file to archive
        archive.addFile(file_path, target_path, format, False)

        # Add metadata to the file
        omexDesc = OmexDescription()
        omexDesc.setAbout(target_path)
        omexDesc.setDescription(description)
        omexDesc.setCreated(OmexDescription.getCurrentDateAndTime())
        archive.addMetadata(target_path, omexDesc)

    def setupXMLNode(self, name, namespace=True):
        # Helper function
        # Creates an XML node
        # for annotations
        node = XMLNode(XMLTriple(name), XMLAttributes(), XMLNamespaces())

        if namespace is True:
            node.addNamespace(self.namespace, "enzymeml")

        return node

    @staticmethod
    def appendAttribute(attributeName, value):
        # Helper function
        # creates XML node
        # <x>XYZ</x>
        value = XMLNode(value)
        attributeNode = XMLNode(
            XMLTriple(attributeName), XMLAttributes(), XMLNamespaces()
        )

        attributeNode.addChild(value)

        return attributeNode

    def appendMultiAttributes(
        self, attributeName, object, objectMapping, annotationNode
    ):
        node = self.setupXMLNode(attributeName, namespace=False)

        for key, value in objectMapping.items():
            # "value" --> 10.00
            if hasattr(object, value):

                attribute = getattr(object, value)
                if attribute:
                    node.addAttr(key, str(attribute))
                else:
                    return 0
            else:
                return 0

        annotationNode.addChild(node)

    def appendOptionalAttribute(
        self, attributeName, object, objectName, annotationNode
    ):
        # Helper function
        # Adds elements to annotation node
        if object.__dict__.get(objectName):
            value = self.appendAttribute(
                attributeName, str(getattr(object, objectName))
            )
            annotationNode.addChild(value)

    def _addRefs(self, model: libsbml.Model, enzmldoc):
        """Converts EnzymeMLDocument refrences to SBML.

        Args:
            model (libsbml.Model): The SBML model the reference is added to.
            enzmldoc (EnzymeMLDocument): The EnzymeMLDocument instance that contains the information.
        """

        # Create reference node
        referenceAnnotation = self.setupXMLNode("enzymeml:references")

        # Optional attributes
        referenceAttributes = {
            "enzymeml:doi": "doi",
            "enzymeml:pubmedID": "pubmedid",
            "enzymeml:url": "url",
        }

        for attributeName, objectName in referenceAttributes.items():
            self.appendOptionalAttribute(
                attributeName=attributeName,
                object=enzmldoc,
                objectName=objectName,
                annotationNode=referenceAnnotation,
            )

        if referenceAnnotation.getNumChildren() > 0:
            model.appendAnnotation(referenceAnnotation)

    def _addUnits(self, model: libsbml.Model, unit_dict: Dict[str, UnitDef]) -> None:
        """Converts EnzymeMLDocument units to SBML.

        Args:
            model (libsbml.Model): The SBML model the units are added to.
            unit_dict (Dict[str, UnitDef]): The EnzymeMLDocument units to be added to the SBML model.
        """

        for unit_id, unit_def in unit_dict.items():

            unit = model.createUnitDefinition()
            unit.setId(unit_id)
            unit.setMetaId(unit_def.meta_id)
            unit.setName(unit_def.name)

            # TODO Add ontology
            # if unit_def.getOntology() != "NONE":
            #     cvterm = CVTerm()
            #     cvterm.addResource(unit_def.getOntology())
            #     cvterm.setQualifierType(BIOLOGICAL_QUALIFIER)
            #     cvterm.setBiologicalQualifierType(BQB_IS)
            #     unit.addCVTerm(cvterm)

            for base_unit in unit_def.units:

                kind = base_unit.kind
                exponent = base_unit.exponent
                scale = base_unit.scale
                multiplier = base_unit.multiplier

                baseUnitDef = unit.createUnit()

                try:
                    baseUnitDef.setKind(libsbml.UnitKind_forName(kind))
                except TypeError:
                    baseUnitDef.setKind(kind)

                baseUnitDef.setExponent(exponent)
                baseUnitDef.setScale(scale)
                baseUnitDef.setMultiplier(multiplier)

    def _addVessel(self, model, vessel_dict: Dict[str, Vessel]) -> None:
        """Converts EnzymeMLDocument vessel to SBML.

        Args:
            model (libsbml.Model): The SBML model the vessel is added to.
            vessel (Vessel): The EnzymeMLDocument vessel to be added to the SBML model.
        """

        for vessel_id, vessel in vessel_dict.items():
            compartment = model.createCompartment()
            compartment.setId(vessel_id)
            compartment.setName(vessel.name)
            compartment.setConstant(vessel.constant)
            compartment.setSpatialDimensions(3)

            if vessel.volume:
                compartment.setSize(vessel.volume)
                compartment.setUnits(vessel._unit_id)

    def _addProteins(
        self, model: libsbml.Model, protein_dict: Dict[str, Protein]
    ) -> None:
        """Converts EnzymeMLDocument proteins to SBML.

        Args:
            model (libsbml.Model): The SBML model the proteins are added to.
            protein_dict (Dict[str, Protein]): The EnzymeMLDocument proteins to be added to the SBML model.
        """

        # EnzymeML attributes
        proteinAttributes = {
            "enzymeml:sequence": "sequence",
            "enzymeml:ECnumber": "ecnumber",
            "enzymeml:uniprotID": "uniprotid",
            "enzymeml:organism": "organism",
            "enzymeml:organismTaxID": "organism_tax_id",
        }

        for protein in protein_dict.values():
            self._addSpecies(
                obj=protein,
                annotation_name="enzymeml:protein",
                model=model,
                optional_attributes=proteinAttributes,
            )

    def _addComplex(
        self, model: libsbml.Model, complex_dict: Dict[str, Protein]
    ) -> None:
        """Converts EnzymeMLDocument proteins to SBML.

        Args:
            model (libsbml.Model): The SBML model the proteins are added to.
            complex_dict (Dict[str, Protein]): The EnzymeMLDocument complex to be added to the SBML model.
        """

        complexAttributes = {
            "enzymeml:participant": "participants",
        }

        for complex in complex_dict.values():
            self._addSpecies(
                obj=complex,
                annotation_name="enzymeml:complex",
                model=model,
                optional_attributes=complexAttributes,
            )

    def _addReactants(self, model: libsbml.Model, reactant_dict: Dict[str, Reactant]):
        """Converts EnzymeMLDocument reactants to SBML.

        Args:
            model (libsbml.Model): The SBML model the reactants are added to.
            reactant_dict (Dict[str, Reactant]): The EnzymeMLDocument reactants to be added to the SBML model.
        """

        # EnzymeML attributes
        reactantAttributes = {
            "enzymeml:inchi": "inchi",
            "enzymeml:smiles": "smiles",
            "enzymeml:chebiID": "chebi_id",
        }

        for reactant in reactant_dict.values():
            self._addSpecies(
                obj=reactant,
                annotation_name="enzymeml:reactant",
                model=model,
                optional_attributes=reactantAttributes,
            )

    def _addGlobalParameters(
        self, model: libsbml.Model, global_parameters: Dict[str, KineticParameter]
    ):
        """Writes global parameters to the SBML document.

        Args:
            model (libsbml.Model): SBML model the global parameters are added to.
            global_parameters (Dict[str, KineticParameter]): Global parameters that will be added to the SBML document.
        """

        for parameter in global_parameters.values():
            sbml_param = self._write_global_parameter(parameter, model)

            # Create a mapping for the 'enzymeml:parameter' annotation
            annotation = self.setupXMLNode("enzymeml:parameter")
            optional_parameters = {
                "enzymeml:initialValue": "initial_value",
                "enzymeml:upperBound": "upper",
                "enzymeml:lowerBound": "lower",
            }

            for attributeName, objectName in optional_parameters.items():

                self.appendOptionalAttribute(
                    attributeName=attributeName,
                    object=parameter,
                    objectName=objectName,
                    annotationNode=annotation,
                )

            if annotation.getNumChildren() > 0:
                sbml_param.appendAnnotation(annotation)

    def _write_global_parameter(
        self, parameter: KineticParameter, model: libsbml.Model
    ):
        """Writes a global parameter to a reaction"""

        global_param = model.createParameter()
        global_param.setId(parameter.name)
        global_param.setConstant(parameter.constant)

        if parameter.value is not None:
            global_param.setValue(parameter.value)

        if parameter._unit_id:
            global_param.setUnits(parameter._unit_id)

        if parameter.ontology:
            global_param.setSBOTerm(parameter.ontology)

        return global_param

    def _addSpecies(
        self,
        obj: AbstractSpecies,
        annotation_name: str,
        model: libsbml.Model,
        optional_attributes: Dict[str, str],
    ) -> None:
        """Helper function to create any EnzymeML species from

        Args:
            obj (AbstractSpecies): Object containing the species informations.
        """

        species = model.createSpecies()
        species.setId(obj.id)
        species.setName(obj.name)
        species.setMetaId(obj.meta_id)
        species.setSBOTerm(obj.ontology)
        species.setCompartment(obj.vessel_id)
        species.setBoundaryCondition(obj.boundary)
        species.setConstant(obj.constant)
        species.setHasOnlySubstanceUnits(False)

        if obj.init_conc is not None and obj._unit_id:
            species.setSubstanceUnits(obj._unit_id)
            species.setInitialConcentration(obj.init_conc)
        elif obj.init_conc and not obj._unit_id:
            raise ValueError(
                f"The object {obj.name} ({obj.id}) has an initial concentration value but no unit. Please specify a unit for a successful export to SBML."
            )

        # Controls if annotation will be added
        objAnnotation = self.setupXMLNode(annotation_name)

        # EnzymeML attributes
        for attributeName, objectName in optional_attributes.items():

            # TODO more elegant way to handle complex parts
            if isinstance(getattr(obj, objectName), list):
                for id in getattr(obj, objectName):
                    value = self.appendAttribute(attributeName, id)
                    objAnnotation.addChild(value)

                continue

            self.appendOptionalAttribute(
                attributeName=attributeName,
                object=obj,
                objectName=objectName,
                annotationNode=objAnnotation,
            )

        if objAnnotation.getNumChildren() > 0:
            species.appendAnnotation(objAnnotation)

    def _addReactions(
        self, model: libsbml.Model, reaction_dict: Dict[str, EnzymeReaction]
    ):
        """Converts EnzymeMLDocument reactions to SBML.

        Args:
            model (libsbml.Model): The SBML model the reactions are added to.
            reaction_dict (Dict[str, EnzymeReaction]): The EnzymeMLDocument reactions to be added to the SBML model.
        """

        for reaction_id, enzyme_reaction in reaction_dict.items():

            reaction = model.createReaction()
            reaction.setId(reaction_id)
            reaction.setMetaId(enzyme_reaction.meta_id)
            reaction.setName(enzyme_reaction.name)
            reaction.setReversible(enzyme_reaction.reversible)
            reaction.setSBOTerm(enzyme_reaction.ontology)

            # Add kinetic model
            if enzyme_reaction.model:
                self._addModelToReaction(
                    reaction=reaction, kinetic_model=enzyme_reaction.model
                )

            # Enzymeml attributes
            reactionAnnotation = self.setupXMLNode("enzymeml:reaction")

            # Track conditions
            conditionsAnnotation = self.setupXMLNode(
                "enzymeml:conditions", namespace=False
            )

            conditionsMapping = {
                "enzymeml:temperature": {
                    "value": "temperature",
                    "unit": "_temperature_unit_id",
                },
                "enzymeml:ph": {"value": "ph"},
            }

            for attributeName, objectMapping in conditionsMapping.items():
                self.appendMultiAttributes(
                    attributeName=attributeName,
                    object=enzyme_reaction,
                    objectMapping=objectMapping,
                    annotationNode=conditionsAnnotation,
                )

            if conditionsAnnotation.getNumChildren() > 0:
                reactionAnnotation.addChild(conditionsAnnotation)
                reaction.appendAnnotation(reactionAnnotation)

            # Write educts
            self.writeElements(
                reaction_elements=enzyme_reaction.educts,
                createFunction=reaction.createReactant,
            )

            # Write products
            self.writeElements(
                reaction_elements=enzyme_reaction.products,
                createFunction=reaction.createProduct,
            )

            # Write modifiers
            self.writeElements(
                reaction_elements=enzyme_reaction.modifiers,
                createFunction=reaction.createModifier,
            )

    def _addModelToReaction(
        self,
        reaction: libsbml.Reaction,
        kinetic_model: KineticModel,
    ) -> None:
        """
        Adds kinetic law to SBML reaction.
        Only relevant for EnzymeML > SBML conversion.

        Args:
            reaction (libsbml.Reaction): SBML reaction class
            kinetic_model (KineticModel): PyEnzyme Model object
        """

        # Set up SBML kinetic law node
        sbml_law = reaction.createKineticLaw()

        for parameter in kinetic_model.parameters:

            if parameter.is_global:
                continue

            param = self._write_local_parameter(parameter, sbml_law)

            # Create a mapping for the 'enzymeml:parameter' annotation
            annotation = self.setupXMLNode("enzymeml:parameter")
            optional_parameters = {
                "enzymeml:initialValue": "initial_value",
                "enzymeml:upperBound": "upper",
                "enzymeml:lowerBound": "lower",
                "enzymeml:stdev": "stdev",
            }

            for attributeName, objectName in optional_parameters.items():

                self.appendOptionalAttribute(
                    attributeName=attributeName,
                    object=parameter,
                    objectName=objectName,
                    annotationNode=annotation,
                )

            if annotation.getNumChildren() > 0:
                param.appendAnnotation(annotation)

        sbml_law.setMath(libsbml.parseL3Formula(kinetic_model.equation))
        sbml_law.setName(kinetic_model.name)

        if kinetic_model.ontology:
            sbml_law.setSBOTerm(kinetic_model.ontology)

    def _write_local_parameter(
        self,
        parameter: KineticParameter,
        kinetic_law: libsbml.KineticLaw,
    ):
        """Writes a local parameter to a reaction"""

        local_param = kinetic_law.createLocalParameter()
        local_param.setId(parameter.name)

        if parameter.value is not None:
            local_param.setValue(parameter.value)

        if parameter._unit_id:
            local_param.setUnits(parameter._unit_id)

        if parameter.ontology:
            local_param.setSBOTerm(parameter.ontology)

        return local_param

    def writeElements(
        self, reaction_elements: List[ReactionElement], createFunction: Callable
    ):
        """Writes SpeciesReference elements to the SBML document.

        Args:
            reaction_elements (List[ReactionElement]): List of reaction elements containing information on stoichiometry, species_id and ontology.
            createFunction (Callable): Function that creates either an educt, product or modifier list to the SBML document.
        """

        for reaction_element in reaction_elements:

            speciesRef = createFunction()
            speciesRef.setSpecies(reaction_element.species_id)
            speciesRef.setSBOTerm(reaction_element.ontology)

            try:
                # Catch modifiers --> No stoich/constant in SBML
                speciesRef.setConstant(reaction_element.constant)
                speciesRef.setStoichiometry(reaction_element.stoichiometry)
            except AttributeError:
                pass

    def writeReplicateData(self, replicate: Replicate, format_annot: XMLNode) -> None:
        """Writes column information to the enzymeml:format annotation.

        Args:
            replicate (Replicate): Replicate holding the time course data.
            format_annot (XMLNode): The enzymeml:format annotation node.
        """

        column = self.setupXMLNode("enzymeml:column", namespace=False)

        # Add attributes
        column.addAttr("replica", replicate.id)
        column.addAttr("species", replicate.species_id)
        column.addAttr("type", replicate.data_type)
        column.addAttr("unit", replicate._data_unit_id)
        column.addAttr("index", str(self.index))
        column.addAttr("isCalculated", str(replicate.is_calculated))

        # Add colum to format annotation
        format_annot.addChild(column)

    def _addData(
        self, model: libsbml.Model, measurement_dict: Dict[str, Measurement]
    ) -> Dict[str, str]:
        """Adds measurement data to the SBML document and writes time course data to DataFrames/CSV.

        Args:
            model (libsbml.Model): The SBML model to which the measurements are added.
            measurement_dict (Dict[str, Measurement]): The EnzymeMLDocument measurement data.

        Returns:
            Dict[str, str]: Mapping from actual CSV paths to the ones added to the OMEX
        """

        # Initialize data lists
        data_annotation = self.setupXMLNode("enzymeml:data")
        files = self.setupXMLNode("enzymeml:files", namespace=False)
        formats = self.setupXMLNode("enzymeml:formats", namespace=False)
        measurements = self.setupXMLNode("enzymeml:listOfMeasurements", namespace=False)
        paths = {}

        for index, (measurement_id, measurement) in enumerate(measurement_dict.items()):

            # setup format/Measurement ID/node and file ID
            format_id = f"format{index}"
            file_id = f"file{index}"

            format_annot = self.setupXMLNode("enzymeml:format", namespace=False)

            format_annot.addAttr("id", format_id)

            measurement_annot = self.setupXMLNode(
                "enzymeml:measurement", namespace=False
            )

            # Get time and add to format node
            data_columns = {}
            if measurement._has_replicates():
                # Only write time data if replicates are present
                self.writeTimeData(
                    measurement=measurement,
                    format_annot=format_annot,
                    data_columns=data_columns,
                )

            self.writeMeasurementData(
                measurement=measurement,
                measurement_annot=measurement_annot,
                format_annot=format_annot,
                data_columns=data_columns,
            )

            # Create DataFrame to save measurement
            if data_columns:
                file_name = f"{measurement_id}.csv"
                file_path = f"./data/{file_name}"
                df = pd.DataFrame(data_columns)

                if self.path:
                    df_path = os.path.join(self.path, "data", file_name)
                    df.to_csv(df_path, index=False, header=False)
                else:
                    df_path = "Unused"

                paths[df_path] = file_path

                # Add data to data annotation
                file_annot = self.setupXMLNode("enzymeml:file", namespace=False)

                file_annot.addAttr("file", file_path)
                file_annot.addAttr("format", format_id)
                file_annot.addAttr("id", file_id)

                files.addChild(file_annot)
                formats.addChild(format_annot)

                measurement_annot.addAttr("file", file_id)

            measurement_annot.addAttr("id", measurement_id)
            measurement_annot.addAttr("name", measurement.name)

            # TODO find a sustainable way
            if measurement.temperature:
                measurement_annot.addAttr(
                    "temperature_unit", measurement._temperature_unit_id
                )
                measurement_annot.addAttr(
                    "temperature_value", str(measurement.temperature)
                )

            if measurement.ph:
                measurement_annot.addAttr("ph", str(measurement.ph))

            measurements.addChild(measurement_annot)

        # add annotation to listOfReactions
        if formats.getNumChildren() > 0:
            data_annotation.addChild(formats)
        if measurements.getNumChildren() > 0:
            data_annotation.addChild(measurements)
        if files.getNumChildren() > 0:
            data_annotation.addChild(files)
        if data_annotation.getNumChildren() > 0:
            model.getListOfReactions().appendAnnotation(data_annotation)

        return paths

    def writeTimeData(
        self, measurement: Measurement, format_annot: XMLNode, data_columns: dict
    ):
        time = measurement.global_time
        time_unit = measurement._global_time_unit_id

        time_column = XMLNode(XMLTriple("enzymeml:column"), XMLAttributes())

        time_column.addAttr("type", "time")
        time_column.addAttr("unit", time_unit)
        time_column.addAttr("index", "0")

        format_annot.addChild(time_column)

        # write initConc annotation and prepare raw data
        data_columns.update({f"time/{time_unit}": time})
        self.index = 1

    def writeMeasurementData(
        self,
        measurement: Measurement,
        measurement_annot: XMLNode,
        format_annot: XMLNode,
        data_columns: Dict[str, List[float]],
    ) -> None:
        """Writes measurement metadata as columns to the SBML document annotation enzymeml:column.

        Args:
            measurement (Measurement): EnzymeML measurement that is written to SBML.
            measurement_annot (XMLNode): The SBML XMLNode the measurement metadata is written to.
            format_annot (XMLNode): The SBML XMLNode the column information is written to.

        Returns:
            List[List[float]]: The time course data from the replicate objects.
        """

        species_dict = measurement.species_dict

        # Init Conc
        # Extract measurementData objects
        proteins = species_dict["proteins"]
        reactants = species_dict["reactants"]

        # Append initConc data to measurement
        self.appendInitConcData(
            measurement_annot=measurement_annot,
            measurement_data_dict=proteins,
            species_type="protein",
        )
        self.appendInitConcData(
            measurement_annot=measurement_annot,
            measurement_data_dict=reactants,
            species_type="reactant",
        )

        if measurement._has_replicates():
            # Replicates
            self.appendReplicateData(
                {**proteins, **reactants},
                format_annot=format_annot,
                data_columns=data_columns,
            )

    def appendInitConcData(
        self,
        measurement_annot: XMLNode,
        measurement_data_dict: Dict[str, MeasurementData],
        species_type: str,
    ):
        """Adds individual intial concentration data to the enzymeml:measurement annotation.

        Args:
            measurement_annot (XMLNode): The SBML XMLNode for the measurement annotation.
            measurement_data_dict (Dict[str, MeasurementData]): The EnzymeMLDocument measurement data.
            species_type (str): The type of species in the measurement_data_dict.
        """

        for species_id, measurement_data in measurement_data_dict.items():

            # Create the initConc annotation
            initConcAnnot = self.setupXMLNode("enzymeml:initConc", namespace=False)

            initConcAnnot.addAttr(f"{species_type}", species_id)
            initConcAnnot.addAttr("value", str(measurement_data.init_conc))

            # TODO Check if the unit given in the unit attribute is compliant
            # TODO Handle this in the base class by assigning a 'None' to the _unit_id
            unit_id_check = self.enzmldoc._convertToUnitDef(measurement_data.unit)

            if measurement_data._unit_id != unit_id_check:
                measurement_data._unit_id = unit_id_check

            initConcAnnot.addAttr("unit", measurement_data._unit_id)

            measurement_annot.addChild(initConcAnnot)

    def appendReplicateData(
        self,
        species: Dict[str, MeasurementData],
        format_annot: XMLNode,
        data_columns: Dict[str, List[float]],
    ) -> Dict[str, List[float]]:
        """Extracts all time course data from the replicate objects and adds them to the the enzymeml:format annotation.

        Args:
            species (Dict[str, MeasurementData]): Reactant/Protein measurement data.
            format_annot (XMLNode): The SBML XMLNode representing the format annotation.

        Returns:
            List[List[float]]: The time course data from the replicate objects.
        """

        # Collect all replicates
        replicates = [
            replicate for data in species.values() for replicate in data.replicates
        ]

        for replicate in replicates:

            # Write data to format_annot
            self.writeReplicateData(replicate=replicate, format_annot=format_annot)

            # Extract series data
            header_info = "/".join(
                [replicate.id, replicate.species_id, replicate.data_type.value]
            )

            data_columns[header_info] = replicate.data

            self.index += 1

        return data_columns

    def _validate_sbml_doc(self, document):
        """Validates an SBML documentument and checks for errors."""

        document.checkConsistency()
        if document.getNumErrors(libsbml.LIBSBML_SEV_ERROR) > 0:
            warnings.warn("Invalid SBML document! See warnings:")
            warnings.warn(document.getErrorLog().toString())
