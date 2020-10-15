'''
Created on 12.08.2020

@author: JR
'''
import setuptools
from setuptools import setup

setup(      
    name='PyEnzyme',
    version='1.0.0',
    description='Handling of EnzymeML files',
    url='https://github.com/EnzymeML/python-enzymeml',
    author='Range, Jan',
    author_email='range.jan@web.de',
    license='MIT',
    packages = setuptools.find_packages(),
    install_requires=['python-libsbml', 'numpy', 'pandas', 'python-libcombine']
    )