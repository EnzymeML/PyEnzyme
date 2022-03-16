# File: complex.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import re

from pydantic import validator, Field
from typing import List, Optional, TYPE_CHECKING
from dataclasses import dataclass

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies
from pyenzyme.enzymeml.core.exceptions import ParticipantIdentifierError
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.utils import (
    type_checking,
)

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class Complex(EnzymeMLBase, AbstractSpecies):

    name: str = Field(
        ...,
        description="Name of the complex",
    )

    participants: List[str] = Field(
        default_factory=list,
        description="Array of IDs the complex contains",
    )

    vessel_id: str = Field(
        ...,
        description="Identifier of the vessel in which the protein was stored.",
        regex=r"v[\d]+",
    )

    init_conc: Optional[float] = Field(
        None, description="Initial concentration of the protein.", inclusiveMinimum=0.0
    )

    unit: Optional[str] = Field(
        None,
        description="Unit of the proteins intial concentration.",
    )

    constant: bool = Field(
        False,
        description="Whether the proteins concentration remains constant or not.",
    )

    meta_id: Optional[str] = Field(
        None,
        description="Unique meta identifier of the protein.",
    )

    id: Optional[str] = Field(
        None, description="Unique identifier of the protein.", regex=r"c[\d]+"
    )

    boundary: bool = Field(
        False,
        description="Whether the protein is under any boundary conditions (SBML Technicality, better leave it to default)",
    )

    ontology: SBOTerm = Field(
        SBOTerm.MACROMOLECULAR_COMPLEX,
        description="Ontology describing the characteristic of the protein.",
    )

    uri: Optional[str] = Field(
        None,
        description="URI of the protein.",
    )

    creator_id: Optional[str] = Field(
        None,
        description="Unique identifier of the author.",
    )

    # ! Validators
    @validator("id")
    def set_meta_id(cls, id: Optional[str], values: dict):
        """Sets the meta ID when an ID is provided"""

        if id:
            # Set Meta ID with ID
            values["meta_id"] = f"METAID_{id.upper()}"

        return id

    @validator("participants")
    def check_reactant_ids(cls, ids: List[str]):
        """Checks ID consistency for reactants"""

        for id in ids:
            if cls._id_checker(id, r"s[\d]+"):
                # Check for reactants
                continue
            elif cls._id_checker(id, r"p[\d]+"):
                # Check for proteins
                continue
            else:
                raise ParticipantIdentifierError(id=id, prefix="s/p")

        return ids

    @staticmethod
    def _id_checker(id: str, pattern: str):
        """Checks ID pattern"""
        return bool(re.match(pattern, id))
