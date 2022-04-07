Validation of EnzymeML documents
================================

EnzymeML is considered a container for data and does not perform any
validation aside from data type checks. Hence, a user is free to insert
whatever is necessary for the application without any restrictions.
However, once data will be published to databases, data compliance needs
to be guaranteed.

For this, PyEnzyme allows EnzymeML documents to be validated against a
database standard before upload. Databases can host a specific YAML file
that can be generated from a spreadsheet, which in turn will validate
compliance or not. In addition, if the document is non-compliant, a
report will be given where and why a document received negative
validation.

The YAML validation file mirrors the complete EnzymeML data model and
offers content to be checked on the following attributes:

-  **Mandatory**: Whether or not this field is required.
-  **Value ranges**: An interval where vertain values should be
-  **Controlled vocabularies**: For fields where only certain values are
   allowed. Intended to use for textual fields.

The following example will demonstrate how to generate a EnzymeML
Validation Spreadsheet and convert it to to a YAML file. Finally, an
example ``EnzymeMLDocument`` will be loaded and validated against the
given YAML file. For the sake of demonstration, validation will fail to
display an example report.

.. code:: ipython3

    import pyenzyme as pe

Generation and conversion of a validation spreadsheet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``EnzymeMLValidator`` class has methods to generate and convert an
EnzymeML validation spreadsheet. It should be noted, that the generated
spreadsheet will always be up to the data models state and is not
maintained manually. The ``EnzymeMLDocument`` class definition is
recursively inferred to generate the file. This way, once the data model
is extended, the spreadsheet will be updated too.

.. code:: ipython3

    from pyenzyme.enzymeml.tools import EnzymeMLValidator

.. code:: ipython3

    # Generation of a validation spreadsheet
    EnzymeMLValidator.generateValidationSpreadsheet(".")
    
    # ... for those who like to go directly to YAML
    yaml_string = EnzymeMLValidator.generateValidationYAML(".")

Using an example spreadsheet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since the blank validation YAML wont demonstrate all types of checks, we
are going to use an example that has been provided in this directory and
convert it to YAML.

.. code:: ipython3

    # Convert an example spreadsheet to YAML
    yaml_string = EnzymeMLValidator.convertSheetToYAML(
        path="EnzymeML_Validation_Template_Example.xlsx",
        filename="EnzymeML_Validation_Template_Example"
    )

Performing validation
~~~~~~~~~~~~~~~~~~~~~

Once the YAML file is ready, validation can be done for an example
``EnzymeMLDocument`` found in this directory. The validation for this
example will fail by intention and thus return a report taht will be
shown here. Such a report is returned as ``Dict`` and can be inspected
either manually or programmatically. This was done to allow automation
workflows to utilize validation.

.. code:: ipython3

    # Load an example document
    enzmldoc = pe.EnzymeMLDocument.fromFile("Model_4.omex")
    
    # Perform validation against the preciously generated YAML
    report, is_valid = enzmldoc.validateDocument(yaml_path="EnzymeML_Validation_Template_Example.yaml")
    
    print(f">> Document is valid: {is_valid}")


.. parsed-literal::

    >> Document is valid: False


.. code:: ipython3

    # Lets inspect the report
    import json
    
    print(json.dumps(report, indent=4))


.. parsed-literal::

    {
        "name": {
            "enum_error": "Value of 'EnzymeML_Lagerman' does not comply with vocabulary ['Specific Title']"
        },
        "reactant_dict": {
            "s0": {
                "init_conc": {
                    "range_error": "Value of '20.0' is out of range for [400.0, 600.0]"
                }
            },
            "s1": {
                "init_conc": {
                    "range_error": "Value of '42.0' is out of range for [400.0, 600.0]"
                }
            },
            "s2": {
                "init_conc": {
                    "range_error": "Value of '0.0' is out of range for [400.0, 600.0]"
                }
            },
            "s3": {
                "init_conc": {
                    "range_error": "Value of '0.0' is out of range for [400.0, 600.0]"
                }
            }
        },
        "global_parameters": {
            "v_r": {
                "value": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "initial_value": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "upper": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "lower": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "stdev": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "ontology": {
                    "mandatory_error": "Mandatory attribute is not given."
                }
            },
            "K_si": {
                "value": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "initial_value": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "upper": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "lower": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "stdev": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "ontology": {
                    "mandatory_error": "Mandatory attribute is not given."
                }
            },
            "K_n": {
                "value": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "initial_value": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "upper": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "lower": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "stdev": {
                    "mandatory_error": "Mandatory attribute is not given."
                },
                "ontology": {
                    "mandatory_error": "Mandatory attribute is not given."
                }
            }
        }
    }


--------------
