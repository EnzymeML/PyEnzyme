'''
File: measurementData.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Thursday July 15th 2021 1:19:51 am
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pydantic import (
    PositiveFloat,
    validate_arguments,
    BaseModel,
    validator,
    Field,
    PrivateAttr
)
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase

from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.exceptions import MeasurementDataSpeciesIdentifierError
from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)

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

    replicates: list[Replicate] = Field(
        default_factory=list,
        description="A list of replicate objects holding raw data of the measurement.",
    )

    # * Private
    _unit_id: Optional[str] = PrivateAttr(default=None)

    # ! Validators

    @validator("protein_id")
    def check_id_occurences(cls, protein_id: str, values: dict):
        reactant_id = values.get("reactant_id")

        if reactant_id is None and protein_id is None:
            raise MeasurementDataSpeciesIdentifierError()

        elif reactant_id and protein_id:
            raise MeasurementDataSpeciesIdentifierError(
                both=[reactant_id, protein_id])

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

        for replicate in self.replicates:
            unit_id = self._rescaleReplicateUnits(
                replicate=replicate,
                kind=kind,
                scale=scale,
                enzmldoc=enzmldoc
            )

        if unit_id:
            return unit_id

    def _rescaleReplicateUnits(self, replicate: Replicate, kind: str, scale: int, enzmldoc) -> None:
        """Rescales a replicates data_unit to match the desired scale.

        Args:
            replicate (Replicate): Replicate object containing time course data.
            kind (str): The kind of unit that will be rescaled.
            scale (int): The scale to whih the data will be transformed.
            enzmldoc ([type]): The EnzymeML document to which the new unit will be added.
        """

        data_unit_id = replicate._data_unit_id
        unitdef: UnitDef = enzmldoc.unit_dict[data_unit_id].copy()

        # Calculate the scale to transform the unit
        transform_value = unitdef.calculateTransformValue(
            kind=kind, scale=scale
        )

        # Re-scale and assign the data of the replicate
        replicate.data = [
            data_point * transform_value
            for data_point in replicate.data
        ]

        # Create a new unit that matches the new scale
        new_unitdef = UnitDef(**unitdef.dict())
        correction_factor = 1 if scale == 0 else 0

        for base_unit in new_unitdef.units:
            if base_unit.kind == kind:
                base_unit.scale = scale + correction_factor

        # Add it to the enzymeml document and replicate
        new_unit_name = new_unitdef._getNewName()
        unit_id = enzmldoc._convertToUnitDef(new_unit_name)
        replicate._data_unit_id = unit_id
        replicate.data_unit = new_unit_name

        # Reset unit id and unit string
        self.__setattr__("unit", new_unit_name)
        self.__setattr__("_unit_id", unit_id)

    @ validate_arguments
    def addReplicate(self, replicate: Replicate) -> None:
        self.replicates.append(replicate)

    @ validate_arguments
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

    @ deprecated_getter("reactant_id")
    def getReactantID(self) -> Optional[str]:
        return self.reactant_id

    @ deprecated_getter("protein_id")
    def getProteinID(self) -> Optional[str]:
        return self.protein_id

    @ deprecated_getter("init_conc")
    def getInitConc(self) -> PositiveFloat:
        return self.init_conc

    @ deprecated_getter("unit")
    def getUnit(self) -> str:
        return self.unit

    @ deprecated_getter("replicates")
    def getReplicates(self) -> list[Replicate]:
        return self.replicates
