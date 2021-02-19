from flask import Flask, request
from flask_restful import Resource, Api

from pyenzyme.restful import Create, Read

app = Flask(__name__)
api = Api(app)

api.add_resource(Create, '/create')
api.add_resource(Read,'/read' )

if __name__ == "__main__":
    
    app.run(debug=False)