# @Author: Jan Range
# @Date:   2021-03-18 22:33:21
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-04-28 10:33:35
from flask import Flask, request
from flask_restful import Resource, Api
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec import FlaskApiSpec
from flask_cors import CORS

from pyenzyme.restful import Create, Read, restfulCOPASI, parameterEstimation, convertTemplate, exportData

app = Flask(__name__)
api = Api(app)

app.secret_key = 'the random string'

docs = FlaskApiSpec(app)

api.add_resource(Create, '/create')
api.add_resource(Read,'/read' )
api.add_resource(restfulCOPASI, '/copasi')
api.add_resource(parameterEstimation, '/model')
api.add_resource(convertTemplate, '/template/convert')
api.add_resource(exportData, '/exportdata')

docs.register(Create, endpoint='create')
docs.register(Read, endpoint='read')
docs.register(parameterEstimation, endpoint='parameterestimation')
docs.register(convertTemplate, endpoint='converttemplate')
docs.register(exportData, endpoint='exportdata')

if __name__ == "__main__":
        
    app.run(host="0.0.0.0")