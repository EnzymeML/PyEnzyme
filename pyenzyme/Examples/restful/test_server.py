from flask import Flask, request
from flask_restful import Resource, Api

from pyenzyme.restful import Create, Read, restfulCOPASI

app = Flask(__name__)
api = Api(app)

api.add_resource(Create, '/create')
api.add_resource(Read,'/read' )
api.add_resource(restfulCOPASI, '/copasi')

if __name__ == "__main__":
    
    app.run(debug=True)