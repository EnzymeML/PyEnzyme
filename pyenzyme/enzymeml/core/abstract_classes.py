from pydantic import BaseModel, PositiveFloat, PrivateAttr, validator
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
    _unit_id: Optional[str] = PrivateAttr(default=None)
    ontology: Enum
    uri: str
    creator_id: str


class AbstractSpecies(ABC, AbstractSpeciesDataclass):
    """Due to inheritance and type-checking issues, the dataclass has to be mixed in."""

    def set_unit_id(self, unit_id: str):
        setattr(self, "_unit_id", unit_id)

    # ! Validators
    @validator("id")
    def set_meta_id(cls, id: Optional[str], values: dict):
        """Sets the meta ID when an ID is provided"""

        if id:
            # Set Meta ID with ID
            values["meta_id"] = f"METAID_{id.upper()}"

        return id
