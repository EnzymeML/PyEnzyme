from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api

import tempfile
import os
import json

from pyenzyme.enzymeml.tools import EnzymeMLReader
from pyenzyme.enzymeml.models import KineticModel

class Read(Resource):
    
    def get(self):
        """
        Reads JSON formatted data and converts to an EnzymeML container.
        """
        
        # receive OMEX file
        file = request.files['omex'].read()
        
        # Write to temp file
        tmp = next(tempfile._get_candidate_names())
        with open(tmp, 'wb') as f:
            f.write(file)
        
        # Save JSON in variable
        enzmldoc = EnzymeMLReader().readFromFile(tmp)
        JSON = enzmldoc.toJSON(d=True)
        
        # remove temp file
        os.remove(tmp)
        
        return jsonify(JSON)