.. math:: \require{mhchem}

Setting up an EnzymeML document
===============================

In order to write an EnzymeML document it needs to be initialized by
calling the ``EnzymeMLDocument`` object. At this point it is possible to
add metadata such as a name, URL, DOI or PubmedID to the document. In
addition, it is necessary but not mandatory to add author information.
Please note, that for a Dataverse upload adding an author is mandatory
though.

-  ``EnzymeMLDocument`` is the container object that stores all
   experiment information based on sub classes.
-  ``Creator`` carries the metadata about an author.
-  ``addCreator`` adds a ``Creator`` object to the ``EnzymeMLdocument``

.. code:: ipython3

    import pyenzyme as pe

.. code:: ipython3

    # Initialize the EnzymeML document
    enzmldoc = pe.EnzymeMLDocument(name="Experiment")
    
    # Add authors to the document
    author = pe.Creator(given_name="Max", family_name="Mustermann", mail="max@mustermann.de")
    author_id = enzmldoc.addCreator(author)

--------------

Documentation of a simple single substrate reaction
---------------------------------------------------

PyEnzyme is capable to document complete experiments from planning to
execution, modelling and ultimately database upload. For this, consider
a simple single substrate enzyme-catalyzed reaction, given in the
following:

.. math::


   \ce{Substrate + Enzyme \rightleftharpoons [ES] \rightleftharpoons [EP] \rightleftharpoons Product + Enzyme}

In order to properly document each step, it is necessary to start with
the definition of all entities. This is done by initializing the
appropriate objects and their metadata. Since pyEnzyme is capable to
report micro-kinetic models, it is possible to define intermediates that
may not be directly observable, such as Enzyme-Substrate complexes. This
facilitates mathematical modeling based on differential equations and
time-course data and offers a flexible way that is independent of
existing models.

**The next steps involve definition of the following entities:**

======== ==============
Type     Name
======== ==============
Vessel   Eppendorf Tube
Protein  Enzyme
Reactant Substrate
Reactant Product
Complex  ES
Complex  EP
======== ==============

Tips and hints:

-  Use the addXYZ-functions to append information to an EnzymeML
   document
-  Add-Methods return the identifier, which can later be used to build
   reactions and models. Thus it is best when these are stored in a
   variable or data structure
-  PyEnzyme takes care of type checking and validation. Furthermore,
   technicalities such as unit-decomposition (used to convert unit
   scales properly) and identifier assignment are done within the
   backend. Hence, focus on what matters.

**Vessels**

-  ``Vessel`` carries the metadata for vessels that are used.
-  ``addVessel`` adds a ``Vessel`` object to the document and returns
   the ID.

.. code:: ipython3

    vessel = pe.Vessel(name="Eppendorf Tube", volume=10.0, unit="ml")
    vessel_id = enzmldoc.addVessel(vessel)

**Proteins**

-  ``Protein`` carries the metadata for proteins that are part of the
   experiment.
-  ``addProtein`` adds a ``Protein`` object to the document and returns
   the ID.

.. code:: ipython3

    enzyme = pe.Protein(name="Enzyme", vessel_id=vessel_id,
                        sequence="MAVKLT", constant=False)
    
    enzyme_id = enzmldoc.addProtein(enzyme)

**Reactants**

-  ``Reactant`` carries the metadata for reactants that are part of the
   experiment.
-  ``addReactant`` adds a ``Reactant`` object to the document and
   returns the ID.

.. code:: ipython3

    substrate = pe.Reactant(name="Substrate", vessel_id=vessel_id)
    substrate_id = enzmldoc.addReactant(substrate)

.. code:: ipython3

    product = pe.Reactant(name="Product", vessel_id=vessel_id)
    product_id = enzmldoc.addReactant(product)

**Complexes**

-  ``Complex`` carries the metadata for complexes that are part of the
   experiment.
-  ``addComplex`` adds a ``Complex`` object to the document and returns
   the ID.

.. code:: ipython3

    es_complex_id = enzmldoc.addComplex(
        name="ES",
        vessel_id=vessel_id,
        participants=[enzyme_id, substrate_id]
    )

.. code:: ipython3

    ep_complex_id = enzmldoc.addComplex(
        name="EP",
        vessel_id=vessel_id, 
        participants=[enzyme_id, product_id]
    )

--------------

Building the reaction network
-----------------------------

In order for the micro-kinetic model to be accessible to various
modeling platforms and EnzymeML, each reaction in the model has to be
documented. Similar to the previous step, this involves the creation of
``EnzymeReaction`` objects which will be added to the EnzymeML document.
Hence, the following part-reactions need to be defined:

