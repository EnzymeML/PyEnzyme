<h1 align="center">
  PyEnzyme
  <img src="https://github.com/EnzymeML/PyENzyme/actions/workflows/build.yml/badge.svg" alt="Build Badge">
</h1>
<p align="center"> 
PyEnzyme is the interface to the data model <b>EnzymeML</b> and offers a convenient way to document and model research data. Lightweight syntax for rapid development of data management solution in enzymology and biocatalysis.</p>

### 🧬 Features

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/2067f8313cbe460f8adcd2de3fb0fc14)](https://app.codacy.com/gh/EnzymeML/PyEnzyme?utm_source=github.com&utm_medium=referral&utm_content=EnzymeML/PyEnzyme&utm_campaign=Badge_Grade_Settings)


- Reproducible **documentation** of enzymatic and biocatalytic experiments.
- **Import** from and **export** to the SBML-based markup language **EnzymeML** and more.
- Perform **database-specific validation** prior to database upload.
- Model your data using a **Thin Layer**  to popular modeling platforms.
- **Visualize** experimental results for inspection and publication.

## ⚡️ Quick start
Get started with PyEnzyme by running the following command 

```
# Using PyPI
python -m pip install pyenzyme
```

Or build by source
```
git clone https://github.com/EnzymeML/PyEnzyme.git
cd PyEnzyme
python3 setup.py install
```

### ⚙️ Package Options
PyEnzyme comes with many flavors, choose whether you want only the base installation, the modeling package or all of it using the following options.
```
# COPASI - modeling
python -m pip install "pyenzyme[copasi]"

# PySCeS - modeling
python -m pip install "pyenzyme[pysces]"

# Modeling package
python -m pip install "pyenzyme[modeling]"

# REST API
python -m pip install "pyenzyme[rest]"

# Complete
python -m pip install "pyenzyme[all]"
```

### 🚀 PyEnzyme's REST-API

If you want to deploy PyEnzyme as a server and use our REST-API to access PyEnzyme from any HTTP-capable programming language, use our official [docker image](https://hub.docker.com/r/enzymeml/pyenzyme/tags) or simply copy and past the following.

```bash
docker pull enzymeml/pyenzyme:latest
docker run -p 8000:8000 enzymeml/pyenzyme:latest
```
See the [API documentation](https://enzymeml.sloppy.zone) for details on our endpoints. You can also use our self-hosted PyEnzyme instance if you have no server space - Use https://enzymeml.sloppy.zone as base URL to the endpoints.

## ⚙️ Example code

This example will demonstrate how to create a simple EnzymeML document using PyEnzyme and how to use initializers from official databases **Chebi** and **UniProt** to gather metadata. For more examples, please visit our [documentation](https://pyenzyme.readthedocs.io/en/refactoring/) (Work in progress)

```python
import pyenzyme as pe

# Initialize your document
enzmldoc = pe.EnzymeMLDocument(name="MyDoc")

# Create a vessel and add it to the document
vessel = pe.Vessel(name="Falcon Tube", volume=10.0, unit="ml")
vessel_id = enzmldoc.addVessel(vessel)

# Set up reactants and proteins from databases
protein = pe.Protein.fromUniProtID(
    uniprotid="P07327", vessel_id=vessel_id,
    init_conc=10.0, unit="fmole / l"
)

substrate = pe.Reactant.fromChebiID(
    chebi_id="CHEBI:16236", vessel_id=vessel_id,
    init_conc=200.0, unit="mmole / l"
) 

product = pe.Reactant.fromChebiID(
    chebi_id="CHEBI:15343", vessel_id=vessel_id,
    init_conc=0.0, unit="mmole / l"
)

# ... and add each to the document
protein_id = enzmldoc.addProtein(protein)
substrate_id = enzmldoc.addReactant(substrate)
product_id = enzmldoc.addReactant(product)

# Build the reaction
reaction = pe.EnzymeReaction.fromEquation(
    equation="ethanol -> acetaldehyde",
    modifiers=[protein_id],
    name="Alocohol dehydrogenation",
    enzmldoc=enzmldoc
)

# ... and add it to the document
reaction_id = enzmldoc.addReaction(reaction)

# Finally, save the document to an OMEX archive
enzmldoc.toFile(".", name="ADH Experiment")
```
<sub>(Code should run as it is)</sup>

## 📖 Documentation and more examples

Explore all the features of **PyEnzyme** in our [documentation](https://pyenzyme.readthedocs.io/en/latest/index.html#) and take part in [Discussions](https://github.com/EnzymeML/PyEnzyme/discussions) and/or [Issues](https://github.com/EnzymeML/PyEnzyme/issues). 

## ⚠️ License

`PyEnzyme` is free and open-source software licensed under the [BSD 2-Clause License](https://github.com/EnzymeML/PyEnzyme/blob/main/LICENSE). 
