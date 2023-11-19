"""
File: setup.py
Project: PyEnzyme
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 9:57:56 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
"""

import setuptools
from setuptools import setup

setup(
    name="PyEnzyme",
    version="1.1.5",
    description="Handling of EnzymeML files",
    url="https://github.com/EnzymeML/PyEnzyme",
    author="Range, Jan",
    author_email="jan.range@simtech.uni-stuttgart.de",
    license="BSD2 Clause",
    packages=setuptools.find_packages(),
    install_requires=[
        "python-libsbml",
        "numpy",
        "pandas",
        "python-libcombine",
        "scipy",
        "texttable",
        "pydantic==1.8.2",
        "deprecation",
        "deepdiff",
        "python-multipart",
        "openpyxl",
        "xlsxwriter",
        "numexpr",
        "seaborn",
        "plotly",
        "pyyaml",
        "deprecation",
        "xmltodict",
        "requests",
    ],
    extras_require={
        "test": ["pytest-cov"],
        "copasi": ["python-copasi"],
        "pysces": ["pysces", "lmfit"],
        "rest": ["fastapi", "uvicorn"],
        "modeling": ["python-copasi", "pysces", "lmfit"],
        "dataverse": ["pyDaRUS", "easyDataverse", "pydataverse"],
        "all": [
            "python-copasi",
            "pysces",
            "lmfit",
            "fastapi",
            "uvicorn",
            "pyDaRUS",
            "easyDataverse",
            "pydataverse",
        ],
    },
)
