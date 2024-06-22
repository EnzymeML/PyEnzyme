import pyenzyme as pe
import pyenzyme.equations as peq

from pyenzyme.sbml.serializer import to_sbml
from pyenzyme.units import mM, s, ml

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
    modifiers=[enzyme.id],
)
reaction.kinetic_law = peq.build_equation(
    "v(t) = kcat * p0(t) * s0(t) / ( K_m + s0(t) )",
    unit=mM / s,
)

doc.reactions += [reaction]

doc.measurements += pe.read_excel(
    "tests/fixtures/tabular/data.xlsx",
    data_unit=mM,
    time_unit=s,
)

to_sbml(doc, "./dev-examples/reactions/sbml.xml")
pe.write_enzymeml(doc=doc, path="./dev-examples/reactions/enzymeml.json")
