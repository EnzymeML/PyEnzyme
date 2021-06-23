'''
File: addModel.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 7:44:17 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from flask import request, send_file, jsonify
from flask_apispec import doc, marshal_with, MethodResource

import os
import json
import shutil
import io

from pyenzyme.enzymeml.tools import EnzymeMLReader
from pyenzyme.enzymeml.models import KineticModel
from pyenzyme.restful.addModel_schema import addModelSchema
from pyenzyme.enzymeml.tools.unitcreator import UnitCreator

import tempfile

desc = 'This endpoint is used to add a kinetic model to an existing EnzymeML document.\
        Upload your document via the "omex" key as form-data as well as a JSON body with the \
        reaction ID to add the model as well as the "equation" and "parameters" in an array.'


class addModel(MethodResource):

    @doc(tags=['Add KineticModel'], description=desc)
    @marshal_with(addModelSchema(), code=200)
    def post(self):

        # check if the post request has the file part
        if 'omex' not in request.files:
            return jsonify(
                {"response": 'No file part'}
            )

        if 'json' not in request.form:
            return jsonify(
                {"response": 'No json part'}
            )

        # receive OMEX file
        file = request.files['omex']
        body = json.loads(request.form['json'])

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify({"response": 'No file selected'})

        if file and file.filename.split('.')[-1] == "omex":

            file = file.read()

            # Send File
            dirpath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "addmodel_temp"
            )

            os.makedirs(dirpath, exist_ok=True)

            dirpath = os.path.join(
                dirpath,
                next(tempfile._get_candidate_names())
            )

            omexpath = os.path.join(
                dirpath,
                next(tempfile._get_candidate_names()) + '.omex'
            )

            os.mkdir(dirpath)

            # Write to temp file
            with open(omexpath, 'wb') as f:
                f.write(file)

            # Save JSON in variable
            enzmldoc = EnzymeMLReader().readFromFile(omexpath)
            os.remove(omexpath)

            # parse parameters
            parameters = dict()
            for param in body['parameters']:

                name = param["name"]
                value = float(param["value"])
                unit = UnitCreator().getUnit(param["unit"], enzmldoc)

                parameters[name] = (value, unit)

            # parse equation
            equation = body['equation']

            # create KineticModel
            km = KineticModel(equation, parameters)

            # Write model to reaction
            enzmldoc.getReactionDict()[body['reaction']].setModel(km)

            enzmldoc.toFile(dirpath)

            path = os.path.join(
                                dirpath,
                                enzmldoc.getName().replace(' ', '_') + '.omex'
                                )

            f = io.BytesIO(open(path, "rb").read())
            f.name = enzmldoc.getName() + '_Modeled.omex'

            shutil.rmtree(
                dirpath,
                ignore_errors=True
            )

            return send_file(
                f,
                mimetype='omex',
                as_attachment=True,
                attachment_filename='%s_Modeled.omex' % enzmldoc.getName()
            )
