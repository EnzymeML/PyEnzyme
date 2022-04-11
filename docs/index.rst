.. PyEnzyme documentation master file, created by
   sphinx-quickstart on Tue Nov 30 22:37:31 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to PyEnzyme's documentation!
====================================

PyEnzyme is the interface to the data model EnzymeML and offers a
convenient way to document and model research data. Lightweight syntax
for rapid development of data management solution in enzymology and
biocatalysis.

Get started with PyEnzyme by running the following command

::

   # Using PyPI
   python -m pip install pyenzyme

Or build by source

::

   git clone https://github.com/EnzymeML/PyEnzyme.git
   cd PyEnzyme
   python3 setup.py install

Package Options
---------------

PyEnzyme comes with many flavors, choose whether you want only the base
installation, the modeling package or all of it using the following
options.

::

   # COPASI - modeling
   python -m pip install "pyenzyme[copasi]"

   # PySCeS - modeling
   python -m pip install "pyenzyme[pysces]"

   # Modeling package
   python -m pip install "pyenzyme[modeling]"

   # REST API
   python -m pip install "pyenzyme[rest]"

   # Dataverse
   python -m pip install "pyenzyme[dataverse]"

   # Complete
   python -m pip install "pyenzyme[all]"

REST-API
-------------------

If you want to deploy PyEnzyme as a server and use our REST-API to
access PyEnzyme from any HTTP-capable programming language, use our
official `docker
image <https://hub.docker.com/r/enzymeml/pyenzyme/tags>`__ or simply
copy and past the following.

.. code:: bash

   docker pull enzymeml/pyenzyme:latest
   docker run -p 8000:8000 enzymeml/pyenzyme:latest

See the `API documentation <https://enzymeml.sloppy.zone>`__ for details
on our endpoints. You can also use our self-hosted PyEnzyme instance if
you have no server space - Use https://enzymeml.sloppy.zone as base URL
to the endpoints.

Table of contents
-------------------

.. toctree::
   :maxdepth: 0
   :caption: First Steps

   _getstarted/01_BasicUsage.rst
   _getstarted/02_Validation.rst
   _getstarted/03_Visualisation.rst
   _getstarted/04_UploadToDataverse.rst

.. toctree::
   :maxdepth: 1
   :caption: Examples

   _examples/01_KineticModeling_PySCeS.rst

.. toctree:: 
   :maxdepth: 2
   :caption: API Reference

   core




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
