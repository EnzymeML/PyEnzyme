import libsbml

from pyenzyme.enzymeml.tools.unitcreator import UnitCreator
from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument
from pyenzyme.enzymeml.core.unitdef import UnitDef


class TestUnitCreator:
    def test_primitive_units(self):
        """Tests if units are parsed correctly"""

        # ! Mole units
        name = "mole"
        expec, result = self._setup_test(name, libsbml.UNIT_KIND_MOLE, 1, 1, 1)
        assert result == expec, f"wrong {name} unit"

        # ! Volumetric units
        name = "l"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_LITRE, 1, 1, 1)
        assert res == expec, f"wrong {name} unit"

        name = "liter"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_LITRE, 1, 1, 1)
        assert res == expec, f"wrong {name} unit"

        name = "litre"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_LITRE, 1, 1, 1)
        assert res == expec, f"wrong {name} unit"

        # ! Weight units
        name = "g"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_GRAM, 1, 1, 1)
        assert res == expec, f"wrong {name} unit"

        name = "gram"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_GRAM, 1, 1, 1)
        assert res == expec, f"wrong {name} unit"

        # ! Time units
        name = "s"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_SECOND, 1, 1, 1)
        assert res == expec, f"wrong {name} unit"

        name = "sec"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_SECOND, 1, 1, 1)
        assert res == expec, f"wrong {name} unit"

        name = "second"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_SECOND, 1, 1, 1)
        assert res == expec, f"wrong {name} unit"

        name = "seconds"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_SECOND, 1, 1, 1)
        assert res == expec, f"wrong {name} unit"

        name = "min"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_SECOND, 1, 1, 60)
        assert res == expec, f"wrong {name} unit"

        name = "mins"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_SECOND, 1, 1, 60)
        assert res == expec, f"wrong {name} unit"

        name = "minutes"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_SECOND, 1, 1, 60)
        assert res == expec, f"wrong {name} unit"

        name = "h"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_SECOND, 1, 1, 60 * 60)
        assert res == expec, f"wrong {name} unit"

        name = "hour"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_SECOND, 1, 1, 60 * 60)
        assert res == expec, f"wrong {name} unit"

        name = "hours"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_SECOND, 1, 1, 60 * 60)
        assert res == expec, f"wrong {name} unit"

        # ! Temperature units
        name = "C"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_KELVIN, 1, 1, 1)
        expec["name"] = "K"
        assert res == expec, f"wrong {name} unit"

        name = "celsius"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_KELVIN, 1, 1, 1)
        expec["name"] = name
        assert res == expec, f"wrong {name} unit"

        name = "Celsius"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_KELVIN, 1, 1, 1)
        expec["name"] = name.lower()
        assert res == expec, f"wrong {name} unit"

        name = "K"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_KELVIN, 1, 1, 1)
        expec["name"] = name
        assert res == expec, f"wrong {name} unit"

        name = "kelvin"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_KELVIN, 1, 1, 1)
        expec["name"] = name
        assert res == expec, f"wrong {name} unit"

        name = "Kelvin"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_KELVIN, 1, 1, 1)
        expec["name"] = name.lower()
        assert res == expec, f"wrong {name} unit"

        # ! Dimensionless unit
        name = "dimensionless"
        expec, res = self._setup_test(name, libsbml.UNIT_KIND_DIMENSIONLESS, 1, 1, 1)
        assert res == expec, f"wrong {name} unit"

    def test_prefix(self):
        """Tests correct prefix parsing"""

        expec, res = self._setup_test("fmole", libsbml.UNIT_KIND_MOLE, 1, -15, 1)
        assert res == expec

        expec, res = self._setup_test("pmole", libsbml.UNIT_KIND_MOLE, 1, -12, 1)
        assert res == expec

        expec, res = self._setup_test("nmole", libsbml.UNIT_KIND_MOLE, 1, -9, 1)
        assert res == expec

        expec, res = self._setup_test("umole", libsbml.UNIT_KIND_MOLE, 1, -6, 1)
        assert res == expec

        expec, res = self._setup_test("mmole", libsbml.UNIT_KIND_MOLE, 1, -3, 1)
        assert res == expec

        expec, res = self._setup_test("cmole", libsbml.UNIT_KIND_MOLE, 1, -2, 1)
        assert res == expec

        expec, res = self._setup_test("dmole", libsbml.UNIT_KIND_MOLE, 1, -1, 1)
        assert res == expec

        expec, res = self._setup_test("mole", libsbml.UNIT_KIND_MOLE, 1, 1, 1)
        assert res == expec

    def test_composite_units(self, creator):
        """Tests rational and multiplicative units"""

        # Set up EnzymeMLDocument
        enzmldoc = EnzymeMLDocument(name="Test")

        # ! Single rational
        # Create result
        id = creator.getUnit("mole / l", enzmldoc)
        res = enzmldoc._unit_dict[id].dict(exclude={"id", "meta_id", "ontology"})

        # Create expectation
        expec = UnitDef(name="mole / l")
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE), 1, 1, 1)
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_LITRE), -1, 1, 1)
        expec = expec.dict(exclude={"id", "meta_id", "ontology"})

        assert res == expec

        # ! Multiple rationals
        # Create result
        id = creator.getUnit("mole g / l s", enzmldoc)
        res = enzmldoc._unit_dict[id].dict(exclude={"id", "meta_id", "ontology"})

        # Create expectation
        expec = UnitDef(name="g mole / l s")
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE), 1, 1, 1)
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_GRAM), 1, 1, 1)
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_LITRE), -1, 1, 1)
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_SECOND), -1, 1, 1)
        expec = expec.dict(exclude={"id", "meta_id", "ontology"})

        assert res == expec

        # ! Potentiated units
        # Create result
        id = creator.getUnit("mole^2", enzmldoc)
        res = enzmldoc._unit_dict[id].dict(exclude={"id", "meta_id", "ontology"})

        # Create expectation
        expec = UnitDef(name="mole^2")
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE), 2, 1, 1)
        expec = expec.dict(exclude={"id", "meta_id", "ontology"})

        assert res == expec

        # ! Potentiated rational units
        # Create result
        id = creator.getUnit("mole^2 / l^4", enzmldoc)
        res = enzmldoc._unit_dict[id].dict(exclude={"id", "meta_id", "ontology"})

        # Create expectation
        expec = UnitDef(name="mole^2 / l^4")
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE), 2, 1, 1)
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_LITRE), -4, 1, 1)
        expec = expec.dict(exclude={"id", "meta_id", "ontology"})

        assert res == expec

        # ! Potentiated multiple rational units
        # Create result
        id = creator.getUnit("mole^2 g^3 / l^4 s", enzmldoc)
        res = enzmldoc._unit_dict[id].dict(exclude={"id", "meta_id", "ontology"})

        # Create expectation
        expec = UnitDef(name="g^3 mole^2 / l^4 s")
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_MOLE), 2, 1, 1)
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_GRAM), 3, 1, 1)
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_LITRE), -4, 1, 1)
        expec.addBaseUnit(libsbml.UnitKind_toString(libsbml.UNIT_KIND_SECOND), -1, 1, 1)
        expec = expec.dict(exclude={"id", "meta_id", "ontology"})

        assert res == expec

    # ! Helper methods
    def _setup_test(self, name, kind, exponent, scale, multiplier):
        """Sets up a test case to reduce boilerplate code"""
        return (
            self._create_expectation(name, kind, exponent, scale, multiplier),
            self._create_result(name),
        )

    @staticmethod
    def _create_expectation(name, kind, exponent, scale, multiplier):
        """Creates a UnitDef to compare against result of UnitCreator"""

        # Create blank unit definition
        unitdef = UnitDef(name=name)

        # Add base unit
        unitdef.addBaseUnit(
            libsbml.UnitKind_toString(kind), exponent, scale, multiplier
        )

        return unitdef.dict(exclude={"id", "meta_id", "ontology"})

    @staticmethod
    def _create_result(name):
        """Sets up UnitCreator process and return the UnitDef"""

        # Initialize blank document and UnitCreator
        enzmldoc = EnzymeMLDocument(name="Test")
        creator = UnitCreator()

        # Create unit and store ID
        id = creator.getUnit(name, enzmldoc)

        return enzmldoc._unit_dict[id].dict(exclude={"id", "meta_id", "ontology"})
