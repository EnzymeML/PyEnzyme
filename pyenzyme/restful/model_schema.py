# @Author: Jan Range
# @Date:   2021-03-19 15:03:19
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-03-19 16:14:27

from marshmallow import fields, Schema, ValidationError

class BytesField(fields.Field):
    def _validate(self, value):
        if not isinstance(value, bytes):
            raise ValidationError('Invalid input type.')

        if value is None or value == b'':
            raise ValidationError('Invalid value')

class ModelSchema(Schema):
    
    ############# JSON #################
    
    omex = fields.Str(required=True, description="EnzymeML OMEX container")
    reaction = fields.Str(required=True, description="Reaction Identifier")
    reactant = fields.Str(required=True, description="Reactant Identifier")
    
    
    