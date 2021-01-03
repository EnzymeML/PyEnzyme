from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core import EnzymeMLDocument, EnzymeReaction, Vessel, Protein, Reactant, Creator 
from pyenzyme.enzymeml.models import KineticModel
from pyenzyme.enzymeml.tools import EnzymeMLReader, EnzymeMLWriter

enzmldoc = EnzymeMLDocument('TEST')
enzmldoc.setDoi('DOI_TEST')
enzmldoc.setPubmedID('PMID_TEST')
enzmldoc.setUrl('URL_TEST')

author = Creator('FAMILY_TEST', 'GIVEN_TEST', 'MAIL_TEST')
enzmldoc.setCreator(author)
print(author)

vessel = Vessel('VESSEL_TEST', 'v0', 10.0, 'ml')
ves_id = enzmldoc.setVessel(vessel)
print(vessel)

protein = Protein('PROTEIN_TEST', 'SEQ_TEST', ves_id, 10.0, 'mmole / l', True)
prot_id = enzmldoc.addProtein(protein)
print(protein)

substrate = Reactant('TEST_REAC1', ves_id, 10.0, 'mmole / l', False)
substrate.setSmiles('TEST_SMILES')
substrate.setInchi('TEST_INCHI')
print(substrate)

sub_id = enzmldoc.addReactant(substrate)

product = Reactant('TEST_REAC2', ves_id, 10.0, 'mmole / l', True)
product.setSmiles('TEST_SMILES')
product.setInchi('TEST_INCHI')

prod_id = enzmldoc.addReactant(product)

reac = EnzymeReaction(10.0, 'C', 7.0, 'TEST_REACT', True)
reac.addEduct(sub_id, 1.0, False, enzmldoc)
reac.addProduct(prod_id, 1.0, False, enzmldoc)
reac.addModifier(prot_id, 1.0, True, enzmldoc)

data = [1,2,3,4,5]
time = [1,2,3,4,5]

repl = Replicate('TEST_REPL', sub_id, 'conc', 'mmole / l', 's')
repl.setData(data, time)
reac.addReplicate(repl, enzmldoc)
print(repl)

equation = f"x_{sub_id}*{sub_id}"
parameters = {f"x_{sub_id}": (10.0, 'mmole / l')}
km = KineticModel(equation, parameters)
print(km)

reac.setModel(km)

reac_id = enzmldoc.addReaction(reac)

import json
with open('example.json', 'w') as f:
    json.dump(enzmldoc.toJSON(d=True), f, indent=4)