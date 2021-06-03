# @Author: Jan Range
# @Date:   2021-03-19 15:03:19
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-05-06 20:18:09

from marshmallow import fields, Schema, ValidationError

class ValidateSchema(Schema):
    
    ############# JSON #################
    
    class JSONSchema(Schema):
        link = fields.Str()
        custom = fields.Str()
    
    omex = fields.Str(required=True, description="EnzymeML OMEX container")
    custom = fields.Str(description="JSON template file")
    json = fields.Nested(JSONSchema())
    
    
    