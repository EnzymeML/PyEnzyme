Modeling a reaction by mass action cascades using PySCeS
========================================================

This notebook is part of the publication “EnzymeML at Work” from
Lauterbach et al. 2022 and adds a given micro-kinetic model to an
EnzymeML document. Prior to this, experimental data was collected using
the EnzymeML spreadsheet and converted to EnzymeML. The following
notebook adresses the following key procedures using PyEnzyme:

-  Editing existing species
-  Adding new species from scratch or by DB-fetch
-  Adding reactions via an equation
-  Setting up a model generator, and assigning rate laws to a kinetic
   model
-  Fitting parameters in this kinetic model to experimental data with
   PySCeS

We demonstrate how to open an EnzymeML document, extend this document
with a micro-kinetic model using PyEnzyme, and then use
`PySCeS <https://pyscesdocs.readthedocs.io>`__ to estimate the
parameters of this micro-kinetic model based on the measurement data
included in the EnzymeML document.

For this to work, you will have to have PySCeS and PyEnzyme installed,
which can be done using:

::

       !pip install pysces
       !pip install git+git://github.com/EnzymeML/PyEnzyme.git

This is **not needed** when running this notebook via **Binder**, as the
environment is already set up.

For the parameter estimation with PySCeS, the CVODE algorithm is needed;
this is provided by **Assimulo**. If you are using the **Anaconda**
Python Distribution (and when running this notebook via **Binder**),
this can easily be achieved by uncommenting and running the following
line of code. Alternatively, refer to the Assimulo documentation:
https://jmodelica.org/assimulo/

.. code:: ipython3

    # !conda install -y -c conda-forge assimulo

We are now ready to import the required modules.

.. code:: ipython3

    from pyenzyme import EnzymeMLDocument, EnzymeReaction, Complex, Reactant, Protein, Creator
    from pyenzyme.enzymeml.models import KineticModel, KineticParameter

Editing an EnzymeML document
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since the previously created EnzymeML document only includes the
macro-kinetic reaction, the micro-kinetic model found in Lagerman et
al. will be introduced to the EnzymeML document.

For this, intermediate species have to be added to the document, which,
aside from small-molecules also include protein-substrate complexes.
Macromolecular structures can be described in EnzymeML by using the
``Complex`` class, which basically acts as a reference container to
participating species that is compatible to SBML.

In addition, the following cell also demonstrates how an exitsing
EnzymeML document can be edited, where we are simplifying names for
model creation. Furthermore, the methanol species will be added using
the ``fromChebiID``-Initializer that fetches and fills in data from the
CHEBI-Database. Ultimately, using the initializer allows for data
consistency and should always be chosen over manual initialization. The
same is available for the ``Protein`` class, namely ``fromUniProtID``.

