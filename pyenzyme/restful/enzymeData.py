# @Author: Jan Range
# @Date:   2021-03-18 22:33:21
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-04-30 11:25:41

from flask import Flask, request, send_file, jsonify, Response
from flask_restful import Resource, Api
from flask_apispec import ResourceMeta, Ref, doc, marshal_with, use_kwargs, MethodResource

import tempfile
import os
import json
import pandas as pd

from pyenzyme.enzymeml.tools import EnzymeMLReader
from pyenzyme.restful.read_schema import ReadSchema

import marshmallow as ma

desc = 'This endpoint is used to deploy data on the EnzymeData Dataverse repository'

class enzymeData(MethodResource):
    
    def post(self):
        
        """
        Reads JSON formatted data and converts to an EnzymeML container.
        """
        
        # check if the post request has the file part
        if 'omex' not in request.files:
            return jsonify( {"response": 'No file part'} )
        
        # receive OMEX file
        file = request.files['omex']
        
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return jsonify( {"response": 'No file selected'} )
        
        if file and file.filename.split('.')[-1] == "omex":
            
            file = file.read()
            
            # Write to temp file
            dirpath = os.path.join( os.path.dirname( os.path.realpath(__file__)), "edata_write_temp" )
            os.makedirs(dirpath, exist_ok=True)
            
            tmp = os.path.join( dirpath, next(tempfile._get_candidate_names()) )

            with open(tmp, 'wb') as f:
                f.write(file)
            
            # Save JSON in variable
            enzmldoc = EnzymeMLReader().readFromFile(tmp)

            # Generate Dataverse Entry
            JSON = self.generateDataverseRequest(enzmldoc)
            
            # remove temp file
            os.remove(tmp)
            
            return Response(json.dumps(JSON),  mimetype='application/json')
        
    def generateDataverseRequest(self, enzmldoc):
        
        # Load mapping
        mapping = pd.read_csv('../../restful/enzymeData_Mapping.csv')
        
        # decompose mapping
        self.keys = { key: mapping[ mapping['classes'] == key ].drop('classes', axis=1) for key in list( set( mapping['classes'] ) ) }

        for key, maps in self.keys.items():
            
            n_maps = maps.set_index("Attributes").dropna().to_dict('index')
            self.keys[key] = n_maps
        
        # Initialize JSON body
        JSON = { "metadataBlocks": { "enzymeML" : { "displayName": "EnzymeML Metadata" }, 'citation': { "displayName": "Citation Metadata" } } }
        fields = list()
        cite_fields = list()
        
        # References
        references_dv = self.getCompound('enzymeMLReferences', enzmldoc.toJSON(d=True), multiple='false')
        if references_dv: fields.append( references_dv )
        
        # Creators
        for creator in enzmldoc.getCreator():
            data = { "given_name" : " ".join( [ creator.getGname(), creator.getFname() ] ), "mail": creator.getMail() }
            author_dv = self.getCompound( 'author', data, multiple='true' )
            dataset_dv = self.getCompound( 'dataset', data, multiple='true' )
            
            if author_dv: cite_fields.append(author_dv)
            if dataset_dv: cite_fields.append(dataset_dv)
            
        # Vessel
        vessel = enzmldoc.getVessel().toJSON(d=True, enzmldoc=enzmldoc)
        vessel_dv = self.getCompound( 'enzymeMLVessel', vessel, multiple='false' )
        if vessel_dv: fields.append(vessel_dv)
        
        # Reactants
        for key, reactant in enzmldoc.getReactantDict().items():
            reactant = reactant.toJSON(d=True, enzmldoc=enzmldoc)
            reactant_dv = self.getCompound( 'enzymeMLReactant', reactant, multiple='true' )
            
            if reactant_dv: fields.append(reactant_dv)
            
        # Proteins
        for key, protein in enzmldoc.getProteinDict().items():
            protein = protein.toJSON(d=True, enzmldoc=enzmldoc)
            protein_dv = self.getCompound( 'enzymeMLProtein', protein, multiple='true' )
            
            if protein_dv: fields.append(protein_dv)
            
        # Reactions
        for key, reaction in enzmldoc.getReactionDict().items():
            
            try: 
                # fetch model
                model = reaction.getModel().toJSON(d=True, enzmldoc=enzmldoc)
                
                kinetic_dv = self.getCompound( 'enzymeMLKineticLaw', model, multiple='true' )
                kinetic_dv['value'].append( self.getEnzymeDataField( 'enzymeMLKineticLawReaction', 'false', key, 'primitive' ) )
                
                fields.append(kinetic_dv)
                
            except AttributeError:
                pass
            
            getElems = lambda fun: [ enzmldoc.getReactant( tup[0] ).getName() if tup[0][0] == 's' else enzmldoc.getProtein( tup[0] ).getName() for tup in fun() ]
            
            educts = getElems( reaction.getEducts )
            products = getElems( reaction.getProducts )
            modifiers = getElems( reaction.getModifiers )
            
            reaction = reaction.toJSON(d=True, enzmldoc=enzmldoc)
            reaction_dv = self.getCompound( 'enzymeMLReaction', reaction, multiple='true' )
            
            # add elements
            reaction_dv['value'] += [ self.getEnzymeDataField( 'enzymeMLReactionEduct', 'true', educt, 'primitive' ) for educt in educts ]
            reaction_dv['value'] += [ self.getEnzymeDataField( 'enzymeMLReactionProduct', 'true', product, 'primitive' ) for product in products ]
            reaction_dv['value'] += [ self.getEnzymeDataField( 'enzymeMLReactionModifier', 'true', modifier, 'primitive' ) for modifier in modifiers ]
            
            fields.append(reaction_dv)

        JSON["metadataBlocks"]["enzymeML"]["fields"] = fields
        JSON["metadataBlocks"]["citation"]["fields"] = cite_fields
        
        return { "datasetVersion": JSON }
    
    def getCompound(self, compound_name, json_data, multiple ):
    
        compound = list()
        
        for key, item in self.keys[compound_name].items():
            
            try:
                compound.append( self.getEnzymeDataField( typename=item['typename'], multiple='false', value=json_data[key], typeclass=item['Typeclass'] ) )
                
            except KeyError:
                if item['Required'] == 'y':
                    print(f"Couldnt find required data {key} - Please make sure to fill out all required fields.")
                else:
                    pass
        
        if len(compound) > 0:
            return self.getEnzymeDataField( compound_name, multiple, compound, 'compound' )
        else:
            return None
    
    def getEnzymeDataField(self, typename, multiple, value, typeclass):
    
        return {
            
            "typeName": typename,
            "multiple": multiple,
            "typeClass": typeclass,
            "value": value
        }