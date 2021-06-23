'''
File: exportData_schema.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 11:02:04 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from marshmallow import fields, Schema


class ExpotSchema(Schema):

    # JSON

    omex = fields.Str(required=True, description="EnzymeML OMEX container")
    reaction = fields.Str(required=True, description="Corresponding reaction")
    reactants = fields.List(fields.Str(required=False), required=False)
