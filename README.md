<h1 align="center">
  PyEnzyme<br>
  <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/pyenzyme">
  <img src="https://github.com/EnzymeML/PyEnzyme/actions/workflows/unit-tests.yaml/badge.svg" alt="Build Badge"> 
</a>
<a href="https://www.codacy.com/gh/EnzymeML/PyEnzyme/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=EnzymeML/PyEnzyme&amp;utm_campaign=Badge_Grade"><img src="https://app.codacy.com/project/badge/Grade/4ceb8d010e7b456c926c8b18737ff102"/></a>
</h1>
<p align="center">
PyEnzyme is the interface to the data model <b>EnzymeML</b> and offers a convenient way to document and model research data. Lightweight syntax for rapid development of data management solution in enzymology and biocatalysis.</p>

### 🧬 Features

- Reproducible **documentation** of enzymatic and biocatalytic experiments.
- **Import** from and **export** to the SBML-based markup language **EnzymeML** and more.
- **Fetch** entities from [CheBI](https://www.ebi.ac.uk/chebi/), [UniProt](https://www.uniprot.org/), [PubChem](https://www.ncbi.nlm.nih.gov/pubchem/), [RHEA](https://www.ebi.ac.uk/rhea/) and [PDB](https://www.rcsb.org/) databases.
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

### 🚀 Try PyEnzyme in Google Colab

Get hands-on experience with PyEnzyme without any local installation! Try our interactive Google Colab notebook by clicking the badge below:

<a target="_blank" href="https://colab.research.google.com/github/EnzymeML/PyEnzyme/blob/main/examples/Basic.ipynb">
  <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>

### ⚙️ Package Options

PyEnzyme comes with many flavors, choose whether you want only the base installation, the modeling package or all of it
using the following options.

```bash
# PySCeS - modeling
python -m pip install "pyenzyme[pysces]"
```

## ⚙️ Example code

This example will demonstrate how to create a simple EnzymeML document using PyEnzyme and how to use initializers from official databases **Chebi** and **UniProt** to gather metadata.

### Create a simple EnzymeML document

```python
import pyenzyme as pe

# Create a simple EnzymeML document
enzmldoc = pe.EnzymeMLDocument(name="Test")

vessel = enzmldoc.add_to_vessels(
    id="vessel_1",
    name="Vessel 1",
    volume=1.0,
    unit="l",  # Units are automatically converted to a UnitDefinition
)

# Add a protein from UniProt
protein = pe.fetch_uniprot("P07327", vessel_id=vessel.id)
enzmldoc.proteins.append(protein)

# Add a reaction from RHEA DB
reaction, participants = pe.fetch_rhea("RHEA:22864", vessel_id=vessel.id)
enzmldoc.small_molecules += participants
enzmldoc.reactions.append(reaction)

# Parse a tabular file to a measurement
measurements = pe.from_excel(
    path="measurements.xlsx",
    data_unit="mmol / l",
    time_unit="h",
)

enzmldoc.measurements += measurements

# Serialize to EnzymeML
pe.write_enzymeml(enzmldoc, "enzmldoc.json")

# Deserialize from EnzymeML
enzmldoc = pe.read_enzymeml("enzmldoc.json")

# Convert to SBML
sbml_doc = pe.to_sbml(enzmldoc, "enzmldoc.omex")
```

<sub>(Code should run as it is)</sub>

### Compose an EnzymeML document

As an alternative to the manual creation of an EnzymeML document, you can use the `compose` function to create an EnzymeML document from a list of identifiers. This function will fetch the corresponding entities from the official databases and compose an EnzymeML document. Duplicate entities are removed to avoid redundancy.

```python
import pyenzyme as pe

doc = pe.compose(
    name="test",
    proteins=["PDB:1A23"],
    small_molecules=["CHEBI:32551"],
    reactions=["RHEA:22864"],
)

pe.write_enzymeml(doc, "enzmldoc.json")
```

<sub>(Code should run as it is)</sub>

Please note, that by providing [RHEA](https://www.ebi.ac.uk/rhea/) identifiers, the function will automatically fetch all associated [CheBI](https://www.ebi.ac.uk/chebi/) molecules that are part of the reaction.

## 📖 Documentation and more examples

Explore all the features of **PyEnzyme** in our [documentation](https://pyenzyme.readthedocs.io/en/latest/index.html#)
and take part in [Discussions](https://github.com/EnzymeML/PyEnzyme/discussions)
and/or [Issues](https://github.com/EnzymeML/PyEnzyme/issues).

## 🔙 Backwards compatibility

For backward compatibility with previous versions of PyEnzyme, this release includes the original `v1.1.5` version of the package under the `v1` subpackage. Users may continue to utilize the legacy API by importing from `pyenzyme.v1` instead of `pyenzyme`. Please be aware that the dependencies for the current `v2` implementation differ from those of `v1` and must be installed separately using `poetry install --with v1`.

For new projects, we recommend utilizing the updated API available in the package root. Existing users of the legacy API are encouraged to migrate to the current version to benefit from the latest features and improvements.

## 🧪 Testing

In order to run tests there are two different ways. First you can utilize `pytest` directly by running the following:

```bash
python -m pytest -vv
```

Or you can the provided Dockerfile to run the tests in a containerized environment.

```bash
docker build -t pyenzyme .
docker run pyenzyme
```

## ⚠️ License

`PyEnzyme` is free and open-source software licensed under
the [BSD 2-Clause License](https://github.com/EnzymeML/PyEnzyme/blob/main/LICENSE).

---

<div align="center">
<strong>Made with ❤️ by the EnzymeML Team</strong>
</div>
