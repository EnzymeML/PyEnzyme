from pydantic.types import PositiveFloat
from enum import Enum
from typing import Protocol


class AbstractSpecies(Protocol):
    """Abstract class to describe an EnzymeML/SBML species."""

    name: str
    id: str
    meta_id: str
    init_conc: PositiveFloat
    constant: bool
    unit: str
    ontology: Enum
    uri: str
    creator_id: str
