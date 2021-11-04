'''
File: createValidate_schema.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 10:41:24 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from marshmallow import fields, Schema


class createValidateSchema(Schema):

    # JSON

    xlsx = fields.Str(
        required=True,
        description="EnzymeML Validation template"
    )
