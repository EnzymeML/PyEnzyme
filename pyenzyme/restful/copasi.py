# @Author: Jan Range
# @Date:   2021-03-18 22:33:21
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-03-24 14:27:36
from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api

import os
import json
import shutil
import io

from pyenzyme.enzymeml.tools import EnzymeMLReader, EnzymeMLWriter
from pyenzyme.enzymeml.core import Replicate
from pyenzyme.enzymeml.models import KineticModel, MichaelisMenten

import COPASI
from builtins import enumerate

import tempfile

class restfulCOPASI(Resource):
    
    def get(self):
        
        # receive OMEX file
        file = request.files['omex'].read()
        body = json.loads( request.form['json'] )
        
        # Send File
        dirpath = os.path.join( os.path.dirname(os.path.realpath(__file__)), "copasi_temp" )
        
        os.makedirs( dirpath, exist_ok=True )      
        
        dirpath = os.path.join( dirpath, next(tempfile._get_candidate_names()) )
        omexpath = os.path.join( dirpath, next(tempfile._get_candidate_names()) + '.omex' )
        
        os.mkdir(dirpath)
        
        # Write to temp file
        with open(omexpath, 'wb') as f:
            f.write(file)
        
        # Save JSON in variable
        enzmldoc = EnzymeMLReader().readFromFile(omexpath)
        
        # Estimate parameters
        km_val, km_unit, vmax_val, vmax_unit = self.importEnzymeML( body['reaction'], body['reactant'], dirpath, enzmldoc )
        
        menten_model = MichaelisMenten(vmax_val, vmax_unit, km_val, km_unit, body['reactant'], enzmldoc)
        
        # Write model to reaction
        enzmldoc.getReactionDict()[body['reaction']].setModel(menten_model)
        
        enzmldoc.toFile( dirpath )
        
        path = os.path.join(  
                            dirpath,
                            enzmldoc.getName(), 
                            enzmldoc.getName() + '.omex' 
                            )

        f = io.BytesIO( open(path, "rb").read() )
        f.name = enzmldoc.getName() + '_COPASI.omex'
        
        shutil.rmtree( dirpath, ignore_errors=True )
        
        return send_file( f,
                          mimetype='omex',
                          as_attachment=True,
                          attachment_filename='%s_COPASI.omex' % enzmldoc.getName() )
    
    def importEnzymeML(self, reaction_id, reactants, dirpath, enzmldoc):
        
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

        # Get reaction and replicates
        reaction = enzmldoc.getReaction(reaction_id)
        
        # Unify units according to selected reactant for
        # COPASI consistency in calculation
        self.unifyUnits(reactants[0], reaction, enzmldoc, 'mole')
        
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
                time_unit = data.index.name.split('/')[-1]
                
                metab = [ metab for metab in dm.getModel().getMetabolites() if metab.sbml_id == reactant][0]
                cn = metab.getInitialConcentrationReference().getCN()
                
                # TSV path
                tsvpath = os.path.join( dirpath, 'experiment_%s_%i.tsv' % ( reactant, i ) )
                
                data.to_csv( tsvpath, 
                             sep='\t', header=True)
                
                exp = COPASI.CExperiment(dm)
                #exp.setObjectName(reaction.getName())  # the name should be unique, so here we have to generate one
                exp.setObjectName('{0} at {1:.2f}'.format(metab.getObjectName(), conc_val))
                exp.setFirstRow(1)
                exp.setLastRow(data.shape[0]+1)
                exp.setHeaderRow(1)
                exp.setFileName( tsvpath )
                exp.setExperimentType(COPASI.CTaskEnum.Task_timeCourse)
                exp.setSeparator('\t')
                exp.setNumColumns(2)
                exp = exp_set.addExperiment(exp)
                info = COPASI.CExperimentFileInfo(exp_set)
                info.setFileName( tsvpath )

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
                    if col == "time":
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
        task = dm.getTask('Parameter Estimation')
        task.setMethodType(COPASI.CTaskEnum.Method_Statistics)
        COPASI.COutputAssistant.getListOfDefaultOutputDescriptions(task)
        COPASI.COutputAssistant.createDefaultOutput(913, task, dm)  # progress of fit plot
        # COPASI.COutputAssistant.createDefaultOutput(910, task, dm)  # parameter estimation result (all experiments in one)
        COPASI.COutputAssistant.createDefaultOutput(911, task, dm)  # parameter estimation result per experiment

        # Gather Menten parameters
        Km_value, vmax_value = self.run_parameter_estimation(dm)
        Km_unit = enzmldoc.getUnitDict()[conc_unit].getName()
        time_unit = enzmldoc.getUnitDict()[time_unit].getName()

        if "M" in Km_unit: 
            vmax_unit = Km_unit + ' / ' + time_unit
        else:
            split_u = Km_unit.split('/')
            vmax_unit = split_u[0] + ' / ' + f'( {split_u[1]} * {time_unit} )'
        
        return Km_value, Km_unit, vmax_value, vmax_unit
        
        '''
        parameters = { 'km_%s' % reactants[0]: (Km, enzmldoc.getReactant(reactants[0]).getSubstanceunits()),
                       'vmax_%s' % reactants[0]: (vmax, enzmldoc.getReactant(reactants[0]).getSubstanceunits()) }
        equation = "vmax_%s*%s/(km_%s+%s)" % tuple([reactants[0]]*4)
        km  = KineticModel(equation, parameters)

        doc.getReaction(reaction_id).setModel( km )

        enzmldoc.toFile(doc, outdir)
        '''
        
    def unifyUnits(self, reactant, reaction, enzmldoc, kind):

        # get unit of specified reactant
        unit = enzmldoc.getUnitDict()[ enzmldoc.getReactant(reactant).getSubstanceUnits() ]
        units = unit.getUnits()
        exponent = [ tup[1] for tup in units if tup[0] == kind ][0]
        scale = [ tup[2] for tup in units if tup[0] == kind ][0]

        # iterate through elements
        all_elems = [reaction.getEducts(), reaction.getProducts(), reaction.getModifiers()]

        for i, elem in enumerate(all_elems):
            for tup in elem:
                
                # get exponent and scale to calculate factor for new calculation
                if tup[0][0] == 's': unit_r = enzmldoc.getUnitDict()[ enzmldoc.getReactant(tup[0]).getSubstanceUnits() ];
                if tup[0][0] == 'p': unit_r = enzmldoc.getUnitDict()[ enzmldoc.getProtein(tup[0]).getSubstanceUnits() ];

                units_r = unit_r.getUnits()
                exponent_r = [ tup[1] for tup in units_r if tup[0] == kind ][0]
                scale_r = [ tup[2] for tup in units_r if tup[0] == kind ][0]

                nu_scale = exponent_r*( scale_r - scale )

                if nu_scale != 0:

                    # Reset Species initial concentrations
                    if tup[0][0] == 's':
                        enzmldoc.getReactant(tup[0]).setSubstanceUnits( unit.getId() )
                        enzmldoc.getReactant(tup[0]).setInitConc( enzmldoc.getReactant(tup[0]).getInitConc()*(10**nu_scale) )
                    elif tup[0][0] == 'p':
                        enzmldoc.getProtein(tup[0]).setSubstanceUnits( unit.getId() )
                        enzmldoc.getProtein(tup[0]).setInitConc( enzmldoc.getProtein(tup[0]).getInitConc()*(10**nu_scale) )

                    # Reset replicate concentrations
                    nu_repls = [ Replicate(
                                            repl.getReplica(), 
                                            repl.getReactant(), 
                                            repl.getType(), 
                                            unit.getId(), 
                                            repl.getTimeUnit(),
                                            repl.getInitConc()*(10**nu_scale)
                                             ) 
                                             
                                             for repl in tup[3] ]
                    
                    # Reset initial concentrations
                    nu_inits = [ init*(10**nu_scale) for init in tup[4] ]
                    
                    for conc in nu_inits:
                        enzmldoc.addConc( (conc, unit.getId()) )

                    # Remove old element
                    if i == 0: 
                        reaction.getEducts()[ reaction.getEduct( tup[0], index=True ) ] = ( tup[0], tup[1], tup[2], nu_repls, nu_inits )
                    if i == 1: 
                        reaction.getProducts()[ reaction.getProduct( tup[0], index=True ) ] = ( tup[0], tup[1], tup[2], nu_repls, nu_inits )
                    if i == 2: 
                        reaction.getModifiers()[ reaction.getModifier( tup[0], index=True ) ] = ( tup[0], tup[1], tup[2], nu_repls, nu_inits )
                        
    ##### COPASI FUNCTIONS #####

    def replace_kinetic_law(self, dm, reaction, function_name):
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


    def run_parameter_estimation(self, dm):
        task = dm.getTask('Parameter Estimation')
        assert (isinstance(task, COPASI.CFitTask))
        task.setScheduled(True)
        problem = task.getProblem()
        problem.setCalculateStatistics(False)
        # problem.setRandomizeStartValues(True)  # not randomizing this time

        reaction = dm.getModel().getReaction(0)
        self.replace_kinetic_law(dm, reaction, "Henri-Michaelis-Menten (irreversible)")
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

        vmax = None
        km = None

        for i in range(problem.getOptItemSize()):
            item = problem.getOptItem(i)
            cn = item.getObjectCN().getString()
            if cn not in cn_name_map:
                continue
            value = results.get(i)

            if cn_name_map[cn] == 'V': vmax = value;
            if cn_name_map[cn] == 'Km': km = value;
        
        return km, vmax