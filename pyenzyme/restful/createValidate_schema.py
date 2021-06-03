# @Author: Jan Range
# @Date:   2021-03-19 15:03:19
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-05-06 21:46:27

from marshmallow import fields, Schema, ValidationError

class createValidateSchema(Schema):
    
    ############# JSON #################
    
    xlsx = fields.Str(required=True, description="EnzymeML Validation template")
    
    
    