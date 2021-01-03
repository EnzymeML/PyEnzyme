from flask import Flask, request
from flask_restful import Resource, Api

from pyenzyme.enzymeml.core import EnzymeMLDocument, Protein, Reactant, EnzymeReaction, Replicate
from pyenzyme.enzymeml.models import KineticModel

app = Flask(__name__)
api = Api(app)

todos = {}

class CreateEnzymeML(Resource):
    
    def parseReacElements(self, func, body, enzmldoc):

        func(
            enzmldoc.getReactant( body['species'], by_id=False ).getId(), 
            body['stoich'], 
            body['constant'], 
            enzmldoc, 
            replicates=[ Replicate(**repl) for repl in body['replicates'] ], 
            init_concs=[]
            )
    
    def post(self):
        """Read JSON formatted data and converts to an EnzymeML container.

        Returns:
            File: OMEX File 
        """
        json_data = request.get_json(force=True)
        
        # create enzymeml document
        param_doc = { key: item for key, item in json_data.items() if type(item) != list }
        enzmldoc = EnzymeMLDocument(**param_doc)
        
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
            for educt in reaction['educts']: self.parseReacElements( reac.addEduct, educt, enzmldoc )
            
            enzmldoc.addReaction(reac)

        return enzmldoc.toJSON(d=True)
            

api.add_resource(CreateEnzymeML, '/name')

if __name__ == '__main__':
    app.run(debug=True)