1. :math:`\ce{Substrate + Enzyme \rightleftharpoons [ES] }`

2. :math:`\ce{[ES] \rightleftharpoons [EP]}`

3. :math:`\ce{[EP] \rightleftharpoons Product + Enzyme}`

**Tips and hints:**

-  Add-methods require the ``EnzymeMLDocument`` object to be added. This
   is necessary to check, whether given identifiers already exist to
   mitigate later errors.
-  Similar to the other add-methods, ``addReaction``\ returns the given
   identifier. Thus it is best to store these in variables or data
   structures too.
-  At this point, kinetic laws can be added to the reaction, but in this
   example we’ll add them afterwards.

Creating reactions from equations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyEnzyme offers two ways of creating ``EnzymeReaction`` objects:

-  By using an equation that either includes the ID or name of a
   Reactant/Protein/Complex
-  By using ``add``-methods to build up all elements

Both methods will result in the same ``EnzymeReaction`` object, but both
might shine individually in different contexts. For instance, when
working on a single experiment using a Jupyter Notebook, initialization
by equation improves readability and reduces boilerplate code. On the
other hand, if your application is meant to maintain a variety of
reaction i.e. using PyEnzyme as a backend for an Electronic Lab
Notebook, using the ``add``-methods should prove to be more flexible and
safe than manipulating string.

.. code:: ipython3

    # Setting up by equation
    reaction_1 = pe.EnzymeReaction.fromEquation("Substrate + Enzyme = ES", "reaction-1", enzmldoc)
    reaction_2 = pe.EnzymeReaction.fromEquation("ES = EP", "reaction-2", enzmldoc)
    reaction_3 = pe.EnzymeReaction.fromEquation("EP = Product", "reaction-3", enzmldoc)

.. code:: ipython3

    # Setting up via add-methods (only for reaction 1 for demo)
    reaction_1 = pe.EnzymeReaction(name="reaction-1", reversible=True)
    
    # Add each element
    reaction_1.addEduct(species_id=substrate_id, stoichiometry=1.0, 
                        enzmldoc=enzmldoc)
    
    reaction_1.addEduct(species_id=enzyme_id, stoichiometry=1.0,
                        enzmldoc=enzmldoc)
    
    reaction_1.addProduct(species_id=product_id, stoichiometry=1.0,
                          enzmldoc=enzmldoc)

Adding the reaction to the document
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``addReaction`` adds an ``EnzymeReaction`` object to the document and
   returns the ID. (not used here)
-  ``addReactions`` adds multiples of ``EnzymeReaction`` objects to the
   document and returns an ID mapping. (used here)

.. code:: ipython3

    # Finally, add al reactions to the document
    reaction_ids = enzmldoc.addReactions([reaction_1, reaction_2, reaction_3])
    reaction_ids




.. parsed-literal::

    {'reaction-1': 'r0', 'reaction-2': 'r1', 'reaction-3': 'r2'}



--------------

Documenting measurement setups
------------------------------

Now that the theoretical foundation of the experiment has been layed
out, it is time to specify the setup of teh measurement. PyEnzyme offers
a lab-like system to document such setups. Typically, experiments
involve multiple runs with varying initial concentrations of every
element that occurs in the reaction network or/and varying conditions
such as temperature and pH. Hence, PyEnzyme builts on top of a
**measurement** system, where each of these represent a ‘run’.

In this example, the following setups will be tracked including changing
inital concentrations and temperatures:

+------------------+-----------+-----------------------+-----------+-------------+-----+
| Measurement Name | Species   | Initial concentration | Unit      | Temperature | pH  |
+==================+===========+=======================+===========+=============+=====+
| Run 1            | Substrate | 10.0                  | mmole / l | 37.0 °C     | 7.4 |
+------------------+-----------+-----------------------+-----------+-------------+-----+
| Run 1            | Enzyme    | 20.0                  | fmole / l | 37.0 °C     | 7.4 |
+------------------+-----------+-----------------------+-----------+-------------+-----+
| Run 1            | Product   | 0.0                   | mmole / l | 37.0 °C     | 7.4 |
+------------------+-----------+-----------------------+-----------+-------------+-----+
| Run 2            | Substrate | 100.0                 | mmole / l | 39.0 °C     | 7.4 |
+------------------+-----------+-----------------------+-----------+-------------+-----+
| Run 2            | Enzyme    | 40.0                  | fmole / l | 39.0 °C     | 7.4 |
+------------------+-----------+-----------------------+-----------+-------------+-----+
| Run 2            | Product   | 0.0                   | mmole / l | 39.0 °C     | 7.4 |
+------------------+-----------+-----------------------+-----------+-------------+-----+

