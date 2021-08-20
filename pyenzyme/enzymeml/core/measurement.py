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

from os import sep
from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.functionalities import TypeChecker
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.measurementData import MeasurementData

import json


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
        self.setReactions(dict())

    def toJSON(self, d=False):

        jsonObject = dict()

        jsonObject['name'] = self.__name
        jsonObject['reactions'] = dict()

        if hasattr(self, '_Measurement__globalTime'):
            jsonObject['global-time'] = self.__globalTime
            jsonObject['global-time-unit'] = self.__globalTimeUnit

        for reactionID, reaction in self.__reactions.items():
            self.setGlobalTimeUnit

            proteins = {
                proteinID: proteinData.toJSON()
                for proteinID, proteinData in reaction['proteins'].items()
            }

            reactants = {
                reactantID: reactantData.toJSON()
                for reactantID, reactantData in reaction['reactants'].items()
            }

            jsonObject["reactions"][reactionID] = {
                "reactants": reactants,
                "proteins": proteins
            }

        if d:
            return jsonObject
        else:
            return json.dumps(jsonObject, indent=4)

    def __str__(self):
        return self.toJSON()

    def addReplicates(self, replicates, reactionID):
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

            try:
                reactionData = self.__reactions[reactionID][speciesType]
            except KeyError:
                raise KeyError(
                    f"Reaction {reactionID} is not part of the measurement yet. If a reaction hasnt been yet defined in a measurement object, use the addData method to define metadata first-hand. You can add the replicates in the same function call then."
                )

            try:
                data = reactionData[speciesID]
                data.addReplicate(replicate)
            except KeyError:
                raise KeyError(
                    f"{speciesType[0:-1]} {speciesID} is not part of the measurement yet. If a {speciesType[0:-1]} hasnt been yet defined in a measurement object, use the addData method to define metadata first-hand. You can add the replicates in the same function call then."
                )

    def addData(
        self,
        reactionID,
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

        # Initialize reaction measurement data if not given yet
        if reactionID not in self.__reactions.keys():
            self.__initializeReactionData(
                reactionID=reactionID,
                reactantID=reactantID,
                proteinID=proteinID,
                initConc=initConc,
                unit=unit,
                replicates=replicates
            )

        else:
            self.__appendReactantData(
                reactionID=reactionID,
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
        self.__reactions[reactionID] = {
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
        reactionID,
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

        # Reference reaction ro reduce boilerplate
        reactionRef = self.__reactions[reactionID]

        if reactantID:
            reactionRef['reactants'][reactantID] = measData
        elif proteinID:
            reactionRef['proteins'][proteinID] = measData
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

    def setReactions(self, reactions):
        self.__reactions = TypeChecker(reactions, dict)

    def getReactions(self):
        return self.__reactions

    def delReactions(self):
        del self.__reactions


if __name__ == "__main__":

    repl1 = Replicate(
        replica="repl1",
        reactant="s1",
        reaction="r1",
        type_="conc",
        data_unit="u1",
        time_unit="u2",
        init_conc=10.0
    )

    repl1.setData([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])

    repl2 = Replicate(
        replica="repl2",
        reactant="s2",
        reaction="r1",
        type_="conc",
        data_unit="u1",
        time_unit="u2",
        init_conc=200.0
    )

    meas = Measurement("Test")

    meas.addData(
        reactionID="r1",
        reactantID="s1",
        initConc=10.0,
        unit="u2",
        replicates=[repl1]
    )

    meas.addData(
        reactionID="r1",
        proteinID="p1",
        initConc=10.0,
        unit="u3"
    )

    print(meas)
