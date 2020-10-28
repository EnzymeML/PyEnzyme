'''
Created on 04.08.2020
@author: JR
'''

from pyenzyme.enzymeml.tools import EnzymeMLReader, EnzymeMLWriter
import os

import COPASI
from builtins import enumerate


def replace_kinetic_law(dm, reaction, function_name):
    # type: (COPASI.CDataModel, COPASI.CReaction, str) -> None
    functions = COPASI.CRootContainer.getFunctionList()
    function = functions.findFunction(function_name)
    if function is None:
        print("No such function defined, can't change kinetics")
        return

    if reaction.isReversible():  # for now force the kinetic to be irreversible
                                 # (otherwise the kinetic law does not apply)
        reaction.setReversible(False)

    # now since we have 2 substrates in this case and we would automatically assign the first substrate
    # to the new function, we want to make sure that we map to the same substrates as the old reaction
    substrates = None
    fun_params = reaction.getFunctionParameters()
    for i in range(fun_params.size()):
        param = fun_params.getParameter(i)
        if param.getUsage() == COPASI.CFunctionParameter.Role_SUBSTRATE:
            substrates = reaction.getParameterCNs(param.getObjectName())
            break

    # set the new function
    reaction.setFunction(function)
    if substrates is not None:
        # in case we found substrates map them
        reaction.setParameterCNs('substrate', substrates)

    # recompile model so it can be simulated later on
    reaction.compile()
    dm.getModel().forceCompile()
    pass


def run_parameter_estimation(dm):
    task = dm.getTask('Parameter Estimation')
    assert (isinstance(task, COPASI.CFitTask))
    task.setScheduled(True)
    problem = task.getProblem()
    problem.setCalculateStatistics(False)
    # problem.setRandomizeStartValues(True)  # not randomizing this time

    reaction = dm.getModel().getReaction(0)
    replace_kinetic_law(dm, reaction, "Henri-Michaelis-Menten (irreversible)")
    objects = reaction.getParameterObjects()

    cn_name_map = {}

    # add fit items for reaction parameters
    for obj in objects:
        param = obj[0]
        if param.getObjectAncestor('Reaction') is None:
            # skip all non-local parameters
            continue
        value = reaction.getParameterValue(param.getObjectName())
        item = problem.addFitItem(param.getValueObject().getCN())
        item.setStartValue(value)  # the current initial concentration
        item.setLowerBound(COPASI.CCommonName(str(value * 0.0001)))
        item.setUpperBound(COPASI.CCommonName(str(value * 10000)))
        cn_name_map[param.getValueObject().getCN().getString()] = param.getObjectName()

    # switch optimization method
    task.setMethodType(COPASI.CTaskEnum.Method_LevenbergMarquardt)

    # run optimization
    task.initialize(COPASI.CCopasiTask.OUTPUT_UI)
    task.process(True)

    # print parameter values
    assert (isinstance(problem, COPASI.CFitProblem))
    results = problem.getSolutionVariables()
    for i in range(problem.getOptItemSize()):
        item = problem.getOptItem(i)
        cn = item.getObjectCN().getString()
        if cn not in cn_name_map:
            continue
        value = results.get(i)
        print(" {0}: {1}".format(cn_name_map[cn], value))


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
        doc = EnzymeMLReader().readFromFile(path, omex=True)
        enzmldoc = deepcopy(doc)

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
                #exp.setObjectName(reaction.getName())  # the name should be unique, so here we have to generate one
                exp.setObjectName('{0} at {1:.2f}'.format(metab.getObjectName(), conc_val))
                exp.setFirstRow(1)
                exp.setLastRow(data.shape[0]+1)
                exp.setHeaderRow(1)
                exp.setFileName( outdir + '/experiment_%s_%i.tsv' % ( reactant, i ))
                exp.setExperimentType(COPASI.CTaskEnum.Task_timeCourse)
                exp.setSeparator('\t')
                exp.setNumColumns(2)
                exp = exp_set.addExperiment(exp)
                info = COPASI.CExperimentFileInfo(exp_set)
                info.setFileName(outdir + '/experiment_%s_%i.tsv' % (reactant, i))

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
        COPASI.COutputAssistant.createDefaultOutput(913, task, dm)  # progress of fit plot
        # COPASI.COutputAssistant.createDefaultOutput(910, task, dm)  # parameter estimation result (all experiments in one)
        COPASI.COutputAssistant.createDefaultOutput(911, task, dm)  # parameter estimation result per experiment
        dm.saveModel( outdir + "/" + fname + ".cps", True)
        
        print("Saved model to " + outdir + "/" + fname + ".cps")

        run_parameter_estimation(dm)
        
if __name__ == '__main__':
    print(os.path.abspath("../../Resources/Examples/ThinLayers/COPASI/3IZNOK_TEST/3IZNOK_TEST.omex"))
    ThinLayerCopasi().importEnzymeML('r0', 's1', os.path.abspath("../../Resources/Examples/ThinLayers/COPASI/3IZNOK_TEST/3IZNOK_TEST.omex") )