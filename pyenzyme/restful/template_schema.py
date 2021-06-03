# @Author: Jan Range
# @Date:   2021-03-19 15:03:19
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-03-19 16:14:27

from marshmallow import fields, Schema, ValidationError

class TemplateSchema(Schema):
    
    ############# JSON #################
    
    xlsm = fields.Str(required=True, description="EnzymeML OMEX container")
    
    
    