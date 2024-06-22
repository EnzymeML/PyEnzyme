from pyenzyme.model import UnitType
from pyenzyme.tools import read_static_file

from .units import BaseUnit, UnitDefinition, Prefix

BaseUnit.model_rebuild()
UnitDefinition.model_rebuild()

ONTOMAPS = read_static_file("pyenzyme.units", "ontomaps.toml")


class Unit:
    @staticmethod
    def mol():
        return BaseUnit(kind=UnitType.MOLE, exponent=1, scale=1)

    @staticmethod
    def litre():
        return BaseUnit(kind=UnitType.LITRE, exponent=1, scale=1)

    @staticmethod
    def second():
        return BaseUnit(kind=UnitType.SECOND, exponent=1, scale=1)

    @staticmethod
    def minute():
        return BaseUnit(kind=UnitType.SECOND, exponent=1, scale=1, multiplier=60)

    @staticmethod
    def hour():
        hour = 60 * 60
        return BaseUnit(kind=UnitType.SECOND, exponent=1, scale=1, multiplier=hour)

    @staticmethod
    def day():
        day = 60**2 * 24
        return BaseUnit(kind=UnitType.SECOND, exponent=1, scale=1, multiplier=day)

    @staticmethod
    def gram():
        return BaseUnit(kind=UnitType.GRAM, exponent=1, scale=1)

    @staticmethod
    def kelvin():
        return BaseUnit(kind=UnitType.KELVIN, exponent=1, scale=1)

    @staticmethod
    def dimensionless():
        return BaseUnit(kind=UnitType.DIMENSIONLESS, exponent=1, scale=1)


###### Single Prefixes ######

k = Prefix.k
m = Prefix.m
u = Prefix.u
n = Prefix.n

##### Predefined units #####

# Dimensionless
dimensionless = UnitDefinition(base_units=[Unit.dimensionless()])

# Molarity
M = Unit.mol() / Unit.litre()
mM = m * Unit.mol() / Unit.litre()
uM = u * Unit.mol() / Unit.litre()
nM = n * Unit.mol() / Unit.litre()

## Ontology
M.ld_id = ONTOMAPS["molarity"]["M"]
mM.ld_id = ONTOMAPS["molarity"]["mM"]
uM.ld_id = ONTOMAPS["molarity"]["uM"]
nM.ld_id = ONTOMAPS["molarity"]["nM"]

# Substance
mol = UnitDefinition(base_units=[Unit.mol()])._get_name()
mmol = UnitDefinition(base_units=[m * Unit.mol()])._get_name()
umol = UnitDefinition(base_units=[u * Unit.mol()])._get_name()
nmol = UnitDefinition(base_units=[n * Unit.mol()])._get_name()

## Ontology
mol.ld_id = ONTOMAPS["substance"]["mol"]
mmol.ld_id = ONTOMAPS["substance"]["mmol"]
umol.ld_id = ONTOMAPS["substance"]["umol"]
nmol.ld_id = ONTOMAPS["substance"]["nmol"]

# Mass
gram = UnitDefinition(base_units=[Unit.gram()])._get_name()
g = UnitDefinition(base_units=[Unit.gram()])._get_name()
mg = UnitDefinition(base_units=[m * Unit.gram()])._get_name()
ug = UnitDefinition(base_units=[u * Unit.gram()])._get_name()
ng = UnitDefinition(base_units=[n * Unit.gram()])._get_name()
kg = UnitDefinition(base_units=[k * Unit.gram()])._get_name()

## Ontology
g.ld_id = ONTOMAPS["mass"]["g"]
gram.ld_id = ONTOMAPS["mass"]["g"]
mg.ld_id = ONTOMAPS["mass"]["mg"]
ug.ld_id = ONTOMAPS["mass"]["ug"]
ng.ld_id = ONTOMAPS["mass"]["ng"]

# Volume
litre = UnitDefinition(base_units=[Unit.litre()])._get_name()
l = UnitDefinition(base_units=[Unit.litre()])._get_name()  # noqa: E741
ml = UnitDefinition(base_units=[m * Unit.litre()])._get_name()
ul = UnitDefinition(base_units=[u * Unit.litre()])._get_name()
nl = UnitDefinition(base_units=[n * Unit.litre()])._get_name()

## Ontology

l.ld_id = ONTOMAPS["volume"]["litre"]
litre.ld_id = ONTOMAPS["volume"]["litre"]
ml.ld_id = ONTOMAPS["volume"]["ml"]
ul.ld_id = ONTOMAPS["volume"]["ul"]
nl.ld_id = ONTOMAPS["volume"]["nl"]

# Time
second = UnitDefinition(base_units=[Unit.second()])._get_name()
s = UnitDefinition(base_units=[Unit.second()])._get_name()
minute = UnitDefinition(base_units=[Unit.minute()])._get_name()
min = UnitDefinition(base_units=[Unit.minute()])._get_name()
hour = UnitDefinition(base_units=[Unit.hour()])._get_name()
h = UnitDefinition(base_units=[Unit.hour()])._get_name()
day = UnitDefinition(base_units=[Unit.day()])._get_name()
d = UnitDefinition(base_units=[Unit.day()])._get_name()

## Ontology
s.ld_id = ONTOMAPS["time"]["s"]
second.ld_id = ONTOMAPS["time"]["s"]
minute.ld_id = ONTOMAPS["time"]["min"]
min.ld_id = ONTOMAPS["time"]["min"]
hour.ld_id = ONTOMAPS["time"]["hour"]
h.ld_id = ONTOMAPS["time"]["hour"]
day.ld_id = ONTOMAPS["time"]["day"]
d.ld_id = ONTOMAPS["time"]["day"]

# Temperature

kelvin = UnitDefinition(base_units=[Unit.kelvin()])._get_name()
K = UnitDefinition(base_units=[Unit.kelvin()])._get_name()

## Ontology

K.ld_id = ONTOMAPS["temperature"]["K"]
kelvin.ld_id = ONTOMAPS["temperature"]["K"]
