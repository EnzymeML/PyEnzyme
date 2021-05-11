# @Author: Jan Range
# @Date:   2021-03-19 15:03:19
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-05-11 19:15:24

from marshmallow import fields, Schema

class TemplateSchema(Schema):
    """Spreadsheet template conversion endpoint schema
    """
    xlsm = fields.Str(required=True, description="EnzymeML OMEX container")