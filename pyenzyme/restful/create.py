from flask import Flask, request, send_file
from flask_restful import Resource, Api

import tempfile
import os
import shutil
import io

from pyenzyme.enzymeml.core import EnzymeMLDocument, Protein, Reactant, EnzymeReaction, Replicate, Vessel
from pyenzyme.enzymeml.models import KineticModel



class Create(Resource):
    
    def post(self):
        """
        Reads JSON formatted data and converts to an EnzymeML container.
        """
        
        json_data = request.get_json(force=True)
        
        # create enzymeml document
        param_doc = { key: item for key, item in json_data.items() 
                      if type(item) != list and type(item) != dict }
        enzmldoc = EnzymeMLDocument(**param_doc)
        
        # create vessel
        vessel = Vessel( **json_data["Vessel"] )
        enzmldoc.setVessel(vessel)
        
        # parse proteins
        for protein in json_data['Protein']:
            enzmldoc.addProtein(
                Protein(**protein)
            )
            
        # parse reactants
        for reactant in json_data['Reactant']:
            enzmldoc.addReactant(
                Reactant(**reactant)
            )
            
        # parse reactions
        for reaction in json_data['Reaction']:
            # initialize reaction meta data
            param_reac = { key: item for key, item in reaction.items()
                            if type(item) != list and type(item) != dict }
            
            reac = EnzymeReaction(**param_reac)
            
            # add educts by name
            for educt in reaction['educts']: self.parseReacElements( reac.addEduct, educt, reac, enzmldoc )
            
            # add products by name
            for product in reaction['products']: self.parseReacElements( reac.addProduct, product, reac, enzmldoc )
            
            # add modifiers by name
            for modifier in reaction['modifiers']: self.parseReacElements( reac.addModifier, modifier, reac, enzmldoc )
            
            enzmldoc.addReaction(reac)

        # Send File  
        dirpath = os.path.join( os.getcwd(), next(tempfile._get_candidate_names()) )
        enzmldoc.toFile( dirpath )
        
        path = os.path.join(  
                            dirpath,
                            enzmldoc.getName(), 
                            enzmldoc.getName() + '.omex' 
                            )

        f = io.BytesIO( open(path, "rb").read() )
        f.name = enzmldoc.getName() + '.omex'
        
        shutil.rmtree( dirpath, ignore_errors=True )
        
        return send_file( f,
                          mimetype='omex',
                          as_attachment=True,
                          attachment_filename='%s.omex' % enzmldoc.getName() )
    
    def parseReacElements(self, func, body, reac, enzmldoc):
        """
        Parses Reaction elements based on given function func. Internal usage!

        Args:
            func (addXXX Function): EnzymeReaction function to add Educt/Product/Modifier
            body (Dictionaly): JSON body describing list of educts/products/modifiers
            reac (EnzymeReaction): Object used to add respective Entities as well as Replicates
            enzmldoc (EnzymeMLDocument): Used for consistency and name parsing

        Raises:
            KeyError: Raises error if given reactants/proteins are not given
        """
        
        try:
            # Check if it is a reactant
            species_id = enzmldoc.getReactant( body['species'], by_id=False ).getId()
        except KeyError:
            try:
                # Check if it is a protein
                species_id = enzmldoc.getProtein( body['species'], by_id=False ).getId()
            except KeyError:
                raise KeyError( f"Reactant/Protein {body['species']} not found in body! Make sure entries are consistent")
            
        func(
            species_id, 
            body['stoich'], 
            body['constant'], 
            enzmldoc
            )
        
        for repl in body['replicates']:
            
            replicate = Replicate(**repl)
            replicate.setReactant(species_id)
            reac.addReplicate(replicate, enzmldoc)