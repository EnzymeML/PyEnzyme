'''
Created on 04.08.2020

@author: JR
'''

from pyenzyme.enzymeml.tools import EnzymeMLReader, EnzymeMLWriter
import os

import COPASI
from builtins import enumerate

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
        if type(reactants) == str:
            reactants = [reactants]
        
        fname = str(os.path.basename(path)).split(".omex")[0]
        
        if outdir is None:
            
            outdir = "/".join( path.split('/')[0:-1] ) +  "/COPASI"
                         
            os.makedirs( outdir, exist_ok=True )
        
        ########### PyEnzyme ########### 
        
        # Read EnzymeML Omex file
        enzmldoc = EnzymeMLReader().readFromFile(path, omex=True)
        
        # Get reaction and replicates
        reaction = enzmldoc.getReaction(reaction)
        
        # initialize COPASI data model
        dm = COPASI.CRootContainer.addDatamodel()
        sbml = EnzymeMLWriter().toXMLString( enzmldoc )
        dm.importSBMLFromString(sbml)
        
        ########### COPASI ###########
        
        # Get Reactant specific ConcentrationReference
        col_cn_map = {metab.sbml_id : metab.getConcentrationReference().getCN()
              for metab in dm.getModel().getMetabolites() if metab.sbml_id in reactants}
        
        # Describe .tsv file and call COPASI bindings
        task = dm.getTask('Parameter Estimation')
        task.setScheduled(True)
        problem = task.getProblem()
        problem.setCalculateStatistics(False)
        exp_set = problem.getExperimentSet()
        
        
        
        for reactant in reactants:
            # include each replicate
            for i, repl in enumerate( reaction.getEduct(reactant)[3] ):
                
                data = repl.getData()
                data.name = data.name.split('/')[1]
                
                conc_val, conc_unit =  enzmldoc.getConcDict()[repl.getInitConc()]
                
                metab = [ metab for metab in dm.getModel().getMetabolites() if metab.sbml_id == reactant][0]
                cn = metab.getInitialConcentrationReference().getCN()
                
                data.to_csv( outdir +'/experiment_%s_%i.tsv' % ( reactant, i ), sep='\t', header=True)
                
                exp = COPASI.CExperiment(dm)
                exp = exp_set.addExperiment(exp)
                info = COPASI.CExperimentFileInfo(exp_set)
                info.setFileName( outdir + '/experiment_%s_%i.tsv' % ( reactant, i ))
                exp.setObjectName(reaction.getName())
                exp.setFirstRow(1)
                exp.setLastRow(data.shape[0]+1)
                exp.setHeaderRow(1)
                exp.setFileName( outdir + '/experiment_%s_%i.tsv' % ( reactant, i ))
                exp.setExperimentType(COPASI.CTaskEnum.Task_timeCourse)
                exp.setSeparator('\t')
                exp.setNumColumns(2)
                
                # add the initial concentration as fit item
                item = problem.addFitItem(cn)
                item.setStartValue(conc_val)  # the current initial concentration 
                item.setLowerBound(COPASI.CCommonName(str(conc_val * 0.01)))
                item.setUpperBound(COPASI.CCommonName(str(conc_val * 100)))
                item.addExperiment(exp.getKey()) # the key of the current experiment

                # Mapping from .tsv file to COPASI bindings
                obj_map = exp.getObjectMap()
                obj_map.setNumCols(2)
                
                for i, col in enumerate(["time"] + [data.name]):
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
    
    ThinLayerCopasi().importEnzymeML('r0', 's1', "../../Resources/Examples/ThinLayers/COPASI/3IZNOK_TEST/3IZNOK_TEST.omex")
