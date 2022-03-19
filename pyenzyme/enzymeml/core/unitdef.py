# File: unitdef.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

from pydantic import Field, validator, validate_arguments
from typing import List, TYPE_CHECKING, Optional
from dataclasses import dataclass

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.utils import type_checking, deprecated_getter


if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class BaseUnit(EnzymeMLBase):
    """Base unit description including kind, exponent, scale and multiplier"""

    kind: str = Field(
        ...,
        description="Unit kind used to write SBML.",
    )

    exponent: float = Field(
        ...,
        description="Unit exponent.",
    )

    scale: int = Field(
        ...,
        description="Unit scale.",
    )

    multiplier: float = Field(
        ...,
        description="Unit multiplier.",
    )

    def get_id(self) -> str:
        """Internal usage to get IDs from objects without ID attribute"""

        if self.kind:
            return self.kind
        else:
            raise AttributeError("No species ID given.")

    def get_name(self) -> str:
        """Returns the appropriate name of the unit"""

        # Get mappings
        prefix_mapping, kind_mapping = self._setup_mappings()

        # Retrieve values to generate the name
        prefix = prefix_mapping[self.scale]
        unit = kind_mapping[self.kind]

        # Special case for time
        if unit == "s":
            if self.multiplier == 60:
                unit = "min"
            if self.multiplier == 60 * 60:
                unit = "hours"

        if abs(self.exponent) != 1:
            exponent = f"^{abs(int(self.exponent))}"
        else:
            exponent = ""

        return f"{prefix}{unit}{exponent}"

    @staticmethod
    def _setup_mappings():
        # TODO integrate this to unitcreator
        # Create a mappings
        prefix_mapping = {
            -15: "f",
            -12: "p",
            -9: "n",
            -6: "u",
            -3: "m",
            -2: "c",
            -1: "d",
            1: "",
            3: "k",
        }

        kind_mapping = {
            "litre": "l",
            "gram": "g",
            "second": "s",
            "kelvin": "K",
            "dimensionless": "dimensionless",
            "mole": "mole",
        }

        return prefix_mapping, kind_mapping


@static_check_init_args
class UnitDef(EnzymeMLBase):

    name: Optional[str] = Field(
        None,
        description="Name of the SI unit.",
    )

    id: Optional[str] = Field(
        None,
        description="Interal Identifier of the SI unit.",
    )

    meta_id: Optional[str] = Field(
        None,
        description="Interal meta identifier of the SI unit.",
    )

    units: List[BaseUnit] = Field(
        default_factory=list,
        description="List of SI baseunits.",
    )

    ontology: Optional[str] = Field(
        None,
        description="Ontology of the SI unit.",
    )

    # ! Validators
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

    def _get_unit_name(self):
        """Generates the unit name based of the given baseunits"""

        nominator, denominator = [], []
        for unit in self.units:
            if unit.exponent > 0:
                nominator.append(unit.get_name())
            elif unit.exponent < 0:
                denominator.append(unit.get_name())

        # Catch empty nominators
        if not nominator:
            nominator = "1"

        # Combine each side and construct the SI string
        nominator = " ".join(nominator)
        denominator = " ".join(denominator)

        if denominator:
            return " / ".join([nominator, denominator])
        else:
            return nominator

    # ! Adders
    @validate_arguments
    def addBaseUnit(
        self, kind: str, exponent: float, scale: int, multiplier: float
    ) -> None:
        """Adds a base unit to the units element and sort the units.

        Args:
            kind (str): SBML unit kind string.
            exponent (float): Exponent of the unit.
            scale (float): Scale of the unit.
            multiplier (float): Muliplier of the unit.
        """

        # Create baseunit
        baseunit = BaseUnit(
            kind=kind, exponent=exponent, scale=scale, multiplier=multiplier
        )

        # Merge both and sort them via kind
        if baseunit not in self.units:
            self.units.append(baseunit)
            self.units = sorted(self.units, key=lambda unit: unit.kind)

    # ! Utilities
    def calculateTransformValue(self, kind: str, scale: int):
        """Calculates the value that is needed to re-scale the given unit to the desired scale.

        Args:
            kind (str): The kind of unit that is used as a reference.
            scale (int): The desired scale.

        Raises:
            ValueError: Raised when the given unit kind is not part of the unitdef.

        Returns:
            float: The value that is needed to re-scale the given unit to the desired scale.
        """

        for base_unit in self.units:
            if base_unit.kind == kind:

                # correction factor used for the case of scale=1
                correction_factor = -1 if base_unit.scale == 1 else 0

                return 10 ** (
                    base_unit.exponent * (base_unit.scale - scale + correction_factor)
                )

        raise ValueError(f"Unit kind of {kind} is not part of the unit definition")

    def _getNewName(self) -> str:
        """Internal function used to derive a units new name. Will be assigned using enzmldoc._convertTounitDef.

        Returns:
            str: The new name of the unit definition.
        """

        # Mapping for abbreviations
        kind_mapping = {
            "mole": "mole",
            "second": "s",
            "liter": "l",
            "litre": "l",
        }

        prefix_mapping = {
            -15: "f",
            -12: "p",
            -9: "n",
            -6: "u",
            -3: "m",
            -2: "c",
            -1: "d",
            1: "",
            3: "k",
        }

        nominator = list(filter(lambda base_unit: base_unit.exponent > 0, self.units))

        denominator = list(filter(lambda base_unit: base_unit.exponent < 0, self.units))

        # Create new unit name
        def constructName(base_unit: BaseUnit) -> str:
            return f"{prefix_mapping[base_unit.scale]}{kind_mapping[base_unit.kind]}"

        nominator_string = " ".join(
            [constructName(base_unit) for base_unit in nominator]
        )
        denominator_string = " ".join(
            [constructName(base_unit) for base_unit in denominator]
        )

        return " / ".join([nominator_string, denominator_string])

    # ! Getters
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

    def getFootprint(self):
        sorted_units = [base_unit.dict() for base_unit in self.units]
        return list(sorted(sorted_units, key=lambda unit: unit["kind"]))
