# @Author: Jan Range
# @Date:   2021-03-18 22:33:21
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-03-19 15:19:43
from flask import Flask, request
from flask_restful import Resource, Api
from flask_apispec import FlaskApiSpec

from pyenzyme.restful import Create, Read, restfulCOPASI

app = Flask(__name__)
api = Api(app)

docs = FlaskApiSpec(app)

api.add_resource(Create, '/create')
api.add_resource(Read,'/read' )
api.add_resource(restfulCOPASI, '/copasi')

docs.register(Create, endpoint='create')
docs.register(Read, endpoint='read')

if __name__ == "__main__":
    
    app.run(debug=True)