.. code:: ipython3

    # Load the dataset that was generated using the EnzymeML spreadsheet
    enzmldoc = EnzymeMLDocument.fromFile("EnzymeML_Lagerman.omex")
    
    # Rename entities for simplicity
    enzmldoc.getReactant("s0").name = "PGME"
    enzmldoc.getReactant("s1").name = "7-ADCA"
    enzmldoc.getReactant("s2").name = "CEX"
    enzmldoc.getReactant("s3").name = "PG"
    enzmldoc.getProtein("p0").name = "E"
    
    # Set missing initial concentration
    enzmldoc.getReactant("CEX").init_conc = 0.0
    enzmldoc.getReactant("CEX").unit = "mmole / l"
    
    enzmldoc.getReactant("PG").init_conc = 0.0
    enzmldoc.getReactant("PG").unit = "mmole / l"
    
    # Change initial concentration of E to mmole / l
    e = enzmldoc.getProtein("E")
    e.init_conc = 0.0002
    e.unit = "mmole / l"
    
    # Add EA enzyme instance
    ea = enzmldoc.getProtein("E").copy(deep=True)
    ea.name = "EA"
    ea.init_conc = 0.0
    enzmldoc.addProtein(ea)
    
    # Add deactivated enzyme instance
    ed = enzmldoc.getProtein("E").copy(deep=True)
    ed.name = "ED"
    ed.init_conc = 0.0
    enzmldoc.addProtein(ed)
    
    # Set proteins to not constant for machnistic modeling
    enzmldoc.getProtein("E").constant = False
    enzmldoc.getProtein("EA").constant = False
    enzmldoc.getProtein("ED").constant = False
    
    # Add model intermediates
    enzmldoc.addComplex("E·PGME", ["E", "PGME"], "v0", 0.0, "mmole/l")
    enzmldoc.addComplex("E·7-ADCA", ["E", "7-ADCA"], "v0", 0.0, "mmole/l")
    enzmldoc.addComplex("E·PG", ["E", "PG"], "v0", 0.0, "mmole/l")
    enzmldoc.addComplex("E·PGME·PGME", ["E", "PGME", "PGME"], "v0", 0.0, "mmole/l")
    enzmldoc.addComplex("EA·7-ADCA", ["EA", "7-ADCA"], "v0", 0.0, "mmole/l")
    enzmldoc.addComplex("EA·PGME", ["EA", "PGME"], "v0", 0.0, "mmole/l")
    enzmldoc.addComplex("E·CEX", ["E", "CEX"], "v0", 0.0, "mmole/l")
    
    # Remove the old reaction since we are going to expand it
    # to a micro-kinetic model for modeling
    del enzmldoc.reaction_dict["r0"]



Adding the micro-kinetic model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that alls necessary species are defined, these will be set in
relation by adding the reaction network defined in Lagerman et al. For
this, the ``EnzymeReaction`` class can either be constructed using
deignated ``addEduct`` methods (see examples on PyEnzyme Git) or the
``fromEquation`` initializer inspired by ``BasiCo``. The latter will
infer the corresponding ID as well as ``reversibility`` attribute from
the equation string and parses educts and products to the object.
Furthermore, both kinds of cunstructors require the ``EnzymeMLDocument``
for consistency checks.

In this case, we prefer the ``fromEquation``-method since there are a
lot of reactions which essentially are only made up of educts and
products but no modifiers. At this point, please note the downside of
``fromEquation`` not being able to include modifiers, but since the
enzymes/complexes are either consumed or produced, this justifies our
usage.

.. code:: ipython3

    # Now define the micro-kinetic model by adding each sub-reaction to the document
    r1 = EnzymeReaction.fromEquation("E·7-ADCA = E + 7-ADCA", "reaction-1", enzmldoc)
    r2 = EnzymeReaction.fromEquation("E·PGME = E + PGME", "reaction-2", enzmldoc)
    r3 = EnzymeReaction.fromEquation("E·PGME -> EA", "reaction-3", enzmldoc)
    r4 = EnzymeReaction.fromEquation("E·PGME·PGME = E·PGME + PGME", "reaction-4", enzmldoc)
    r5 = EnzymeReaction.fromEquation("EA·PGME = EA + PGME", "reaction-5", enzmldoc)
    r6 = EnzymeReaction.fromEquation("EA·PGME -> E + PG", "reaction-6", enzmldoc)
    r7 = EnzymeReaction.fromEquation("EA -> E + PG", "reaction-7", enzmldoc)
    r8 = EnzymeReaction.fromEquation("E·PG = E + PG", "reaction-8", enzmldoc)
    r9 = EnzymeReaction.fromEquation("EA·7-ADCA = EA + 7-ADCA", "reaction-9", enzmldoc)
    r10 = EnzymeReaction.fromEquation("EA·7-ADCA -> E + PG + 7-ADCA", "reaction-10", enzmldoc)
    r11 = EnzymeReaction.fromEquation("EA·7-ADCA = E·CEX", "reaction-11", enzmldoc)
    r12 = EnzymeReaction.fromEquation("E·CEX = E + CEX", "reaction-12", enzmldoc)
    r13 = EnzymeReaction.fromEquation("E -> ED", "Enzyme deactivation", enzmldoc)



