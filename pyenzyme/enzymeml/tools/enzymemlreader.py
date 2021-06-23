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

from pyenzyme.enzymeml.core.creator import Creator
from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction

from libsbml import SBMLReader
import xml.etree.ElementTree as ET
import pandas as pd
from pyenzyme.enzymeml.models.kineticmodel import KineticModel
from libcombine import CombineArchive
from _io import StringIO


class EnzymeMLReader():

    def readFromFile(
        self,
        path
    ):
        '''
        Reads EnzymeML document to an object layer EnzymeMLDocument class.

        Args:
            String path: Path to .omex container or
                         folder destination for plain .xml
        '''

        # Read omex archive
        self.__path = path
        self.archive = CombineArchive()
        self.archive.initializeFromArchive(self.__path)

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
            model.getName(),
            model.getLevel(),
            model.getVersion()
        )

        # Fetch references
        self.__getRefs(model, enzmldoc)

        # Fetch Creators
        numCreators = desc.getNumCreators()
        creators = list()
        for i in range(numCreators):
            creator = desc.getCreator(i)
            creators.append(
                Creator(
                    creator.getFamilyName(),
                    creator.getGivenName(),
                    creator.getEmail()
                )
            )

        enzmldoc.setCreator(creators)

        try:
            # TODO extract VCard
            model_hist = model.getModelHistory()
            enzmldoc.setCreated(
                model_hist.getCreatedDate().getDateAsString()
            )

            enzmldoc.setModified(
                model_hist.getModifiedDate().getDateAsString()
            )

        except AttributeError:
            enzmldoc.setCreated("2020")
            enzmldoc.setModified("2020")

        # Fetch units
        unitDict = self.__getUnits(model)
        enzmldoc.setUnitDict(unitDict)

        # Fetch Vessel
        vessel = self.__getVessel(model)
        enzmldoc.setVessel(vessel, use_parser=False)

        # Fetch Species
        proteinDict, reactantDict = self.__getSpecies(model)
        enzmldoc.setReactantDict(reactantDict)
        enzmldoc.setProteinDict(proteinDict)

        # fetch reaction
        reactionDict = self.__getReactions(model, enzmldoc)
        enzmldoc.setReactionDict(reactionDict)

        del self.__path

        return enzmldoc

    def __getRefs(self, model, enzmldoc):

        if len(model.getAnnotationString()) > 0:
            root = ET.fromstring(
                model.getAnnotationString()
            )[0]

            for elem in root:
                if "doi" in elem.tag:
                    enzmldoc.setDoi(elem.text)
                elif 'pubmedID' in elem.tag:
                    enzmldoc.setPubmedID(elem.text)
                elif 'url' in elem.tag:
                    enzmldoc.setUrl(elem.text)

    def __getCreators(self, model):

        model_hist = model.getModelHistory()
        creator_list = model_hist.getListCreators()
        creators = list()

        for creator in creator_list:

            creators.append(

                Creator(
                    creator.getFamilyName(),
                    creator.getGivenName(),
                    creator.getEmail()
                )

            )

        return creators

    def __getUnits(self, model):

        unitDict = dict()
        unitdef_list = model.getListOfUnitDefinitions()

        for unit in unitdef_list:

            name = unit.getName()
            id_ = unit.getId()
            metaid = unit.getMetaId()
            ontology = unit.getCVTerms()[0].getResourceURI(0)

            unitdef = UnitDef(name, id_, ontology)
            unitdef.setMetaid(metaid)

            for baseunit in unit.getListOfUnits():

                unitdef.addBaseUnit(

                    baseunit.toXMLNode().getAttrValue('kind'),
                    baseunit.getExponentAsDouble(),
                    baseunit.getScale(),
                    baseunit.getMultiplier()

                    )

            unitDict[id_] = unitdef

        return unitDict

    def __getVessel(self, model):

        compartment = model.getListOfCompartments()[0]

        vessel = Vessel(
            compartment.getName(),
            compartment.getId(),
            compartment.getSize(),
            compartment.getUnits()
        )

        return vessel

    @staticmethod
    def __parseAnnotation(annotationString):
        # __getSpecies helper function
        # extracts annotations to dict
        speciesAnnot = ET.fromstring(
            annotationString
        )[0]

        # Initialize annotation dictionary
        annotDict = dict()

        # fetch attributes from both types of species
        speciesType = speciesAnnot.tag.split('}')[-1]

        for enzymeMLAnnot in speciesAnnot:
            key = enzymeMLAnnot.tag.split('}')[-1].lower()
            attribute = enzymeMLAnnot.text

            annotDict[key] = attribute

        return speciesType, annotDict

    def __getSpecies(self, model):

        proteinDict = dict()
        reactantDict = dict()
        speciesList = model.getListOfSpecies()

        for species in speciesList:

            # get Annotations
            speciesType, annotDict = self.__parseAnnotation(
                species.getAnnotationString()
            )

            if speciesType == 'protein':
                protein = Protein(
                            name=species.getName(),
                            vessel=species.getCompartment(),
                            init_conc=species.getInitialConcentration(),
                            substanceunits=species.getSubstanceUnits(),
                            constant=species.getConstant(),
                            **annotDict
                        )

                # Set IDs manually
                protein.setId(species.getId())
                protein.setMetaid(species.getMetaId())

                # Add to document
                proteinDict[species.getId()] = protein

            elif speciesType == 'reactant':

                reactant = Reactant(
                            name=species.getName(),
                            vessel=species.getCompartment(),
                            init_conc=species.getInitialConcentration(),
                            substanceunits=species.getSubstanceUnits(),
                            constant=species.getConstant(),
                            **annotDict
                        )

                # Set IDs manually
                reactant.setMetaid(species.getMetaId())
                reactant.setId(species.getId())

                reactantDict[species.getId()] = reactant

        return proteinDict, reactantDict

    @staticmethod
    def __getInitConcs(specref, enzmldoc):

        if len(specref.getAnnotationString()) == 0:
            # Check if there are any initConcs
            return list()

        initConcAnnot = ET.fromstring(specref.getAnnotationString())[0]
        initConcs = list()

        for initConc in initConcAnnot:

            value = float(initConc.attrib['value'])
            initConcID = initConc.attrib['id']
            unit = initConc.attrib['unit']

            enzmldoc.getConcDict()[initConcID] = (value, unit)
            initConcs.append((value, unit))

        return initConcs

    @staticmethod
    def __parseConditions(reactionAnnot):

        conditions = reactionAnnot[0]
        conditionDict = dict()

        for condition in conditions:

            if 'temperature' in condition.tag:
                conditionDict['temperature'] = float(condition.attrib['value'])
                conditionDict['tempunit'] = condition.attrib['unit']
            elif 'ph' in condition.tag:
                conditionDict['ph'] = float(condition.attrib['value'])

        return conditionDict

    @staticmethod
    def __parseReactionReplicates(reactionAnnot, allReplicates):

        try:
            replicateAnnot = reactionAnnot[1]
        except IndexError:
            replicateAnnot = []

        reactionReplicates = dict()

        for replicate in replicateAnnot:

            replicateID = replicate.attrib['replica']
            replicate = allReplicates[replicateID]
            speciesID = replicate.getReactant()

            if speciesID in reactionReplicates.keys():
                reactionReplicates[speciesID].append(
                    replicate
                )
            else:
                reactionReplicates[speciesID] = \
                    [replicate]

        return reactionReplicates

    def __getElements(
        self,
        speciesRefs,
        reactionReplicates,
        enzmldoc,
        modifiers=False
    ):
        elements = list()
        for speciesRef in speciesRefs:

            speciesID = speciesRef.getSpecies()
            stoichiometry = 1.0 if modifiers else speciesRef.getStoichiometry()
            constant = True if modifiers else speciesRef.getConstant()
            initConcs = self.__getInitConcs(speciesRef, enzmldoc)

            if speciesID in reactionReplicates.keys():
                replicates = reactionReplicates[speciesID]
            else:
                replicates = list()

            elements.append(
                (
                    speciesID,
                    stoichiometry,
                    constant,
                    replicates,
                    initConcs
                )
            )

        return elements

    @staticmethod
    def __getKineticModel(kineticLaw, enzmldoc):

        equation = kineticLaw.getFormula()
        parameters = {
            localParam.getId():
            (
                localParam.getValue(),
                localParam.getUnits()
                )
            for localParam in
            kineticLaw.getListOfLocalParameters()
                }

        return KineticModel(
            equation=equation,
            parameters=parameters,
            enzmldoc=enzmldoc
        )

    def __getReactions(self, model, enzmldoc):

        reactionsList = model.getListOfReactions()
        allReplicates = self.__getReplicates(reactionsList)

        # Initialize reaction dictionary
        reactionDict = dict()

        # parse annotations and filter replicates
        for reaction in reactionsList:

            reactionAnnot = ET.fromstring(reaction.getAnnotationString())[0]

            # Fetch conditions
            conditions = self.__parseConditions(reactionAnnot)

            # Fetch reaction replicates
            reactionReplicates = self.__parseReactionReplicates(
                reactionAnnot,
                allReplicates
            )

            # Fetch Elements in SpeciesReference
            educts = self.__getElements(
                reaction.getListOfReactants(),
                reactionReplicates,
                enzmldoc
            )

            products = self.__getElements(
                reaction.getListOfProducts(),
                reactionReplicates,
                enzmldoc
            )

            modifiers = self.__getElements(
                reaction.getListOfModifiers(),
                reactionReplicates,
                enzmldoc,
                modifiers=True
            )

            # Create object
            enzymeReaction = EnzymeReaction(
                name=reaction.getName(),
                reversible=reaction.getReversible(),
                educts=educts,
                products=products,
                modifiers=modifiers,
                **conditions
            )

            # Check for kinetic model
            try:
                # Check if model exists
                kineticLaw = reaction.getKineticLaw()
                kineticModel = self.__getKineticModel(kineticLaw, enzmldoc)
                enzymeReaction.setModel(kineticModel)
            except AttributeError:
                pass

            # Add reaction to reactionDict
            enzymeReaction.setId(reaction.getId())
            enzymeReaction.setMetaid(
                'META_' + reaction.getId().upper()
            )
            reactionDict[enzymeReaction.getId()] = enzymeReaction

        return reactionDict

    @staticmethod
    def __parseListOfFiles(dataAnnot):
        # __getReplicates helper function
        # reads file anntations to dict
        fileAnnot = dataAnnot[1]
        files = {
            file.attrib['id']:
            {
                'file': file.attrib['file'],
                'format': file.attrib['format'],
                'id': file.attrib['id']

                } for file in fileAnnot
        }

        return files

    @staticmethod
    def __parseListOfFormats(dataAnnot):
        # __getReplicates helper function
        # reads format anntations to dict
        formatAnnot = dataAnnot[0]
        formats = dict()

        for format in formatAnnot:
            formatID = format.attrib['id']
            format = [
                column.attrib
                for column in format
            ]

            formats[formatID] = format

        return formats

    @staticmethod
    def __parseListOfMeasurements(dataAnnot):
        # __getReplicates helper function
        # reads measurement anntations to
        # tuple list
        measurementAnnot = dataAnnot[2]
        measurements = [
            (
                measurement.attrib['id'],
                measurement.attrib['file'],
                measurement.attrib['name']
            )
            for measurement in measurementAnnot
        ]

        return measurements

    def __getReplicates(self, reactions):

        # Parse EnzymeML:format annotation
        dataAnnot = ET.fromstring(reactions.getAnnotationString())[0]

        # Fetch list of files
        files = self.__parseListOfFiles(dataAnnot)

        # Fetch formats
        formats = self.__parseListOfFormats(dataAnnot)

        # Fetch measurements
        measurements = self.__parseListOfMeasurements(dataAnnot)

        # Initialize replicates dictionary
        replicates = dict()

        # Iterate over measurements and assign replicates
        for measurementID, measurementFile, measurementName in measurements:

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
                    replicateInitConcID = format['initConcID']

                    replicate = Replicate(
                        replica=replicateID,
                        reactant=replicateReactant,
                        type_=replicateType,
                        measurement=measurementID,
                        data_unit=replicateUnitID,
                        time_unit=timeUnitID,
                        init_conc=replicateInitConcID,
                        data=replicateValues.values.tolist(),
                        time=timeValues
                    )

                    replicates[replicateID] = replicate

        return replicates