**Measurement 1: ‘Run 1’**

-  ``Measurement`` carries the metadata for measurements that are
   conducted in the experiment.
-  ``addData`` appends measurement data to the ``Measurement`` object
   and checks consistency.

.. code:: ipython3

    measurement_1 = pe.Measurement(
        name="Run 1", temperature=37.0, temperature_unit="C",
        ph=7.4, global_time_unit="mins"
    )
    
    # Add each entity that will be measured
    measurement_1.addData(reactant_id=substrate_id,
                          init_conc=10.0, unit="mmole / l")
    
    measurement_1.addData(reactant_id=product_id,
                          unit="mmole / l")
    
    measurement_1.addData(protein_id=enzyme_id, init_conc=20.0,
                          unit="fmole / l")
    
    # Add it to the EnzymeML document
    meas_1_id = enzmldoc.addMeasurement(measurement_1)

**Measurement 2: ‘Run 2’**

-  ``Measurement`` carries the metadata for measurements that are
   conducted in the experiment.
-  ``addData`` appends measurement data to the ``Measurement`` object
   and checks consistency.

.. code:: ipython3

    measurement_2 = pe.Measurement(
        name="Run 2", temperature=39.0, temperature_unit="C",
        ph=7.4, global_time_unit="mins"
    )
    
    # Add each entity that will be measured
    measurement_2.addData(reactant_id=substrate_id,
                          init_conc=100.0, unit="mmole / l")
    
    measurement_2.addData(reactant_id=product_id,
                          unit="mmole / l")
    
    measurement_2.addData(protein_id=enzyme_id,
                          init_conc=40.0, unit="fmole / l")
    
    # Add it to the EnzymeML document
    meas_2_id = enzmldoc.addMeasurement(measurement_2)

.. code:: ipython3

    # Check the measurement table
    print(enzmldoc.printMeasurements())


.. parsed-literal::

    >>> Measurement m0: Run 1
        s0 | initial conc: 10.0 mmole / l 	| #replicates: 0
        s1 | initial conc: 0.0 mmole / l 	| #replicates: 0
        p0 | initial conc: 20.0 fmole / l 	| #replicates: 0
    >>> Measurement m1: Run 2
        s0 | initial conc: 100.0 mmole / l 	| #replicates: 0
        s1 | initial conc: 0.0 mmole / l 	| #replicates: 0
        p0 | initial conc: 40.0 fmole / l 	| #replicates: 0
    None


--------------

Adding experimental raw data
----------------------------

After the setup has been defined in terms of measurements, the actual
time-course data can be generated and added to the documemnt. PyEnzyme
offers a ``Replicate`` class as a container for raw data that aside from
raw data carries metadata describing the replicate itself.

In the following example, replication data will be hard-coded and added
to our measurement of choice. For this our digital lab measured the
product formation as well as substrate depletion for each measurement
setup.

**Data for ‘Run 1’**

-  ``Replicate`` carries the tim-courses and metadata for each measured
   entity.
-  ``addReplicates`` adds ``Replicate`` objects to a measurement to the
   corresponding ``MeasurementData`` container where the concentrations
   are also stored.

.. code:: ipython3

    repl_substrate_1 = pe.Replicate(
        id="repl_substrate_1",
        species_id=substrate_id,
        data_unit="mmole / l",
        time_unit="min",
        time=[1,2,3,4,5,6],
        data=[5,4,3,2,1,0]
    )
    
    repl_product_1 = pe.Replicate(
        id="repl_product_1",
        species_id=product_id,
        data_unit="mmole / l",
        time_unit="min",
        time=[1,2,3,4,5,6],
        data=[0,1,2,3,4,5]
    )

.. code:: ipython3

    # Add it to the first measurement 'Run 1'
    measurement = enzmldoc.getMeasurement(meas_1_id)
    measurement.addReplicates([repl_product_1, repl_substrate_1], enzmldoc=enzmldoc)

**Data for ‘Run 2’**

-  ``Replicate`` carries the tim-courses and metadata for each measured
   entity.
-  ``addReplicates`` adds ``Replicate`` objects to a measurement to the
   corresponding ``MeasurementData`` container where the concentrations
   are also stored.

.. code:: ipython3

    repl_substrate_2 = pe.Replicate(
        id="repl_substrate_2",
        species_id=substrate_id,
        data_unit="mmole / l",
        time_unit="min",
        time=[1,2,3,4,5,6],
        data=[50,40,30,20,10,0]
    )
    
    repl_product_2 = pe.Replicate(
        id="repl_product_2",
        species_id=product_id,
        data_unit="mmole / l",
        time_unit="min",
        time=[1,2,3,4,5,6],
        data=[0,10,20,30,40,50]
    )

