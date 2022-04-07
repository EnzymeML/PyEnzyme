# File: measurement.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import copy
import logging
import pandas as pd

from typing import List, Dict, Tuple, Optional, TYPE_CHECKING, Union
from dataclasses import dataclass
from pydantic import validate_arguments, Field, PrivateAttr, validator

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.measurementData import MeasurementData
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.exceptions import SpeciesNotFoundError
from pyenzyme.utils.log import log_object
from pyenzyme.enzymeml.core.utils import type_checking, deprecated_getter

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking

# Initialize the logger
logger = logging.getLogger("pyenzyme")


@static_check_init_args
class Measurement(EnzymeMLBase):

    name: str = Field(
        ...,
        description="Name of the measurement",
    )

    temperature: Optional[float] = Field(
        None,
        description="Numeric value of the temperature of the reaction.",
        template_alias="Temperature value",
    )

    temperature_unit: Optional[str] = Field(
        None,
        description="Unit of the temperature of the reaction.",
        regex=r"kelvin|Kelvin|k|K|celsius|Celsius|C|c",
    )

    ph: Optional[float] = Field(
        None,
        description="PH value of the reaction.",
        inclusiveMinimum=0,
        inclusiveMaximum=14,
    )

    species_dict: Dict[str, Dict[str, MeasurementData]] = Field(
        {"proteins": {}, "reactants": {}},
        description="Species of the measurement.",
    )

    global_time: List[float] = Field(
        default_factory=list,
        description="Global time of the measurement all replicates agree on.",
    )

    global_time_unit: Optional[str] = Field(
        None,
        description="Unit of the global time.",
    )

    id: Optional[str] = Field(
        None, description="Unique identifier of the measurement.", regex=r"m[\d]+"
    )

    uri: Optional[str] = Field(
        None,
        description="URI of the reaction.",
    )

    creator_id: Optional[str] = Field(
        None,
        description="Unique identifier of the author.",
    )

    # * Private attributes
    _temperature_unit_id: str = PrivateAttr(None)
    _global_time_unit_id: str = PrivateAttr(None)
    _enzmldoc = PrivateAttr(default=None)

    # ! Validators
    @validator("temperature_unit")
    def convert_temperature_unit(cls, unit, values):
        """Converts celsius to kelvin due to SBML limitations"""

        if unit:
            if unit.lower() in ["celsius", "c"]:
                values["temperature"] = values["temperature"] + 273.15
                return "K"

        return unit

    # ! Utility methods
    def __repr__(self):
        return self.printMeasurementScheme(stdout=False)

    def printMeasurementScheme(
        self, species_type: str = "all", stdout: bool = True
    ) -> Optional[str]:
        """Prints the scheme of the measurement and as such an overview of what has been done.

        Args:
            species_type (str, optional): Specifies whether only "reactants"/"proteins" should be displayed or all of them. Defaults to "all".
        """

        # Get all measurement data objects
        reactants = self.getReactants()
        proteins = self.getProteins()

        if species_type == "reactants":
            species = list(reactants.values())
        elif species_type == "proteins":
            species = list(proteins.values())
        elif species_type == "all":
            species = list(reactants.values()) + list(proteins.values())
        else:
            raise ValueError(
                f"Species type of {species_type} is not supported. Please enter use one of the following: 'reactants', 'proteins' or 'all'."
            )

        # Start printing
        output = []
        output.append(f">>> Measurement {self.id}: {self.name}")

        for meas_data in species:
            output.append(
                f"    {meas_data.get_id()} | initial conc: {meas_data.init_conc} {meas_data.unit} \t| #replicates: {len(meas_data.replicates)}"
            )

        output = "\n".join(output)

        if stdout:
            print(output)
        else:
            return output

    def exportData(
        self, species_ids: Union[str, List[str]] = "all"
    ) -> Dict[str, Dict[str, Union[Dict[str, Tuple[float, str]], pd.DataFrame]]]:
        """Returns data stored in the measurement object as DataFrames nested in dictionaries. These are sorted hierarchially by reactions where each holds a DataFrame each for proteins and reactants.

        Returns:
            measurements (dict): Follows the hierarchy Reactions > Proteins/Reactants > { initial_concentration, data }
            species_ids (Union[str, List[str]]): List of species IDs to extract data from. Defaults to 'all'.
        """

        # Combine Replicate objects for each reaction
        proteins = self._combineReplicates(
            measurement_species=self.species_dict["proteins"], species_ids=species_ids
        )
        reactants = self._combineReplicates(
            measurement_species=self.species_dict["reactants"], species_ids=species_ids
        )

        return {"proteins": proteins, "reactants": reactants}

    def _combineReplicates(
        self,
        measurement_species: Dict[str, MeasurementData],
        species_ids: Union[str, List[str]] = "all",
    ) -> Dict[str, Union[Dict[str, Tuple[float, str]], pd.DataFrame]]:
        """Combines replicates of a certain species to a dataframe.

        Args:
            measurement_species (Dict[str, MeasurementData]): The species_dict from the measurement.

        Returns:
            Dict[str, Any]: The associated replicat and initconc data.
        """

        if isinstance(species_ids, str):
            species_ids = [species_ids]

        columns = {}
        initial_concentration = {}
        num_replicates = 0

        # Iterate over measurementData to fill columns
        for species_id, data in measurement_species.items():

            if species_id in species_ids or species_ids == ["all"]:

                # Fetch initial concentration
                initial_concentration[species_id] = (data.init_conc, data.unit)

                # Fetch replicate data
                if len(data.replicates) > num_replicates:
                    num_replicates = len(data.replicates)
                for replicate in data.replicates:

                    if columns.get(species_id):
                        # For multiple replicates
                        columns[species_id] += copy.deepcopy(replicate.data)
                    else:
                        columns[species_id] = copy.deepcopy(replicate.data)

        # Add global time to columns according to the number of replicates
        columns["time"] = self.global_time * num_replicates

        return {
            "data": pd.DataFrame(columns) if len(columns) > 1 else pd.DataFrame(),
            "initConc": initial_concentration,
        }

    @validate_arguments
    def addReplicates(
        self, replicates: Union[List[Replicate], Replicate], enzmldoc, log: bool = True
    ) -> None:
        """Adds a replicate to the corresponding measurementData object. This method is meant to be called if the measurement metadata of a reaction/species has already been done and replicate data has to be added afterwards. If not, use addData instead to introduce the species metadata.

        Args:
            replicate (List<Replicate>): Objects describing time course data
        """

        # Check if just a single Replicate has been handed
        if isinstance(replicates, Replicate):
            replicates = [replicates]

        for replicate in replicates:

            # Check for the species type
            species_id = replicate.species_id
            speciesType = "reactants" if species_id[0] == "s" else "proteins"
            speciesData = self.species_dict[speciesType]

            try:

                data = speciesData[species_id]

                replicate._data_unit_id = enzmldoc._convertToUnitDef(
                    replicate.data_unit
                )
                replicate._time_unit_id = enzmldoc._convertToUnitDef(
                    replicate.time_unit
                )

                data.addReplicate(replicate)

                if len(self.global_time) == 0:

                    # Add global time if this is the first replicate to be added
                    self.global_time = replicate.time
                    self.global_time_unit = replicate.time_unit
                    self._global_time_unit_id = replicate._time_unit_id

                # Log Replicate creation
                if log:
                    log_object(logger, replicate)
                    logger.debug(
                        f"Added {type(replicate).__name__} '{replicate.id}' to data '{data.get_id()}' of measurement '{self.name}'"
                    )

            except KeyError:
                raise KeyError(
                    f"{speciesType[0:-1]} {species_id} is not part of the measurement yet. If a {speciesType[0:-1]} hasnt been yet defined in a measurement object, use the addData method to define metadata first-hand. You can add the replicates in the same function call then."
                )

    @validate_arguments
    def addData(
        self,
        unit: str,
        init_conc: float = 0.0,
        reactant_id: Optional[str] = None,
        protein_id: Optional[str] = None,
        replicates: List[Replicate] = [],
        log: bool = True,
    ) -> None:
        """Adds data to the measurement object.

        Args:
            init_conc (PositiveFloat): Corresponding initial concentration of species.
            unit (str): The SI unit of the measurement.
            reactant_id (Optional[str], optional): Identifier of the reactant that was measured. Defaults to None.
            protein_id (Optional[str], optional): Identifier of the protein that was measured. Defaults to None.
            replicates (List[Replicate], optional): List of replicates that were measured. Defaults to [].
        """

        self._appendReactantData(
            reactant_id=reactant_id,
            protein_id=protein_id,
            init_conc=init_conc,
            unit=unit,
            replicates=replicates,
            log=log,
        )

    def _appendReactantData(
        self,
        reactant_id: Optional[str],
        protein_id: Optional[str],
        init_conc: float,
        unit: str,
        replicates: List[Replicate],
        log: bool = True,
    ) -> None:

        # Create measurement data class before sorting
        measData = MeasurementData(
            reactant_id=reactant_id,
            protein_id=protein_id,
            init_conc=init_conc,
            unit=unit,
            replicates=replicates,
            measurement_id=self.id,
        )

        if reactant_id:
            self.species_dict["reactants"][reactant_id] = measData
        elif protein_id:
            self.species_dict["proteins"][protein_id] = measData
        else:
            raise ValueError(
                "Please enter a reactant or protein ID to add measurement data"
            )

        # Log the new object
        if log:
            log_object(logger, measData)
            logger.debug(
                f"Added {type(measData).__name__} '{measData.get_id()}' to measurement '{self.name}'"
            )

    def updateReplicates(self, replicates: List[Replicate]) -> None:
        for replicate in replicates:
            # Set the measurement name for the replicate
            replicate.measurement_id = self.name

    def _setReplicateMeasIDs(self) -> None:
        """Sets the measurement IDs for the replicates."""
        for measData in self.species_dict["proteins"].values():
            measData.measurement_id = self.id

        for measData in self.species_dict["reactants"].values():
            measData.measurement_id = self.id

    def unifyUnits(self, kind: str, scale: int, enzmldoc) -> None:
        """Rescales all replicates and measurements to match the scale of a unit kind.

        Args:
            kind (str): The unit kind from which to rescale. Currently supported: 'mole', 'gram', 'litre'.
            scale (int): Decade scale to which the values will be rescaled.
            enzmldoc (EnzymeMLDocument): The EnzymeMLDocument to which the new unit will be added.
        """

        if kind not in ["mole", "gram", "litre"]:
            raise ValueError(
                f"Kind {kind} is not supported. Please use 'mole', 'gram', or 'litre'"
            )

        if abs(scale) % 3 > 0:
            if abs(scale) == 1:
                pass
            else:
                raise ValueError(
                    f"Scale {scale} is not a multiple of 3. Please make sure the scale is a multiple of 3."
                )

        for measurement_data in {**self.getProteins(), **self.getReactants()}.values():
            measurement_data.unifyUnits(kind=kind, scale=scale, enzmldoc=enzmldoc)

    def _has_replicates(self) -> bool:
        """Checks whether replicates are present in the measurement.

        This is only used for the to check whether to write time course data or not.

        Returns:
            bool: Returns True if there are any replicate otherwise False.
        """

        all_species = {
            **self.species_dict["proteins"],
            **self.species_dict["reactants"],
        }

        for obj in all_species.values():
            if len(obj.replicates) > 0:
                return True

        return False

    # ! Getters
    def temperature_unitdef(self):
        """Returns the appropriate unitdef if an enzmldoc is given"""

        if not self._enzmldoc:
            return None

        return self._enzmldoc._unit_dict[self._temperature_unit_id]

    @validate_arguments
    def getReactant(self, reactant_id: str) -> MeasurementData:
        """Returns a single MeasurementData object for the given reactant_id.

        Args:
            reactant_id (String): Unqiue identifier of the reactant

        Returns:
            MeasurementData: Object representing the data and initial concentration
        """
        return self._getSpecies(reactant_id)

    def getProtein(self, protein_id: str) -> MeasurementData:
        """Returns a single MeasurementData object for the given protein_id.

        Args:
            protein_id (String): Unqiue identifier of the protein

        Returns:
            MeasurementData: Object representing the data and initial concentration
        """
        return self._getSpecies(protein_id)

    def getReactants(self) -> Dict[str, MeasurementData]:
        """Returns a dict of all participating reactants in the measurement.

        Returns:
            dict: Dict of MeasurementData objects representing data
        """
        return self.species_dict["reactants"]

    def getProteins(self) -> Dict[str, MeasurementData]:
        """Returns a dict of all participating proteins in the measurement.

        Returns:
            dict: Dict of MeasurementData objects representing data
        """
        return self.species_dict["proteins"]

    def _getAllSpecies(self):
        return {**self.species_dict["proteins"], **self.species_dict["reactants"]}

    @validate_arguments
    def _getSpecies(self, species_id: str) -> MeasurementData:
        all_species = {
            **self.species_dict["proteins"],
            **self.species_dict["reactants"],
        }

        try:
            return all_species[species_id]
        except KeyError:
            raise SpeciesNotFoundError(
                species_id=species_id, enzymeml_part="Measurement"
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
