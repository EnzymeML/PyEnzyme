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

import numpy as np
import pandas as pd

from typing import Optional, Any, TYPE_CHECKING
from dataclasses import dataclass
from pydantic import PositiveFloat, validate_arguments, Field

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.measurementData import MeasurementData
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.exceptions import SpeciesNotFoundError
from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class Measurement(EnzymeMLBase):

    name: str = Field(
        description="Name of the measurement",
        required=True
    )

    species_dict: dict[str, dict[str, MeasurementData]] = Field(
        default={"proteins": {}, "reactants": {}},
        description="Species of the measurement.",
        required=True
    )

    global_time: list[float] = Field(
        default_factory=list,
        description="Global time of the measurement all replicates agree on.",
        required=True
    )

    global_time_unit: Optional[str] = Field(
        default=None,
        description="Unit of the global time.",
        required=True,
    )

    global_time_unit_id: Optional[str] = Field(
        default=None,
        description="Unique internal identifier of the global time unit.",
        required=False,
    )

    id: Optional[str] = Field(
        description="Unique identifier of the measurement.",
        required=True,
        regex=r"m[\d]+"
    )

    uri: Optional[str] = Field(
        default=None,
        description="URI of the reaction.",
        required=False
    )

    creator_id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the author.",
        required=False
    )

    # Utility methods
    def exportData(self) -> dict[str, dict[str, Any]]:
        """Returns data stored in the measurement object as DataFrames nested in dictionaries. These are sorted hierarchially by reactions where each holds a DataFrame each for proteins and reactants.

        Returns:
            measurements (dict): Follows the hierarchy Reactions > Proteins/Reactants > { initConcs, data }
        """

        # Combine Replicate objects for each reaction
        proteins = self.__combineReplicates(
            measurement_species=self.species_dict['proteins'],
        )
        reactants = self.__combineReplicates(
            measurement_species=self.species_dict['reactants'],
        )

        return {
            "proteins": proteins,
            "reactants": reactants
        }

    def __combineReplicates(
        self,
        measurement_species: dict[str, MeasurementData]
    ) -> dict[str, Any]:

        # Initialize columns and headers
        columns = [self.global_time]
        header = [f"time/{self.global_time_unit}"]
        initConcs = {}

        # Iterate over measurementData to fill columns
        for speciesID, data in measurement_species.items():

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

        return {
            "data": pd.DataFrame(np.array(columns).T, columns=header)
            if len(columns) > 1
            else None,
            "initConc": initConcs,
        }

    @validate_arguments
    def addReplicates(self, replicates: list[Replicate]) -> None:
        """Adds a replicate to the corresponding measurementData object. This method is meant to be called if the measurement metadata of a reaction/species has already been done and replicate data has to be added afterwards. If not, use addData instead to introduce the species metadata.

        Args:
            replicate (List<Replicate>): Objects describing time course data
        """

        # Check if just a single Replicate has been handed
        if isinstance(replicates, Replicate):
            replicates = [replicates]

        for replicate in replicates:

            # Check for the species type
            speciesID = replicate.getReactant()
            speciesType = "reactants" if speciesID[0] == "s" else "proteins"
            speciesData = self.species_dict[speciesType]

            try:

                data = speciesData[speciesID]
                data.addReplicate(replicate)

                if len(self.global_time) == 0:

                    # Add global time if this is the first replicate to be added
                    self.global_time = replicate.getData(sep=True)[0]
                    self.global_time_unit = (replicate.getTimeUnit())

            except KeyError:
                raise KeyError(
                    f"{speciesType[0:-1]} {speciesID} is not part of the measurement yet. If a {speciesType[0:-1]} hasnt been yet defined in a measurement object, use the addData method to define metadata first-hand. You can add the replicates in the same function call then."
                )

    @validate_arguments
    def addData(
        self,
        init_conc: PositiveFloat,
        unit: str,
        reactant_id: Optional[str] = None,
        protein_id: Optional[str] = None,
        replicates: list[Replicate] = []
    ) -> None:
        """Adds data via reaction ID to the measurement class.

        Args:
            reactant_id (string): Identifier of the reactant/protein that has been measured.
            init_concValue (float): Numeric value of the initial concentration
            init_concUnit (string): UnitID of the initial concentration
            replicates (list<Replicate>, optional): List of actual time-coiurse data in Replicate objects. Defaults to None.
        """

        self.__appendReactantData(
            reactant_id=reactant_id,
            protein_id=protein_id,
            init_conc=init_conc,
            unit=unit,
            replicates=replicates
        )

    def __appendReactantData(
        self,
        reactant_id: Optional[str],
        protein_id: Optional[str],
        init_conc: PositiveFloat,
        unit: str,
        replicates: list[Replicate]
    ) -> None:

        # Create measurement data class before sorting
        measData = MeasurementData(
            reactant_id=reactant_id,
            protein_id=protein_id,
            init_conc=init_conc,
            unit=unit,
            replicates=replicates
        )

        if reactant_id:
            self.species_dict['reactants'][reactant_id] = measData
        elif protein_id:
            self.species_dict['proteins'][protein_id] = measData
        else:
            raise ValueError(
                "Please enter a reactant or protein ID to add measurement data"
            )

    def updateReplicates(self, replicates: list[Replicate]) -> None:
        for replicate in replicates:
            # Set the measurement name for the replicate
            replicate.measurement_id = self.name

    def _setReplicateMeasIDs(self) -> None:
        """Sets the measurement IDs for the replicates."""
        for measData in self.species_dict['proteins'].values():
            measData.measurement_id = self.id

        for measData in self.species_dict['reactants'].values():
            measData.measurement_id = self.id

    @ validate_arguments
    def getReactant(self, reactantID: str) -> MeasurementData:
        """Returns a single MeasurementData object for the given reactantID.

        Args:
            reactantID (String): Unqiue identifier of the reactant

        Returns:
            MeasurementData: Object representing the data and initial concentration
        """
        return self.__getSpecies(reactantID)

    def getProtein(self, proteinID: str) -> MeasurementData:
        """Returns a single MeasurementData object for the given proteinID.

        Args:
            reactantID (String): Unqiue identifier of the protein

        Returns:
            MeasurementData: Object representing the data and initial concentration
        """
        return self.__getSpecies(proteinID)

    def getReactants(self) -> dict[str, MeasurementData]:
        """Returns a list of all participating reactants in the measurement.

        Returns:
            list: List of MeasurementData objects representing data
        """
        return self.species_dict["reactants"]

    def getProteins(self) -> dict[str, MeasurementData]:
        """Returns a list of all participating proteins in the measurement.

        Returns:
            list: List of MeasurementData objects representing data
        """
        return self.species_dict["proteins"]

    @ validate_arguments
    def __getSpecies(self, species_id: str) -> MeasurementData:
        all_species = {
            **self.species_dict["proteins"],
            **self.species_dict["reactants"]
        }

        try:
            return all_species[species_id]
        except KeyError:
            raise SpeciesNotFoundError(
                species_id=species_id,
                enzymeml_part="Measurement"
            )

    @deprecated_getter("id")
    def getId(self):
        return self.id

    @deprecated_getter("global_time_unit")
    def getGlobalTimeUnit(self):
        return self.global_time_unit

    @deprecated_getter("global_time")
    def getGlobalTime(self):
        return self.global_time

    @deprecated_getter("name")
    def getName(self):
        return self.name

    @deprecated_getter("species_dict")
    def getSpeciesDict(self):
        return self.species_dict
