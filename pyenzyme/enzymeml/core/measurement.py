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

        for reactionID, reaction in self.__reactions.items():

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
