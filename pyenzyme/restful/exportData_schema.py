# @Author: Jan Range
# @Date:   2021-03-19 15:03:19
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-04-28 10:28:30

from marshmallow import fields, Schema, ValidationError

class ExpotSchema(Schema):
    
    ############# JSON #################
    
    omex = fields.Str(required=True, description="EnzymeML OMEX container")
    reaction = fields.Str( required=True, description="Corresponding reaction" )
    reactants = fields.List( fields.Str(required=False), required=False )
    
    
    