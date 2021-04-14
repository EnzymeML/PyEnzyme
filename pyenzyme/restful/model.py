# @Author: Jan Range
# @Date:   2021-03-18 22:33:21
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-04-14 19:23:45
from flask import Flask, request, send_file, jsonify, redirect, flash
from flask_restful import Resource, Api
from flask_apispec import ResourceMeta, Ref, doc, marshal_with, use_kwargs, MethodResource
from werkzeug.utils import secure_filename

import os
import json
import shutil
import io

from pyenzyme.enzymeml.tools import EnzymeMLReader, EnzymeMLWriter
from pyenzyme.enzymeml.core import Replicate
from pyenzyme.enzymeml.models import KineticModel, MichaelisMenten
from pyenzyme.restful.model_schema import ModelSchema

from builtins import enumerate

from scipy.optimize import curve_fit

import tempfile
import numpy as np

desc = 'This endpoint is used to estimate Michaelis-Menten kinetic parameters.\
        Upload your OMEX file using form-data with the "omex" tag and specifiy the modeled \n\
        reaction/reactant via "reactant" and "reaction" JSON body. \
        The endpoint will return an OMEX file including the Michaelis-Menten equation as well \
        as the estimated parameters as an KineticModel annotation.'

class parameterEstimation(MethodResource):
    
    @doc(tags=['Model EnzymeReaction'], description=desc)
    @marshal_with(ModelSchema(), code=200)
    def get(self):
        
        # check if the post request has the file part
        if 'omex' not in request.files:
            return jsonify( {"response": 'No file part'} )
        
        if 'json' not in request.form:
            return jsonify( {"response": 'No json part'} )
        
        # receive OMEX file
        file = request.files['omex']
        body = json.loads( request.form['json'] )
        
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify( {"response": 'No file selected'} )
        
        if file and file.filename.split('.')[-1] == "omex":
            
            file = file.read()
        
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
            replicate = tc_data.name.split('/')[0]
            reactant = tc_data.name.split('/')[1]
            
            
            # generate product data for each
            init_conc_id = [ repl for repl in reac.getEduct(reactant)[3] if repl.getReplica() == replicate ][0].getInitConc()
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