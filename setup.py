'''
Created on 12.08.2020

@author: JR
'''
import setuptools
from setuptools import setup

setup(      
    name='PyEnzyme',
    version='1.0.2',
    description='Handling of EnzymeML files',
    url='https://github.com/EnzymeML/PyEnzyme',
    author='Range, Jan',
    author_email='range.jan@web.de',
    license='BSD2',
    packages = setuptools.find_packages(),
    install_requires=[
        'flask',
        'flask-restful',
        'flask-apispec',
        'flask-cors',
        'python-libsbml',
        'numpy',
        'pandas',
        'python-libcombine',
        'python-copasi',
        'openpyxl',
        'marshmallow',
        'scipy',
        'apispec'
    ]
    )