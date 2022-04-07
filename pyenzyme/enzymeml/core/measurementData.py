# File: measurementData.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

from pydantic import PositiveFloat, validate_arguments, validator, Field, PrivateAttr
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING
from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase

from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.exceptions import MeasurementDataSpeciesIdentifierError
from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.core.utils import type_checking, deprecated_getter

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class MeasurementData(EnzymeMLBase):
    """Helper class to organize elements"""

    init_conc: float = Field(
        ...,
        description="Initial concentration of the measurement data.",
    )

    unit: str = Field(
        ...,
        description="The unit of the measurement data.",
    )

    measurement_id: Optional[str] = Field(
        None,
        description="Unique measurement identifier this dataset belongs to.",
    )

    reactant_id: Optional[str] = Field(
        None,
        description="The identifier for the described reactant.",
    )

    protein_id: Optional[str] = Field(
        None,
        description="The identifier for the described protein.",
    )

    replicates: List[Replicate] = Field(
        default_factory=list,
        description="A list of replicate objects holding raw data of the measurement.",
    )

    # * Private
    _unit_id: Optional[str] = PrivateAttr(default=None)
    _enzmldoc = PrivateAttr(default=None)

    # ! Validators

    @validator("protein_id")
    def check_id_occurences(cls, protein_id: str, values: dict):
        reactant_id = values.get("reactant_id")

        if reactant_id is None and protein_id is None:
            raise MeasurementDataSpeciesIdentifierError()

        elif reactant_id and protein_id:
            raise MeasurementDataSpeciesIdentifierError(both=[reactant_id, protein_id])

        return protein_id

    # ! Utilities
    def unifyUnits(self, kind: str, scale: int, enzmldoc) -> Optional[str]:
        """Rescales all replicates data_unit to match the desired scale.

        Args:
            replicate (Replicate): Replicate object containing time course data.
            kind (str): The kind of unit that will be rescaled.
            scale (int): The scale to whih the data will be transformed.
            enzmldoc ([type]): The EnzymeML document to which the new unit will be added.
        """

        unit_id = None

        # Transform initial concentration
        unitdef: UnitDef = enzmldoc._unit_dict[self._unit_id].copy()
        transform_value, new_unit_name, unit_id = self._getTransformation(
            unitdef, kind, scale, enzmldoc
        )

        self.init_conc *= transform_value
        self._unit_id = unit_id
        self.unit = new_unit_name

        # Apply to replicates
        for replicate in self.replicates:
            self._rescaleReplicateUnits(
                replicate=replicate, kind=kind, scale=scale, enzmldoc=enzmldoc
            )

    @staticmethod
    def _getTransformation(unitdef: UnitDef, kind: str, scale: int, enzmldoc):
        """Calculates the new transformation value and returns new UnitDef"""

        # Calculate transformation value
        transform_value = unitdef.calculateTransformValue(kind=kind, scale=scale)

        # Create a new unit that matches the new scale
        new_unitdef = UnitDef(**unitdef.dict())
        correction_factor = 1 if scale == 0 else 0

        for base_unit in new_unitdef.units:
            if base_unit.kind == kind:
                base_unit.scale = scale + correction_factor

        new_unit_name = new_unitdef._getNewName()
        unit_id = enzmldoc._convertToUnitDef(new_unit_name)

        return transform_value, new_unit_name, unit_id

    def _rescaleReplicateUnits(
        self, replicate: Replicate, kind: str, scale: int, enzmldoc
    ) -> None:
        """Rescales a replicates data_unit to match the desired scale.

        Args:
            replicate (Replicate): Replicate object containing time course data.
            kind (str): The kind of unit that will be rescaled.
            scale (int): The scale to whih the data will be transformed.
            enzmldoc ([type]): The EnzymeML document to which the new unit will be added.
        """

        data_unit_id = replicate._data_unit_id
        unitdef: UnitDef = enzmldoc._unit_dict[data_unit_id].copy()

        # Calculate the scale to transform the unit
        transform_value, new_unit_name, unit_id = self._getTransformation(
            unitdef, kind, scale, enzmldoc
        )

        # Re-scale and assign the new data of the replicate
        replicate.data = [data_point * transform_value for data_point in replicate.data]
        replicate._data_unit_id = unit_id
        replicate.data_unit = new_unit_name

    @validate_arguments
    def addReplicate(self, replicate: Replicate) -> None:
        self.replicates.append(replicate)

    @validate_arguments
    def setMeasurementIDs(self, id: str) -> None:
        for replicate in self.replicates:
            replicate.measurement_id = id

    def get_id(self) -> str:
        """Internal usage to get IDs from objects without ID attribute"""

        if self.reactant_id:
            return self.reactant_id
        elif self.protein_id:
            return self.protein_id
        else:
            raise AttributeError("Neither reactant nor protein ID are given.")

    # ! Getters
    def unitdef(self):
        """Returns the appropriate unitdef if an enzmldoc is given"""

        if not self._enzmldoc:
            return None

        return self._enzmldoc._unit_dict[self._unit_id]

    @deprecated_getter("reactant_id")
    def getReactantID(self) -> Optional[str]:
        return self.reactant_id

    @deprecated_getter("protein_id")
    def getProteinID(self) -> Optional[str]:
        return self.protein_id

    @deprecated_getter("init_conc")
    def getInitConc(self) -> PositiveFloat:
        return self.init_conc

    @deprecated_getter("unit")
    def getUnit(self) -> str:
        return self.unit

    @deprecated_getter("replicates")
    def getReplicates(self) -> List[Replicate]:
        return self.replicates
