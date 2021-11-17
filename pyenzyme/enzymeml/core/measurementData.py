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

from pydantic import PositiveFloat, validate_arguments, BaseModel, validator, Field
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.exceptions import IdentifierError
from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class MeasurementData(BaseModel):
    """Helper class to organize elements"""

    init_conc: PositiveFloat = Field(
        description="Initial concentration of the measurement data.",
        required=True
    )

    unit: str = Field(
        description="The unit of the measurement data.",
        required=True
    )

    measurement_id: Optional[str] = Field(
        description="Unique measurement identifier this dataset belongs to.",
    )

    reactant_id: Optional[str] = Field(
        description="The identifier for the described reactant.",
        required=False
    )

    protein_id: Optional[str] = Field(
        description="The identifier for the described protein.",
        required=False
    )

    replicates: list[Replicate] = Field(
        default_factory=list,
        description="A list of replicate objects holding raw data of the measurement.",
        required=False
    )

    @validator("protein_id")
    def check_id_occurences(cls, protein_id: str, values: dict):
        reactant_id = values.get("reactant_id")

        if reactant_id is None and protein_id is None:
            raise IdentifierError(
                "Neither a reactant nor protein identifier has been provided. Please specify either one or the other."
            )

        elif reactant_id and protein_id:
            raise IdentifierError(
                "Both a reactant and protein identifier have been provided. Please specify either one or the other"
            )

        return protein_id

    @validate_arguments
    def addReplicate(self, replicate: Replicate) -> None:
        self.replicates.append(replicate)

    @validate_arguments
    def setMeasurementIDs(self, id: str) -> None:
        for replicate in self.replicates:
            replicate.measurement_id = id

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
    def getReplicates(self) -> list[Replicate]:
        return self.replicates
