'''
File: unitdef.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 15th 2021 7:48:57 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

import libsbml

from pydantic import Field, validator, validate_arguments
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.exceptions import UnitKindError
from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)


if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class BaseUnit(EnzymeMLBase):
    """Base unit description including kind, exponent, scale and multiplier"""

    kind: str = Field(
        description="Unit kind used to write SBML.",
        required=True
    )

    exponent: float = Field(
        description="Unit exponent.",
        required=True
    )

    scale: float = Field(
        description="Unit scale.",
        required=True
    )

    multiplier: float = Field(
        description="Unit multiplier.",
        required=True
    )

    @validator("kind")
    def check_sbml_unit_enum(cls, kind_int: int):
        kind_string: str = libsbml.UnitKind_toString(kind_int)

        if "Invalid UnitKind" in kind_string:
            raise UnitKindError()


@static_check_init_args
class UnitDef(EnzymeMLBase):

    name: str = Field(
        description="Name of the SI unit.",
        required=True
    )

    id: str = Field(
        description="Interal Identifier of the SI unit.",
        required=True
    )

    meta_id: Optional[str] = Field(
        description="Interal meta identifier of the SI unit.",
        required=True
    )

    units: list[BaseUnit] = Field(
        default_factory=list,
        description="List of SI baseunits.",
        required=True
    )

    ontology: str = Field(
        default="NONE",
        description="Ontology of the SI unit.",
        required=False
    )

    # Validators
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

    @validate_arguments
    def addBaseUnit(self, kind: str, exponent: float, scale: float, multiplier: float) -> None:
        """Adds a base unit to the units element and sort the units.

        Args:
            kind (str): SBML unit kind string.
            exponent (float): Exponent of the unit.
            scale (float): Scale of the unit.
            multiplier (float): Muliplier of the unit.
        """

        # Create baseunit
        baseunit = BaseUnit(kind=kind, exponent=exponent,
                            scale=scale, multiplier=multiplier)

        # Merge both and sort them via kind
        self.units = sorted(
            self.units,
            key=lambda unit: unit.kind
        )

    @deprecated_getter("units")
    def getUnits(self):
        return self.units

    @deprecated_getter("name")
    def getName(self):
        return self.name

    @deprecated_getter("id")
    def getId(self):
        return self.id

    @deprecated_getter("meta_id")
    def getMetaid(self):
        return self.meta_id

    @deprecated_getter("ontology")
    def getOntology(self):
        return self.ontology
