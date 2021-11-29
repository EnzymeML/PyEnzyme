from pyenzyme.enzymeml import EnzymeMLDocument, Vessel, Reactant, Protein, EnzymeReaction, Measurement, Replicate
from pyenzyme.enzymeml.models import MichaelisMenten
from pyenzyme.enzymeml.core.ontology import DataTypes

enzmldoc = EnzymeMLDocument(name="Hello")

# Vessel
vessel = Vessel(name="Vessel", volume=10.0, unit="ml")
vessel_id = enzmldoc.addVessel(vessel)


# Protein
protein = Protein(name="Protein", sequence="Sequence",
                  vessel_id=vessel_id, init_conc=10.0, unit="mmole / l", constant=True, uniprotid="lololol")

protein_id = enzmldoc.addProtein(protein)

# Reactant
substrate = Reactant(name="Substrate", vessel_id=vessel_id,
                     init_conc=10.0, unit="mmole / l")
substrate_id = enzmldoc.addReactant(substrate)

product = Reactant(name="Product", vessel_id=vessel_id,
                   init_conc=10.0, unit="mmole / l")
product_id = enzmldoc.addReactant(product)

# Reaction
reaction = EnzymeReaction(name="Reaction", temperature=100.0,
                          temperature_unit="C", ph=7.0, reversible=True)

reaction.addEduct(species_id=substrate_id, stoichiometry=1.0,
                  constant=False, enzmldoc=enzmldoc)

reaction.addProduct(species_id=product_id, stoichiometry=1.0,
                    constant=False, enzmldoc=enzmldoc)

reaction.addModifier(species_id=protein_id, stoichiometry=1.0,
                     constant=True, enzmldoc=enzmldoc)

# Add a kinetic law
kinetic_law = MichaelisMenten(
    kcat_val=100.0,
    kcat_unit="mmole / l",
    km_val=10.0,
    km_unit="mmole / l",
    substrate_id=substrate_id,
    protein_id=protein_id,
    enzmldoc=enzmldoc
)

reaction.model = kinetic_law

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

meas = enzmldoc.getMeasurement(meas2_id)
meas.unifyUnits(kind="mole", scale=0, enzmldoc=enzmldoc)


print(enzmldoc)

exit()

data = enzmldoc.exportMeasurementData()

enzmldoc.toFile('.')

enzmldoc = EnzymeMLDocument.fromFile(
    f"./{enzmldoc.name.replace(' ', '_')}.omex")

print(enzmldoc.json())
