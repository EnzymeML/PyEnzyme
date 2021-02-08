from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api

import os
import json

from pyenzyme.enzymeml.tools import EnzymeMLReader, EnzymeMLWriter

class trackMLFlow(Resource):
    
    def post(self):
        
        # receive OMEX file
        file = request.files['omex'].read()
        body = json.loads( request.form['json'] )
        
        # Get parameters
        URI = body["URI"]
        options = body["options"]
        
        if "parameters" in body.keys(): 
            parameters = { key: value for key, value in body["parameters"].items() }
        if "metrics" in body.keys()
            metrics = { key: value for key, value in body["metrics"].items() }
        
        # Write to temp file
        tmp = next(tempfile._get_candidate_names())
        with open(tmp, 'wb') as f:
            f.write(file)
        
        # Save JSON in variable
        enzmldoc = EnzymeMLReader().readFromFile(tmp)
        
        with ml
        
        return jsonify({ "Status": "Done" })
    
 