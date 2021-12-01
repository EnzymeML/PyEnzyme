'''
File: creator.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 15th 2021 6:28:16 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pydantic import BaseModel, PositiveFloat, PrivateAttr, validator
from typing import Optional
from enum import Enum
from abc import ABC, abstractmethod


class AbstractSpeciesDataclass(BaseModel):
    """Abstract dataclass to describe an EnzymeML/SBML species."""

    name: str
    id: str
    meta_id: str
    init_conc: PositiveFloat
    constant: bool
    unit: str
    ontology: Enum
    _unit_id: Optional[str] = PrivateAttr(default=None)
    uri: Optional[str]
    creator_id: Optional[str]


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


class AbstractSpeciesFactory(ABC):
    """
    Factory that returns a specific species instance.
    """

    enzymeml_part: str

    @abstractmethod
    def get_species(
        self, **kwargs
    ) -> AbstractSpecies:
        """Return a new species object"""
