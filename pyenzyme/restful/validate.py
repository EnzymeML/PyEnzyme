'''
File: validate.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 12:26:04 am
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
from pyenzyme.restful.validate_schema import ValidateSchema

desc = 'This endpoint is used to validate an EnzymeML OMEX container.\
        Upload your OMEX file using form-data with the "omex" tag and a valid \
        link to a JSON validation template via key "link". \
        Alternatively, you can also provide your own JSON template by using \
        the key "custom" in the JSON body or provide a file with "custom". \
        Please note, that, when a link has already been given, the "custom" \
        key will be overridden. \
        The endpoint will return a JSON representation \
        of your EnzymeML document.'


class Validate(MethodResource):

    @doc(tags=['Validate EnzymeML'], description=desc)
    @marshal_with(ValidateSchema(), code=200)
    def get(self):
        """
        Reads JSON formatted data and converts to an EnzymeML container.
        """

        # check if the post request has the file part
        if 'omex' not in request.files:
            return jsonify(
                {"response": 'No file part'})

        if 'json' not in request.form:

            if 'custom' not in request.files:
                return jsonify(
                    {"response": 'No template has been provided'}
                )

            else:
                custom = request.files['custom'].read()
                body = {'custom': json.loads(custom)}

        else:
            # load json body
            body = json.loads(request.form['json'])

            if 'link' not in body.keys():
                # check if custom is given
                if 'custom' not in body.keys():
                    return jsonify(
                        {"response": 'No validate link/json part'}
                    )

        # receive OMEX file
        file = request.files['omex']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify({"response": 'No file selected'})

        if file and file.filename.split('.')[-1] == "omex":

            file = file.read()

            # Write to temp file
            dirpath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "validate_temp"
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

            print(body)

            # Fetch validate template
            if 'link' in body.keys():
                response = enzmldoc.validate(
                    link=body['link'],
                    log=True
                )

            elif 'custom' in body.keys():
                response = enzmldoc.validate(
                    JSON=body['custom'],
                    log=True
                )

            # remove temp file
            os.remove(tmp)

            return Response(json.dumps(response),  mimetype='application/json')