Setting up rate laws
~~~~~~~~~~~~~~~~~~~~

Given the now added reaction network, it is necessary to add appropriate
rate laws to each reaction to facilitate parameter estimation using
SBML-based modeling platforms. Since most of the reactions follow normal
Mass Action laws, we can set up so called ``ModelFactories`` that
represent an abstract model.

Previous PyEnzyme versions would require to implement an explicit model
for each reaction in the form of

``s0 * vmax / (Km + s0)``

which requires an equation string for each model. This can become quite
tedious and for models, where most reactions share the same rate law
quite error prone if done manually. Hence, the
``createGenerator``-initializer of the ``KineticModel`` offers a
convinient way to generalize models and ensure consistency as well as
re-usability.

Excursion: Setting up a model generator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to set up a model generator it requires a ``name``, an
``equation`` and an explicit description of the used parameters occuring
in the equation. For instance, lets set up an ``Example-Model`` with
equation ``param * substrate`` and parameter ``param`` for simplicity.

The algorithm will detect parameters based on the keyword arguments
passed to the generator. In addtion, these keyword arguments should
include a dicitonary that can optionally be equipped with all prossible
attributes the ``KineticParameter`` class can hold.

.. code:: ipython3

    # Setting up the generator
    example_gen = KineticModel.createGenerator(name="Example-Model", equation="param * substrate", param={"unit": "1 / s"})

The generator can now be applied to any type of reaction by calling the
object using the variables as keyword arguments and the corresponding
actual species as values. For instance, in our example, ``substrate`` is
the variable and thus has to be provided as a keyword argument. If for
instance the reaction we want the model has a substrate called
``Pyruvate`` we can explicitly include this in our call.

.. code:: ipython3

    # Using the generator with a single species
    single_example = example_gen(substrate="Pyruvate")
    print("One substrate --", single_example, end="\n\n")
    
    # Generators can also take lists and convert them to the model
    multi_example = example_gen(substrate=["Pyruvate", "H2O"])
    print("Multiple substrate --", multi_example, end="\n\n")


.. parsed-literal::

    One substrate -- name='Example-Model' equation="param * 'Pyruvate'" parameters=[KineticParameter(name='param', value=None, unit='1 / s', initial_value=None, upper=None, lower=None, is_global=False, stdev=None, constant=False, ontology=None)] ontology=None
    
    Multiple substrate -- name='Example-Model' equation="param * ('Pyruvate' * 'H2O')" parameters=[KineticParameter(name='param', value=None, unit='1 / s', initial_value=None, upper=None, lower=None, is_global=False, stdev=None, constant=False, ontology=None)] ontology=None
    


Such a generated model can now be added to a reaction by assigning it to
the ``model`` attribute.

Adding rate laws
~~~~~~~~~~~~~~~~

As previously discussed, all rate laws will be set up as generator
objects that are assigned to each reaction using the corrsponding
educts/products. In addition, parameters that occur in more than one
reaction, are defined as gobal parameters.

Finally, after that has been done, all reactions will be added to the
``EnzymeMLDocument`` object and an overview generated to control the
assignment using the ``printReactionSchemes`` method of the EnzymeML
document.

.. code:: ipython3

    # Set up generators for kinetic models
    eq_rev = KineticModel.createGenerator(
        name="MassAction Reversible", equation="K_1 * substrate - K_2 * product",
        K_1={"unit": "1 / min"}, K_2={"unit": "1 / min"}
    )
    
    eq_irrev = KineticModel.createGenerator(
        name="MassAction Irreversible", equation="K_1 * substrate",
        K_1={"unit": "1 / min"}
    )
    
    mass_eq = KineticModel.createGenerator(
        name="MassAction Keq", equation=f"v_r*(K_eq * substrate - product)",
        K_eq={"unit": "mmole / l"}, v_r={"unit": "l / mmole min", "constant": True}
    )

