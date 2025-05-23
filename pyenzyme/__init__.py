from __future__ import annotations

from mdmodels.units.unit_definition import UnitDefinition

from .versions.v2 import *  # noqa: F403
from .versions.io import EnzymeMLHandler
from .fetcher import *  # noqa: F403
from .composer import compose
from .suite import EnzymeMLSuite
from .plotting import plot, plot_interactive

# Input functions
from_csv = EnzymeMLHandler.from_csv
from_dataframe = EnzymeMLHandler.from_dataframe
from_excel = EnzymeMLHandler.from_excel
from_sbml = EnzymeMLHandler.from_sbml
read_enzymeml = EnzymeMLHandler.read_enzymeml
read_enzymeml_from_string = EnzymeMLHandler.read_enzymeml_from_string

# Output functions
to_pandas = EnzymeMLHandler.to_pandas
to_sbml = EnzymeMLHandler.to_sbml
write_enzymeml = EnzymeMLHandler.write_enzymeml

__all__ = [
    "UnitDefinition",
    "EnzymeMLSuite",
    "EnzymeMLHandler",
    "from_csv",
    "from_dataframe",
    "from_excel",
    "from_sbml",
    "read_enzymeml",
    "to_pandas",
    "to_sbml",
    "write_enzymeml",
    "compose",
    "plot",
]
