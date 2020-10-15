'''
Created on 04.08.2020

@author: JR
'''

from pyenzyme.enzymeml.tools import EnzymeMLReader, EnzymeMLWriter
import os

import COPASI

class ThinLayerCopasi(object):
    
    def importEnzymeML(self, reaction, reactants, path, outdir=None):
        
        '''
        ThinLayer interface from an .omex EnzymeML container 
        to COPASI comatible .cps fiel format.
        
        Args:
            String path: Path to .omex EnzymeML file
            String outdir: Path to store .cps COPASI file
            String reaction: Reaction ID to extract data from
            String reactants: Single or multiple IDs for desired reactant(s)
        '''
        
        fname = str(os.path.basename(path)).split(".omex")[0]
        
        if outdir is None:
            
            outdir = "/".join( path.split('/')[0:-1] ) +  "/COPASI"
                         
            os.makedirs( outdir, exist_ok=True )
        
        ########### PyEnzyme ########### 
        
        # Read EnzymeML Omex file
        enzmldoc = EnzymeMLReader().readFromFile(path, omex=True)
        
        # Get reaction and replicates
        reaction = enzmldoc.getReaction(reaction)
                
        repls = reaction.exportReplicates(reactants)
        repls.columns = [ column.split('/')[1] for column in repls.columns ]
        repls.index.name = "time"
        repls.to_csv( outdir + '/data.tsv', sep='\t')
        
        # initialize COPASI data model
        dm = COPASI.CRootContainer.addDatamodel()
        sbml = EnzymeMLWriter().toXMLString( enzmldoc )
        dm.importSBMLFromString(sbml)
        
        ########### COPASI ###########
        
        # Get Reactant specific ConcentrationReference
        all_elems = reaction.getEducts() + reaction.getProducts() + reaction.getModifiers()
        reaction_species = [ tup[0] for tup in all_elems ]
        col_cn_map = {metab.sbml_id : metab.getConcentrationReference().getCN()
              for metab in dm.getModel().getMetabolites() if metab.sbml_id in repls.columns}
        
        # Describe .tsv file and call COPASI bindings
        task = dm.getTask('Parameter Estimation')
        task.setScheduled(True)
        problem = task.getProblem()
        problem.setCalculateStatistics(False)
        exp_set = problem.getExperimentSet()
        
        exp = COPASI.CExperiment(dm)
        exp = exp_set.addExperiment(exp)
        info = COPASI.CExperimentFileInfo(exp_set)
        info.setFileName( outdir + "/data.tsv")
        exp.setObjectName(reaction.getName())
        exp.setFirstRow(1)
        exp.setLastRow(repls.shape[0]+1)
        exp.setHeaderRow(1)
        exp.setFileName( outdir + "/data.tsv")
        exp.setExperimentType(COPASI.CTaskEnum.Task_timeCourse)
        exp.setSeparator('\t')
        exp.setNumColumns(repls.shape[1]+1)
        
        # Mapping from .tsv file to COPASI bindings
        obj_map = exp.getObjectMap()
        obj_map.setNumCols(repls.shape[1]+1)
        
        for i, col in enumerate(["time"] + list(repls.columns)):
            
            if col is "time":
                role = COPASI.CExperiment.time
                obj_map.setRole(i, role)
                
            elif col in col_cn_map.keys():
                role = COPASI.CExperiment.dependent
                obj_map.setRole(i, role)
                obj_map.setObjectCN(i, col_cn_map[col])
                
            else:
                role = COPASI.CExperiment.ignore
                obj_map.setRole(i, role)
                
        # Finally save the model and add plot/progress
        dm.saveModel( outdir + "/" + fname + ".cps", True)
        
        dm.loadModel( outdir + "/" + fname + ".cps" )
        task = dm.getTask('Parameter Estimation')
        task.setMethodType(COPASI.CTaskEnum.Method_Statistics)
        COPASI.COutputAssistant.getListOfDefaultOutputDescriptions(task)
        COPASI.COutputAssistant.createDefaultOutput(913, task, dm)
        COPASI.COutputAssistant.createDefaultOutput(910, task, dm)
        dm.saveModel( outdir + "/" + fname + ".cps", True)
        
        print("Saved model to " + outdir + "/" + fname + ".cps")
        
if __name__ == '__main__':
    
    ThinLayerCopasi().importEnzymeML('r0', 's0', "../../Resources/Examples/ThinLayers/COPASI/3IZNOK_TEST/3IZNOK_TEST.omex")
