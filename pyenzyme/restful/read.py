# @Author: Jan Range
# @Date:   2021-03-18 22:33:21
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-03-19 15:30:52

from flask import Flask, request, send_file, jsonify
from flask_restful import Resource, Api
from flask_apispec import ResourceMeta, Ref, doc, marshal_with, use_kwargs, MethodResource

import tempfile
import os
import json

from pyenzyme.enzymeml.tools import EnzymeMLReader
from pyenzyme.enzymeml.models import KineticModel

import marshmallow as ma

class OMEXField(ma.fields.Field):
    """Field that serializes to a string of numbers and deserializes
    to a list of numbers.
    """

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ""
        return "".join(str(d) for d in value)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return [int(c) for c in value]
        except ValueError as error:
            raise ValidationError("TEST") from error

class Read(MethodResource):
    
    @doc(tags=['Read EnzymeML'], description='This endpoint is used to read an EnzymeML document to JSON data. Make sure to send your data via form-data and specify the file-object as "omex"')
    @use_kwargs({'omex': OMEXField()})
    def get(self):
        """
        Reads JSON formatted data and converts to an EnzymeML container.
        """
        
        # receive OMEX file
        file = request.files['omex'].read()
        
        # Write to temp file
        tmp = os.path.join( os.path.dirname(os.path.realpath(__file__)), next(tempfile._get_candidate_names()) )

        with open(tmp, 'wb') as f:
            f.write(file)
        
        # Save JSON in variable
        enzmldoc = EnzymeMLReader().readFromFile(tmp)
        JSON = enzmldoc.toJSON(d=True)
        
        # remove temp file
        os.remove(tmp)
        
        return jsonify(JSON)