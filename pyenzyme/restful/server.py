from flask import Flask, request
from flask_restful import Resource, Api

from pyenzyme.restful import Create, Read, restfulCOPASI

class RestfulServer():

    def run(self, debug=False):
        
        app = Flask(__name__)
        api = Api(app)

        api.add_resource(Create, '/create')
        api.add_resource(Read,'/read' )
        

        app.run(debug=debug)