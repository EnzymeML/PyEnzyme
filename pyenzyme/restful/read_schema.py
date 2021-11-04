'''
File: read_schema.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 11:20:29 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from marshmallow import fields, Schema


class ReadSchema(Schema):

    # JSON
    omex = fields.Str(required=True, description="EnzymeML OMEX container")
