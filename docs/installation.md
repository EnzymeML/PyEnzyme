# Installation

PyEnzyme is the interface to the data model EnzymeML and offers a convenient way to document and model research data. Lightweight syntax for rapid development of data management solution in enzymology and biocatalysis.</p>

__Features__

- Reproducible documentation of enzymatic and biocatalytic experiments.
- Import from and export to the SBML-based markup language EnzymeML and more.
- Perform database-specific validation prior to database upload.
- Model your data using a Thin Layer  to popular modeling platforms.
- Visualize experimental results for inspection and publication.

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

## Package Options
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

## PyEnzyme's REST-API

If you want to deploy PyEnzyme as a server and use our REST-API to access PyEnzyme from any HTTP-capable programming language, use our official [docker image](https://hub.docker.com/r/enzymeml/pyenzyme/tags) or simply copy and past the following.

```bash
docker pull enzymeml/pyenzyme:latest
docker run -p 8000:8000 enzymeml/pyenzyme:latest
```
See the [API documentation](https://enzymeml.sloppy.zone) for details on our endpoints. You can also use our self-hosted PyEnzyme instance if you have no server space - Use https://enzymeml.sloppy.zone as base URL to the endpoints.
