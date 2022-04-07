# File: vessel.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

from pydantic import Field, PositiveFloat, validator, PrivateAttr, BaseModel
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.utils import type_checking, deprecated_getter

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class Vessel(EnzymeMLBase):

    name: str = Field(
        ..., description="Name of the used vessel.", template_alias="Name"
    )

    volume: Optional[PositiveFloat] = Field(
        None,
        description="Volumetric value of the vessel.",
        template_alias="Volume value",
    )

    unit: Optional[str] = Field(
        None, description="Volumetric unit of the vessel.", template_alias="Volume unit"
    )

    constant: bool = Field(
        True,
        description="Whether the volume of the vessel is constant or not.",
    )

    meta_id: Optional[str] = Field(
        None,
        description="Unique meta identifier of the vessel.",
    )

    id: Optional[str] = Field(
        None,
        description="Unique identifier of the vessel.",
        template_alias="ID",
        regex=r"v[\d]+",
    )

    uri: Optional[str] = Field(
        None,
        description="URI of the vessel.",
    )

    creator_id: Optional[str] = Field(
        None,
        description="Unique identifier of the author.",
    )

    # * Private
    _unit_id: Optional[str] = PrivateAttr(None)
    _enzmldoc = PrivateAttr(default=None)

    # ! Validators
    @validator("id")
    def set_meta_id(cls, id: Optional[str], values: dict):
        """Sets the meta ID when an ID is provided"""

        if id:
            # Set Meta ID with ID
            values["meta_id"] = f"METAID_{id.upper()}"

        return id

    # ! Getters
    def unitdef(self):
        """Returns the appropriate unitdef if an enzmldoc is given"""

        if not self._enzmldoc:
            return None

        return self._enzmldoc._unit_dict[self._unit_id]

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
