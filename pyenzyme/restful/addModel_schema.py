'''
File: addModel_schema.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 10:19:09 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from marshmallow import fields, Schema


class addModelSchema(Schema):

    # JSON

    omex = fields.Str(required=True, description="EnzymeML OMEX container")

    class JSONSchema(Schema):

        reaction = fields.Str(required=True, description="Reaction Identifier")
        equation = fields.Str(required=True, description="Reactant Identifier")

        class ParametersSchema(Schema):

            name = fields.Str(required=True, description="Parameter name")
            value = fields.Float(required=True, description="Parameter value")
            unit = fields.Str(required=True, description="Parameter unit")

        parameters = fields.List(
            fields.Nested(
                ParametersSchema(),
                required=True
            )
        )

    json = fields.Nested(
        JSONSchema(),
        required=True
    )
