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

import json


class Measurement(EnzymeMLBase):

    def __init__(
        self,
        name,
        reactants=dict(),
        proteins=dict(),
        replicates=dict(),
        uri=None,
        creatorId=None,
    ):
        super().__init__(uri, creatorId)

        # Initialize attributes
        self.setName(name)
        self.setReactants(reactants)
        self.setProteins(proteins)
        self.addReplicates(replicates)

    def addReplicates(self, replicates):
        if not isinstance(replicates, list):
            replicates = [replicates]

        self.__updateReactants(replicates)

    def __updateReactants(self, replicates):
        for replicate in replicates:
            replicate = TypeChecker(replicate, Replicate)
            reactantID = replicate.getReactant()
            replicateConcValue = replicate.getInitConc()
            replicateUnit = replicate.getDataUnit()

            # Check if the reactantID is already defined
            if reactantID in self.__reactants.keys():

                reactantConcValue, reactantConcUnit = self.__reactants[
                    reactantID
                ]["initConc"]

                # Check if initConc matches
                if replicateConcValue == reactantConcValue:

                    self.__reactants[reactantID]["replicates"].append(
                        replicate)

                else:

                    raise KeyError(
                        f"Replicate {replicate.getReplica()} initConc {replicateConcValue} doesnt match."
                    )

            else:

                raise KeyError(
                    f"Reactant {reactantID} is not defined in the measurement."
                )

    def setName(self, name):
        self.__name = TypeChecker(name, str)

    def getName(self):
        return self.__name

    def delName(self):
        del self.__name

    def setReactants(self, reactants):
        self.__reactants = TypeChecker(reactants, dict)
        self.__checkObjectCompliance(self.__reactants)

    def __checkObjectCompliance(self, elementDict):

        for key, item in elementDict.items():
            if "initConc" not in item.keys():
                raise KeyError(
                    f"Please specify an initial concentration for the element {key}"
                )
            if "replicates" not in item.keys():
                elementDict[key]["replicates"] = list()

        print(elementDict)

    def getReactants(self):
        return self.__reactants

    def delReactants(self):
        del self.__reactants

    def setProteins(self, proteins):
        self.__proteins = TypeChecker(proteins, dict)
        self.__checkObjectCompliance(self.__proteins)

    def getProteins(self):
        return self.__proteins

    def delProteins(self):
        del self.__proteins


if __name__ == "__main__":

    repl1 = Replicate(
        replica="repl1",
        reactant="s1",
        type_="conc",
        data_unit="u1",
        time_unit="u2",
        init_conc=10.0
    )

    repl2 = Replicate(
        replica="repl2",
        reactant="s2",
        type_="conc",
        data_unit="u1",
        time_unit="u2",
        init_conc=200.0
    )

    repls = [repl1, repl2]
    reactants = {
        "s1": {
            "initConc": (10.0, "u2")
        },
        "s2": {
            "initConc": (200.0, "u1")
        }
    }

    proteins = {
        "p1": {
            "initConc": (100.0, "u2")
        }
    }

    meas = Measurement(
        "Test",
        reactants=reactants,
        proteins=proteins,
        replicates=repls
    )

    def toJSON(object, d=True):

        d = dict()

        for key, item in object.__dict__.items():
            key = key.split('__')[-1]

            if key == "reactants" or key == "proteins":
                elementDict = dict()
                for elementID, elementItem in item.items():

                    elementDict[elementID] = dict()

                    concValue, concUnit = elementItem["initConc"]
                    elementDict[elementID]["initConc"] = {
                        "value": concValue,
                        "unit": concUnit
                    }

                    if "replicates" in elementItem.keys():
                        replicates = [
                            replicate.toJSON(d=True)
                            for replicate in elementItem["replicates"]
                        ]
                        elementDict[elementID]["replicates"] = replicates

                d[key] = elementDict

            else:
                d[key] = item

        return d

    print(
        json.dumps(toJSON(meas), indent=4)
    )
