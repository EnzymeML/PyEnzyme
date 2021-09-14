'''
File: measurement.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Thursday July 15th 2021 1:19:51 am
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

import json

import numpy as np
import pandas as pd

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pyenzyme.enzymeml.core.measurementData import MeasurementData
from pyenzyme.enzymeml.core.replicate import Replicate
from pprint import pprint


class Measurement(EnzymeMLBase):

    def __init__(
        self,
        name,
        uri=None,
        creatorId=None,
    ):
        super().__init__(uri, creatorId)

        # Initialize attributes
        self.setName(name)
        self.setSpeciesDict({
            "proteins": dict(),
            "reactants": dict()
        })

    def toJSON(self, d=False):

        jsonObject = dict()

        jsonObject['name'] = self.__name

        if hasattr(self, '_Measurement__globalTime'):
            jsonObject['global-time'] = self.__globalTime
            jsonObject['global-time-unit'] = self.__globalTimeUnit

        proteins = {
            proteinID: proteinData.toJSON()
            for proteinID, proteinData in self.__speciesDict['proteins'].items()
        }

        reactants = {
            reactantID: reactantData.toJSON()
            for reactantID, reactantData in self.__speciesDict['reactants'].items()
        }

        jsonObject['reactants'] = reactants
        jsonObject['proteins'] = proteins

        if d:
            return jsonObject
        else:
            return json.dumps(jsonObject, indent=4)

    def __str__(self):
        return self.toJSON()

    def exportData(self):
        """Returns data stored in the measurement object as DataFrames nested in dictionaries. These are sorted hierarchially by reactions where each holds a DataFrame each for proteins and reactants.

        Returns:
            measurements (dict): Follows the hierarchy Reactions > Proteins/Reactants > { initConcs, data }
        """

        # Combine Replicate objects for each reaction
        proteins = self.__combineReplicates(
            measurementSpecies=self.__speciesDict['proteins'],
        )
        reactants = self.__combineReplicates(
            measurementSpecies=self.__speciesDict['reactants'],
        )

        measurements = {
            "proteins": proteins,
            "reactants": reactants
        }

        return measurements

    def __combineReplicates(
        self,
        measurementSpecies
    ):

        # Initialize columns and headers
        columns = [self.__globalTime]
        header = [f"time/{self.__globalTimeUnit}"]
        initConcs = dict()
        stoichiometries = dict()

        # Iterate over measurementData to fill columns
        for speciesID, data in measurementSpecies.items():

            # Fetch replicate data
            for replicate in data.getReplicates():

                columns.append(
                    replicate.getData(sep=True)[1]
                )

                header.append(
                    f"{replicate.getReplica()}/{speciesID}/{replicate.getDataUnit()}"
                )

            # Fetch initial concentration
            initConcs[speciesID] = (data.getInitConc(), data.getUnit())

        if len(columns) > 1:
            return {
                "data": pd.DataFrame(np.array(columns).T, columns=header),
                "initConc": initConcs,
            }

    def addReplicates(self, replicates):
        """Adds a replicate to the corresponding measurementData object. This method is meant to be called if the measurement metadata of a reaction/species has already been done and replicate data has to be added afterwards. If not, use addData instead to introduce the species metadata.

        Args:
            replicate (List<Replicate>): Objects describing time course data
            reactionID (String): Reaction identifier where the data is added to.
        """

        # Check if just a single Replicate has been handed
        if isinstance(replicates, Replicate):
            replicates = [replicates]

        for replicate in replicates:

            # Check for the species type
            speciesID = replicate.getReactant()
            speciesType = "reactants" if speciesID[0] == "s" else "proteins"
            speciesData = self.__speciesDict[speciesType]

            try:

                data = speciesData[speciesID]
                data.addReplicate(replicate)

                if hasattr(self, "_Measurement__globalTime") is False:

                    # Add global time if this is the first replicate to be added
                    self.setGlobalTime(replicate.getData(sep=True)[0])
                    self.setGlobalTimeUnit(replicate.getTimeUnit())

            except KeyError:
                raise KeyError(
                    f"{speciesType[0:-1]} {speciesID} is not part of the measurement yet. If a {speciesType[0:-1]} hasnt been yet defined in a measurement object, use the addData method to define metadata first-hand. You can add the replicates in the same function call then."
                )

    def addData(
        self,
        initConc,
        unit,
        reactantID=None,
        proteinID=None,
        replicates=list()
    ):
        """Adds data via reaction ID to the measurement class.

        Args:
            reactionID (string): Identifier of the reaction that the measurement refers toself.
            reactantID (string): Identifier of the reactant/protein that has been measured.
            initConcValue (float): Numeric value of the initial concentration
            initConcUnit (string): UnitID of the initial concentration
            replicates (list<Replicate>, optional): List of actual time-coiurse data in Replicate objects. Defaults to None.
        """

        self.__appendReactantData(
            reactantID=reactantID,
            proteinID=proteinID,
            initConc=initConc,
            unit=unit,
            replicates=replicates
        )

    def __initializeReactionData(
        self,
        reactionID,
        reactantID,
        proteinID,
        initConc,
        unit,
        replicates
    ):

        # initialiaze reaction data structure to add data
        self.__speciesDict[reactionID] = {
            'reactants': dict(),
            'proteins': dict()
        }

        # Add data to matching species (reactant/protein)
        self.__appendReactantData(
            reactionID=reactionID,
            reactantID=reactantID,
            proteinID=proteinID,
            initConc=initConc,
            unit=unit,
            replicates=replicates
        )

        if replicates:
            # Set the measurements global time with
            # the initial measurement point
            self.setGlobalTime(replicates[0].getData(sep=True)[0])
            self.setGlobalTimeUnit(replicates[0].getTimeUnit())

    def __appendReactantData(
        self,
        reactantID,
        proteinID,
        initConc,
        unit,
        replicates
    ):

        # Create measurement data class before sorting
        measData = MeasurementData(
            reactantID=reactantID,
            proteinID=proteinID,
            initConc=initConc,
            unit=unit,
            replicates=self.__updateReplicates(replicates, initConc)
        )

        if reactantID:
            self.__speciesDict['reactants'][reactantID] = measData
        elif proteinID:
            self.__speciesDict['proteins'][proteinID] = measData
        else:
            raise ValueError(
                "Please enter a reactant or protein ID to add measurement data"
            )

    def __updateReplicates(self, replicates, initConc):

        for replicate in replicates:

            # Check if the initConc given in the replicates matches
            self.__checkReplicate(replicate, initConc)

            # Set the measurement name for the replicate
            replicate.setMeasurement(self.__name)

        return replicates

    def __checkReplicate(self, replicate, initConc):
        if replicate.getInitConc() != initConc:
            raise ValueError(
                f"The given concentration value of replicate {replicate.getInitConc()} does not match the measurement object's value of {initConc}. Please make sure to only add replicates, which share the same initial concentration. If you like to track different initial concentrations, create a new measurement object, since these are fixed per measurement object."
            )

    def setId(self, ID):
        self.__id = TypeChecker(ID, str)

        self.__setReplicateMeasIDs()

    def __setReplicateMeasIDs(self):

        for measData in self.__speciesDict['proteins'].values():
            measData.setMeasurementIDs(self.__id)

        for measData in self.__speciesDict['reactants'].values():
            measData.setMeasurementIDs(self.__id)

    def getId(self):
        return self.__id

    def delId(self):
        del self.__id

    def setGlobalTimeUnit(self, unit):
        self.__globalTimeUnit = TypeChecker(unit, str)

    def getGlobalTimeUnit(self):
        return self.__globalTimeUnit

    def delGlobalTimeUnit(self):
        del self.__globalTimeUnit

    def setGlobalTime(self, time):
        self.__globalTime = TypeChecker(time, list)

    def getGlobalTime(self):
        return self.__globalTime

    def delGlobalTime(self):
        del self.__globalTime

    def setName(self, name):
        self.__name = name

    def getName(self):
        return self.__name

    def delName(self):
        del self.__name

    def setSpeciesDict(self, reactions):
        self.__speciesDict = TypeChecker(reactions, dict)

    def getSpeciesDict(self):
        return self.__speciesDict

    def delSpeciesDict(self):
        del self.__speciesDict

    def getReactant(self, reactantID):
        """Returns a single MeasurementData object for the given reactantID.

        Args:
            reactantID (String): Unqiue identifier of the reactant

        Returns:
            MeasurementData: Object representing the data and initial concentration
        """
        return self.__getSpecies(reactantID, "reactants")

    def getProtein(self, proteinID):
        """Returns a single MeasurementData object for the given proteinID.

        Args:
            reactantID (String): Unqiue identifier of the protein

        Returns:
            MeasurementData: Object representing the data and initial concentration
        """
        return self.__getSpecies(proteinID, "proteins")

    def getReactants(self):
        """Returns a list of all participating reactants in the measurement.

        Returns:
            list: List of MeasurementData objects representing data
        """
        return self.__speciesDict["reactants"]

    def getProteins(self):
        """Returns a list of all participating proteins in the measurement.

        Returns:
            list: List of MeasurementData objects representing data
        """
        return self.__speciesDict["proteins"]

    def __getSpecies(self, speciesID, type_):
        TypeChecker(speciesID, str)
        TypeChecker(type_, str)

        try:
            return self.__speciesDict[type_][speciesID]
        except KeyError:
            raise KeyError(
                f"{type_[0:-1]}ID {speciesID} is not defined yet. Please use the addData method to add the corresponding {type_[0:-1]}"
            )
