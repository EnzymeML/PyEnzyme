import pyenzyme as pe
import pyenzyme.equations as peq

from pyenzyme.sbml.serializer import to_sbml
from pyenzyme.units import mM, s, ml, K

doc = pe.EnzymeMLDocument(name="Test")

# Add Vessels
vessel = doc.add_to_vessels(name="Vessel 1", volume=10.0, unit=ml, id="v0")

# Add Species
substrate = doc.add_to_small_molecules(id="s0", name="Substrate", vessel_id=vessel.id)
product = doc.add_to_small_molecules(id="s1", name="Product", vessel_id=vessel.id)

# Add Enzyme
enzyme = doc.add_to_proteins(
    id="p0",
    name="Enzyme",
    sequence="MTEY",
    vessel_id=vessel.id,
)

doc.equations += peq.build_equations(
    "s1'(t) = kcat * E_tot * s0(t) / (K_m + s0(t))",
    "E_tot = 100",
    units=[mM / s, mM],
    enzmldoc=doc,
)

doc.measurements += pe.read_excel(
    "tests/fixtures/tabular/data.xlsx",
    data_unit=mM,
    time_unit=s,
)

for meas in doc.measurements:
    meas.temperature = 298.15
    meas.temperature_unit = K
    meas.ph = 7.0

to_sbml(doc, "./dev-examples/odes/sbml.xml")
pe.write_enzymeml(doc=doc, path="./dev-examples/odes/enzymeml.json")
