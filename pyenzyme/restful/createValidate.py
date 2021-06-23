'''
File: createValidate.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 10:44:57 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from flask import request, send_file, jsonify
from flask_apispec import doc, marshal_with, MethodResource
from werkzeug.utils import secure_filename

import json
import io
import numpy as np
import pandas as pd

from pyenzyme.restful.createValidate_schema import createValidateSchema

desc = 'This endpoint is used to convert an EnzymeML-Validation spreadsheet to an EnzymeML-Validation JSON.\
        Upload your XLSX file using form-data with the "xlsx" tag. \
        The endpoint will return the converted template as a JSON file.'


class createValidate(MethodResource):

    @doc(tags=['Create EnzymeML-Validate'], description=desc)
    @marshal_with(createValidateSchema(), code=200)
    def post(self):

        # check if the post request has the file part
        if 'xlsx' not in request.files:
            return jsonify(
                {"response": 'No file part'}
            )

        file = request.files['xlsx']

        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify(
                {"response": 'No file selected'}
            )

        if file and file.filename.split('.')[-1] in "xlsx":

            filename = secure_filename(file.filename).split('.')[0]

            file.seek(0)

            df = pd.read_excel(file, skiprows=2)
            classes = list(set(df.clss))

            params = dict()

            # Parse into fields
            for clss in classes:

                df_red = df[df.clss == clss]
                df_red = df_red.replace(np.nan, 'nan', regex=True)
                fields = dict()

                for _, row in df_red.iterrows():

                    att_name = row['atts']
                    att_type = row['Data Type']

                    if row['Range'] != 'nan':

                        val_max = row['Range'].split('-')[1]
                        val_min = row['Range'].split('-')[0]
                        val_range = [float(val_min), float(val_max)]

                    elif row['Range'] == 'nan':
                        val_range = None

                    if row['Vocabulary'] != 'nan':

                        vocab = row['Vocabulary'].split(',')

                    elif row['Vocabulary'] == 'nan':
                        vocab = None

                    # Create Field for JSON valid file
                    importance = row['Attribute Importance']
                    fields[att_name] = self.generateValidField(
                        att_type,
                        importance,
                        val_range,
                        vocab
                    )

                params[clss] = fields

            valid_file = self.composeValidationTemplate(**params)

            f = io.BytesIO(str.encode(json.dumps(valid_file, indent=4)))
            f.name = filename + '.json'

            return send_file(
                f,
                mimetype='json',
                as_attachment=True,
                attachment_filename=f.name
            )

    def generateValidField(
        self,
        type_,
        importance,
        val_range=None,
        vocab=None
    ):

        if vocab:
            # Vocab check
            if type(vocab) != list: 
                vocab = [vocab]

            for voc in vocab:
                # Check if vocabulary is string
                if type(voc) != str:
                    raise TypeError("Vocab element has to be string!")

        if val_range:
            # val_range check
            if type(val_range) != list:
                raise TypeError("val_range has to be provided as list")
            if len(val_range) != 2:
                raise AttributeError(
                    "val_range hast to include minimum and maximum exclusively"
                )

        # check types via dirctionary
        type_dict = {
            "string": str,
            "integer": int,
            "float": float,
            "boolean": bool
        }

        # generate dicionary
        valid_template = dict()
        valid_template["importance"] = importance

        if type_ in type_dict.keys():
            valid_template["type"] = type_

        if val_range:
            if type_ == "int" or type_ == "float":
                valid_template["val_range"] = [val_range[0], val_range[1]]

        elif vocab:
            valid_template["vocab"] = vocab

        return valid_template

    def composeValidationTemplate(
                                self,
                                enzmldoc=None,
                                creator=None,
                                reaction=None,
                                protein=None,
                                reactant=None,
                                replicate=None,
                                vessel=None,
                                model=None,
                                ):

        valid_temp = dict()

        if enzmldoc:
            valid_temp["EnzymeMLDocument"] = enzmldoc
        if creator:
            valid_temp["Creator"] = creator
        if reaction:
            valid_temp["EnzymeReaction"] = reaction
        if protein:
            valid_temp["Protein"] = protein
        if reactant:
            valid_temp["Reactant"] = reactant
        if replicate:
            valid_temp["Replicate"] = replicate
        if vessel:
            valid_temp["Vessel"] = vessel
        if model:
            valid_temp["model"] = model

        return valid_temp
