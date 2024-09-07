from copy import deepcopy
from enum import Enum
from functools import partial

from pydantic import model_validator

from pyenzyme.model import (
    UnitDefinition as _UnitDefinition,
    BaseUnit as _BaseUnit,
    UnitType,
)

UNIT_OF_MEAS_TYPE = "OBO:UO_0000000"
NAME_MAPS = {
    UnitType.LITRE: "l",
    UnitType.MOLE: "mol",
    UnitType.SECOND: "s",
    UnitType.GRAM: "g",
    UnitType.KELVIN: "K",
}


def _is_unit(other: object) -> bool:
    """Check if the given object is an instance of 'unit'.

    Args:
        other (object): The object to check.

    Returns:
        bool: True if the object is an instance of 'unit', False otherwise.
    """
    return other.__class__.__name__ == "unit"


def set_scale(unit: _BaseUnit, scale: int) -> _BaseUnit:
    """Set the scale of a unit.

    Args:
        unit (_BaseUnit): The unit to set the scale for.
        scale (int): The scale value to set.

    Returns:
        _BaseUnit: The unit with the updated scale.
    """
    unit.scale = scale
    return unit


class Prefix(Enum):
    """Enumeration for unit prefixes with corresponding scales."""

    k = partial(set_scale, scale=3.0)
    m = partial(set_scale, scale=-3.0)
    u = partial(set_scale, scale=-6.0)
    n = partial(set_scale, scale=-9.0)

    def __mul__(self, other: _BaseUnit) -> _BaseUnit:
        """Multiply prefix with a BaseUnit.

        When multiplying a prefix with a BaseUnit, the scale of the BaseUnit is updated.

        Args:
            other (_BaseUnit): The other operand, which should be a BaseUnit.

        Returns:
            _BaseUnit: The resulting unit with the prefix applied.

        Raises:
            TypeError: If the other operand is not a BaseUnit.
        """
        if isinstance(other, _BaseUnit):
            return self.value(other)

        raise TypeError(
            f"unsupported operand type(s) for *: 'Prefix' and '{type(other)}'"
        )


class UnitDefinition(_UnitDefinition):
    """Extended UnitDefinition class with additional operations."""

    @model_validator(mode="after")
    def set_name_and_type(self):
        """Initialize the UnitDefinition object."""
        self._get_name()
        self.ld_type = [UNIT_OF_MEAS_TYPE]
        return self

    def __rtruediv__(self, other: object) -> "UnitDefinition":
        """Right division operation to handle unit division.

        If the other operand is a UnitDefinition, the base units are appended to the current unit.
        If the other operand is a BaseUnit, the base unit is appended to the current unit.

        Args:
            other (object): The numerator in the division.

        Returns:
            UnitDefinition: The resulting unit after division.

        Raises:
            TypeError: If the other operand type is unsupported.
        """

        unit_def = deepcopy(self)
        unit_def.id = None

        for base in unit_def.base_units:
            base.exponent = -abs(base.exponent)

        if isinstance(other, UnitDefinition):
            unit_def.base_units.extend(other.base_units)
        elif isinstance(other, _BaseUnit):
            unit_def.base_units.append(other)

        unit_def._get_name()

        return unit_def

    def __truediv__(self, other: object) -> "UnitDefinition":
        """Division operation to handle unit division.

        If the other operand is a UnitDefinition, the base units are appended to the current unit.
        If the other operand is a BaseUnit, the base unit is appended to the current unit.

        Args:
            other (object): The numerator in the

        Returns:
            UnitDefinition: The resulting unit after division.

        Raises:
            TypeError: If the other operand type is unsupported.

        """

        unit_def = deepcopy(self)
        unit_def.id = None

        if isinstance(other, UnitDefinition):
            for base in other.base_units:
                base.exponent = -abs(base.exponent)
            unit_def.base_units.extend(other.base_units)
        elif isinstance(other, _BaseUnit):
            other.exponent = -abs(other.exponent)
            unit_def.base_units.append(other)

        unit_def._get_name()

        return unit_def

    def __mul__(self, other: object) -> "UnitDefinition":
        """Multiplication operation to handle unit multiplication.

        Args:
            other (object): The multiplier in the multiplication.

        Returns:
            UnitDefinition: The resulting unit after multiplication.

        Raises:
            TypeError: If the other operand type is unsupported.
        """

        unit_def = deepcopy(self)
        unit_def.id = None

        if isinstance(other, (int, float)):
            for base in unit_def.base_units:
                if base.multiplier:
                    base.multiplier *= other
                else:
                    base.multiplier = other

            unit_def._get_name()

            return unit_def

        raise TypeError(
            f"unsupported operand type(s) for *: 'UnitDefinition' and '{type(other)}'"
        )

    def _get_name(self):
        """Get the name of the unit based on the base units."""
        self.name = str(self)

        return self

    def __str__(self) -> str:
        """String representation of the UnitDefinition.

        Returns:
            str: The string representation of the unit.

        Raises:
            ValueError: If no base units are found.
        """

        numerator = [
            self._map_prefix(base.scale)
            + self._map_name(base.kind)
            + self._exponent(base.exponent)
            for base in self.base_units
            if base.exponent > 0
        ]
        denominator = [
            self._map_prefix(base.scale)
            + self._map_name(base.kind)
            + self._exponent(base.exponent)
            for base in self.base_units
            if base.exponent < 0
        ]

        numerator_str = " ".join(numerator) if numerator else ""
        denominator_str = " ".join(denominator) if denominator else ""

        if numerator_str and denominator_str:
            return f"{numerator_str} / {denominator_str}"
        elif numerator_str:
            return numerator_str
        elif denominator_str:
            return f"1 / {denominator_str}"

        raise ValueError("No base units found")

    @staticmethod
    def _map_prefix(scale: int | None) -> str:
        """Map a scale to its corresponding prefix.

        Args:
            scale (int): The scale value to map.

        Returns:
            str: The corresponding prefix.
        """

        if scale is None:
            return ""

        mapping = {
            3: "k",
            -3: "m",
            -6: "u",
            -9: "n",
        }

        return mapping.get(scale, "")

    @staticmethod
    def _map_name(kind: UnitType) -> str:
        return NAME_MAPS.get(kind, kind.name.capitalize())

    @staticmethod
    def _exponent(exponent: int) -> str:
        """Format the exponent for display.

        Args:
            exponent (int): The exponent value to format.

        Returns:
            str: The formatted exponent string.
        """
        if abs(exponent) == 1:
            return ""

        return f"^{abs(exponent)}"


