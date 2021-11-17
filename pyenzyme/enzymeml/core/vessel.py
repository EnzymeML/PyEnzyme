'''
File: vessel.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 15th 2021 8:26:08 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pydantic import Field, PositiveFloat, validator
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class Vessel(EnzymeMLBase):

    name: str = Field(
        description="Name of the used vessel.",
        required=True
    )

    id: str = Field(
        description="Unique identifier of the vessel.",
        required=True,
        regex=r"v[\d]+"
    )

    meta_id: Optional[str] = Field(
        default=None,
        description="Unique meta identifier of the vessel.",
        required=True
    )

    volume: PositiveFloat = Field(
        description="Volumetric value of the vessel.",
        required=True
    )

    unit: str = Field(
        description="Volumetric unit of the vessel.",
        required=True
    )

    constant: bool = Field(
        default=True,
        description="Whether the volume of the vessel is constant or not.",
        required=True
    )

    uri: Optional[str] = Field(
        default=None,
        description="URI of the vessel.",
        required=False
    )

    creator_id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the author.",
        required=False
    )

    @validator("id")
    def set_meta_id(cls, id: Optional[str], values: dict):
        """Sets the meta ID when an ID is provided"""

        if id:
            # Set Meta ID with ID
            values["meta_id"] = f"METAID_{id.upper()}"

        return id

    @validator("meta_id")
    def check_meta_id(cls, meta_id: Optional[str], values: dict):
        """Checks if the meta ID provided is following the standard"""

        if values.get("meta_id"):
            # When the ID init already set the meta ID
            return values.get("meta_id")

        return None

    @deprecated_getter("name")
    def getName(self):
        return self.name

    @deprecated_getter("id")
    def getId(self):
        return self.id

    @deprecated_getter("meta_id")
    def getMetaid(self):
        return self.meta_id

    @deprecated_getter("constant")
    def getConstant(self):
        return self.constant

    @deprecated_getter("volume")
    def getSize(self):
        return self.volume

    @deprecated_getter("unit")
    def getUnit(self):
        return self.unit
