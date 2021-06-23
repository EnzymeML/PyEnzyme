'''
File: validate_schema.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 12:22:25 am
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from marshmallow import fields, Schema


class ValidateSchema(Schema):

    # JSON

    class JSONSchema(Schema):
        link = fields.Str()
        custom = fields.Str()

    omex = fields.Str(required=True, description="EnzymeML OMEX container")
    custom = fields.Str(description="JSON template file")
    json = fields.Nested(JSONSchema())
