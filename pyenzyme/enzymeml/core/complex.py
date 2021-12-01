'''
File: complex.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 9:53:42 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pydantic import PositiveFloat, validator, Field
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies
from pyenzyme.enzymeml.core.utils import (
    type_checking,
)

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class Protein(EnzymeMLBase, AbstractSpecies):

    name: Optional[str] = Field(
        None,
        description="Name of the complex",
    )

    reactants: list[str] = Field(
        None,
        description="Array of reactant IDs the complex contains",
        regex=r"s[\d]+"
    )

    proteins: list[str] = Field(
        None,
        description="Array of reactant IDs the complex contains",
        regex=r"p[\d]+"
    )

    vessel_id: str = Field(
        ...,
        description="Identifier of the vessel in which the protein was stored.",
        regex=r"v[\d.]+"
    )

    init_conc: PositiveFloat = Field(
        ...,
        description="Initial concentration of the protein.",
        inclusiveMinimum=0.0
    )

    unit: str = Field(
        ...,
        description="Unit of the proteins intial concentration.",
    )

    constant: bool = Field(
        False,
        description="Whether the proteins concentration remains constant or not.",
    )

    id: Optional[str] = Field(
        None,
        description="Unique identifier of the protein.",
        regex=r"c[\d]+"
    )

    meta_id: Optional[str] = Field(
        None,
        description="Unique meta identifier of the protein.",
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
