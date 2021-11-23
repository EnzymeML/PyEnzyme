'''
File: enzymemlwriter.py
Project: tools
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 9:09:19 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

import pandas as pd
import os
import shutil

from libsbml import (
    SBMLDocument,
    XMLNode,
    XMLTriple,
    XMLAttributes,
    XMLNamespaces,
    SBMLWriter
)

import libsbml
import tempfile

from typing import Callable
from libcombine import CombineArchive, OmexDescription, KnownFormats, VCard

from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.measurement import Measurement
from pyenzyme.enzymeml.core.measurementData import MeasurementData
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction, ReactionElement


class EnzymeMLWriter:

    def __init__(self):
        self.namespace = "http://sbml.org/enzymeml/version2"

    def toFile(self, enzmldoc, path: str, verbose: int = 1):
        '''
        Writes EnzymeMLDocument object to an .omex container

        Args:
            EnzymeMLDocument enzmldoc: Previously created instance of an
                                       EnzymeML document
            String path: EnzymeML file is written to this destination
        '''

        self.path = os.path.normpath(path)

        try:
            os.makedirs(
                os.path.join(self.path, 'data')
            )
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
        paths = self.__addData(model, enzmldoc.measurement_dict)

        # Write to EnzymeML
        writer = SBMLWriter()
        writer.writeSBMLToFile(
            doc,
            os.path.join(
                self.path,
                'experiment.xml'
            )
        )

        # Write to OMEX
        self.__createArchive(enzmldoc, paths, verbose)

        shutil.rmtree(
            os.path.join(self.path, 'data'),
            ignore_errors=True
        )

        os.remove(
            os.path.join(
                self.path, 'experiment.xml'
            )
        )

    def toXMLString(self, enzmldoc):
        '''
        Converts EnzymeMLDocument to XML string.

        Args:
            EnzymeMLDocument enzmldoc: Previously created instance of an
                                       EnzymeML document
        '''
        doc = SBMLDocument()
        doc.setLevelAndVersion(3, 2)

        model = doc.createModel()
        model.setName(enzmldoc.name)
        model.setId(enzmldoc.name)

        self.path = None

        # Convert the SBML model to EnzymeML
        self.convertEnzymeMLToSBML(model, enzmldoc)

        # Add data
        self.__addData(model, enzmldoc.measurement_dict)

        # Write to EnzymeML
        writer = SBMLWriter()
        return writer.writeToString(doc)

    def toSBML(self, enzmldoc):
        '''
        Returns libSBML model.

        Args:
            EnzymeMLDocument enzmldoc: Previously created instance of an
                                       EnzymeML document
        '''

        doc = SBMLDocument()
        doc.setLevelAndVersion(3, 2)

        model = doc.createModel()
        model.setName(enzmldoc.getName())
        model.setId(enzmldoc.getName())

        # Convert the SBML model to EnzymeML
        self.convertEnzymeMLToSBML(model, enzmldoc)

        return doc

    def convertEnzymeMLToSBML(self, model: libsbml.Model, enzmldoc):
        """Manages the conversion of EnzymeML to SBML.

        Args:
            model (libsbml.Model): The blank SBML model, where the EnzymeML document is converted to.
            enzmldoc (EnzymeMLDocument): The EnzymeML document to be converted.
        """

        self.__addRefs(model, enzmldoc)
        self.__addUnits(model, enzmldoc.unit_dict)
        self.__addVessel(model, enzmldoc.vessel_dict)
        self.__addProteins(model, enzmldoc.protein_dict)
        self.__addReactants(model, enzmldoc.reactant_dict)
        self.__addReactions(model, enzmldoc.reaction_dict)

    def __createArchive(self, enzmldoc, listofPaths, verbose=1):

        archive = CombineArchive()

        # add experiment file to archive
        archive.addFile(
            f'{self.path}/experiment.xml',
            "./experiment.xml",
            KnownFormats.lookupFormat("sbml"),
            True
        )

        # add metadata to the experiment file
        location = "./experiment.xml"
        description = OmexDescription()
        description.setAbout(location)
        description.setDescription("EnzymeML model")
        description.setCreated(OmexDescription.getCurrentDateAndTime())

        try:
            for creat in enzmldoc.getCreator():
                creator = VCard()
                creator.setFamilyName(creat.getFname())
                creator.setGivenName(creat.getGname())
                creator.setEmail(creat.getMail())
                description.addCreator(creator)

        except AttributeError:
            pass

        archive.addMetadata(".", description)
        archive.addMetadata(location, description)

        # Add CSV files to archive
        for csvPath, file_path in listofPaths.items():

            self.addFileToArchive(
                archive=archive,
                file_path=csvPath,
                targetPath=file_path,
                format=KnownFormats.lookupFormat("csv"),
                description="Time course data",
            )

        # Add files from fileDict
        tmpFolder = None
        if enzmldoc.getFileDict() != {}:
            # create temporary directory for files
            tmpFolder = tempfile.mkdtemp()

            for fileDict in enzmldoc.getFileDict().values():

                fileContent = fileDict["content"]
                file_name = fileDict["name"]
                fileDescription = fileDict["description"]
                tmpPath = os.path.join(tmpFolder, file_name)

                # Write file locally and add it to the document
                with open(tmpPath, "wb") as fileHandle:
                    fileHandle.write(fileContent)

                self.addFileToArchive(
                    archive=archive,
                    file_path=tmpPath,
                    targetPath=f"./files/{file_name}",
                    format=KnownFormats.guessFormat(file_name),
                    description=fileDescription
                )

        out_file = "%s.omex" % enzmldoc.getName().replace(' ', '_')
        out_path = os.path.join(self.path, out_file)

        try:
            os.remove(out_path)
        except FileNotFoundError:
            pass

        archive.writeToFile(out_path)

        # Remove temporary directory
        if tmpFolder is not None:
            shutil.rmtree(tmpFolder, ignore_errors=True)

        if verbose > 0:
            print('\nArchive created:', out_file, '\n')

    @staticmethod
    def addFileToArchive(
        archive,
        file_path,
        targetPath,
        format,
        description
    ):

        # Add file to archive
        archive.addFile(
            file_path,
            targetPath,
            format,
            False
        )

        # Add metadata to the file
        omexDesc = OmexDescription()
        omexDesc.setAbout(targetPath)
        omexDesc.setDescription(description)
        omexDesc.setCreated(OmexDescription.getCurrentDateAndTime())
        archive.addMetadata(targetPath, omexDesc)

    def setupXMLNode(self, name, namespace=True):
        # Helper function
        # Creates an XML node
        # for annotations
        node = XMLNode(
            XMLTriple(name),
            XMLAttributes(),
            XMLNamespaces()
        )

        if namespace is True:
            node.addNamespace(
                self.namespace,
                "enzymeml"
            )

        return node

    @staticmethod
    def appendAttribute(attributeName, value):
        # Helper function
        # creates XML node
        # <x>XYZ</x>
        value = XMLNode(value)
        attributeNode = XMLNode(
            XMLTriple(attributeName),
            XMLAttributes(),
            XMLNamespaces()
        )

        attributeNode.addChild(value)

        return attributeNode

    def appendMultiAttributes(
        self,
        attributeName,
        object,
        objectMapping,
        annotationNode
    ):
        node = self.setupXMLNode(
            attributeName,
            namespace=False)

        for key, value in objectMapping.items():
            # "value" --> 10.00
            if hasattr(object, value):
                node.addAttr(
                    key,
                    str(getattr(object, value))
                )
            else:
                return 0

        annotationNode.addChild(node)

    def appendOptionalAttribute(
        self,
        attributeName,
        object,
        objectName,
        annotationNode
    ):
        # Helper function
        # Adds elements to annotation node
        if object.__dict__.get(objectName):
            value = self.appendAttribute(
                attributeName,
                getattr(object, objectName)
            )
            annotationNode.addChild(value)

    def __addRefs(self, model: libsbml.Model, enzmldoc):
        """Converts EnzymeMLDocument refrences to SBML.

        Args:
            model (libsbml.Model): The SBML model the reference is added to.
            enzmldoc (EnzymeMLDocument): The EnzymeMLDocument instance that contains the information.
        """

        # Create reference node
        referenceAnnotation = self.setupXMLNode(
            "enzymeml:references"
        )

        # Optional attributes
        referenceAttributes = {
            'enzymeml:doi': 'doi',
            'enzymeml:pubmedID': 'pubmedid',
            'enzymeml:url': 'url'
        }

        for attributeName, objectName in referenceAttributes.items():
            self.appendOptionalAttribute(
                attributeName=attributeName,
                object=enzmldoc,
                objectName=objectName,
                annotationNode=referenceAnnotation
            )

        if referenceAnnotation.getNumChildren() > 0:
            model.appendAnnotation(referenceAnnotation)

    def __addUnits(self, model: libsbml.Model, unit_dict: dict[str, UnitDef]) -> None:
        """Converts EnzymeMLDocument units to SBML.

        Args:
            model (libsbml.Model): The SBML model the units are added to.
            unit_dict (dict[str, UnitDef]): The EnzymeMLDocument units to be added to the SBML model.
        """

        for unit_id, unit_def in unit_dict.items():

            unit = model.createUnitDefinition()
            unit.setId(unit_id)
            unit.setMetaId(unit_def.getMetaid())
            unit.setName(unit_def.getName())

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
                    baseUnitDef.setKind(
                        libsbml.UnitKind_forName(kind)
                    )
                except TypeError:
                    baseUnitDef.setKind(kind)

                baseUnitDef.setExponent(exponent)
                baseUnitDef.setScale(scale)
                baseUnitDef.setMultiplier(multiplier)

    def __addVessel(self, model, vessel_dict: dict[str, Vessel]) -> None:
        """Converts EnzymeMLDocument vessel to SBML.

        Args:
            model (libsbml.Model): The SBML model the vessel is added to.
            vessel (Vessel): The EnzymeMLDocument vessel to be added to the SBML model.
        """

        for vessel_id, vessel in vessel_dict.items():
            compartment = model.createCompartment()
            compartment.setId(vessel_id)
            compartment.setName(vessel.name)
            compartment.setUnits(vessel._unit_id)
            compartment.setSize(vessel.volume)
            compartment.setConstant(vessel.constant)
            compartment.setSpatialDimensions(3)

    def __addProteins(self, model: libsbml.Model, protein_dict: dict[str, Protein]) -> None:
        """Converts EnzymeMLDocument proteins to SBML.

        Args:
            model (libsbml.Model): The SBML model the proteins are added to.
            protein_dict (dict[str, Protein]): The EnzymeMLDocument proteins to be added to the SBML model.
        """

        for protein_id, protein in protein_dict.items():

            species = model.createSpecies()
            species.setId(protein_id)
            species.setName(protein.name)
            species.setMetaId(protein.meta_id)
            species.setSBOTerm(protein.ontology)
            species.setCompartment(protein.vessel_id)
            species.setBoundaryCondition(protein.boundary)
            species.setInitialConcentration(protein.init_conc)
            species.setSubstanceUnits(protein._unit_id)
            species.setConstant(protein.constant)
            species.setHasOnlySubstanceUnits(False)

            # EnzymeML annotation
            proteinAnnotation = self.setupXMLNode('enzymeml:protein')

            # EnzymeML attributes
            proteinAttributes = {
                'enzymeml:sequence': 'sequence',
                'enzymeml:ECnumber': 'ecnumber',
                'enzymeml:uniprotID': 'uniprotid',
                'enzymeml:organism': 'organism'
            }

            for attributeName, objectName in proteinAttributes.items():
                self.appendOptionalAttribute(
                    attributeName=attributeName,
                    object=protein,
                    objectName=objectName,
                    annotationNode=proteinAnnotation
                )

            species.appendAnnotation(proteinAnnotation)

    def __addReactants(self, model: libsbml.Model, reactant_dict: dict[str, Reactant]):
        """Converts EnzymeMLDocument reactants to SBML.

        Args:
            model (libsbml.Model): The SBML model the reactants are added to.
            reactant_dict (dict[str, Reactant]): The EnzymeMLDocument reactants to be added to the SBML model.
        """

        for reactant_id, reactant in reactant_dict.items():

            species = model.createSpecies()
            species.setId(reactant_id)
            species.setName(reactant.name)
            species.setMetaId(reactant.meta_id)
            species.setSBOTerm(reactant.ontology)
            species.setCompartment(reactant.vessel_id)
            species.setBoundaryCondition(reactant.boundary)
            species.setConstant(reactant.constant)
            species.setHasOnlySubstanceUnits(False)
            species.setInitialConcentration(reactant.init_conc)
            species.setSubstanceUnits(reactant._unit_id)

            # Controls if annotation will be added
            reactantAnnotation = self.setupXMLNode('enzymeml:reactant')

            # EnzymeML attributes
            reactantAttributes = {
                'enzymeml:inchi': 'inchi',
                'enzymeml:smiles': 'smiles'
            }

            for attributeName, objectName in reactantAttributes.items():
                self.appendOptionalAttribute(
                    attributeName=attributeName,
                    object=reactant,
                    objectName=objectName,
                    annotationNode=reactantAnnotation
                )

            if reactantAnnotation.getNumChildren() > 0:
                species.appendAnnotation(reactantAnnotation)

    def __addReactions(self, model: libsbml.Model, reaction_dict: dict[str, EnzymeReaction]):
        """Converts EnzymeMLDocument reactions to SBML.

        Args:
            model (libsbml.Model): The SBML model the reactions are added to.
            reaction_dict (dict[str, EnzymeReaction]): The EnzymeMLDocument reactions to be added to the SBML model.
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
                enzyme_reaction.model.addToReaction(reaction)

            # Enzymeml attributes
            reactionAnnotation = self.setupXMLNode('enzymeml:reaction')

            # Track conditions
            conditionsAnnotation = self.setupXMLNode(
                'enzymeml:conditions',
                namespace=False
            )

            conditionsMapping = {
                'enzymeml:temperature': {
                    'value': 'temperature',
                    'unit': 'temperature_unit_id'
                },
                'enzymeml:ph': {
                    'value': 'ph'
                }
            }

            for attributeName, objectMapping in conditionsMapping.items():
                self.appendMultiAttributes(
                    attributeName=attributeName,
                    object=enzyme_reaction,
                    objectMapping=objectMapping,
                    annotationNode=conditionsAnnotation
                )

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

            # Finally, add EnzymeML annotations if given
            if conditionsAnnotation.getNumChildren() > 0:
                reactionAnnotation.addChild(conditionsAnnotation)

            reaction.appendAnnotation(reactionAnnotation)

    def writeElements(
        self,
        reaction_elements: list[ReactionElement],
        createFunction: Callable
    ):
        """Writes SpeciesReference elements to the SBML document.

        Args:
            reaction_elements (list[ReactionElement]): List of reaction elements containing information on stoichiometry, species_id and ontology.
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

    def writeReplicateData(
        self,
        replicate: Replicate,
        format_annot: XMLNode
    ) -> None:
        """Writes column information to the enzymeml:format annotation.

        Args:
            replicate (Replicate): Replicate holding the time course data.
            format_annot (XMLNode): The enzymeml:format annotation node.
        """

        column = self.setupXMLNode(
            'enzymeml:column',
            namespace=False
        )

        # Add attributes
        column.addAttr('replica', replicate.replicate_id)
        column.addAttr('species', replicate.reactant_id)
        column.addAttr('type', replicate.data_type)
        column.addAttr('unit', replicate._data_unit_id)
        column.addAttr('index', str(self.index))
        column.addAttr('isCalculated', str(replicate.is_calculated))

        # Add colum to format annotation
        format_annot.addChild(column)

    def __addData(
        self,
        model: libsbml.Model,
        measurement_dict: dict[str, Measurement]
    ) -> dict[str, str]:
        """Adds measurement data to the SBML document and writes time course data to DataFrames/CSV.

        Args:
            model (libsbml.Model): The SBML model to which the measurements are added.
            measurement_dict (dict[str, Measurement]): The EnzymeMLDocument measurement data.

        Returns:
            dict[str, str]: Mapping from actual CSV paths to the ones added to the OMEX
        """

        # Initialize data lists
        data_annotation = self.setupXMLNode('enzymeml:data')
        files = self.setupXMLNode(
            'enzymeml:files', namespace=False
        )
        formats = self.setupXMLNode(
            'enzymeml:formats', namespace=False
        )
        measurements = self.setupXMLNode(
            'enzymeml:listOfMasurements', namespace=False
        )
        paths = {}

        for index, (measurement_id, measurement) in enumerate(measurement_dict.items()):

            # setup format/Measurement ID/node and file ID
            format_id = f'format{index}'
            file_id = f'file{index}'

            format_annot = self.setupXMLNode(
                'enzymeml:format',
                namespace=False
            )

            format_annot.addAttr('id', format_id)

            measurement_annot = self.setupXMLNode(
                'enzymeml:measurement',
                namespace=False
            )

            # Get time and add to format node
            time = measurement.global_time
            time_unit = measurement.global_time_unit_id

            time_column = XMLNode(
                XMLTriple('enzymeml:column'),
                XMLAttributes()
            )

            time_column.addAttr('type', 'time')
            time_column.addAttr('unit', time_unit)
            time_column.addAttr('index', '0')

            format_annot.addChild(time_column)

            # write initConc annotation and prepare raw data
            data_columns = [time]
            self.index = 1
            data_columns += self.writeMeasurementData(
                measurement=measurement,
                measurement_annot=measurement_annot,
                format_annot=format_annot
            )

            # Create DataFrame to save measurement
            file_name = f'{measurement_id}.csv'
            file_path = f'./data/{file_name}'
            df = pd.DataFrame(data_columns).T

            if self.path:
                df_path = os.path.join(self.path, 'data', file_name)
                df.to_csv(
                    df_path,
                    index=False,
                    header=False
                )

                paths[df_path] = file_path

            # Add data to data annotation
            file_annot = self.setupXMLNode(
                'enzymeml:file',
                namespace=False)

            file_annot.addAttr('file', file_path)
            file_annot.addAttr('format', format_id)
            file_annot.addAttr('id', file_id)

            measurement_annot.addAttr('file', file_id)
            measurement_annot.addAttr('id', measurement_id)
            measurement_annot.addAttr('name', measurement.getName())

            formats.addChild(format_annot)
            files.addChild(file_annot)
            measurements.addChild(measurement_annot)

        # add annotation to listOfReactions
        data_annotation.addChild(formats)
        data_annotation.addChild(files)
        data_annotation.addChild(measurements)

        model.getListOfReactions().appendAnnotation(data_annotation)

        return paths

    def writeMeasurementData(
        self,
        measurement: Measurement,
        measurement_annot: XMLNode,
        format_annot: XMLNode
    ) -> list[list[float]]:
        """Writes measurement metadata as columns to the SBML document annotation enzymeml:column.

        Args:
            measurement (Measurement): EnzymeML measurement that is written to SBML.
            measurement_annot (XMLNode): The SBML XMLNode the measurement metadata is written to.
            format_annot (XMLNode): The SBML XMLNode the column information is written to.

        Returns:
            list[list[float]]: The time course data from the replicate objects.
        """

        speciesDict = measurement.species_dict
        data_columns = []

        # Init Conc
        # Extract measurementData objects
        proteins = speciesDict['proteins']
        reactants = speciesDict['reactants']

        # Append initConc data to measurement
        self.appendInitConcData(
            measurement_annot=measurement_annot,
            measurement_data_dict=proteins, species_type="protein"
        )
        self.appendInitConcData(
            measurement_annot=measurement_annot,
            measurement_data_dict=reactants, species_type="reactant"
        )

        # Replicates
        data_columns += self.appendReplicateData(
            {**proteins, **reactants},
            format_annot=format_annot,
        )

        return data_columns

    def appendInitConcData(
        self,
        measurement_annot: XMLNode,
        measurement_data_dict: dict[str, MeasurementData],
        species_type: str
    ):
        """Adds individual intial concentration data to the enzymeml:measurement annotation.

        Args:
            measurement_annot (XMLNode): The SBML XMLNode for the measurement annotation.
            measurement_data_dict (dict[str, MeasurementData]): The EnzymeMLDocument measurement data.
            species_type (str): The type of species in the measurement_data_dict.
        """

        for species_id, data in measurement_data_dict.items():

            # Create the initConc annotation
            initConcAnnot = self.setupXMLNode(
                'enzymeml:initConc', namespace=False
            )

            initConcAnnot.addAttr(f'{species_type}', species_id)
            initConcAnnot.addAttr('value', str(data.init_conc))
            initConcAnnot.addAttr('unit', data._unit_id)

            measurement_annot.addChild(initConcAnnot)

    def appendReplicateData(
        self,
        species: dict[str, MeasurementData],
        format_annot: XMLNode
    ) -> list[list[float]]:
        """Extracts all time course data from the replicate objects and adds them to the the enzymeml:format annotation.

        Args:
            species (dict[str, MeasurementData]): Reactant/Protein measurement data.
            format_annot (XMLNode): The SBML XMLNode representing the format annotation.

        Returns:
            list[list[float]]: The time course data from the replicate objects.
        """

        # Initialize data columns
        data_columns = []

        # Collect all replicates
        replicates = [
            replicate
            for data in species.values()
            for replicate in data.getReplicates()
        ]

        for replicate in replicates:

            # Write data to format_annot
            self.writeReplicateData(
                replicate=replicate, format_annot=format_annot
            )

            # Extract series data
            data_columns.append(
                replicate.getData(sep=True)[1]
            )

            self.index += 1

        return data_columns