.. code:: ipython3

    # Add it to the first measurement 'Run 2'
    measurement = enzmldoc.getMeasurement(meas_2_id)
    measurement.addReplicates([repl_product_2, repl_substrate_2], enzmldoc=enzmldoc)

--------------

Saving and distributing an EnzymeML document
--------------------------------------------

Finally, the experiment has been finished and meta- as well as raw-data
been documented. In order to make the data exchangable, PyEnzyme offers
several options for data export. First and foremost, the complete
experiment can be exported to EnzymeML which is SBML compatible and thus
accessible by SBML-based modeling tools (e.g. COPASI, PySCeS).
Furthermore, in regard of the web, PyEnzyme offers a JSON export too.

Apart from raw exports, PyEnzyme can also interface with the federated
databases system Dataverse by providing a simple upload method that
automatically uploads and processes the document contents to a Dataverse
compatible format. Please note, the Dataverse must support the
‘EnzymeML’ metadatablock for a successful upload.

**Export**

-  ``toFile`` writes the EnzymeML document to an OMEX archive at the
   specified path.
-  ``json`` converts the EnzymeML document to a JSON string, which in
   turn can be used for REST interfaces or data storage.
-  ``toXMLString`` returns the XML representation that is also found in
   the OMEX archive.

.. code:: ipython3

    # To an OMEX archive
    enzmldoc.toFile(".", name="My_Experiment")
    
    # To a JSON string
    with open("My_Experiment.json", "w") as file_handle:
        file_handle.write(enzmldoc.json(indent=2))
        
    # To an XML string
    xml_string = enzmldoc.toXMLString()


.. parsed-literal::

    
    Archive was written to ./My_Experiment.omex
    


**Upload**

-  ``uploadToDataverse`` uploads the document to a Dataverse
   installation.
-  Please note, that in order to work, your environment should contain
   these variables

   -  ``DATAVERSE_URL``: The URL to your installation.
   -  ``DATAVERSE_API_TOKEN``: The API Token to access the dataverse.

.. code:: ipython3

    # Uncomment if you want to use this on your own Dataverse
    # enzmldoc.uploadToDataverse(dataverse_name="playground")

--------------

Loading and editing
===================

It is not expected to create an EnzymeML document in a single session,
but to let it evolve over the course of an experiment. Thus it is
necessary to load and edit an EnzymeML document, without re-creating
everything from start. PyEnzyme’s ``EnzymeMLDocument`` object offers an
initialization method ``fromFile`` to edit an already existing document.
In addition, it is also possible to use the aforementioned JSON

**Tips and hints:**

-  PyEnzyme stores a history in the document, which keeps track of what
   has been changed and added in the course of an experiment. This is
   done, to spot potential errors and facilitate teh documentation of an
   experiment’s lifeline.

.. code:: ipython3

    # Load an EnzymeML document from OMEX
    enzmldoc = pe.EnzymeMLDocument.fromFile("./My_Experiment.omex")
    
    # Load an EnzymeML document from JSON 
    json_string = open("My_Experiment.json").read()
    enzmldoc = enzmldoc.fromJSON(json_string)
    
    enzmldoc.printDocument(measurements=True)


.. parsed-literal::

    Experiment
    >>> Reactants
    	ID: s0 	 Name: Substrate
    	ID: s1 	 Name: Product
    >>> Proteins
    	ID: p0 	 Name: Enzyme
    >>> Complexes
    	ID: c0 	 Name: ES
    	ID: c1 	 Name: EP
    >>> Reactions
    	ID: r0 	 Name: reaction-1
    	ID: r1 	 Name: reaction-2
    	ID: r2 	 Name: reaction-3
    >>> Measurements
    >>> Measurement m0: Run 1
        s0 | initial conc: 10.0 mmole / l 	| #replicates: 1
        s1 | initial conc: 0.0 mmole / l 	| #replicates: 1
        p0 | initial conc: 20.0 fmole / l 	| #replicates: 0
    >>> Measurement m1: Run 2
        s0 | initial conc: 100.0 mmole / l 	| #replicates: 1
        s1 | initial conc: 0.0 mmole / l 	| #replicates: 1
        p0 | initial conc: 40.0 fmole / l 	| #replicates: 0


Special case: From the EnzymeML spreadsheet template
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Apart from programmatic creation of an EnzymeML document, PyEnzyme
offers a way to convert the ‘EnzymeML spreadhseet template’ to an OMEX
file. Since spreadsheets are the bread and butter of current lab
documentation, the template widely covers teh data model and thus
provides an easy access to EnzymeML’s capabilities.

