'''
Created on 03.07.2020

@author: JR
'''
from libsbml import SBMLDocument, CVTerm, XMLNode, XMLTriple, XMLAttributes,\
    XMLNamespaces, SBMLWriter
import libsbml
from libsbml._libsbml import BIOLOGICAL_QUALIFIER, BQB_IS
from libcombine import CombineArchive, OmexDescription, KnownFormats, VCard
import pandas as pd
import numpy as np
import os

class EnzymeMLWriter(object):

    def toFile(self, enzmldoc, path):
        
        '''
        Writes EnzymeMLDocument object to an .omex container
        
        Args:
            EnzymeMLDocument enzmldoc: Previously created instance of an EnzymeML document
            String path: EnzymeML file is written to this destination
        '''
        
        self.path = path + '/' + enzmldoc.getName()
        
        try:
            os.makedirs( self.path + '/data' )
        except FileExistsError:
            pass
        
        doc = SBMLDocument()
        doc.setLevelAndVersion(enzmldoc.getLevel(), enzmldoc.getVersion())
        
        model = doc.createModel()
        model.setName(enzmldoc.getName())
        model.setId(enzmldoc.getName())
        
        # Add references
        self.__addRefs(model, enzmldoc)
        
        # Add units
        self.__addUnits(model, enzmldoc)
        
        # Add Vessel
        self.__addVessel(model, enzmldoc)
        
        # Add protein
        self.__addProteins(model, enzmldoc)
        
        # Add reactants
        self.__addReactants(model, enzmldoc)
        
        # Add reactions
        self.__addReactions(model, enzmldoc)
        
        # Write to EnzymeML
        writer = SBMLWriter()
        writer.writeSBMLToFile(doc, self.path + '/experiment.xml')
        
        # Write to OMEX
        self.__createArchive(enzmldoc, doc)
        
        os.remove(self.path + '/experiment.xml')
        os.remove(self.path + '/data/data.csv')
        os.rmdir(self.path + '/data')
        
    def toXMLString(self, enzmldoc):
        
        '''
        Converts EnzymeMLDocument to XML string.
        
        Args:
            EnzymeMLDocument enzmldoc: Previously created instance of an EnzymeML document
        '''
        doc = SBMLDocument()
        doc.setLevelAndVersion(enzmldoc.getLevel(), enzmldoc.getVersion())
        
        model = doc.createModel()
        model.setName(enzmldoc.getName())
        model.setId(enzmldoc.getName())
        
        # Add references
        self.__addRefs(model, enzmldoc)
        
        # Add units
        self.__addUnits(model, enzmldoc)
        
        # Add Vessel
        self.__addVessel(model, enzmldoc)
        
        # Add protein
        self.__addProteins(model, enzmldoc)
        
        # Add reactants
        self.__addReactants(model, enzmldoc)
        
        # Add reactions
        self.__addReactions(model, enzmldoc, csv=False)
        
        # Write to EnzymeML
        writer = SBMLWriter()
        return writer.writeToString(doc)
    
    def toSBML(self, enzmldoc):
        
        '''
        Returns libSBML model.
        
        Args:
            EnzymeMLDocument enzmldoc: Previously created instance of an EnzymeML document
        '''

        doc = SBMLDocument()
        doc.setLevelAndVersion(enzmldoc.getLevel(), enzmldoc.getVersion())
        
        model = doc.createModel()
        model.setName(enzmldoc.getName())
        model.setId(enzmldoc.getName())
        
        # Add references
        self.__addRefs(model, enzmldoc)
        
        # Add units
        self.__addUnits(model, enzmldoc)
        
        # Add Vessel
        self.__addVessel(model, enzmldoc)
        
        # Add protein
        self.__addProteins(model, enzmldoc)
        
        # Add reactants
        self.__addReactants(model, enzmldoc)
        
        # Add reactions
        self.__addReactions(model, enzmldoc, csv=False)
        
        return doc
        
    def __createArchive(self, enzmldoc, doc):
    
        archive = CombineArchive()
        archive.addFile(
            self.path + '/experiment.xml',  # filename
            "./experiment.xml",  # target file name
            KnownFormats.lookupFormat("sbml"),  # look up identifier for SBML models
            True  # mark file as master
        )
        
        archive.addFile(
            self.path + '/data/data.csv',  # filename
            "./data/data.csv",  # target file name
            KnownFormats.lookupFormat("csv"),  # look up identifier for SBML models
            False  # mark file as master
        )
    
        # add metadata to the archive itself
        description = OmexDescription()
        description.setAbout(".")
        description.setDescription(enzmldoc.getName())
        description.setCreated(OmexDescription.getCurrentDateAndTime())
        
        try:
            for creat in enzmldoc.get_creator():
                
                creator = VCard()
                creator.setFamilyName(creat.getFname())
                creator.setGivenName(creat.getGname())
                creator.setEmail(creat.getMail())
        
                description.addCreator(creator)
        except AttributeError:
            pass
    
        archive.addMetadata(".", description)
    
        # add metadata to the experiment file
        location = "./experiment.xml"
        description = OmexDescription()
        description.setAbout(location)
        description.setDescription("EnzymeML model")
        description.setCreated(OmexDescription.getCurrentDateAndTime())
        archive.addMetadata(location, description)
        
        # add metadata to the csv file
        location = "./data/data.csv"
        description = OmexDescription()
        description.setAbout(location)
        description.setDescription("EnzymeML Time Course Data")
        description.setCreated(OmexDescription.getCurrentDateAndTime())
        archive.addMetadata(location, description)
    
        # write the archive
        out_file = "%s.omex" % enzmldoc.getName().replace(' ', '_')
        
        try:
            os.remove(self.path + '/' + out_file)
        except FileNotFoundError:
            pass
        
        archive.writeToFile(self.path + '/' + out_file)
    
        print('\nArchive created:', out_file)
        
    def __addRefs(self, model, enzmldoc):
        
        annot_bool = False
        ref_annot = XMLNode( XMLTriple("enzymeml:references"), XMLAttributes(), XMLNamespaces() )
        ref_annot.addNamespace("http://sbml.org/enzymeml/version1", "enzymeml")
        
        try:
            doi = XMLNode( enzmldoc.getDoi() )
            doi_node = XMLNode( XMLTriple("enzymeml:doi"), XMLAttributes(), XMLNamespaces() )
            doi_node.addChild( doi )
            ref_annot.addChild(doi_node)
            annot_bool = True
        except AttributeError:
            pass
        
        try:
            pubmedid = XMLNode( enzmldoc.getPubmedID() )
            pubmed_node = XMLNode( XMLTriple("enzymeml:pubmedID"), XMLAttributes(), XMLNamespaces() )
            pubmed_node.addChild( pubmedid )
            ref_annot.addChild(pubmed_node)
            annot_bool = True
        except AttributeError:
            pass
        
        try:
            url = XMLNode( enzmldoc.getUrl() )
            url_node = XMLNode( XMLTriple("enzymeml:url"), XMLAttributes(), XMLNamespaces() )
            url_node.addChild( url )
            ref_annot.addChild(url_node)
            annot_bool = True
        except AttributeError:
            pass
        
        if annot_bool:
            model.appendAnnotation(ref_annot)
        
    def __addUnits(self, model, enzmldoc):
        
        for key, unitdef in enzmldoc.getUnitDict().items():
            
            unit = model.createUnitDefinition()
            unit.setId(key)
            unit.setMetaId(unitdef.getMetaid())
            unit.setName(unitdef.getName())
            
            cvterm = CVTerm()
            cvterm.addResource(unitdef.getOntology())
            cvterm.setQualifierType(BIOLOGICAL_QUALIFIER)
            cvterm.setBiologicalQualifierType(BQB_IS)
            unit.addCVTerm(cvterm)
            
            for baseunit in unitdef.getUnits():
                
                u = unit.createUnit()
                
                try:
                    u.setKind( libsbml.UnitKind_forName(baseunit[0]) )
                except TypeError:
                    u.setKind( baseunit[0] )
                    
                u.setExponent( baseunit[1] )
                u.setScale( baseunit[2] )
                u.setMultiplier( baseunit[3] )
                
    def __addVessel(self, model, enzmldoc):
        
        vessel = enzmldoc.getVessel()
        
        compartment = model.createCompartment()
        compartment.setId(vessel.getId())
        compartment.setName(vessel.getName())
        compartment.setUnits(vessel.getUnit())
        compartment.setSize(vessel.getSize())
        compartment.setConstant(vessel.getConstant())
        compartment.setSpatialDimensions(3)
        
    def __addProteins(self, model, enzmldoc):
        
        for key, protein in enzmldoc.getProteinDict().items():
            
            species = model.createSpecies()
            species.setId(key)
            species.setName(protein.getName())
            species.setMetaId(protein.getMetaid())
            species.setSBOTerm(protein.getSboterm())
            species.setCompartment(protein.getCompartment())
            species.setBoundaryCondition(protein.getBoundary());
            species.setInitialConcentration(protein.getInitConc());
            species.setSubstanceUnits(protein.getSubstanceUnits());
            species.setConstant(protein.getConstant())
            species.setHasOnlySubstanceUnits(False)
            
            # add annotation
            annot_root = XMLNode( XMLTriple('enzymeml:protein'), XMLAttributes(), XMLNamespaces() )
            annot_root.addNamespace("http://sbml.org/enzymeml/version1", "enzymeml")
            
            annot_sequence = XMLNode( XMLTriple('enzymeml:sequence'), XMLAttributes(), XMLNamespaces() )
            sequence = XMLNode(protein.getSequence())
            
            annot_sequence.addChild(sequence)
            annot_root.addChild(annot_sequence)
            
            try:
                annot_ec = XMLNode( XMLTriple('enzymeml:ECnumber'), XMLAttributes(), XMLNamespaces() )
                ecnumber = XMLNode(protein.getEcnumber())
                annot_ec.addChild(ecnumber)
                annot_root.addChild(annot_ec)
            except AttributeError:
                pass
            
            try:
                annot_uniprot = XMLNode( XMLTriple('enzymeml:uniprotID'), XMLAttributes(), XMLNamespaces() )
                uniprotid = XMLNode(protein.getUniprotID())
                annot_uniprot.addChild(uniprotid)
                annot_root.addChild(annot_uniprot)
            except AttributeError:
                pass
            
            try:
                annot_org = XMLNode( XMLTriple('enzymeml:organism'), XMLAttributes(), XMLNamespaces() )
                organism = XMLNode(protein.getOrganism())
                annot_org.addChild(organism)
                annot_root.addChild(annot_org)
            except AttributeError:
                pass
            
            species.appendAnnotation(annot_root)
            
    def __addReactants(self, model, enzmldoc):
        
        for key, reactant in enzmldoc.getReactantDict().items():
            
            species = model.createSpecies()
            species.setId(key)
            species.setName(reactant.getName())
            species.setMetaId(reactant.getMetaid())
            species.setSBOTerm(reactant.getSboterm())
            species.setCompartment(reactant.getCompartment())
            species.setBoundaryCondition(reactant.getBoundary());
            
            if reactant.getInitConc() > 0: species.setInitialConcentration(reactant.getInitConc());
            if reactant.getSubstanceunits() != 'NAN': species.setSubstanceUnits(reactant.getSubstanceunits());
            
            species.setConstant(reactant.getConstant())
            species.setHasOnlySubstanceUnits(False)
            
            # Controls if annotation will be added
            append_bool = False
            reactant_annot = inchi_annot = XMLNode( XMLTriple('enzymeml:reactant'), XMLAttributes(), XMLNamespaces() )
            reactant_annot.addNamespace("http://sbml.org/enzymeml/version1", "enzymeml")
            
            try:
                append_bool = True
                inchi_annot = XMLNode( XMLTriple('enzymeml:inchi'), XMLAttributes(), XMLNamespaces() )
                inchi_annot.addAttr('inchi', reactant.getInchi())
                reactant_annot.addChild(inchi_annot)
            except AttributeError:
                pass
            
            try:
                append_bool = True
                smiles_annot = XMLNode( XMLTriple('enzymeml:smiles'), XMLAttributes(), XMLNamespaces() )
                smiles_annot.addAttr('smiles', reactant.getSmiles())
                reactant_annot.addChild(smiles_annot)
            except AttributeError:
                pass
            
            if append_bool == True: species.appendAnnotation(reactant_annot)
            
            
    def __addReactions(self, model, enzmldoc, csv=True):
        
        # initialize format annotation
        data_root = XMLNode( XMLTriple('enzymeml:data'), XMLAttributes(), XMLNamespaces() )
        data_root.addNamespace("http://sbml.org/enzymeml/version1", "enzymeml")
        
        list_formats = XMLNode( XMLTriple('enzymeml:listOfFormats'), XMLAttributes(), XMLNamespaces() )
        format_ = XMLNode( XMLTriple('enzymeml:format'), XMLAttributes(), XMLNamespaces() )
        format_.addAttr( 'id', 'format0' )
        
        # initialize csv data collection
        data = []
        
        # initialize time
        index = 0
        
        if len(list(enzmldoc.getReactionDict().items())) == 0:
            raise ValueError( "Please define a reaction before writing" )
        
        for key, reac in enzmldoc.getReactionDict().items():
            
            reaction = model.createReaction()
            reaction.setName(reac.getName())
            reaction.setId(key)
            reaction.setMetaId(reac.getMetaid())
            reaction.setReversible(reac.getReversible())
            
            # initialize conditions annotations
            annot_root = XMLNode( XMLTriple('enzymeml:reaction'), XMLAttributes(), XMLNamespaces() )
            annot_root.addNamespace("http://sbml.org/enzymeml/version1", "enzymeml")
            
            conditions_root = XMLNode( XMLTriple('enzymeml:conditions'), XMLAttributes(), XMLNamespaces() )
            
            temp_node = XMLNode( XMLTriple('enzymeml:temperature'), XMLAttributes(), XMLNamespaces() )
            temp_node.addAttr('value', str(reac.getTemperature()) )
            temp_node.addAttr('unit', reac.getTempunit())
            
            ph_node = XMLNode( XMLTriple('enzymeml:ph'), XMLAttributes(), XMLNamespaces() )
            ph_node.addAttr('value', str(reac.getPh()) )
            
            conditions_root.addChild(temp_node)
            conditions_root.addChild(ph_node)
            
            annot_root.addChild(conditions_root)
            
            all_elems = reac.getEducts() + reac.getProducts()
            all_repls = [ repl for tup in all_elems for repl in tup[3] ]
            
            if len( all_repls ) > 0:
            
                # initialize replica/format annotations
                replica_root = XMLNode( XMLTriple('enzymeml:replicas'), XMLAttributes(), XMLNamespaces() )
                
                replicate = all_repls[0]
                
                time = replicate.getData().index.tolist()
                time_unit = replicate.getTimeUnit()
            
                
                time_node = XMLNode( XMLTriple('enzymeml:column'), XMLAttributes(), XMLNamespaces() )
                time_node.addAttr('type', 'time')
                time_node.addAttr('unit', time_unit)
                time_node.addAttr('index', str(index) )
                
                format_.addChild(time_node)
                data.append( time )
                index += 1
                
            # iterate over lists
            # educts
            for educt in reac.getEducts():
                
                species = educt[0]
                stoich = educt[1]
                const = educt[2]
                init_concs = educt[-1]
                
                specref = reaction.createReactant()
                specref.setSpecies(species)
                specref.setStoichiometry(stoich)
                specref.setConstant(const)
                
                # if there are different initial concentrations create an annotation
                try:
                    # DIRTY WAY ATM TO MAINTAIN FUNCTIONALITY
                    init_concs.remove([])
                except ValueError:
                    pass
                
                if len(init_concs) > 0:
                    
                    conc_annot = XMLNode( XMLTriple('enzymeml:initConcs'), XMLAttributes(), XMLNamespaces() )
                    conc_annot.addNamespace("http://sbml.org/enzymeml/version1", "enzymeml")
                    
                    for conc in init_concs:
                        
                        try:
                            conc_node = XMLNode( XMLTriple('enzymeml:initConc'), XMLAttributes(), XMLNamespaces() )
                            conc_node.addAttr( "id", str(conc) )
                            conc_node.addAttr( "value", str(enzmldoc.getConcDict()[conc][0]) )
                            conc_node.addAttr( "unit", enzmldoc.getReactant(species).getSubstanceunits() )
                            conc_annot.addChild( conc_node )
                            
                        except KeyError:
                            
                            inv_initconc = { item: key for key, item in enzmldoc.getConcDict().items() }
                            init_entry = enzmldoc.getConcDict()[
                                
                                inv_initconc[ (conc, enzmldoc.getReactant(species).getSubstanceunits() ) ]
                                
                                ]
                            
                            conc_node = XMLNode( XMLTriple('enzymeml:initConc'), XMLAttributes(), XMLNamespaces() )
                            conc_node.addAttr( "id", inv_initconc[ (conc, enzmldoc.getReactant(species).getSubstanceunits() ) ] )
                            conc_node.addAttr( "value", str(init_entry[0]) )
                            conc_node.addAttr( "unit", str(init_entry[1]) )
                            conc_annot.addChild( conc_node )
                        
                    specref.appendAnnotation(conc_annot)
                
                for repl in educt[3]:
                    
                    repl_node = XMLNode( XMLTriple('enzymeml:replica'), XMLAttributes(), XMLNamespaces() )
                    repl_node.addAttr('measurement', 'M0')
                    repl_node.addAttr('replica', repl.getReplica())
                    
                    form_node = XMLNode( XMLTriple('enzymeml:column'), XMLAttributes(), XMLNamespaces() )
                    form_node.addAttr( 'replica', repl.getReplica() )
                    form_node.addAttr( 'species', repl.getReactant() )
                    form_node.addAttr( 'type', repl.getType() )
                    form_node.addAttr( 'unit', repl.getDataUnit() )
                    form_node.addAttr( 'index', str(index) )
                    form_node.addAttr( 'initConcID', str(repl.getInitConc()) )
                        
                    replica_root.addChild(repl_node)
                    format_.addChild(form_node)
                    
                    data.append( repl.getData().values.tolist() )
                    
                    index += 1
                    
            # products
            for product in reac.getProducts():
                
                species = product[0]
                stoich = product[1]
                const = product[2]
                
                specref = reaction.createProduct()
                specref.setSpecies(species)
                specref.setStoichiometry(stoich)
                specref.setConstant(const)
                
                for repl in product[3]:
                    
                    repl_node = XMLNode( XMLTriple('enzymeml:replica'), XMLAttributes(), XMLNamespaces() )
                    repl_node.addAttr('measurement', 'M0')
                    repl_node.addAttr('replica', repl.getReplica())
                    
                    form_node = XMLNode( XMLTriple('enzymeml:column'), XMLAttributes(), XMLNamespaces() )
                    form_node.addAttr( 'replica', repl.getReplica() )
                    form_node.addAttr( 'species', repl.getReactant() )
                    form_node.addAttr( 'type', repl.getType() )
                    form_node.addAttr( 'unit', repl.getDataUnit() )
                    form_node.addAttr( 'index', str(index) )
                    form_node.addAttr( 'initConcID', str(repl.getInitConc()) )
                        
                    replica_root.addChild(repl_node)
                    format_.addChild(form_node)
                    
                    data.append( repl.getData().values.tolist() )
                    
                    index += 1
                    
            # modifiers
            for modifier in reac.getModifiers():
                
                species = modifier[0]
                
                specref = reaction.createModifier()
                specref.setSpecies(species)
                
                for repl in modifier[-1]:
                    
                    repl_node = XMLNode( XMLTriple('enzymeml:replica'), XMLAttributes(), XMLNamespaces() )
                    repl_node.addAttr('measurement', 'M0')
                    repl_node.addAttr('replica', repl.getReplica())
                    
                    form_node = XMLNode( XMLTriple('enzymeml:column'), XMLAttributes(), XMLNamespaces() )
                    form_node.addAttr( 'replica', repl.getReplica() )
                    form_node.addAttr( 'species', repl.getReactant() )
                    form_node.addAttr( 'initConcID', str(repl.getInitConc()) )
                        
                    replica_root.addChild(repl_node)
                    format_.addChild(form_node)
                    
                    data.append( repl.getData().values.tolist() )
                    
                    index += 1
                
                try:
                    # add kinetic law if existent
                    reac.getModel().addToReaction(reaction)
                except AttributeError:
                    pass
                
            if len( all_repls ) > 0:
                annot_root.addChild( replica_root )
                    
            reaction.appendAnnotation(annot_root)
        
        
        # finalize all reactions
        list_formats.addChild(format_)
        
        list_measurements = XMLNode( XMLTriple('enzymeml:listOfMeasurements'), XMLAttributes(), XMLNamespaces() )
        
        meas = XMLNode( XMLTriple('enzymeml:measurement'), XMLAttributes(), XMLNamespaces() )
        meas.addAttr('file', 'file0')
        meas.addAttr('id', 'M0')
        meas.addAttr('name', 'AnyName')
        
        list_measurements.addChild(meas)
        
        if len( all_repls ) > 0:
            list_files = XMLNode( XMLTriple('enzymeml:listOfFiles'), XMLAttributes(), XMLNamespaces() )
            
            
            file = XMLNode( XMLTriple( 'enzymeml:file' ), XMLAttributes(), XMLNamespaces() )
            file.addAttr('file', './data/Data.csv')
            file.addAttr('format', 'format0')
            file.addAttr('id', 'file0')
            
            list_files.addChild(file)
        
        if csv:
            # write file to csv
            df = pd.DataFrame( np.array(data).T )
            df.to_csv( self.path + '/data/data.csv', index=False, header=False)
        
        if len( all_repls ) > 0:
            data_root.addChild(list_formats)
            data_root.addChild(list_files)
                
        data_root.addChild(list_measurements)
    
        model.getListOfReactions().appendAnnotation(data_root)