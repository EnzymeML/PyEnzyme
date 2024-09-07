from pathlib import Path

import pyenzyme as pe

doc = pe.EnzymeMLDocument.from_sbml(path=Path("./tests/fixtures/sbml/v1_example.omex"))

with open("./tests/fixtures/sbml/v1_example_enzml.json", "w") as f:
    f.write(doc.model_dump_json(indent=2))
