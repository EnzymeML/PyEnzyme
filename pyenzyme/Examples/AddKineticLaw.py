'''
Created on 12.08.2020

@author: JR
'''

from pyenzyme.enzymeml.tools import EnzymeMLReader, EnzymeMLWriter
from pyenzyme.enzymeml.models.kineticmodel import KineticModel

# Read EnzymeML
enzmldoc = EnzymeMLReader().readFromFile('../Resources/Examples/AddKineticLaw/Original/TEST.omex', omex=True)
enzmldoc.setName("Modified")

# Get reaction
reaction = enzmldoc.getReactionDict()['r0']

# create kinetic model
equation = "(vmax*s1)/(Km + s1)"

parameters = {
        
        'Km': 10.0,
        'vmax': 2.5
        
    }

kineticmodel = KineticModel(equation, parameters)

# Set KineticModel for reaction
reaction.setModel(kineticmodel)

print('Added Kinetic Model\n')
print(">>>>>  " + enzmldoc.getReactionDict()['r0'].getModel().getEquation())

for key, item in enzmldoc.getReactionDict()['r0'].getModel().getParameters().items():
    
    print(">>>>>  " + key, ' : ', item)

# Write to new EnzymeML-File
writer = EnzymeMLWriter()
writer.toFile( enzmldoc, '../Resources/Examples/AddKineticLaw' )

print( '\nFile has been written to: ../Resources/Examples/AddKineticLaw/' + enzmldoc.getName() )