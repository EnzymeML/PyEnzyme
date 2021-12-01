from pyenzyme import EnzymeMLDocument, Vessel, Protein, Reactant

# Initialize the EnzymeMLDocument clas
enzmldoc = EnzymeMLDocument(name="First example")

# Create a vessel object
vessel = Vessel(name="Falcon Tube", volume=10.0, unit="ml")
vessel_id = enzmldoc.addVessel(vessel)

# Create a protein object from the UniProt database (Alcohol Dehydrogenase)
adh = Protein(
    uniprotid="P07327", vessel_id=vessel_id,
    init_conc=10.0, unit="mmole / l"
)

adh_id = enzmldoc.addProtein(adh)

# Create a custom reactant object
ethanol = Reactant(
    name="Ethanol", vessel_id=vessel_id,
    init_conc=20.0, unit="mmole / l"
)

ethanol_id = enzmldoc.addReactant(ethanol)
