'''
File: exportData.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 11:05:36 pm
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
from pyenzyme.restful.exportData_schema import ExpotSchema

desc = 'This endpoint is used to read an EnzymeML OMEX container and extract experimental data to JSON.\
        Upload your OMEX file using form-data with the "omex" tag in conjunction with a JSON body which reaction \
        and optionally species should be extracted. The endpoint will return a JSON representation of your data.'


class exportData(MethodResource):

    @doc(tags=['Export experimental data'], description=desc)
    @marshal_with(ExpotSchema(), code=200)
    def get(self):
        """
        Reads JSON formatted data and converts to an EnzymeML container.
        """

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

            # Write to temp file
            dirpath = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                "exportData_temp"
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

            # fetch reaction
            reac = enzmldoc.getReaction(body['reaction'])

            # export replicates
            if 'reactants' not in body.keys():
                reactants = [
                    tup[0] for tup in reac.getEducts()
                    + reac.getProducts()
                    + reac.getModifiers()
                ]
            else:
                reactants = body['reactants']

            JSON = {"educts": dict(), "products": dict(), "modifiers": dict()}

            for reactant in reactants:

                fundict = {

                    "educts": reac.getEduct,
                    "products": reac.getProduct,
                    "modifiers": reac.getModifier

                }

                for role, fun in fundict.items():

                    try:
                        # Check for ole and transform data
                        elem = fun(reactant)
                        repls = [
                            repl.toJSON(d=True, enzmldoc=enzmldoc)
                            for repl in elem[3]
                        ]

                        if len(repls) > 0:
                            # Add data to JSON response
                            JSON[role][reactant] = repls

                    except KeyError:
                        pass

            # remove temp file
            os.remove(tmp)

            return Response(json.dumps(JSON),  mimetype='application/json')
