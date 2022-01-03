from pyenzyme.enzymeml import EnzymeMLDocument, Vessel, Reactant, Protein, EnzymeReaction, Measurement, Replicate
from pyenzyme.enzymeml.models import MichaelisMenten
from pyenzyme.enzymeml.core.ontology import DataTypes

print(EnzymeMLDocument.schema_json(indent=2))
exit()

enzmldoc = EnzymeMLDocument(name="Hello")

# Vessel
vessel = Vessel(name="Vessel", volume=10.0, unit="ml")
vessel_id = enzmldoc.addVessel(vessel)


# Protein
protein = Protein(
    uniprotid="P12345",
    vessel_id=vessel_id,
    init_conc=10.0,
    unit="mmole / l"
)

protein_id = enzmldoc.addProtein(protein)

# Reactant
substrate = Reactant(
    chebi_id="15377",
    vessel_id=vessel_id,
    init_conc=10.0,
    unit="mmole / l"
)

substrate_id = enzmldoc.addReactant(substrate)

product = Reactant(
    chebi_id="25806",
    vessel_id=vessel_id,
    init_conc=10.0,
    unit="mmole / l"
)
product_id = enzmldoc.addReactant(product)

# Reaction
reaction = EnzymeReaction(
    name="Reaction",
    temperature=100.0,
    temperature_unit="C",
    ph=7.0,
    reversible=True
)

reaction.addEduct(species_id=substrate_id, stoichiometry=1.0,
                  constant=False, enzmldoc=enzmldoc)

reaction.addProduct(species_id=product_id, stoichiometry=1.0,
                    constant=False, enzmldoc=enzmldoc)

reaction.addModifier(species_id=protein_id, stoichiometry=1.0,
                     constant=True, enzmldoc=enzmldoc)

# Create a kinetic law
kinetic_law = MichaelisMenten(
    kcat_val=100.0,
    kcat_unit="mmole / l",
    km_val=10.0,
    km_unit="mmole / l",
    substrate_id=substrate_id,
    protein_id=protein_id,
    enzmldoc=enzmldoc
)

# Add it to the reaction
reaction.model = kinetic_law

# Add reaction to the EnzymeMLDocument
reaction_id = enzmldoc.addReaction(reaction)

# Measurements
measurement = Measurement(name="Measurement", global_time_unit="s")

replicate_substrate = Replicate(replicate_id="repl0", reactant_id=substrate_id, data_type=DataTypes.CONCENTRATION,
                                data_unit="mmole / l", time_unit="s", time=[1, 2, 3, 4, 5], data=[1, 2, 3, 4, 5])

measurement.addData(init_conc=10.0, reactant_id=substrate_id,
                    unit="mmole / l", replicates=[replicate_substrate])

meas1_id = enzmldoc.addMeasurement(measurement)

measurement2 = Measurement(name="Measurement2", global_time_unit="s")

replicate_substrate = Replicate(replicate_id="repl0", reactant_id=substrate_id, data_type=DataTypes.CONCENTRATION,
                                data_unit="mmole / l", time_unit="s", time=[1, 2, 3, 4, 5], data=[1, 2, 3, 4, 5])
measurement2.addData(init_conc=10.0, reactant_id=substrate_id,
                     unit="mmole / l", replicates=[replicate_substrate])


meas2_id = enzmldoc.addMeasurement(measurement2)

# enzmldoc.unifyMeasurementUnits(kind="mole", scale=1)

enzmldoc.toFile(path="examples/CreateEnzymeML/")

enzmldoc = EnzymeMLDocument.fromFile(path="examples/CreateEnzymeML/Hello.omex")

print(enzmldoc.json())
