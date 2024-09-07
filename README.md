<h1 align="center">
  PyEnzyme<br>
  <img src="https://img.shields.io/badge/PyEnzyme-1.1.5-blue" alt="v1.1.5">
  <img src="https://github.com/EnzymeML/PyENzyme/actions/workflows/build.yml/badge.svg" alt="Build Badge"> <img src='https://readthedocs.org/projects/pyenzyme/badge/?version=latest' alt='Documentation Status' />
</a>
<a href="https://www.codacy.com/gh/EnzymeML/PyEnzyme/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=EnzymeML/PyEnzyme&amp;utm_campaign=Badge_Grade"><img src="https://app.codacy.com/project/badge/Grade/4ceb8d010e7b456c926c8b18737ff102"/></a>
</h1>
<p align="center">
PyEnzyme is the interface to the data model <b>EnzymeML</b> and offers a convenient way to document and model research data. Lightweight syntax for rapid development of data management solution in enzymology and biocatalysis.</p>

### 🧬 Features

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

PyEnzyme comes with many flavors, choose whether you want only the base installation, the modeling package or all of it
using the following options.

```
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
```

## ⚙️ Example code

This example will demonstrate how to create a simple EnzymeML document using PyEnzyme and how to use initializers from
official databases **Chebi** and **UniProt** to gather metadata. For more examples, please visit
our [documentation](https://pyenzyme.readthedocs.io/en/latest/index.html#) (Work in progress)

```python
# To be added for V2
```

<sub>(Code should run as it is)</sup>

## 📖 Documentation and more examples

Explore all the features of **PyEnzyme** in our [documentation](https://pyenzyme.readthedocs.io/en/latest/index.html#)
and take part in [Discussions](https://github.com/EnzymeML/PyEnzyme/discussions)
and/or [Issues](https://github.com/EnzymeML/PyEnzyme/issues).

## 🧪 Testing

In order to run tests there are two different ways. First you can utilize `pytest` directly by running the following:

```bash
python -m pytest -vv
```

Or you can the provided Dockerfile to run the tests in a containerized environment.

```bash
docker build -t pyenzyme .
```

## ⚠️ License

`PyEnzyme` is free and open-source software licensed under
the [BSD 2-Clause License](https://github.com/EnzymeML/PyEnzyme/blob/main/LICENSE).
