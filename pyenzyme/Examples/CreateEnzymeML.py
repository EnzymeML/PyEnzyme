'''
Created on 12.08.2020

@author: JR
'''

from pyenzyme.enzymeml.core import EnzymeMLDocument, Vessel, Reactant, EnzymeReaction, Replicate, Creator
from pyenzyme.enzymeml.tools import EnzymeMLWriter
import pandas as pd
from pyenzyme.enzymeml.core.protein import Protein

enzmldoc = EnzymeMLDocument('TEST', 3, 2)

creators = [ Creator("GNAME1", "FNAME1", "MAIL1"), Creator("GNAME2", "FNAME2", "MAIL2") ]
enzmldoc.setCreator(creators)

vessel = Vessel('name', 'v0', 10.0, 'l')
enzmldoc.setVessel(vessel)

reactant = Reactant("Substrate", "v0", 10.0, "mM", False)
enzmldoc.addReactant(reactant)

protein = Protein("EnzymeMLase", "ENZYMEML", "v0", 1.00, "nM")
enzmldoc.addProtein(protein)

reac = EnzymeReaction(30.0, "C", 7.0, "Enzyme Reaction", True)
reac.addEduct('s0', 1.0, True, enzmldoc)

repl = Replicate("replica", "s0", "conc", "mmole / l", "s", 100.00)
data = pd.Series([1,2,3,4,5,6,7])
data.Index = [1,2,3,4,5,6,7]
repl.setData(data)

reac.addReplicate(repl, enzmldoc)

enzmldoc.addReaction(reac)

writer = EnzymeMLWriter()
writer.toFile(enzmldoc, '../Resources/Examples/CreateEnzymeML')

enzmldoc.printUnits()
enzmldoc.printReactants()
enzmldoc.printProteins()
enzmldoc.printReactions()

enzmldoc.toFile('TEST')