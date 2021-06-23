'''
File: read.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 11:22:54 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from flask import request, jsonify, Response
from flask_apispec import doc, marshal_with, MethodResource

import tempfile
import os
import json

from pyenzyme.enzymeml.tools import EnzymeMLReader
from pyenzyme.restful.read_schema import ReadSchema

desc = 'This endpoint is used to read an EnzymeML OMEX container to JSON.\
        Upload your OMEX file using form-data with the "omex" tag. \
        The endpoint will return a JSON representation of your EnzymeML document.'


class Read(MethodResource):

    @doc(tags=['Read EnzymeML'], description=desc)
    @marshal_with(ReadSchema(), code=200)
    def get(self):
        """
        Reads JSON formatted data and converts to an EnzymeML container.
        """

        # check if the post request has the file part
        if 'omex' not in request.files:
            return jsonify(
                {"response": 'No file part'}
            )

        # receive OMEX file
        file = request.files['omex']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify(
                {"response": 'No file selected'}
            )

        if file and file.filename.split('.')[-1] == "omex":

            file = file.read()

            # Write to temp file
            dirpath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "read_temp"
            )

            os.makedirs(dirpath, exist_ok=True)

            tmp = os.path.join(
                dirpath,
                next(tempfile._get_candidate_names())
            )

            with open(tmp, 'wb') as f:
                f.write(file)

            # Save JSON in variable
            enzmldoc = EnzymeMLReader().readFromFile(tmp)

            # remove temp file
            os.remove(tmp)

            # Convert to JSON
            JSON = enzmldoc.toJSON(d=True)

            return Response(json.dumps(JSON),  mimetype='application/json')
