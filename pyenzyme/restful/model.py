# @Author: Jan Range
# @Date:   2021-03-18 22:33:21
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-03-26 18:39:17
from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api

import os
import json
import shutil
import io

from pyenzyme.enzymeml.tools import EnzymeMLReader, EnzymeMLWriter
from pyenzyme.enzymeml.core import Replicate
from pyenzyme.enzymeml.models import KineticModel, MichaelisMenten

from builtins import enumerate

from scipy.optimize import curve_fit

import tempfile
import numpy as np

class parameterEstimation(Resource):
    
    def get(self):
        
        # receive OMEX file
        file = request.files['omex'].read()
        body = json.loads( request.form['json'] )
        
        # Send File
        dirpath = os.path.join( os.path.dirname(os.path.realpath(__file__)), "model_temp" )
        
        os.makedirs( dirpath, exist_ok=True )      
        
        dirpath = os.path.join( dirpath, next(tempfile._get_candidate_names()) )
        omexpath = os.path.join( dirpath, next(tempfile._get_candidate_names()) + '.omex' )
        
        os.mkdir(dirpath)
        
        # Write to temp file
        with open(omexpath, 'wb') as f:
            f.write(file)
        
        # Save JSON in variable
        enzmldoc = EnzymeMLReader().readFromFile(omexpath)
        
        # Get reacitons and time course data
        reac = enzmldoc.getReaction(body['reaction'])
        repls = reac.exportReplicates(body['reactant'])
        
        # Define model TODO
        def Menten( s, vmax, km ):
            return vmax*s / (s+km)
        
        # Estimate parameters
        km_val, km_stdev, vmax_val, vmax_stdev = self.estimateParams( Menten, reac, repls, enzmldoc )
        
        print(km_val, km_stdev, vmax_val, vmax_stdev)
        
        reactant_unit_id = enzmldoc.getReactant(body['reactant']).getSubstanceUnits()
        reactant_unit = enzmldoc.getUnitDict()[reactant_unit_id].getName()

        time_unit_id = repls.index.name.split('/')[-1]
        time_unit = enzmldoc.getUnitDict()[time_unit_id].getName()
        
        km_unit = reactant_unit
        
        if '/' in reactant_unit: 
            vmax_unit = f"{reactant_unit} {time_unit}"
        else:
            vmax_unit = f"{reactant_unit} / {time_unit}"
        
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
        f.name = enzmldoc.getName() + '_Modeled.omex'
        
        shutil.rmtree( dirpath, ignore_errors=True )
        
        return send_file( f,
                          mimetype='omex',
                          as_attachment=True,
                          attachment_filename='%s_Modeled.omex' % enzmldoc.getName() )
    
    def estimateParams(self, model, reac, repls, enzmldoc):
    
        vmax_vals = []
        km_vals = []
        
        for col in range(repls.shape[-1]):
            
            tc_data = repls.iloc[:,col]
            reactant = tc_data.name.split('/')[0]
            
            # generate product data for each
            init_conc_id = [ repl for repl in reac.getEduct("s1")[3] if repl.getReplica() == reactant ][0].getInitConc()
            init_conc = enzmldoc.getConcDict()[init_conc_id][0]


            # calculate deltas
            prev_val = init_conc
            prev_time = 0
            deltas = []

            for i in range(tc_data.shape[0]):
            
                if tc_data.index[i] == 0:
                    delta = ( prev_val - tc_data[i] )
                else:
                    delta = ( prev_val - tc_data[i] ) / abs( tc_data.index[i] - prev_time )

                deltas.append(delta)
                
                prev_val = tc_data[i]
                prev_time = tc_data.index[i] 
            
            # use deltas and substrate data to fit menten
            popt, pcov = curve_fit(model, tc_data.values, deltas)
            
            vmax_vals.append( popt[0] )
            km_vals.append( popt[1] )
        
        vmax_vals = np.array(vmax_vals)
        km_vals = np.array(km_vals)
        
        return vmax_vals.mean(), vmax_vals.std(), km_vals.mean(), km_vals.std()