from pyenzyme.enzymeml.core import EnzymeMLDocument, Protein, Reactant, Vessel, Creator, EnzymeReaction, Replicate
from pyenzyme.enzymeml.models import KineticModel, MichaelisMenten
import numpy as np
import json

def getEnzymeDataField(typename, multiple, value, typeclass):
    
    return {
        
        "typeName": typename,
        "multiple": multiple,
        "typeClass": typeclass,
        "value": value
    }

# initialize Document
enzmldoc = EnzymeMLDocument("Test_Data")
enzmldoc.setPubmedID("TEST_PUBMEDID")
enzmldoc.setUrl("TEST_URL")
enzmldoc.setDoi("TEST_DOI")

# add Creator
creator = Creator("FNAME", "GNAME", "test@gmail.com")
enzmldoc.setCreator(creator)

# add Vessel
vessel = Vessel("TEST_VESSEL", "v0", 10.0, "ml")
vessel_id = enzmldoc.setVessel(vessel)


# add Protein
protein = Protein("TEST_PROT", "MLPV", vessel_id, 10.0, "mmole / l", ecnumber="EC_TEST", uniprotid="UNIPROT_TEST")
protein_id = enzmldoc.addProtein(protein)

# add substrate
substrate = Reactant("TEST_SUB", vessel_id, 10.0, "mmole / l", False, "TEST_SMILES", "TEST_INCHI")
substrate_id = enzmldoc.addReactant(substrate)

# add product
product = Reactant("TEST_PROD", vessel_id, 10.0, "mmole / l", False, "TEST_SMILES2", "TEST_INCHI2")
product_id = enzmldoc.addReactant(product)

# create reaction
reaction = EnzymeReaction(37.0, "C", 7.0, "TEST_REAC", True)

# add elements
reaction.addEduct(substrate_id, 1.0, False, enzmldoc)
reaction.addProduct(product_id, 1.0, False, enzmldoc)
reaction.addModifier(protein_id, 1.0, True, enzmldoc)

# create replicates
sub_repl = Replicate("repl0", substrate_id, "conc", "mmole / l", "s", data = np.linspace(0,100,100).tolist(), time = np.linspace(0,100,100).tolist())
reaction.addReplicate(sub_repl, enzmldoc)

# add kineticmodel
km = MichaelisMenten(10.0, "mole / s", 1.0, "mmole / l", substrate_id)
reaction.setModel(km)

# add to EnzymeML document
enzmldoc.addReaction(reaction)

def trackVessel(enzmldoc):

    instances = list()
    
    vessel = enzmldoc.getVessel()
    
    field = {
        
        "enzymeMLVesselId": getEnzymeDataField( "enzymeMLVesselId", False, vessel.getId(), "primitive" ),
        "enzymeMLVesselName": getEnzymeDataField( "enzymeMLVesselName", False, vessel.getName(), "primitive" ),
        "enzymeMLVesselSize": getEnzymeDataField( "enzymeMLVesselSize", False, vessel.getSize(), "primitive" ),
        "enzymeMLVesselUnits": getEnzymeDataField( "enzymeMLVesselUnits", False, enzmldoc.getUnitDict()[vessel.getUnit()].getName(), "controlledVocabulary" ),
        "enzymeMLVesselConstant": getEnzymeDataField( "enzymeMLVesselConstant", False, vessel.getConstant(), "primitive")
    }
    
    instances.append(field)
    
    parentblock = getEnzymeDataField("enzymeMLVessel", True, instances, "compound")
    
    
    return parentblock

def trackReactants(enzmldoc):
    
    instances = list()
    
    for reactant in enzmldoc.getReactantDict().values():
        
        field = {
            
            "enzymeMLReactantId": getEnzymeDataField("enzymeMLReactantId", False, reactant.getId(), "primitive"),
            "enzymeMLReactantName": getEnzymeDataField("enzymeMLReactantName", False, reactant.getName(), "primitive"),
            "enzymeMLReactantVessel": getEnzymeDataField("enzymeMLReactantVessel", False, reactant.getCompartment(), "primitive"),
            "enzymeMLReactantInitialConcentration": getEnzymeDataField("enzymeMLReactantInitialConcentration", False, reactant.getInitConc(), "primitive"),
            "enzymeMLReactantSubstanceUnits": getEnzymeDataField("enzymeMLReactantSubstanceUnits", False, enzmldoc.getUnitDict()[reactant.getSubstanceUnits()].getName(), "controlledVocabulary"),
            "enzymeMLReactantConstant": getEnzymeDataField("enzymeMLReactantConstant", False, reactant.getConstant(), "controlledVocabulary"),
            "enzymeMLReactantInchi": getEnzymeDataField("enzymeMLReactantInchi", False, reactant.getInchi(), "primitive"),
            "enzymeMLReactantSmiles": getEnzymeDataField("enzymeMLReactantSmiles", False, reactant.getSmiles(), "primitive")
            
        }
        
        instances.append(field)
        
    parentblock = getEnzymeDataField("enzymeMLReactant", True, instances, "compound")
    
    return parentblock

def trackProteins(enzmldoc):
    
    instances = list()
    
    for protein in enzmldoc.getProteinDict().values():
        
        field = {
            
            "enzymeMLProteinId": getEnzymeDataField("enzymeMLProteinId", False, protein.getId(), "primitive"),
            "enzymeMLProteinName": getEnzymeDataField("enzymeMLProteinName", False, protein.getName(), "primitive"),
            "enzymeMLProteinVessel": getEnzymeDataField("enzymeMLProteinVessel", False, protein.getCompartment(), "primitive"),
            "enzymeMLProteinInitialConcentration": getEnzymeDataField("enzymeMLProteinInitialConcentration", False, protein.getInitConc(), "primitive"),
            "enzymeMLProtenSubstanceUnits": getEnzymeDataField("enzymeMLProtenSubstanceUnits", False, enzmldoc.getUnitDict()[protein.getSubstanceUnits()].getName(), "controlledVocabulary"),
            "enzymeMLProteinConstant": getEnzymeDataField("enzymeMLProteinConstant", False, protein.getConstant(), "controlledVocabulary"),
            "enzymeMLProteinSequence": getEnzymeDataField("enzymeMLProteinSequence", False, protein.getSequence(), "primitive"),
            "enzymeMLProteinOrganism": getEnzymeDataField("enzymeMLProteinOrganism", False, protein.getOrganism(), "primitive"),
            "enzymeMLProteinUniProtID": getEnzymeDataField("enzymeMLProteinUniProtID", False, protein.getUniprotID(), "primitive"),
            "enzymeMLProteinECNumber": getEnzymeDataField("enzymeMLProteinECNumber", False, protein.getEcnumber(), "primitive")
            
        }
        
        instances.append(field)
        
    parentblock = getEnzymeDataField("enzymeMLProtein", True, instances, "compound")
        
    return parentblock

def trackReactions(enzmldoc):
    
    instances = list()
    
    for reaction in enzmldoc.getReactionDict():
        
        field = {
            
            "enzymeMLReactionName": getEnzymeDataField("enzymeMLReactionName", False, reaction.getName())
            
        }