.. code:: ipython3

    # Set up global parameters
    v_r = enzmldoc.addGlobalParameter("v_r", unit="l / mmole min", constant=True)
    K_si = enzmldoc.addGlobalParameter("K_si", unit="mmole / l")
    K_n = enzmldoc.addGlobalParameter("K_n", unit="mmole / l")

.. code:: ipython3

    r1.model = mass_eq(product=["E", "7-ADCA"], substrate="E·7-ADCA", mapping={"K_eq": "K_n"})
    r2.model = mass_eq(product=["E", "PGME"], substrate="E·PGME", mapping={"K_eq": "K_s"})
    r3.model = eq_irrev(substrate="E·PGME", mapping={"K_1": "k_2"})
    r4.model = mass_eq(product=["E·PGME", "PGME"], substrate="E·PGME·PGME", mapping={"K_eq": "K_si"})
    r5.model = mass_eq(product=["EA", "PGME"], substrate="EA·PGME", mapping={"K_eq": "K_si"})
    r6.model = eq_irrev(substrate="EA·PGME", mapping={"K_1": "k_6"})
    r7.model = eq_irrev(substrate="EA", mapping={"K_1": "k_3"})
    r8.model = mass_eq(product=["E", "PG"], substrate="E·PG", mapping={"K_eq": "K_pg"})
    r9.model = mass_eq(product=["EA", "7-ADCA"], substrate="EA·7-ADCA", mapping={"K_eq": "K_n"})
    r10.model = eq_irrev(substrate="EA·7-ADCA", mapping={"K_1": "k_5"})
    r11.model = eq_rev(substrate="EA·7-ADCA", product="E·CEX", mapping={"K_1": "k_4", "K_2": "k_4b"})
    r12.model = mass_eq(substrate="E·CEX", product=["E", "CEX"], mapping={"K_eq": "K_p"})
    r13.model = eq_irrev(substrate="E", mapping={"K_1": "k_d"} )

.. code:: ipython3

    # Finally, add all reactions to the EnzymeML document
    reaction_ids = enzmldoc.addReactions(
        [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13]
    )

