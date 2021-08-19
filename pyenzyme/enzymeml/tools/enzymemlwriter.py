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

from libsbml import SBMLDocument, CVTerm, XMLNode, XMLTriple, XMLAttributes,\
    XMLNamespaces, SBMLWriter
import libsbml
from libsbml._libsbml import BIOLOGICAL_QUALIFIER, BQB_IS
from libcombine import CombineArchive, OmexDescription, KnownFormats, VCard

from pyenzyme.enzymeml.tools.unitcreator import UnitCreator

import pandas as pd
import os
import shutil
import re


class EnzymeMLWriter(object):

    def __init__(self):
        self.namespace = "http://sbml.org/enzymeml/version1"

    def toFile(self, enzmldoc, path):
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
        doc.setLevelAndVersion(enzmldoc.getLevel(), enzmldoc.getVersion())

        model = doc.createModel()
        model.setName(enzmldoc.getName())
        model.setId(enzmldoc.getName())

        # Add references
        self.__addRefs(model, enzmldoc)

        # Add units
        self.__addUnits(model, enzmldoc)

        # Add Vessel
        self.__addVessel(model, enzmldoc)

        # Add protein
        self.__addProteins(model, enzmldoc)

        # Add reactants
        self.__addReactants(model, enzmldoc)

        # Add reactions
        self.__addReactions(model, enzmldoc)

        # Add data
        listOfPaths = self.__addData(model, enzmldoc)

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
        self.__createArchive(enzmldoc, listOfPaths)

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
        doc.setLevelAndVersion(enzmldoc.getLevel(), enzmldoc.getVersion())

        model = doc.createModel()
        model.setName(enzmldoc.getName())
        model.setId(enzmldoc.getName())

        self.path = None

        # Add references
        self.__addRefs(model, enzmldoc)

        # Add units
        self.__addUnits(model, enzmldoc)

        # Add Vessel
        self.__addVessel(model, enzmldoc)

        # Add protein
        self.__addProteins(model, enzmldoc)

        # Add reactants
        self.__addReactants(model, enzmldoc)

        # Add reactions
        self.__addReactions(model, enzmldoc)

        # Add data
        self.__addData(model, enzmldoc)

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
        doc.setLevelAndVersion(enzmldoc.getLevel(), enzmldoc.getVersion())

        model = doc.createModel()
        model.setName(enzmldoc.getName())
        model.setId(enzmldoc.getName())

        # Add references
        self.__addRefs(model, enzmldoc)

        # Add units
        self.__addUnits(model, enzmldoc)

        # Add Vessel
        self.__addVessel(model, enzmldoc)

        # Add protein
        self.__addProteins(model, enzmldoc)

        # Add reactants
        self.__addReactants(model, enzmldoc)

        # Add reactions
        self.__addReactions(model, enzmldoc, csv=False)

        return doc

    def __createArchive(self, enzmldoc, listofPaths):

        archive = CombineArchive()

        # add experiment file to archive
        archive.addFile(
            self.path + '/experiment.xml',
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

        for csvPath, filePath in listofPaths.items():

            # Add file to archive
            archive.addFile(
                csvPath,
                filePath,
                KnownFormats.lookupFormat("csv"),
                False
            )

            # add metadata to the csv file
            location = filePath
            description = OmexDescription()
            description.setAbout(location)
            description.setDescription("EnzymeML Time Course Data")
            description.setCreated(OmexDescription.getCurrentDateAndTime())
            archive.addMetadata(location, description)

        # write the archive
        out_file = "%s.omex" % enzmldoc.getName().replace(' ', '_')

        try:
            os.remove(self.path + '/' + out_file)
        except FileNotFoundError:
            pass

        archive.writeToFile(self.path + '/' + out_file)

        print('\nArchive created:', out_file, '\n')

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
        if hasattr(object, objectName):
            value = self.appendAttribute(
                attributeName,
                getattr(object, objectName)
            )
            annotationNode.addChild(value)

    def __addRefs(self, model, enzmldoc):

        # Create reference node
        referenceAnnotation = self.setupXMLNode(
            "enzymeml:references"
        )

        # Optional attributes
        prefix = '_EnzymeMLDocument__'
        referenceAttributes = {
            'enzymeml:doi': prefix + 'doi',
            'enzymeml:pubmedID': prefix + 'pubmedID',
            'enzymeml:url': prefix + 'url'
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

    def __addUnits(self, model, enzmldoc):

        for unitID, unitDef in enzmldoc.getUnitDict().items():

            unit = model.createUnitDefinition()
            unit.setId(unitID)
            unit.setMetaId(unitDef.getMetaid())
            unit.setName(unitDef.getName())

            # Add ontology
            cvterm = CVTerm()
            cvterm.addResource(unitDef.getOntology())
            cvterm.setQualifierType(BIOLOGICAL_QUALIFIER)
            cvterm.setBiologicalQualifierType(BQB_IS)
            unit.addCVTerm(cvterm)

            for baseUnit in unitDef.getUnits():

                kind = baseUnit[0]
                exponent = baseUnit[1]
                scale = baseUnit[2]
                multiplier = baseUnit[3]

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

    def __addVessel(self, model, enzmldoc):

        vessel = enzmldoc.getVessel()

        compartment = model.createCompartment()
        compartment.setId(vessel.getId())
        compartment.setName(vessel.getName())
        compartment.setUnits(vessel.getUnit())
        compartment.setSize(vessel.getSize())
        compartment.setConstant(vessel.getConstant())
        compartment.setSpatialDimensions(3)

    def __addProteins(self, model, enzmldoc):

        for key, protein in enzmldoc.getProteinDict().items():

            species = model.createSpecies()
            species.setId(key)
            species.setName(protein.getName())
            species.setMetaId(protein.getMetaid())
            species.setSBOTerm(protein.getSboterm())
            species.setCompartment(protein.getVessel())
            species.setBoundaryCondition(protein.getBoundary())
            species.setInitialConcentration(protein.getInitConc())
            species.setSubstanceUnits(protein.getSubstanceUnits())
            species.setConstant(protein.getConstant())
            species.setHasOnlySubstanceUnits(False)

            # EnzymeML annotation
            proteinAnnotation = self.setupXMLNode('enzymeml:protein')

            # EnzymeML attributes
            prefix = "_Protein__"
            proteinAttributes = {
                'enzymeml:sequence': prefix + 'sequence',
                'enzymeml:ECnumber': prefix + 'ecnumber',
                'enzymeml:uniprotID': prefix + 'uniprotID',
                'enzymeml:organism': prefix + 'organism'
            }

            for attributeName, objectName in proteinAttributes.items():
                self.appendOptionalAttribute(
                    attributeName=attributeName,
                    object=protein,
                    objectName=objectName,
                    annotationNode=proteinAnnotation
                )

            species.appendAnnotation(proteinAnnotation)

    def __addReactants(self, model, enzmldoc):

        for key, reactant in enzmldoc.getReactantDict().items():

            species = model.createSpecies()
            species.setId(key)
            species.setName(reactant.getName())
            species.setMetaId(reactant.getMetaid())
            species.setSBOTerm(reactant.getSboterm())
            species.setCompartment(reactant.getVessel())
            species.setBoundaryCondition(reactant.getBoundary())
            species.setConstant(reactant.getConstant())
            species.setHasOnlySubstanceUnits(False)

            if reactant.getInitConc() > 0:
                species.setInitialConcentration(reactant.getInitConc())
            if reactant.getSubstanceUnits() != 'NAN':
                species.setSubstanceUnits(reactant.getSubstanceUnits())

            # Controls if annotation will be added
            reactantAnnotation = self.setupXMLNode('enzymeml:reactant')

            # EnzymeML attributes
            prefix = "_Reactant__"
            reactantAttributes = {
                'enzymeml:inchi': prefix + 'inchi',
                'enzymeml:smiles': prefix + 'smiles'
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

    @staticmethod
    def __setInitConc(concValue, concUnit, enzmldoc):
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
                    return concID
                index += 1

        else:
            return [
                key for key, item in enzmldoc.getConcDict().items()
                if concTuple == item
            ][0]

    def __addReactions(self, model, enzmldoc):

        for enzymeReaction in enzmldoc.getReactionDict().values():

            reaction = model.createReaction()
            reaction.setId(enzymeReaction.getId())
            reaction.setMetaId(enzymeReaction.getMetaid())
            reaction.setName(enzymeReaction.getName())
            reaction.setReversible(enzymeReaction.getReversible())

            # Add kinetic model
            try:
                enzymeReaction.getModel().addToReaction(reaction)
            except AttributeError:
                pass

            # Enzymeml attributes
            reactionAnnotation = self.setupXMLNode('enzymeml:reaction')

            # Track conditions
            conditionsAnnotation = self.setupXMLNode(
                'enzymeml:conditions',
                namespace=False
            )

            prefix = '_EnzymeReaction__'
            conditionsMapping = {
                'enzymeml:temperature': {
                    'value': prefix + 'temperature',
                    'unit': prefix + 'tempunit'
                },
                'enzymeml:ph': {
                    'value': prefix + 'ph'
                }
            }

            for attributeName, objectMapping in conditionsMapping.items():
                self.appendMultiAttributes(
                    attributeName=attributeName,
                    object=enzymeReaction,
                    objectMapping=objectMapping,
                    annotationNode=conditionsAnnotation
                )

            # Write educts
            self.writeElements(
                elementTuples=enzymeReaction.getEducts(),
                createFunction=reaction.createReactant
            )

            # Write products
            self.writeElements(
                elementTuples=enzymeReaction.getProducts(),
                createFunction=reaction.createProduct
            )

            # Write modifiers
            self.writeElements(
                elementTuples=enzymeReaction.getModifiers(),
                createFunction=reaction.createModifier
            )

            # Finally, add EnzymeML annotations if given
            if conditionsAnnotation.getNumChildren() > 0:
                reactionAnnotation.addChild(conditionsAnnotation)

            reaction.appendAnnotation(reactionAnnotation)

    def writeElements(
        self,
        elementTuples,
        createFunction
    ):

        for species, stoich, isConstant in elementTuples:

            speciesRef = createFunction()
            speciesRef.setSpecies(species)

            try:
                # Catch modifiers --> No stoich/constant in SBML
                speciesRef.setStoichiometry(stoich)
                speciesRef.setConstant(isConstant)
            except AttributeError:
                pass

    def writeReplicateData(
        self,
        replicate,
        formatAnnot
    ):
        # Helper function
        # Creates column annot
        # for replicate object

        column = self.setupXMLNode(
            'enzymeml:column',
            namespace=False
        )

        # Add attributes
        column.addAttr('replica', replicate.getReplica())
        column.addAttr('species', replicate.getReactant())
        column.addAttr('type', replicate.getType())
        column.addAttr('unit', replicate.getDataUnit())
        column.addAttr('index', str(self.index))
        column.addAttr('isCalculated', str(replicate.getIsCalculated()))

        # Add colum to format annotation
        formatAnnot.addChild(column)

    def __addData(
        self,
        model,
        enzmldoc
    ):

        # Initialize data lists
        dataAnnotation = self.setupXMLNode('enzymeml:data')
        listOfFiles = self.setupXMLNode(
            'enzymeml:listOfFiles', namespace=False
        )
        listOfFormats = self.setupXMLNode(
            'enzymeml:listOfFormats', namespace=False
        )
        listOfMeasurements = self.setupXMLNode(
            'enzymeml:listOfMasurements', namespace=False
        )
        listOfPaths = dict()

        measurementDict = enzmldoc.getMeasurementDict()
        for Index, (measurementID, measurement) in enumerate(measurementDict.items()):

            # setup format/Measurement ID/node and file ID
            formatID = f'format{Index}'
            fileID = f'file{Index}'

            formatAnnot = self.setupXMLNode(
                'enzymeml:format',
                namespace=False
            )

            formatAnnot.addAttr('id', formatID)

            measurementAnnot = self.setupXMLNode(
                'enzymeml:measurement',
                namespace=False
            )

            # Get time and add to format node
            time = measurement.getGlobalTime()
            timeUnit = measurement.getGlobalTimeUnit()

            timeColumn = XMLNode(
                XMLTriple('enzymeml:column'),
                XMLAttributes()
            )

            timeColumn.addAttr('type', 'time')
            timeColumn.addAttr('unit', timeUnit)
            timeColumn.addAttr('index', '0')

            formatAnnot.addChild(timeColumn)

            # write initConc annotation and prepare raw data
            dataColumns = [time]
            self.index = 1
            dataColumns += self.writeMeasurementData(
                measurement=measurement,
                measurementAnnot=measurementAnnot,
                formatAnnot=formatAnnot
            )

            # Create DataFrame to save measurement
            fileName = f'{measurementID}.csv'
            filePath = f'./data/{fileName}'
            df = pd.DataFrame(dataColumns).T

            if self.path:
                dfPath = os.path.join(self.path, 'data', fileName)
                df.to_csv(
                    dfPath,
                    index=False,
                    header=False
                )

                listOfPaths[dfPath] = filePath

            # Add data to data annotation
            fileAnnot = self.setupXMLNode(
                'enzymeml:file',
                namespace=False)

            fileAnnot.addAttr('file', filePath)
            fileAnnot.addAttr('format', formatID)
            fileAnnot.addAttr('id', fileID)

            measurementAnnot.addAttr('file', fileID)
            measurementAnnot.addAttr('id', measurementID)
            measurementAnnot.addAttr('name', measurement.getName())

            listOfFormats.addChild(formatAnnot)
            listOfFiles.addChild(fileAnnot)
            listOfMeasurements.addChild(measurementAnnot)

        # add annotation to listOfReactions
        dataAnnotation.addChild(listOfFormats)
        dataAnnotation.addChild(listOfFiles)
        dataAnnotation.addChild(listOfMeasurements)

        model.getListOfReactions().appendAnnotation(dataAnnotation)

        return listOfPaths

    def writeMeasurementData(
        self,
        measurement,
        measurementAnnot,
        formatAnnot
    ):
        reactions = measurement.getReactions().items()
        dataColumns = list()
        for reactionID, reactionObj in reactions:

            # Init Conc
            # Extract measurementData objects
            proteins = reactionObj['proteins']
            reactants = reactionObj['reactants']

            # Append initConc data to measurement
            self.appendInitConcData(
                measurementAnnot=measurementAnnot,
                dictionary=proteins, reactionID=reactionID, speciesType="protein"
            )
            self.appendInitConcData(
                measurementAnnot=measurementAnnot,
                dictionary=reactants, reactionID=reactionID, speciesType="reactant"
            )

            # Replicates
            dataColumns += self.appendReplicateData(
                {**proteins, **reactants},
                formatAnnot=formatAnnot,
            )

        return dataColumns

    def appendReplicateData(self, species, formatAnnot):

        # Initialize data columns
        dataColumns = list()

        # Collect all replicates
        replicates = [
            replicate
            for data in species.values()
            for replicate in data.getReplicates()
        ]

        for replicate in replicates:

            # Write data to formatAnnot
            self.writeReplicateData(
                replicate=replicate, formatAnnot=formatAnnot
            )

            # Extract series data
            dataColumns.append(
                replicate.getData(sep=True)[1]
            )

            self.index += 1

        return dataColumns

    def appendInitConcData(self, measurementAnnot, dictionary, reactionID, speciesType):

        for speciesID, data in dictionary.items():

            # Create the initConc annotation
            initConcAnnot = self.setupXMLNode(
                'enzymeml:initConc', namespace=False
            )

            initConcAnnot.addAttr('reactionID', reactionID)
            initConcAnnot.addAttr(f'{speciesType}ID', speciesID)
            initConcAnnot.addAttr('value', str(data.getInitConc()))
            initConcAnnot.addAttr('unit', data.getUnit())

            measurementAnnot.addChild(initConcAnnot)