class BaseUnit(_BaseUnit):
    """Extended BaseUnit class with additional operations."""

    def __rtruediv__(self, other: object) -> "UnitDefinition | BaseUnit":
        """Right division operation to handle unit division.

        Args:
            other (object): The numerator in the division.

        Returns:
            UnitDefinition: The resulting unit after division.

        Raises:
            TypeError: If the other operand type is unsupported.
        """

        base_unit = deepcopy(self)

        if isinstance(other, UnitDefinition):
            base_unit.exponent = -base_unit.exponent
            other.base_units.append(base_unit)

            other._get_name()

            return other
        elif isinstance(other, (int, float)):
            base_unit.exponent = -base_unit.exponent
            return base_unit

        raise TypeError(
            f"unsupported operand type(s) for /: 'BaseUnit' and '{type(other)}'"
        )

    def __truediv__(self, other: object) -> "UnitDefinition":
        """Division operation to handle unit division.

        Args:
            other (object): The denominator in the division.

        Returns:
            UnitDefinition: The resulting unit after division.

        Raises:
            TypeError: If the other operand type is unsupported.
        """

        this_bu = deepcopy(self)

        if isinstance(other, BaseUnit):
            other.exponent = -other.exponent
            return UnitDefinition(base_units=[this_bu, other])._get_name()
        elif isinstance(other, UnitDefinition):
            for base_unit in other.base_units:
                base_unit.exponent = -base_unit.exponent
            other.base_units.append(this_bu)
            other._get_name()

            return other

        raise TypeError(
            f"unsupported operand type(s) for /: 'BaseUnit' and '{type(other)}'"
        )

    def __pow__(self, other: int) -> "_BaseUnit":
        """Exponentiation operation to handle unit exponentiation.

        Args:
            other (int): The exponent value.

        Returns:
            _BaseUnit: The resulting unit after exponentiation.

        Raises:
            TypeError: If the exponent is not an integer.
        """

        this_bu = deepcopy(self)

        if isinstance(other, int):
            this_bu.exponent = other
            return this_bu

        raise TypeError(
            f"unsupported operand type(s) for **: 'BaseUnit' and '{type(other)}'"
        )

    def __mul__(self, other: object) -> object:
        """Multiplication operation to handle unit multiplication.

        Args:
            other (object): The multiplier in the multiplication.

        Returns:
            object: The resulting unit after multiplication.

        Raises:
            TypeError: If the other operand type is unsupported.
        """

        this_bu = deepcopy(self)

        if isinstance(other, BaseUnit):
            if this_bu.exponent < 0 or other.exponent < 0:
                this_bu.exponent = abs(this_bu.exponent)
                other.exponent = abs(other.exponent)

            return UnitDefinition(base_units=[this_bu, other])._get_name()
        elif isinstance(other, UnitDefinition):
            other.base_units.append(this_bu)
            other._get_name()

            return other
        elif isinstance(other, Prefix):
            return other * this_bu
        elif isinstance(other, (int, float)):
            if this_bu.multiplier:
                this_bu.multiplier *= other
            else:
                this_bu.multiplier = other
            return this_bu

        raise TypeError(
            f"unsupported operand type(s) for *: 'BaseUnit' and '{type(other)}'"
        )