.. code:: ipython3

    enzmldoc.printReactionSchemes(by_name=True)




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
          <th>Name</th>
          <th>equation</th>
          <th>kinetic law</th>
        </tr>
        <tr>
          <th>ID</th>
          <th></th>
          <th></th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>r0</th>
          <td>reaction-1</td>
          <td>1.0 E·7-ADCA &lt;=&gt; 1.0 E + 1.0 7-ADCA</td>
          <td>v_r*(K_n * E·7-ADCA - (E * 7-ADCA))</td>
        </tr>
        <tr>
          <th>r1</th>
          <td>reaction-2</td>
          <td>1.0 E·PGME &lt;=&gt; 1.0 E + 1.0 PGME</td>
          <td>v_r*(K_s * E·PGME - (E * PGME))</td>
        </tr>
        <tr>
          <th>r2</th>
          <td>reaction-3</td>
          <td>1.0 E·PGME -&gt; 1.0 EA</td>
          <td>k_2 * E·PGME</td>
        </tr>
        <tr>
          <th>r3</th>
          <td>reaction-4</td>
          <td>1.0 E·PGME·PGME &lt;=&gt; 1.0 E·PGME + 1.0 PGME</td>
          <td>v_r*(K_si * E·PGME·PGME - (E·PGME * PGME))</td>
        </tr>
        <tr>
          <th>r4</th>
          <td>reaction-5</td>
          <td>1.0 EA·PGME &lt;=&gt; 1.0 EA + 1.0 PGME</td>
          <td>v_r*(K_si * EA·PGME - (EA * PGME))</td>
        </tr>
        <tr>
          <th>r5</th>
          <td>reaction-6</td>
          <td>1.0 EA·PGME -&gt; 1.0 E + 1.0 PG</td>
          <td>k_6 * EA·PGME</td>
        </tr>
        <tr>
          <th>r6</th>
          <td>reaction-7</td>
          <td>1.0 EA -&gt; 1.0 E + 1.0 PG</td>
          <td>k_3 * EA</td>
        </tr>
        <tr>
          <th>r7</th>
          <td>reaction-8</td>
          <td>1.0 E·PG &lt;=&gt; 1.0 E + 1.0 PG</td>
          <td>v_r*(K_pg * E·PG - (E * PG))</td>
        </tr>
        <tr>
          <th>r8</th>
          <td>reaction-9</td>
          <td>1.0 EA·7-ADCA &lt;=&gt; 1.0 EA + 1.0 7-ADCA</td>
          <td>v_r*(K_n * EA·7-ADCA - (EA * 7-ADCA))</td>
        </tr>
        <tr>
          <th>r9</th>
          <td>reaction-10</td>
          <td>1.0 EA·7-ADCA -&gt; 1.0 E + 1.0 PG + 1.0 7-ADCA</td>
          <td>k_5 * EA·7-ADCA</td>
        </tr>
        <tr>
          <th>r10</th>
          <td>reaction-11</td>
          <td>1.0 EA·7-ADCA &lt;=&gt; 1.0 E·CEX</td>
          <td>k_4 * EA·7-ADCA - k_4b * E·CEX</td>
        </tr>
        <tr>
          <th>r11</th>
          <td>reaction-12</td>
          <td>1.0 E·CEX &lt;=&gt; 1.0 E + 1.0 CEX</td>
          <td>v_r*(K_p * E·CEX - (E * CEX))</td>
        </tr>
        <tr>
          <th>r12</th>
          <td>Enzyme deactivation</td>
          <td>1.0 E -&gt; 1.0 ED</td>
          <td>k_d * E</td>
        </tr>
      </tbody>
    </table>
    </div>



.. code:: ipython3

    # Finally, write the document to an OMEX archive
    enzmldoc.toFile(".", name="Model_4")


.. parsed-literal::

    
    Archive was written to ./Model_4.omex
    


--------------

Kinetic Modeling
----------------

Now that the EnzymeMLDocument has been adapted to the micro-kinetic
model, it can be modeled and optimized using PySCeS and COPASI. Since
both modeling package interfaces are an integral part of PyEnzyme,
called Thin Layer, a simple call to the corresponding Thin Layer object
is necessary.

But before optimization, it might be necessary to define initial values.
Since manipulating the KineticParameter initial_values attributes inside
the script that generates the EnzymeMLDocument can get quite tedious,
PyEnzyme offers an external data structure from within initial values
can be applied. This way, the EnzymeML document is only modifed at
optimization and remains untouched until then.

The initialization file is in the YAML format and contains all reactions
and their parameters. In addtion, PyEnzyme offers a method to generate
such a YAML file, which can be edited manually with the initial
parameter values for the optimization.

.. code:: ipython3

    # In addition, generate a blank YAML file to manually enter initial values for modeling
    enzmldoc.generateInitialValueTemplate()

Using the PySCeS thin layer
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The PySCeS thin layer can be used in conjunction with the initialization
YAML file. The thin layer will extract all necessary data, feed it into
the simulation framework and iteratively optimizes the given parameters
until convergence. At the end, the estimated parameters will be written
to a new EnzymeMLDocument and saved.

.. code:: ipython3

    from pyenzyme.thinlayers import ThinLayerPysces

First, the SBML model is converted to a PySCeS input file, this happens
automatically. The warning about SBML Level 3 can be safely ignored as
PySCeS has all the functionality required for this simulation.

.. code:: ipython3

    # Initialize the layer
    tl_pysces = ThinLayerPysces(
        "Model_4.omex", init_file="EnzymeML_Lagerman_init_values_.yaml",
        model_dir="pySCeS"
    )


