
import os
from pyenzyme import EnzymeMLDocument
from pyenzyme.enzymeml import Vessel, Protein, Reactant, EnzymeReaction, Measurement, Replicate, Creator
from pyenzyme.enzymeml.models import KineticModel

# Initialize EnzymeML document
enzmldoc = EnzymeMLDocument(name="Test")

# Define creators
creator1 = Creator(family_name="Family", given_name="Given",
                   mail="Mail@mail.de")
enzmldoc.setCreator(creator1)

# Define vessel
vessel = Vessel(name="Test_Vessel", id_="v0", size=10.0, unit="ml")
vessel_id = enzmldoc.setVessel(vessel)

# Define proteins
protein1 = Protein(name="PROTEIN1", sequence="ENZYMMALLAL",
                   vessel=vessel_id, init_conc=0.0, substanceunits="mmole / l", uniprotid="UNIPROTID", organism="ORGANISM", organismTaxId="ORGANISM_TAX_ID", ecnumber="1.1.1.1")
protein1_id = enzmldoc.addProtein(protein1)

protein2 = Protein(name="PROTEIN2", sequence="ENZYMMALLAL",
                   vessel=vessel_id, init_conc=10.0, substanceunits="mmole / l", uniprotid="UNIPROTID", organism="ORGANISM", organismTaxId="ORGANISM_TAX_ID", ecnumber="1.1.1.1")
protein2_id = enzmldoc.addProtein(protein2)

# Define reactants
substrate1 = Reactant(name="SUBSTRATE1", vessel=vessel_id,
                      init_conc=0.0, substanceunits="mmole / l", inchi="INCHI", smiles="SMILES")
substrate1_id = enzmldoc.addReactant(substrate1)

substrate2 = Reactant(name="SUBSTRATE2", vessel=vessel_id,
                      init_conc=10.0, substanceunits="mmole / l", inchi="INCHI", smiles="SMILES")
substrate2_id = enzmldoc.addReactant(substrate2)

substrate3 = Reactant(name="SUBSTRATE3", vessel=vessel_id,
                      init_conc=10.0, substanceunits="mmole / l", inchi="INCHI", smiles="SMILES")
substrate3_id = enzmldoc.addReactant(substrate3)

product1 = Reactant(name="PRODUCT1", vessel=vessel_id,
                    init_conc=10.0, substanceunits="mmole / l", inchi="INCHI", smiles="SMILES")
product1_id = enzmldoc.addReactant(product1)

product2 = Reactant(name="PRODUCT2", vessel=vessel_id,
                    init_conc=10.0, substanceunits="mmole / l", inchi="INCHI", smiles="SMILES")
product2_id = enzmldoc.addReactant(product2)

# Define Reactions

# Reaction 1
reaction1 = EnzymeReaction(
    name="REACTION1", temperature=30.0, tempunit="C", ph=10.0, reversible=True)

reaction1.addEduct(
    speciesID=substrate1_id, stoichiometry=1.0, isConstant=False, enzmldoc=enzmldoc)
reaction1.addProduct(
    speciesID=product1_id, stoichiometry=1.0, isConstant=False, enzmldoc=enzmldoc)
reaction1.addModifier(
    speciesID=protein1_id, stoichiometry=1.0, isConstant=False, enzmldoc=enzmldoc)

# Do some modeling and finally add the appropriate kinetics
kl1 = KineticModel(
    name="KineticLawName1",
    equation=f"{substrate1_id}*p_aram + {product1_id}",
    parameters={"p_param": (10.0, "mmole / l")},
    enzmldoc=enzmldoc
)


reaction1_id = enzmldoc.addReaction(reaction1)

# Reaction 2
reaction2 = EnzymeReaction(
    name="REACTION2", temperature=30.0, tempunit="celsius", ph=10.0, reversible=True)

reaction2.addEduct(
    speciesID=substrate2_id, stoichiometry=1.0, isConstant=False, enzmldoc=enzmldoc)
reaction2.addEduct(
    speciesID=substrate3_id, stoichiometry=1.0, isConstant=False, enzmldoc=enzmldoc)
reaction2.addProduct(
    speciesID=product2_id, stoichiometry=1.0, isConstant=False, enzmldoc=enzmldoc)
reaction2.addModifier(
    speciesID=protein2_id, stoichiometry=1.0, isConstant=False, enzmldoc=enzmldoc)

kl2 = KineticModel(
    name="KineticLawName2",
    equation=f"{substrate1_id}*p_aram + {product1_id}",
    parameters={"p_param": (10.0, "dimensionless")},
    enzmldoc=enzmldoc
)

reaction2.setModel(kl2)

reaction2_id = enzmldoc.addReaction(reaction2)

# Define a measurement
measurement = Measurement(name="TEST_MEAS1")

# Create replicates to further add them to the measurement
repl1 = Replicate(replica="repl1", reactant=substrate1_id, type_="conc",
                  data_unit="mmole / l", time_unit="s",
                  data=[1, 1, 1, 1, 1, 1], time=[1, 2, 3, 4, 5, 6])
repl2 = Replicate(replica="repl2", reactant=product1_id, type_="conc",
                  data_unit="mmole / l", time_unit="s",
                  data=[1, 1, 1, 1, 1, 1], time=[1, 2, 3, 4, 5, 6])
repl3 = Replicate(replica="repl3", reactant=substrate2_id, type_="conc",
                  data_unit="mmole / l", time_unit="s",
                  data=[1, 1, 1, 1, 1, 1], time=[1, 2, 3, 4, 5, 6])
repl4 = Replicate(replica="repl4", reactant=product2_id, type_="conc",
                  data_unit="mmole / l", time_unit="s",
                  data=[1, 1, 1, 1, 1, 1], time=[1, 2, 3, 4, 5, 6])

# Please note, each species can only obtain a single initical concentryxixon.
# Hence adding replicates with different initial concentration will throw an error

# One measurement but taken over the course of two distinct reactions

# Reaction 1
measurement.addData(reactantID=substrate1_id,
                    initConc=10.0, unit="dimensionless")
measurement.addData(reactantID=product1_id,
                    initConc=10.0, unit="mmole / l")
measurement.addData(proteinID=protein1_id,
                    initConc=100.0, unit="umole / l")

# Reaction 2
measurement.addData(reactantID=substrate2_id,
                    initConc=10.0, unit="mmole / l", replicates=[repl3])
measurement.addData(reactantID=substrate3_id,
                    initConc=10.0, unit="mmole / l")
measurement.addData(reactantID=product2_id,
                    initConc=10.0, unit="mmole / l", replicates=[repl4])
measurement.addData(proteinID=protein2_id,
                    initConc=50.0, unit="umole / l")

# Add replicates
measurement.addReplicates(repl1)
measurement.addReplicates(repl2)

enzmldoc.getReaction(reaction1_id).setModel(kl1)
enzmldoc.getReaction(reaction2_id).setModel(kl2)

# Finally add to the EnzymeML document
measurementID = enzmldoc.addMeasurement(measurement)

# Add an arbitrary file
enzmldoc.addFile(
    filepath="./examples/CreateEnzymeML/CreateEnzymeML_Measurements.py"
)

enzmldoc.toFile(".")

# Read EnzymeML document
enzmldoc = EnzymeMLDocument.fromFile("./examples/CreateEnzymeML/Test.omex")
meas = enzmldoc.getMeasurement("m0")

print(enzmldoc.toJSON())
