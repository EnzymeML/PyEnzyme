'''
File: CreateEnzymeML.py
Project: CreateEnzymeML
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 12:33:32 am
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pyenzyme.enzymeml.core import EnzymeMLDocument, Vessel, Reactant, \
    EnzymeReaction, Replicate, Creator
from pyenzyme.enzymeml.tools import EnzymeMLWriter
from pyenzyme.enzymeml.models import KineticModel
from pyenzyme.enzymeml.core.protein import Protein

enzmldoc = EnzymeMLDocument('TEST', 3, 2)

creators = [
    Creator("GNAME1", "FNAME1", "MAIL1"),
    Creator("GNAME2", "FNAME2", "MAIL2")
]

enzmldoc.setCreator(creators)

enzmldoc.setDoi('DOI_TEST')
enzmldoc.setUrl('URL_TEST')
enzmldoc.setPubmedID('PUBMED_ID')

vessel = Vessel(
    name="Vessel",
    id_='v0',
    size=10.0,
    unit='ml'
)
vessel = enzmldoc.setVessel(vessel)

substrate = Reactant(
    name="Substrate",
    vessel=vessel,
    init_conc=10.0,
    substanceunits="mM",
    constant=False,
    smiles="SMILESTEST",
    inchi="InChITEST"
)


product = Reactant(
    name="Product",
    vessel=vessel,
    init_conc=0.0,
    substanceunits="mM",
    constant=False,
    smiles="SMILESTEST2",
    inchi="InChITEST2"
)

substrate = enzmldoc.addReactant(substrate)
product = enzmldoc.addReactant(product)

protein = Protein(
    name="Protein",
    vessel=vessel,
    sequence="EnzymeMLASE",
    init_conc=10.0,
    substanceunits="nM",
    constant=True,
    ecnumber='EC:1.2.3.4'
)

protein = enzmldoc.addProtein(protein)

reaction = EnzymeReaction(
    temperature=10.0,
    tempunit='C',
    ph=7.0,
    name="TEST_REACTION",
    reversible=True
)

# Create reaction equation
reaction.addEduct(
    speciesID=substrate,
    stoichiometry=1.0,
    isConstant=False,
    enzmldoc=enzmldoc
)

reaction.addProduct(
    speciesID=product,
    stoichiometry=1.0,
    isConstant=False,
    enzmldoc=enzmldoc,
    initConcs=[
        (10.0, 'mM'),
        (20.0, 'mM')
    ]
)

reaction.addModifier(
    speciesID=protein,
    stoichiometry=1.0,
    isConstant=True,
    enzmldoc=enzmldoc
)

replicate1 = Replicate(
    replica="Repl1",
    reactant=substrate,
    type_="conc",
    measurement="m0",
    data_unit="mM",
    time_unit="s",
    init_conc=10.0
)

replicate2 = Replicate(
    replica="Repl2",
    reactant=substrate,
    type_="conc",
    measurement="m0",
    data_unit="mM",
    time_unit="s",
    init_conc=100.0
)

data = [1, 2, 3, 4, 5, 6, 7]
time = [0, 2, 3, 4, 5, 6, 7]

replicate1.setData(data, time)
replicate2.setData(data, time)

reaction.addReplicate(
    replicate1,
    enzmldoc
)

reaction.addReplicate(
    replicate2,
    enzmldoc
)

km = KineticModel(
    "vmax * s0 / ( s0 + Km )",
    parameters={
        'vmax': (10.0, 'mM / s'),
        'Km': (4.0, 'mM')
    },
    enzmldoc=enzmldoc
)

reaction.setModel(km)
enzmldoc.addReaction(reaction)

writer = EnzymeMLWriter()
writer.toFile(enzmldoc, '.')
