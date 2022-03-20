Upload to Dataverse
===================

PyEnzyme offers the upload to any Dataverse installation that supports
the official `EnzymeML
metadatablock <https://doi.org/10.18419/darus-2105>`__ by utilizing the
Dataverse API `PyDaRUS <https://github.com/JR-1991/pyDaRUS>`__ to map
all relevant fields and perform upload. The following steps will be done
in this example:

-  Convert an EnzymeML spreadsheet to an ``EnzymeMLDocument``
-  Upload the dataset to Dataverse

.. code:: ipython3

    import pyenzyme as pe

.. code:: ipython3

    # Load the EnzymeMLDocument
    enzmldoc = pe.EnzymeMLDocument.fromTemplate("EnzymeML_Template_Example.xlsm")

.. code:: ipython3

    # Upload it to Dataverse (Dataset is private)
    enzmldoc.uploadToDataverse(dataverse_name="playground")

For reasons of data quality, the resulting dataset cant be viewed on the
web. In order to visit examples that have utilized the method, see the
`EnzymeML at
Work <https://darus.uni-stuttgart.de/dataverse/enzymeml_at_work>`__
collection.

--------------
