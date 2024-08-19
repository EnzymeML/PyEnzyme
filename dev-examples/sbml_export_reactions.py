import pyenzyme as pe
import pyenzyme.equations as peq
from pyenzyme.sbml.serializer import to_sbml
from pyenzyme.tools import get_all_parameters
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

# Set reactions
reaction = peq.build_reaction(
    scheme="s0 -> s1",
    name="Reaction 1",
    id="r0",
    modifiers=[enzyme.id],
)

reaction.kinetic_law = peq.build_equation(
    "kcat * p0(t) * s0(t) / ( K_m + s0(t) )",
    unit_mapping={"kcat": 1 / s, "K_m": mM},
    enzmldoc=doc,
)

doc.reactions += [reaction]

doc.measurements += pe.read_excel(
    "tests/fixtures/tabular/data.xlsx",
    data_unit=mM,
    time_unit=s,
)

for parameter in get_all_parameters(doc):
    parameter.lower = 0.0
    parameter.upper = 100.0
    parameter.stderr = 0.1

for meas in doc.measurements:
    meas.temperature = 298.15
    meas.temperature_unit = K
    meas.ph = 7.0

# Write sbml doc to file
with open("./dev-examples/reactions/reactions_example.xml", "w") as file:
    file.write(to_sbml(doc)[0])

# Write to omex file
doc.to_sbml("./dev-examples/reactions/reactions_example.omex")

# Write to EnzymeML JSON file
pe.write_enzymeml(self=doc, path="./dev-examples/reactions/enzymeml.json")
