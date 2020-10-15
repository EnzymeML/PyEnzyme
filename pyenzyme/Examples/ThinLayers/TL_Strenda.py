'''
Created on 17.08.2020

@author: JR
'''

import xml.etree.ElementTree as ET
import numpy as np
from pyenzyme.enzymeml.core import EnzymeMLDocument
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.tools.enzymemlwriter import EnzymeMLWriter
from pyenzyme.enzymeml.models.kineticmodel import KineticModel

class ThinLayerStrendaML(object):


    def exportEnzymeML(self, path, out_dir):
        '''
        Args:
        ThinLayer interface from an .xml STRENDA-DB data model 
        to an .omex EnzymeML container.
        
            String path: Path to .xml file describing a STRENDA-DB entry
        '''
        
        # load xml data
        xml_string = open(path).read()
        
        xml_string = xml_string.replace('<sequenceModifiations value="yes"/>', '<sequenceModifiations value="yes">')
        
        root = ET.fromstring(xml_string)
        name = root.attrib["strendaId"]
        self.exp_name = root.find("experimentDescription").text.strip()
        
        # Initialize EnzymeMLDocument
        self.enzmldoc = EnzymeMLDocument(name, 3, 2)
        
        # Create references
        doi = root.attrib["doi"]
        self.enzmldoc.setDoi(doi)
        self.enzmldoc.setUrl("StrendaID:" + name)
        
        # Since no Vessel is given, it will be pre-defined with the unit
        vessel = Vessel("VesselUNK", "v0", 1.0, "l")
        self.enzmldoc.setVessel(vessel)
        
        # extract protein information
        self.__getProtein(root)
        
        # extract reaction and thus reactant information
        self.__getReactions(root)
        
        writer = EnzymeMLWriter()
        writer.toFile(self.enzmldoc, out_dir )
        #print(writer.toXMLString(self.enzmldoc))
        
    def __getReactions(self, root):
        
        # get all datasets in STRENDA XML
        datasets = root.find("datasets").findall("dataset")
        
        for i, dataset in enumerate(datasets):
            
            # Get meta information
            name = dataset.attrib["name"]
            assay_conds = dataset.find("assayConditions")
            temperature = float(assay_conds[2].attrib["value"])
            tempunit = assay_conds[2].attrib["unit"]
            ph = float(assay_conds[1].attrib["value"])
            
            reaction = EnzymeReaction(
                                        temperature, 
                                        tempunit,
                                        ph, 
                                        self.exp_name, 
                                        True
                                        )
            
            # add respective protein
            reaction.addModifier("p%i" % i, 1, True, self.enzmldoc)
            reaction.setName( 
                        
                        self.exp_name + " PConc: %.2f %s" % \
                        ( self.enzmldoc.getProtein("p%i" % i).getInitConc(),
                          self.enzmldoc.getUnitDict()[self.enzmldoc.getProtein("p%i" % i).getSubstanceUnits()].getName())
                        
                 )
            
            # add compounds to EnzymeMLDocument and reaction
            small_comps = assay_conds.findall("smallCompound")
            self.refID_dict = dict()
            
            for small_comp in small_comps:
                
                name = small_comp.find("name").text
                inchi = small_comp.find("inchi").text
                smiles = small_comp.find("smiles").text
                
                try:
                    stoich = float(small_comp.find("stoichiometry").text)
                except ValueError:
                    stoich = 'NULL'
                
                if "Range" in small_comp.find("value").attrib["type"]:
                
                    conc = np.linspace( float( small_comp.find("value").attrib["startValue"]), float( small_comp.find("value").attrib["endValue"]) , 4 ).tolist()
                    unit = small_comp.find("value").attrib["unit"]
                    
                else:
                    
                    conc = [float( small_comp.find("value").attrib["value"] )]
                    unit = small_comp.find("value").attrib["unit"]
                
                reactant = Reactant(name, "v0", conc[0], unit, False)
                    
                if inchi != "null": reactant.setInchi(inchi);
                if smiles != "null": reactant.setSmiles(smiles);
                
                
                id_ = self.enzmldoc.addReactant(reactant)
                
                if small_comp.attrib["role"] != "Substrate":
                    reaction.addModifier( id_ , 1.0, True, self.enzmldoc, [], conc )
                else:
                    reaction.addEduct( id_, stoich, False, self.enzmldoc, [], conc )
                    
                
                self.refID_dict[ small_comp.attrib["refId"] ] = id_
                
            # get the kinetic model
            kinetic_models = dataset.find("resultSet").findall('kineticParameter')
            parameters = dict()
            
            for model in kinetic_models:
                sub_id = self.refID_dict[ model.attrib['substanceId'] ]
                
                kcat_val = model[1].attrib['value']
                kcat_unit = model[1].attrib['unit']
                
                km_val =  model[2].attrib['value']
                km_unit = model[2].attrib['unit']
                
                parameters[ 'kcat_%s' % sub_id ] = ( float(kcat_val), kcat_unit )
                parameters[ 'km_%s' % sub_id ] = ( float(km_val), km_unit )
            
            km = KineticModel( "kcat_%s*p%i*%s / ( km_%s + %s )" % ( sub_id, i, sub_id, sub_id, sub_id ) , parameters)    
            reaction.setModel(km)
            
            # Add Reaction to EnzymeMLDocument
            self.enzmldoc.addReaction(reaction)
        
    def __getProtein(self, root):
        
        # extract protein information
        prot_node = root.find("protein")
        name = prot_node.find("name").text
        
        if prot_node.find("sequenceModifiations").attrib['value'] == "yes":
            sequence = prot_node.find("sequenceModifiations").find("modifiedSequence").text
        else:
            sequence = prot_node.find("originalSequence").text
            
        # get all datasets in STRENDA XML
        datasets = root.find("datasets").findall("dataset")
        
        # Since different concentrations per reaction were used, the protein will be duplicated
        for dataset in datasets:
            
            init_conc = float( dataset.find("assayConditions")[0].attrib["value"] )
            substance_units = dataset.find("assayConditions")[0].attrib["unit"]
            
            protein = Protein(name + " " + str(init_conc) + " " + substance_units, sequence, "v0", init_conc, substance_units)
            
            # add properties
            protein.setOrganism(prot_node.find("organism").text)
            if prot_node.attrib[ "uniprotKbAC" ] != 'N.A.': protein.setUniprotID(prot_node.attrib[ "uniprotKbAC" ]);
            
            self.enzmldoc.addProtein(protein)
        
        
        
if __name__ == '__main__':
    
    path = "../../Resources/Examples/ThinLayers/STRENDA/3IZNOK_TEST.xml"
    out_dir = "../../Resources/Examples/ThinLayers/STRENDA/Generated"
    ThinLayerStrendaML().exportEnzymeML(path, out_dir )
