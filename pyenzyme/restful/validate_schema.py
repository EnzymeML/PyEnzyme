# @Author: Jan Range
# @Date:   2021-03-19 15:03:19
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-05-11 18:38:23

from marshmallow import fields, Schema

class ValidateSchema(Schema):
    """Schema describing the Form-Data request to the calidation endpoint
    """
    
    class JSONSchema(Schema):
        """Schema describing the JSON part 
        """
        link = fields.Str()
        custom = fields.Str()
    
    omex = fields.Str(required=True, description="EnzymeML OMEX container")
    custom = fields.Str(description="JSON template file")
    json = fields.Nested(JSONSchema())
    
    
    