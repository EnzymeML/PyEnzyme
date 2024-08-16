from pathlib import Path

import rich

from pyenzyme.sbml import read_sbml

doc = read_sbml(Path("./dev-examples/reactions/reactions_example.omex"))

rich.print(doc)
