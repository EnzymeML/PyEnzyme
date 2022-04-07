# File: creator.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

from pydantic import BaseModel, PrivateAttr, validator
from typing import Optional
from abc import ABC, abstractmethod

from pyenzyme.enzymeml.core.ontology import SBOTerm


class AbstractSpeciesDataclass(BaseModel):
    """Abstract dataclass to describe an EnzymeML/SBML species."""

    name: str
    meta_id: Optional[str]
    id: Optional[str]
    vessel_id: str
    init_conc: Optional[float] = None
    constant: bool
    boundary: bool
    unit: Optional[str] = None
    ontology: SBOTerm
    uri: Optional[str]
    creator_id: Optional[str]

    # * Private attributes
    _unit_id: Optional[str] = PrivateAttr(default=None)
    _enzmldoc = PrivateAttr(default=None)


class AbstractSpecies(ABC, AbstractSpeciesDataclass):
    """Due to inheritance and type-checking issues, the dataclass has to be mixed in."""

    # ! Validators
    @validator("id")
    def set_meta_id(cls, id: Optional[str], values: dict):
        """Sets the meta ID when an ID is provided"""

        if id:
            # Set Meta ID with ID
            values["meta_id"] = f"METAID_{id.upper()}"

        return id

    # ! Getters
    def unitdef(self):
        """Returns the appropriate unitdef if an enzmldoc is given"""

        if not self._enzmldoc:
            return None
        if not self.unit:
            return None

        return self._enzmldoc._unit_dict[self._unit_id]


class AbstractSpeciesFactory(ABC):
    """
    Factory that returns a specific species instance.
    """

    enzymeml_part: str

    @abstractmethod
    def get_species(self, **kwargs) -> AbstractSpecies:
        """Return a new species object"""
