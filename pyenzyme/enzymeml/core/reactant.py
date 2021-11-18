'''
File: reactant.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 15th 2021 8:40:52 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pydantic import Field, PositiveFloat, validator
from typing import TYPE_CHECKING, Optional
from enum import Enum
from dataclasses import dataclass

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class Reactant(EnzymeMLBase, AbstractSpecies):

    name: str = Field(
        description="Name of the reactant.",
        required=True
    )

    vessel_id: str = Field(
        description="Identifier of the vessel in which the reactant was stored.",
        required=True
    )

    init_conc: PositiveFloat = Field(
        default=0.0,
        description="Initial concentration of the reactant.",
        required=True,
        inclusiveMinimum=0.0
    )

    unit: str = Field(
        description="Unit of the reactant intial concentration.",
        required=True
    )

    constant: bool = Field(
        default=True,
        description="Whether the reactants concentration remains constant or not.",
        required=True
    )

    id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the protein.",
        required=False,
        regex=r"s[\d]+"
    )

    meta_id: Optional[str] = Field(
        default=None,
        description="Unique meta identifier of the protein.",
        required=False
    )

    smiles: Optional[str] = Field(
        description="Simplified Molecular Input Line Entry System (SMILES) encoding of the reactant.",
        required=False
    )

    inchi: Optional[str] = Field(
        description="International Chemical Identifier (InChI) encoding of the reactant.",
        required=False
    )

    boundary: bool = Field(
        default=False,
        description="Whether the reactant is under any boundary conditions (SBML Technicality, better leave it to default)",
        required=True
    )

    ontology: Enum = Field(
        default=SBOTerm.SMALL_MOLECULE,
        description="Ontology describing the characteristic of the reactant.",
        required=True
    )

    uri: Optional[str] = Field(
        default=None,
        description="URI of the protein.",
        required=False
    )

    creator_id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the author.",
        required=False
    )

    # * Private
    _unit_id: Optional[str] = None

    # ! Validators
    @validator("id")
    def set_meta_id(cls, id: Optional[str], values: dict):
        """Sets the meta ID when an ID is provided"""

        if id:
            # Set Meta ID with ID
            values["meta_id"] = f"METAID_{id.upper()}"

        return id

    @validator("meta_id")
    def check_meta_id(cls, meta_id: Optional[str], values: dict):
        """Checks if the meta ID provided is following the standard"""

        if values.get("meta_id"):
            # When the ID init already set the meta ID
            return values.get("meta_id")

        return None

    # ! Getters
    @deprecated_getter("inchi")
    def getInchi(self):
        return self.inchi

    @deprecated_getter("smiles")
    def getSmiles(self):
        return self.smiles

    @deprecated_getter("init_conc")
    def getInitConc(self):
        return self.init_conc

    @deprecated_getter("name")
    def getName(self):
        return self.name

    @deprecated_getter("id")
    def getId(self):
        return self.id

    @deprecated_getter("meta_id")
    def getMetaid(self):
        return self.meta_id

    @deprecated_getter("ontology")
    def getSboterm(self):
        return self.ontology

    @deprecated_getter("vessel_id")
    def getVessel(self):
        return self.vessel_id

    @deprecated_getter("unit")
    def getSubstanceUnits(self):
        return self.unit

    @deprecated_getter("boundary")
    def getBoundary(self):
        return self.boundary

    @deprecated_getter("constant")
    def getConstant(self):
        return self.constant
