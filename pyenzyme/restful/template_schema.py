'''
File: template_schema.py
Project: restful
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 7:45:15 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from marshmallow import fields, Schema


class TemplateSchema(Schema):

    # JSON

    xlsm = fields.Str(required=True, description="EnzymeML OMEX container")
