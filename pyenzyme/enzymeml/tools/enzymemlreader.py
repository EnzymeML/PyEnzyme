'''
Created on 10.06.2020

@author: JR
'''

from pyenzyme.enzymeml.core.creator import Creator
from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument
from pyenzyme.enzymeml.core.protein import Protein
from pyenzyme.enzymeml.core.reactant import Reactant
from pyenzyme.enzymeml.core.replicate import Replicate
from pyenzyme.enzymeml.core.unitdef  import UnitDef
from pyenzyme.enzymeml.core.vessel import Vessel
from pyenzyme.enzymeml.core.enzymereaction import EnzymeReaction

from libsbml import SBMLReader
import xml.etree.ElementTree as ET
import pandas as pd
from pyenzyme.enzymeml.models.kineticmodel import KineticModel
from libcombine import CombineArchive
from _io import StringIO

class EnzymeMLReader(object):

    def readFromFile(self, path, omex=False):
        '''
        Reads EnzymeML document to an object layer EnzymeMLDocument class.
        
        Args:
            String path: Path to .omex container or folder destination for plain .xml
            Boolean omex: Determines whether reader handles an .omex file or not
        '''
        
        self.omex = omex
        self.__path = path
        
        if self.omex:
            self.archive = CombineArchive()
            self.archive.initializeFromArchive(self.__path)
        
            sbmlfile = self.archive.getEntry(0)
            content = self.archive.extractEntryToString(sbmlfile.getLocation())

        
        reader = SBMLReader()
        
        if self.omex:
            document = reader.readSBMLFromString(content)

        else:
            document = reader.readSBMLFromFile(self.__path + '/experiment.xml')
            
        document.getErrorLog().printErrors()
        
        model = document.getModel()
        
        enzmldoc = EnzymeMLDocument(model.getName(), model.getLevel(), model.getVersion())
        
        # Fetch references
        self.__getRefs(model, enzmldoc)
        
        # Fetch meta data
        try:
            creators = self.__getCreators(model)
            enzmldoc.setCreator(creators)
        except AttributeError:
            enzmldoc.setCreator( Creator("UNKNOWN", "UNKNOWN", "UNKNOWN") )
        
        try:
            model_hist = model.getModelHistory()
            enzmldoc.setCreated(model_hist.getCreatedDate().getDateAsString())
            enzmldoc.setModified(model_hist.getModifiedDate().getDateAsString())
        except AttributeError:
            enzmldoc.setCreated("2020")
            enzmldoc.setModified("2020")
               
        # Fetch units
        unitDict = self.__getUnits(model)
        enzmldoc.setUnitDict(unitDict)
        
        # Fetch Vessel
        vessel = self.__getVessel(model)
        enzmldoc.setVessel(vessel, use_parser=False)
        
        # Fetch Species
        proteinDict, reactantDict = self.__getSpecies(model)
        enzmldoc.setReactantDict(reactantDict)
        enzmldoc.setProteinDict(proteinDict)
        
        # fetch reaction
        reactionDict = self.__getReactions(model, enzmldoc)
        enzmldoc.setReactionDict(reactionDict)
        
        del self.__path
        
        return enzmldoc
    
    def __getRefs(self, model, enzmldoc):
        
        if len(model.getAnnotationString()) > 0:
            root = ET.fromstring( model.getAnnotationString() )[0]
            
            for elem in root:
                if "doi" in elem.tag:
                    enzmldoc.setDoi( elem.text )
                elif 'pubmedID' in elem.tag:
                    print(elem.text)
                elif 'url' in elem.tag:
                    enzmldoc.setUrl(elem.text)
        
    def __getCreators(self, model):
        
        model_hist = model.getModelHistory()
        creator_list = model_hist.getListCreators()
        creators = list()
        
        for creator in creator_list:

            creators.append(
                
                Creator(creator.getFamilyName(), creator.getGivenName(), creator.getEmail())
                
                )
            
        return creators
        
    def __getUnits(self, model):
        
        unitDict = dict()
        unitdef_list = model.getListOfUnitDefinitions()
        
        for unit in unitdef_list:
            
            name = unit.getName()
            id_ = unit.getId()
            metaid = unit.getMetaId()
            ontology = unit.getCVTerms()[0].getResourceURI(0)
            
            unitdef = UnitDef( name, id_, ontology  )
            unitdef.setMetaid(metaid)
            
            for baseunit in unit.getListOfUnits():
                
                unitdef.addBaseUnit(
                    
                    baseunit.toXMLNode().getAttrValue('kind'),
                    baseunit.getExponentAsDouble(),
                    baseunit.getScale(),
                    baseunit.getMultiplier()
                    
                    )
                
            unitDict[id_] = unitdef
            
        return unitDict   

    def __getVessel(self, model):
        
        compartment = model.getListOfCompartments()[0]
        
        vessel = Vessel(
                            compartment.getName(), 
                            compartment.getId(), 
                            compartment.getSize(), 
                            compartment.getUnits()
                        )
        
        return vessel

    def __getSpecies(self, model):
        
        proteinDict = dict()
        reactantDict = dict()
        species_list = model.getListOfSpecies()
        
        for species in species_list:   
            
            try:
                root = ET.fromstring(species.getAnnotationString())
            except ET.ParseError :
                root = None
                
            sequence = False
            
            if root != None:
                # Iterate throufh annotation and fetch seqeunce
                for child1 in root:
                    if 'protein' in child1.tag:
                        
                        for child2 in child1:
                        
                            if 'sequence' in child2.tag:
                            
                                sequence = child2.text
                                
                            elif 'organism' in child2.tag:
                                
                                organism = child2.text
                                
                            elif 'uniprot' in child2.tag:
                                
                                uniprotid = child2.text
            
            if sequence != False:
                
                # make sure that a sequence has been fetched
                # Future might include normal reactant annotations
                # thus making sure its a protein will be important
                
                          
                protein = Protein(
                                species.getName(), 
                                sequence, 
                                species.getCompartment(), 
                                species.getInitialConcentration(), 
                                species.getSubstanceUnits(),
                                species.getConstant()
                                )
                
                protein.setId(species.getId())
                protein.setMetaid(species.getMetaId())
                
                try:
                    protein.setOrganism(organism)
                except UnboundLocalError:
                    pass
                
                try:
                    protein.setUniprotID(uniprotid)
                except UnboundLocalError:
                    pass
                
                proteinDict[species.getId()] = protein
                
                
                
                # Reactants are parsed here if the species is not
                # matching protein conditions (sequence etc)
                
            else:
                
                reactant = Reactant(
                                    species.getName(),
                                    species.getCompartment(), 
                                    species.getInitialConcentration(), 
                                    species.getSubstanceUnits(),
                                    species.getConstant()
                                    )
                
                reactant.setMetaid(species.getMetaId())
                
                if len(species.getAnnotationString()) > 0:
                
                    root = ET.fromstring(species.getAnnotationString())
                    
                    for child1 in root[0]:
                        if 'inchi' in child1.tag:
                            reactant.setInchi(child1.attrib['inchi'])
                        elif 'smiles' in child1.tag:
                            reactant.setSmiles(child1.attrib['smiles'])
                                    
                                      
                
                 
                reactantDict[ species.getId() ] = reactant
         
        return proteinDict, reactantDict
    
    def __getInitConcs(self, specref, enzmldoc):
        
        if len( specref.getAnnotationString() ) > 0:
            root = ET.fromstring(specref.getAnnotationString())
            initconc = list()
            
            for node in root[0]:
                
                val = float( node.attrib['value'] )
                id = node.attrib['id']
                unit = node.attrib['unit']
                
                enzmldoc.getConcDict()[id] = (val, unit)
                
                initconc.append(val)
                
            return initconc
        
        else:
            return list()

    def __getReactions(self, model, enzmldoc):
        
        reaction_list = model.getListOfReactions()
        
        try:
            global_replicates = self.__getReplicates(reaction_list)
        except ( ET.ParseError, pd.errors.EmptyDataError) as e:
            global_replicates = dict()
        
        reaction_replicates = dict()
        
        reactionDict = dict()
        
        # parse annotations and filter replicates
        for reac in reaction_list:
            
            root = ET.fromstring(reac.getAnnotationString())
            
            for child in list(root)[0]:
                
                if "conditions" in child.tag:
                    
                    for cond in child:
                        # iterate through conditions 
                        if 'ph' in cond.tag: ph=float(cond.attrib["value"]);
                        if 'temperature' in cond.tag: temperature=float(cond.attrib["value"]);
                        if 'temperature' in cond.tag: tempunit=cond.attrib["unit"];
                        
                elif 'replica' in child.tag:

                    for repl in child:
                        # iterate through replicates
                        repl_id = repl.attrib["replica"]
                        replica = global_replicates[repl_id]
                        
                        try:
                            reaction_replicates[replica.getReactant()].append( replica )
                        except KeyError:
                            reaction_replicates[replica.getReactant()] = [replica]
            
            # parse list of educts/products/modifiers
            educts = [ 
                
                         ( species_ref.getSpecies(),
                         species_ref.getStoichiometry(),
                         species_ref.getConstant(),
                         reaction_replicates[ species_ref.getSpecies() ],
                         self.__getInitConcs(species_ref, enzmldoc)
                         ) if species_ref.getSpecies() in reaction_replicates.keys()
                         
                         else ( species_ref.getSpecies(),
                         species_ref.getStoichiometry(),
                         species_ref.getConstant(),
                         list(),
                        self.__getInitConcs(species_ref, enzmldoc)
                         )
                      
                        for species_ref in reac.getListOfReactants() 
                        
                        ]
            
            products = [ 
                
                         ( species_ref.getSpecies(),
                         species_ref.getStoichiometry(),
                         species_ref.getConstant(),
                         reaction_replicates[ species_ref.getSpecies() ],
                         self.__getInitConcs(species_ref, enzmldoc)
                         ) if species_ref.getSpecies() in reaction_replicates.keys()
                         
                         else ( species_ref.getSpecies(),
                         species_ref.getStoichiometry(),
                         species_ref.getConstant(),
                         list(),
                         self.__getInitConcs(species_ref, enzmldoc)
                         )
                      
                        for species_ref in reac.getListOfProducts()
                        
                        ]
            
            modifiers = [ 
                
                         ( species_ref.getSpecies(),
                         reaction_replicates[ species_ref.getSpecies() ]
                         ) if species_ref.getSpecies() in reaction_replicates.keys()
                         
                         else ( species_ref.getSpecies(),
                         list()
                         )
                      
                        for species_ref in reac.getListOfModifiers()
                        
                        ]
            
            reactionDict[reac.getId()] = EnzymeReaction(
                
                temperature, 
                tempunit, 
                ph, 
                reac.getName(), 
                reac.getReversible(), 
                educts, 
                products, 
                modifiers
                
                )
            
            reactionDict[reac.getId()].setId(reac.getId())
            
            try:
                
                kinlaw = reac.getKineticLaw()
                equation = kinlaw.getFormula()
                
                
                    
                
                parameters = { loc_param.getId(): (loc_param.getValue(), loc_param.getUnits()) 
                               for loc_param in kinlaw.getListOfLocalParameters() }
                
                reactionDict[reac.getId()].setModel(
                    
                    KineticModel(equation, parameters)
                    
                    )
                
            except AttributeError:
                pass
            
        return reactionDict   
            
            
    def __getReplicates(self, reaction_list):
        
        root = ET.fromstring(reaction_list.getAnnotationString())[0]
        
        listOfFiles = [ file.attrib['file'] 
                        for child in root 
                            for file in child 
                                if 'listOfFiles' in child.tag  ]
        
        # load csv file to extract replicate data
        
        if self.omex:
            
            csv_entry = self.archive.getEntry(1)
            content = self.archive.extractEntryToString(csv_entry.getLocation())
            csv_data = StringIO(content)
        
            listOfCSV = [
                    
                    pd.read_csv( csv_data, header=None )
                
                ]
         
        else:
                
            listOfCSV = [
                    
                    pd.read_csv( self.__path + path_csv[1::], header=None )
                    for path_csv in listOfFiles
                
                ]
        
        """TODO PROCESS ALL MEAS DATA"""
        
        data = listOfCSV[0]
        
        listOfFormats = [ file 
                        for child in root 
                            for file in child 
                                if 'listOfFormats' in child.tag  ]
        
        # Name columns accordingly
        columns = [ "time/%s" % child.attrib["unit"]  if child.attrib["type"] == "time"
                    else "%s/%s/%s" % ( child.attrib["replica"], child.attrib["species"], child.attrib["type"] )
                        
                        for format_ in listOfFormats
                        for child in format_
                    ]
        
        # get unit of time
        time_unit = [ child.attrib["unit"]
                        for format_ in listOfFormats
                        for child in format_
                        if child.attrib["type"] == "time"
                    ][0]
        
        data.columns = columns
        data.set_index("time/%s" % time_unit, inplace=True)
        
        # derive data from annotations
        replicates = dict()
        for format_ in listOfFormats:
            for child in format_:
                
                if child.attrib["type"] != "time":
                    repl = Replicate(   child.attrib["replica"], 
                                        child.attrib["species"], 
                                        child.attrib["type"], 
                                        child.attrib["unit"], 
                                        time_unit,
                                        child.attrib["initConcID"]
                                        )
                    
                    repl.setData( data[ "%s/%s/%s" % ( child.attrib["replica"], child.attrib["species"], child.attrib["type"] ) ] )
                    
                    replicates[ repl.getReplica() ] = repl
        
        return replicates