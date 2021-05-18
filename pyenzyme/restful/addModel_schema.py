# @Author: Jan Range
# @Date:   2021-03-19 15:03:19
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-05-18 07:47:35

from marshmallow import fields, Schema

class addModelSchema(Schema):
    
    ############# JSON #################
    
    omex = fields.Str(required=True, description="EnzymeML OMEX container")
    
    class JSONSchema(Schema):
        
        reaction = fields.Str(required=True, description="Reaction Identifier")
        equation = fields.Str(required=True, description="Reactant Identifier")
        
        class ParametersSchema(Schema):
            
            name = fields.Str(required=True, description="Parameter name")
            value = fields.Float(required=True, description="Parameter value")
            unit = fields.Str(required=True, description="Parameter unit")
        
        parameters = fields.List( fields.Nested( ParametersSchema() ), required=True )
        
    json = fields.Nested( JSONSchema(), required=True )
    
    