.. parsed-literal::

    Check SBML support is at action level 2
    SBML file is L3V2
    
    
    
    *********ERRORS***********
    
    WARNING: Model is encoded as SBML Level 3, PySCeS only officially supports L2V5.
    
    *********ERRORS***********
    
    
    Possible errors detected in SBML conversion, Model may be incomplete. Please check the error log file "EnzymeML_Lagerman.xml-sbml_conversion_errors.txt" for details.
    
    
    *******************************************************************
    Issues encountered in SBML translation (model processed anyway)
    SBML source: pySCeS/EnzymeML_Lagerman.xml
    *******************************************************************
    
    Parameter units ignored for parameters:
    ['v_r', 'K_si', 'K_n'] 
    
    Parameter units ignored for (local) parameters:
    ['K_s', 'k_2', 'k_6', 'k_3', 'K_pg', 'k_5', 'k_4', 'k_4b', 'K_p', 'k_d'] 
    
    *******************************************************************
    
    Info: single compartment model: locating "r0" in default compartment
    Info: single compartment model: locating "r1" in default compartment
    Info: single compartment model: locating "r2" in default compartment
    Info: single compartment model: locating "r3" in default compartment
    Info: single compartment model: locating "r4" in default compartment
    Info: single compartment model: locating "r5" in default compartment
    Info: single compartment model: locating "r6" in default compartment
    Info: single compartment model: locating "r7" in default compartment
    Info: single compartment model: locating "r8" in default compartment
    Info: single compartment model: locating "r9" in default compartment
    Info: single compartment model: locating "r10" in default compartment
    Info: single compartment model: locating "r11" in default compartment
    Info: single compartment model: locating "r12" in default compartment
    Writing file: pySCeS/EnzymeML_Lagerman.xml.psc
    
    SBML2PSC
    in : pySCeS/EnzymeML_Lagerman.xml
    out: pySCeS/EnzymeML_Lagerman.xml.psc
    Assuming extension is .psc
    Using model directory: pySCeS
    pySCeS/EnzymeML_Lagerman.xml.psc loading ..... 
    Parsing file: pySCeS/EnzymeML_Lagerman.xml.psc
    Info: No reagents have been fixed
     
    Calculating L matrix . . . . . . .  done.
    Calculating K matrix . . . . . . . . .  done.
     


