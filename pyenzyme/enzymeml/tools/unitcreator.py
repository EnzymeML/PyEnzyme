'''
File: unitcreator.py
Project: tools
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 10:12:25 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

import libsbml
from pyenzyme.enzymeml.core.unitdef import UnitDef
from pyenzyme.enzymeml.tools.unitparser import UnitParser


class UnitCreator(object):

    def __init__(self):

        self.__functionDict = {

            "M": self.__Molar,
            "m": self.__Mole,
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
            "minute": self.__Minutes,
            "minutes": self.__Minutes,
            "h": self.__Hours,
            "hour": self.__Hours,
            "hours": self.__Hours,
            "C": self.__Celsius,
            "c": self.__Celsius,
            "celsius": self.__Celsius,
            "K": self.__Kelvin,
            "kelvin": self.__Kelvin,
            "dimensionless": self.__Dimensionless


            }

    def getUnit(self, unit_string, enzmldoc):

        '''
        Args:
            String unit_string: Standard short form of unit
        '''

        index = 0
        while True:

            id_ = "u%i" % index

            if id_ not in enzmldoc.getUnitDict().keys():
                break
            else:
                index += 1

        # Check dimensionless units
        dimlessToCheck = ('abs', 'absorption', 'dimensionless')

        if unit_string.lower().endswith(dimlessToCheck):

            # Initialize UnitDef object
            unitdef = UnitDef("absorption", id_, "NONE")

            self.__functionDict["dimensionless"](
                unitdef,
                1.0,
                1.0
            )

            # Check if there is already a similar unit defined
            if self.__checkFootprints(
                enzmldoc,
                unitdef.getFootprint()
            ) != "NEW":

                return self.__checkFootprints(enzmldoc, unitdef.getFootprint())

            enzmldoc.getUnitDict()[unitdef.getId()] = unitdef

            return unitdef.getId()

        # Call unit parser to identify units
        parser = UnitParser()
        units = sorted(parser.parse(unit_string))

        # Initialize UnitDef
        nominator, denominator = [], []
        for prefix, baseunit, exponent in units:

            pre_unit = "".join([prefix, baseunit])

            if float(exponent) > 0:
                if abs(float(exponent)) > 1:
                    nominator.append(
                        pre_unit +
                        f"**{exponent}"
                    )
                if abs(float(exponent)) == 1:
                    nominator.append(pre_unit)
            else:
                if abs(float(exponent)) > 1:
                    denominator.append(
                        pre_unit +
                        f"**{exponent}"
                    )
                if abs(float(exponent)) == 1:
                    denominator.append(pre_unit)

        # Reformat unit string to a convenient format
        if len(denominator) > 0:
            name = " / ".join([
                    " ".join(nominator),
                    " ".join(denominator)
                    ])
        if len(denominator) == 0:
            name = " ".join(nominator)

        # Convert Celsius to Kelvin - No SBML kind for C!
        if name.lower() == 'c':
            name = 'K'

        # Initialize UnitDef object
        unitdef = UnitDef(name, id_, "NONE")

        for prefix, baseunit, exponent in units:
            self.__functionDict[baseunit](
                unitdef,
                prefix,
                exponent
            )

        # Check if there is already a similar unit defined
        if self.__checkFootprints(enzmldoc, unitdef.getFootprint()) != "NEW":

            return self.__checkFootprints(enzmldoc, unitdef.getFootprint())

        enzmldoc.getUnitDict()[unitdef.getId()] = unitdef

        return unitdef.getId()

    def __checkFootprints(self, enzmldoc, footprint):

        unitdict = enzmldoc.getUnitDict()

        def __compare(f1, f2):
            return sorted(f1) == sorted(f2)

        for unitdef in unitdict:
            if __compare(unitdict[unitdef].getFootprint(), footprint):

                return unitdict[unitdef].getId()

        return "NEW"

    def __Mole(self, unitdef, prefix, exponent):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE)
        scale = self.__getPrefix(prefix)
        multiplier = 1

        unitdef.addBaseUnit(
            kind,
            exponent,
            scale,
            multiplier
        )

    def __Molar(self, unitdef, prefix, exponent):

        self.__Mole(unitdef, prefix, exponent)

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_LITRE)
        scale = 1
        multiplier = 1

        unitdef.addBaseUnit(
            kind,
            -1,
            scale,
            multiplier
        )

    def __Volume(self, unitdef, prefix, exponent):

        kind = libsbml.UnitKind_toString(
            libsbml.UNIT_KIND_LITRE
            )
        scale = self.__getPrefix(prefix)
        multiplier = 1

        unitdef.addBaseUnit(
            kind,
            exponent,
            scale,
            multiplier
        )

    def __Amount(self, unitdef, prefix, exponent):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_GRAM)
        scale = self.__getPrefix(prefix)
        multiplier = 1

        unitdef.addBaseUnit(
            kind,
            exponent,
            scale,
            multiplier
        )

    def __Seconds(self, unitdef, prefix, exponent):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_SECOND)
        scale = 1
        multiplier = 1

        unitdef.addBaseUnit(
            kind,
            exponent,
            scale,
            multiplier
        )

    def __Minutes(self, unitdef, prefix=None, exponent=1):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_SECOND)
        scale = 1
        multiplier = 60

        unitdef.addBaseUnit(
            kind,
            exponent,
            scale,
            multiplier
        )

    def __Hours(self, unitdef, prefix=None, exponent=1):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_SECOND)
        scale = 1
        multiplier = 60*60

        unitdef.addBaseUnit(
            kind,
            exponent,
            scale,
            multiplier
        )

    def __Celsius(self, unitdef, prefix=None, exponent=1):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_KELVIN)
        scale = 1
        multiplier = 1

        unitdef.addBaseUnit(
            kind,
            exponent,
            scale,
            multiplier
        )

    def __Kelvin(self, unitdef, prefix=None, exponent=1):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_KELVIN)
        scale = 1
        multiplier = 1

        unitdef.addBaseUnit(
            kind,
            exponent,
            scale,
            multiplier
        )

    def __Dimensionless(self, unitdef, prefix=None, exponent=1):

        kind = libsbml.UnitKind_toString(libsbml.UNIT_KIND_DIMENSIONLESS)
        scale = 1
        multiplier = 1

        unitdef.addBaseUnit(
            kind,
            exponent,
            scale,
            multiplier
        )

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
            raise KeyError(
                f"Prefix {prefix} is unknown. Please define unit manually"
            )

    def __Time(self, baseunit):

        if baseunit == "s" or baseunit == "sec" or baseunit == "seconds":
            return 1
        elif baseunit == "m" or baseunit == "min" or baseunit == "minutes":
            return 60
        elif baseunit == "h" or baseunit == "hours":
            return 60*60
        else:
            raise KeyError(
                f"Time unit {baseunit} is unknown. Please define unit manually"
            )
