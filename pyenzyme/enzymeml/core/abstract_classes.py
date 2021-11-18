from pydantic import BaseModel, PositiveFloat
from typing import Optional
from enum import Enum
from abc import ABC


class AbstractSpeciesDataclass(BaseModel):
    """Abstract dataclass to describe an EnzymeML/SBML species."""

    name: str
    id: str
    meta_id: str
    init_conc: PositiveFloat
    constant: bool
    unit: str
    _unit_id: Optional[str] = None
    ontology: Enum
    uri: str
    creator_id: str


class AbstractSpecies(ABC, AbstractSpeciesDataclass):
    """Due to inheritance and type-checking issues, the dataclass has to be mixed in."""
    pass