Now, the optimization is run. Two different numerical integration
algorithms are available in PySCeS, i.e. ``LSODA`` and ``CVODE``. Here
we choose ``CVODE``. The optimization algorithm can also be specified,
any of the algorithms available in LMFIT
(https://lmfit.github.io/lmfit-py/fitting.html#choosing-different-fitting-methods)
can be chosen.

.. code:: ipython3

    # Run optimization
    tl_pysces.model.mode_integrator='CVODE'
    tl_opt = tl_pysces.optimize(method="least_squares")

.. code:: ipython3

    tl_opt




.. raw:: html

    <h2>Fit Statistics</h2><table><tr><td>fitting method</td><td>least_squares</td><td></td></tr><tr><td># function evals</td><td>18</td><td></td></tr><tr><td># data points</td><td>320</td><td></td></tr><tr><td># variables</td><td>12</td><td></td></tr><tr><td>chi-square</td><td> 2951.22432</td><td></td></tr><tr><td>reduced chi-square</td><td> 9.58189715</td><td></td></tr><tr><td>Akaike info crit.</td><td> 734.929405</td><td></td></tr><tr><td>Bayesian info crit.</td><td> 780.149257</td><td></td></tr></table><h2>Variables</h2><table><tr><th> name </th><th> value </th><th> standard error </th><th> relative error </th><th> initial value </th><th> min </th><th> max </th><th> vary </th></tr><tr><td> v_r </td><td>  1.0000e+09 </td><td>  0.00000000 </td><td> (0.00%) </td><td> 1000000000.0 </td><td>        -inf </td><td>         inf </td><td> False </td></tr><tr><td> K_si </td><td>  5.39337342 </td><td>  0.93246815 </td><td> (17.29%) </td><td> 6.346729249 </td><td>  0.01000000 </td><td>  1000.00000 </td><td> True </td></tr><tr><td> K_n </td><td>  6.50049502 </td><td>  1.55960885 </td><td> (23.99%) </td><td> 11.00542741 </td><td>  0.01000000 </td><td>  10000.0000 </td><td> True </td></tr><tr><td> r1_K_s </td><td>  5.12950319 </td><td>  1.03650938 </td><td> (20.21%) </td><td> 5.676255758 </td><td>  0.01000000 </td><td>  1000.00000 </td><td> True </td></tr><tr><td> r2_k_2 </td><td>  569452.681 </td><td>  92198.7563 </td><td> (16.19%) </td><td> 652085.5139 </td><td>  1.00000000 </td><td>  1000000.00 </td><td> True </td></tr><tr><td> r5_k_6 </td><td>  249555.287 </td><td>  77303.5694 </td><td> (30.98%) </td><td> 393169.3931 </td><td>  1.00000000 </td><td>  10000000.0 </td><td> True </td></tr><tr><td> r6_k_3 </td><td>  15.8995797 </td><td>  6.25028953 </td><td> (39.31%) </td><td> 8.93817854 </td><td>  1.00000000 </td><td>  1000000.00 </td><td> True </td></tr><tr><td> r7_K_pg </td><td>  129.952300 </td><td>  29.9876732 </td><td> (23.08%) </td><td> 47.34446037 </td><td>  0.01000000 </td><td>  1000.00000 </td><td> True </td></tr><tr><td> r9_k_5 </td><td>  884605.533 </td><td>  204522.629 </td><td> (23.12%) </td><td> 672295.823 </td><td>  1.00000000 </td><td>  1000000.00 </td><td> True </td></tr><tr><td> r10_k_4 </td><td>  1577461.07 </td><td>  345178.098 </td><td> (21.88%) </td><td> 1870570.524 </td><td>  1.00000000 </td><td>  1.0000e+08 </td><td> True </td></tr><tr><td> r10_k_4b </td><td>  36802.5461 </td><td>  5963.80588 </td><td> (16.20%) </td><td> 42451.1374 </td><td>  1.00000000 </td><td>  1.0000e+08 </td><td> True </td></tr><tr><td> r11_K_p </td><td>  1.29574677 </td><td>  0.34043006 </td><td> (26.27%) </td><td> 0.9433184993 </td><td>  0.01000000 </td><td>  1000.00000 </td><td> True </td></tr><tr><td> r12_k_d </td><td>  0.32920628 </td><td>  0.23138589 </td><td> (70.29%) </td><td> 0.5149464784 </td><td>  1.0000e-03 </td><td>  1.00000000 </td><td> True </td></tr></table><h2>Correlations (unreported correlations are < 0.100)</h2><table><tr><td>K_si</td><td>r2_k_2</td><td>-0.9611</td></tr><tr><td>r9_k_5</td><td>r10_k_4</td><td>0.8630</td></tr><tr><td>r1_K_s</td><td>r2_k_2</td><td>0.6379</td></tr><tr><td>r1_K_s</td><td>r5_k_6</td><td>-0.6288</td></tr><tr><td>K_si</td><td>r1_K_s</td><td>-0.5700</td></tr><tr><td>K_n</td><td>r5_k_6</td><td>-0.5434</td></tr><tr><td>r10_k_4</td><td>r11_K_p</td><td>-0.5423</td></tr><tr><td>K_n</td><td>r10_k_4b</td><td>-0.4756</td></tr><tr><td>r5_k_6</td><td>r10_k_4</td><td>0.4694</td></tr><tr><td>r9_k_5</td><td>r10_k_4b</td><td>-0.4659</td></tr><tr><td>r6_k_3</td><td>r10_k_4</td><td>-0.4555</td></tr><tr><td>r6_k_3</td><td>r9_k_5</td><td>-0.4515</td></tr><tr><td>K_n</td><td>r1_K_s</td><td>0.4407</td></tr><tr><td>r5_k_6</td><td>r11_K_p</td><td>-0.4210</td></tr><tr><td>r7_K_pg</td><td>r9_k_5</td><td>-0.4191</td></tr><tr><td>K_n</td><td>r12_k_d</td><td>-0.3832</td></tr><tr><td>r1_K_s</td><td>r12_k_d</td><td>-0.3732</td></tr><tr><td>r1_K_s</td><td>r6_k_3</td><td>-0.3514</td></tr><tr><td>r7_K_pg</td><td>r10_k_4</td><td>-0.3464</td></tr><tr><td>K_si</td><td>r11_K_p</td><td>0.3307</td></tr><tr><td>r1_K_s</td><td>r10_k_4b</td><td>-0.3208</td></tr><tr><td>r2_k_2</td><td>r5_k_6</td><td>-0.3110</td></tr><tr><td>r7_K_pg</td><td>r10_k_4b</td><td>0.3106</td></tr><tr><td>r2_k_2</td><td>r11_K_p</td><td>-0.2926</td></tr><tr><td>r5_k_6</td><td>r12_k_d</td><td>0.2885</td></tr><tr><td>r5_k_6</td><td>r9_k_5</td><td>0.2838</td></tr><tr><td>r9_k_5</td><td>r11_K_p</td><td>-0.2721</td></tr><tr><td>r5_k_6</td><td>r10_k_4b</td><td>0.2640</td></tr><tr><td>K_si</td><td>r10_k_4</td><td>-0.2627</td></tr><tr><td>r10_k_4</td><td>r10_k_4b</td><td>-0.2584</td></tr><tr><td>r5_k_6</td><td>r7_K_pg</td><td>-0.2483</td></tr><tr><td>r10_k_4b</td><td>r12_k_d</td><td>0.2313</td></tr><tr><td>K_si</td><td>r6_k_3</td><td>0.2301</td></tr><tr><td>r7_K_pg</td><td>r11_K_p</td><td>0.2282</td></tr><tr><td>K_si</td><td>r5_k_6</td><td>0.2018</td></tr><tr><td>K_n</td><td>r7_K_pg</td><td>0.1983</td></tr><tr><td>r2_k_2</td><td>r6_k_3</td><td>-0.1950</td></tr><tr><td>K_n</td><td>r11_K_p</td><td>0.1950</td></tr><tr><td>r11_K_p</td><td>r12_k_d</td><td>-0.1878</td></tr><tr><td>r10_k_4b</td><td>r11_K_p</td><td>0.1768</td></tr><tr><td>K_n</td><td>r6_k_3</td><td>-0.1702</td></tr><tr><td>K_si</td><td>r12_k_d</td><td>0.1581</td></tr><tr><td>r7_K_pg</td><td>r12_k_d</td><td>-0.1562</td></tr><tr><td>r6_k_3</td><td>r12_k_d</td><td>-0.1559</td></tr><tr><td>K_si</td><td>r10_k_4b</td><td>0.1410</td></tr><tr><td>r2_k_2</td><td>r10_k_4</td><td>0.1405</td></tr><tr><td>K_si</td><td>r9_k_5</td><td>-0.1372</td></tr><tr><td>r1_K_s</td><td>r7_K_pg</td><td>0.1354</td></tr><tr><td>r1_K_s</td><td>r11_K_p</td><td>0.1068</td></tr></table>



Finally, the result is written to a new EnzymeML Document and saved to
file.

.. code:: ipython3

    # Write to new EnzymeMLDocument and save
    nu_doc = tl_pysces.write()
    nu_doc.toFile(".", name="EnzymeML_Lagerman_M4_PySCeS_Modeled")


.. parsed-literal::

    
    Archive was written to ./EnzymeML_Lagerman_M4_PySCeS_Modeled.omex
    