.. code:: ipython3

    # Similar to the OMEX and JSON loaders, its a simple call
    enzmldoc = pe.EnzymeMLDocument.fromTemplate("EnzymeML_Template_Example.xlsm")
    enzmldoc.printDocument()

Adding a kinetic model
^^^^^^^^^^^^^^^^^^^^^^

Building on top of the previous section about loading an EnzymeML
document, this example will demonstrate how to interact with an already
created EnzymeML document using the OMEX loader. Since the purpose of an
experiment is to generate data from a theory, modeling takes care of the
interpretation of an experiment outcome. However, PyEnzyme and EnzymeML
are no modeling platforms, but provides a convinient way to interface to
such. Hence, this example will demonstrate how such an interfacing could
look like.

The enzyme-catalyzed reaction that has been reported in the course of
this example obviously follows a simple Michaelis-Menten-Kinetic and
thus will be reported as such. But first of all, the next part will
demonstrate how measurement data can be exported to be used by a
modeling framework/platform.

First, load the EnzymeML document:

.. code:: ipython3

    # Load the EnzymeML document
    enzmldoc = pe.EnzymeMLDocument.fromFile("My_Experiment.omex")

In order to get the measurement data given in the document, the
``EnzymeMLDocument`` object offers the ``exportMeasurementData``-method
which will export the data of ‘all’ or specified measurements to a
Pandas DataFrame object.

.. code:: ipython3

    # Get the data from measurement "m0" ...
    meas_data = enzmldoc.exportMeasurementData(measurement_ids="m0")
    
    # Which is a dict containing "data" and "initConc" information, where data is the part we want
    meas_data = meas_data["data"]
    meas_data




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    
        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>s0</th>
          <th>s1</th>
          <th>time</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>5.0</td>
          <td>0.0</td>
          <td>1.0</td>
        </tr>
        <tr>
          <th>1</th>
          <td>4.0</td>
          <td>1.0</td>
          <td>2.0</td>
        </tr>
        <tr>
          <th>2</th>
          <td>3.0</td>
          <td>2.0</td>
          <td>3.0</td>
        </tr>
        <tr>
          <th>3</th>
          <td>2.0</td>
          <td>3.0</td>
          <td>4.0</td>
        </tr>
        <tr>
          <th>4</th>
          <td>1.0</td>
          <td>4.0</td>
          <td>5.0</td>
        </tr>
        <tr>
          <th>5</th>
          <td>0.0</td>
          <td>5.0</td>
          <td>6.0</td>
        </tr>
      </tbody>
    </table>
    </div>



The given output could now be used for an optimizer in conjunction with
the metadata that is given in the EnzymeML document. In order to gather
stoichiometries and such, one can access other data in the document by
specifically exporting the desired reactions:

.. code:: ipython3

    for reaction in enzmldoc.reaction_dict.values():
        # Every entity of an EnzymeML document is stored in its corresponding
        # dictionary. This example serves as a get-go solution to access all
        # other objects
        
        educts = reaction.educts
        products = reaction.products
        
        # From this point on, a modeling framework/platform could derive important metadata

Assuming the modeling has now been done, the estimated parameters for
the desired reactions can now be added to each reaction. Since this is
an example for demonstration, this will only be carried out for the
first reaction by using a Michaelis-Menten-Model.

.. code:: ipython3

    from pyenzyme.enzymeml.models import MichaelisMentenKCat
    
    # Get the appropriate IDs by using the getter-methods
    substrate = enzmldoc.getReactant("Substrate")
    enzyme = enzmldoc.getProtein("Enzyme")
    
    # Create the model
    model = MichaelisMentenKCat(
        substrate=substrate.id,
        protein=enzyme.id,
        k_cat={"value": 10.0, "unit": "1 / s"},
        k_m={"value": 20.0, "unit": "mmole / l"},
        enzmldoc=enzmldoc
    )
    
    # Add it to 'Reaction 1'
    reaction = enzmldoc.getReaction("reaction-1")
    reaction.model = model

Finally, write the EnzymeML document to an OMEX file or upload it to a
database, such as described in the corresponding section. Please note,
that this is a minimal example to demonstrate the capabilities of
PyEnzyme. However, if you like to inspect an actual interface
implementation to modeling platforms, please inspect the Thin Layer
implementations for **COPASI** and **PySCeS** in the
`GitHub <https://github.com/EnzymeML/PyEnzyme>`__ repository and
examples in the `“EnzymeML at
Work” <https://github.com/EnzymeML/Lauterbach_2022/tree/main/Scenario5>`__
repository.

--------------
