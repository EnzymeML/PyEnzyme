# @Author: Jan Range
# @Date:   2021-03-18 22:33:21
# @Last Modified by:   Jan Range
# @Last Modified time: 2021-05-18 09:34:16
from pyenzyme.restful.addModel import addModel
from flask import Flask, render_template
from flask_restful import Api
from flask_apispec import FlaskApiSpec
from flask_cors import CORS

from pyenzyme.restful import Create, Read, restfulCOPASI, parameterEstimation, convertTemplate, exportData, enzymeData, Validate, createValidate

app = Flask(__name__,template_folder='.')
api = Api(app)

app.secret_key = 'secretkeyexample'

CORS(app)

docs = FlaskApiSpec(app)

api.add_resource(Create, '/create')
api.add_resource(Read,'/read' )
api.add_resource(restfulCOPASI, '/copasi')
api.add_resource(parameterEstimation, '/model')
api.add_resource(convertTemplate, '/template/convert')
api.add_resource(exportData, '/exportdata')
api.add_resource(enzymeData, '/enzymedata')
api.add_resource(Validate, '/validate')
api.add_resource(createValidate, '/validate/create')
api.add_resource(addModel, '/addmodel')

@app.route('/template/upload')
def upload_file():
    return render_template('upload.html')

@app.route('/validate/upload')
def validate_template():
    return render_template('validate_template.html')

docs.register(Create, endpoint='create')
docs.register(Read, endpoint='read')
docs.register(parameterEstimation, endpoint='parameterestimation')
docs.register(convertTemplate, endpoint='converttemplate')
docs.register(exportData, endpoint='exportdata')
docs.register(Validate, endpoint='validate')
docs.register(createValidate, endpoint='createvalidate')
docs.register(addModel, endpoint='addmodel')

if __name__ == "__main__":
        
    app.run(host="0.0.0.0")