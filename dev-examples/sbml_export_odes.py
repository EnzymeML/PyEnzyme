import pyenzyme as pe
import pyenzyme.equations as peq
from pyenzyme.sbml.serializer import to_sbml
from pyenzyme.tools import get_all_parameters
from pyenzyme.units import mM, s, ml, K

doc = pe.EnzymeMLDocument(name="Test")

ml.id = "u0"
s.id = "u1"
mM.id = "u2"
K.id = "u3"

# Add Vessels
vessel = doc.add_to_vessels(name="Vessel 1", volume=10.0, unit=ml, id="v0")

# Add Species
substrate = doc.add_to_small_molecules(
    id="s0",
    name="Substrate",
    vessel_id=vessel.id,
    canonical_smiles="CC(=O)O",
    inchikey="QTBSBXVTEAMEQO-UHFFFAOYSA-N",
)
product = doc.add_to_small_molecules(
    id="s1",
    name="Product",
    vessel_id=vessel.id,
    canonical_smiles="CC(=O)O",
    inchikey="QTBSBXVTEAMEQO-UHFFFAOYSA-N",
)

# Add Enzyme
enzyme = doc.add_to_proteins(
    id="p0",
    name="Enzyme",
    sequence="MTEY",
    vessel_id=vessel.id,
    ecnumber="1.1.1.1",
    organism="E.coli",
    organism_tax_id="12345",
)

enzyme_complex = doc.add_to_complexes(
    id="c0",
    name="Enzyme-Substrate Complex",
    participants=[enzyme.id, substrate.id],
)

doc.equations += peq.build_equations(
    "s1'(t) = kcat * E_tot * s0(t) / (K_m + s0(t))",
    "E_tot = 100",
    unit_mapping={"kcat": 1 / s, "K_m": mM, "E_tot": mM},
    enzmldoc=doc,
)

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
with open("./dev-examples/odes/odes_example.xml", "w") as file:
    file.write(to_sbml(doc)[0])

# Write to omex file
doc.to_sbml("./dev-examples/odes/odes_example.omex")

# Write to EnzymeML JSON file
pe.write_enzymeml(self=doc, path="./dev-examples/odes/enzymeml.json")
