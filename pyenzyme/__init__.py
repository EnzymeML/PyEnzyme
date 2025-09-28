from __future__ import annotations

from mdmodels.units.unit_definition import UnitDefinition, UnitType

from .composer import compose
from .fetcher import *  # noqa: F403
from .plotting import plot, plot_interactive
from .pretty import summary
from .suite import EnzymeMLSuite
from .tools import group_measurements
from .versions.io import EnzymeMLHandler
from .versions.v2 import *  # noqa: F403

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
to_petab = EnzymeMLHandler.to_petab
write_enzymeml = EnzymeMLHandler.write_enzymeml

__all__ = [
    "UnitDefinition",
    "UnitType",
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
    "plot_interactive",
    "summary",
    "group_measurements",
]

__version__ = "2.2.0"
