from pathlib import Path

import rich

import pyenzyme as pe
from pyenzyme.tools import to_dict_wo_json_ld

doc = pe.EnzymeMLDocument.from_sbml(
    path=Path("./dev-examples/reactions/reactions_example.omex")
)

rich.print(to_dict_wo_json_ld(doc))

df = doc.to_pandas(doc)

rich.print(df)
