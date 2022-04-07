# File: unitcreator.py
# Project: tools
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import libsbml

from deepdiff import DeepDiff

from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.tools.unitparser import UnitParser


class UnitCreator:
    def __init__(self):

        self.__functionDict = {
            "M": self.__Molar,
            "mole": self.__Mole,
            "l": self.__Volume,
            "liter": self.__Volume,
            "litre": self.__Volume,
            "g": self.__Amount,
            "gram": self.__Amount,
            "s": self.__Seconds,
            "sec": self.__Seconds,
            "second": self.__Seconds,
            "seconds": self.__Seconds,
            "min": self.__Minutes,
            "mins": self.__Minutes,
            "minutes": self.__Minutes,
            "h": self.__Hours,
            "hour": self.__Hours,
            "hours": self.__Hours,
            "C": self.__Celsius,
            "celsius": self.__Celsius,
            "Celsius": self.__Celsius,
            "K": self.__Kelvin,
            "kelvin": self.__Kelvin,
            "Kelvin": self.__Kelvin,
            "dimensionless": self.__Dimensionless,
        }

    def getUnit(self, unit_string, enzmldoc) -> str:
        """
        Args:
            String unit_string: Standard short form of unit
        """
        if unit_string.count("/") > 1:
            splitted = unit_string.split("/")
            corrected = splitted[0] + "/" + "".join(splitted[1::])
            raise ValueError(
                f"Unit '{unit_string}' contains multiple backlashes. Please stick to using a single backslash instead for units involving two or more base units per side. Use the following to enter your unit '{corrected}'"
            )

        # Generate ID
        id = enzmldoc._generateID(prefix="u", dictionary=enzmldoc._unit_dict)

        # Call unit parser to identify units
        parser = UnitParser()
        units = sorted(parser.parse(unit_string))

        # Initialize UnitDef
        nominator, denominator = [], []
        for prefix, baseunit, exponent in units:

            pre_unit = "".join([prefix, baseunit])

            if float(exponent) > 0:
                if abs(float(exponent)) > 1:
                    nominator.append(pre_unit + f"^{exponent[1::]}")
                if abs(float(exponent)) == 1:
                    nominator.append(pre_unit)
            else:
                if abs(float(exponent)) > 1:
                    denominator.append(pre_unit + f"^{exponent[1::]}")
                if abs(float(exponent)) == 1:
                    denominator.append(pre_unit)

        # Reformat unit string to a convenient format
        if not nominator:
            nominator = ["1"]

        if denominator:
            name = " / ".join([" ".join(nominator), " ".join(denominator)])
        if not denominator:
            name = " ".join(nominator)

        # Convert Celsius to Kelvin - No SBML kind for C!
        if name.lower() == "c":
            name = "K"

        # Initialize UnitDef object
        unitdef = UnitDef(name=name, id=id)

        for prefix, baseunit, exponent in units:
            self.__functionDict[baseunit](unitdef, prefix, exponent)

        # Check if there is already a similar unit defined
        if self.__checkFootprints(enzmldoc, unitdef.getFootprint()) != "NEW":
            return self.__checkFootprints(enzmldoc, unitdef.getFootprint())

        enzmldoc._unit_dict[unitdef.id] = unitdef

        return unitdef.id

    def __checkFootprints(self, enzmldoc, footprint):

        for unit_id, unitdef in enzmldoc._unit_dict.items():
            if DeepDiff(unitdef.getFootprint(), footprint) == {}:
                return unit_id

        return "NEW"

    def __Mole(self, unitdef, prefix, exponent):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE)
        scale = self.__getPrefix(prefix)
        multiplier = 1

        unitdef.addBaseUnit(kind, exponent, scale, multiplier)

    def __Molar(self, unitdef, prefix, exponent):

        self.__Mole(unitdef, prefix, exponent)

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_LITRE)
        scale = 1
        multiplier = 1

        unitdef.addBaseUnit(kind, -1, scale, multiplier)

    def __Volume(self, unitdef, prefix, exponent):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_LITRE)
        scale = self.__getPrefix(prefix)
        multiplier = 1

        unitdef.addBaseUnit(kind, exponent, scale, multiplier)

    def __Amount(self, unitdef, prefix, exponent):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_GRAM)
        scale = self.__getPrefix(prefix)
        multiplier = 1

        unitdef.addBaseUnit(kind, exponent, scale, multiplier)

    def __Seconds(self, unitdef, prefix, exponent):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_SECOND)
        scale = 1
        multiplier = 1

        unitdef.addBaseUnit(kind, exponent, scale, multiplier)

    def __Minutes(self, unitdef, prefix=None, exponent=1):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_SECOND)
        scale = 1
        multiplier = 60

        unitdef.addBaseUnit(kind, exponent, scale, multiplier)

    def __Hours(self, unitdef, prefix=None, exponent=1):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_SECOND)
        scale = 1
        multiplier = 60 * 60

        unitdef.addBaseUnit(kind, exponent, scale, multiplier)

    def __Celsius(self, unitdef, prefix=None, exponent=1):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_KELVIN)
        scale = 1
        multiplier = 1

        unitdef.addBaseUnit(kind, exponent, scale, multiplier)

    def __Kelvin(self, unitdef, prefix=None, exponent=1):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_KELVIN)
        scale = 1
        multiplier = 1

        unitdef.addBaseUnit(kind, exponent, scale, multiplier)

    def __Dimensionless(self, unitdef, prefix=None, exponent=1):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_DIMENSIONLESS)
        scale = 1
        multiplier = 1
        exponent = 1

        unitdef.addBaseUnit(kind, exponent, scale, multiplier)

    def __getPrefix(self, prefix):

        if prefix == "f":
            return -15
        elif prefix == "p":
            return -12
        elif prefix == "n":
            return -9
        elif prefix == "u":
            return -6
        elif prefix == "m":
            return -3
        elif prefix == "c":
            return -2
        elif prefix == "d":
            return -1
        elif prefix == "k":
            return 3
        elif len(prefix) == 0:
            return 1
        else:
            raise KeyError(f"Prefix {prefix} is unknown. Please define unit manually")
