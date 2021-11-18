'''
File: protein.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 9:53:42 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

import re

from pydantic import PositiveFloat, validator, Field
from typing import Optional, TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass

from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.exceptions import ECNumberError
from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies
from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class Protein(EnzymeMLBase, AbstractSpecies):

    name: str = Field(
        description="Name of the protein",
        required=True
    )

    sequence: str = Field(
        description="Amino acid sequence of the protein",
        required=True
    )

    vessel_id: str = Field(
        description="Identifier of the vessel in which the protein was stored.",
        required=True,
        regex=r"v[\d.]+"
    )

    init_conc: PositiveFloat = Field(
        description="Initial concentration of the protein.",
        required=True,
        inclusiveMinimum=0.0
    )

    unit: str = Field(
        description="Unit of the proteins intial concentration.",
        required=True
    )

    constant: bool = Field(
        default=True,
        description="Whether the proteins concentration remains constant or not.",
        required=True
    )

    id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the protein.",
        required=False,
        regex=r"p[\d]+"
    )

    meta_id: Optional[str] = Field(
        default=None,
        description="Unique meta identifier of the protein.",
        required=False
    )

    ec_number: Optional[str] = Field(
        default=None,
    )

    uniprot_id: Optional[str] = Field(
        default=None,
        description="Unique identifier referencing a protein entry at UniProt.",
        required=False
    )

    organism: Optional[str] = Field(
        default=None,
        description="Organism the protein was expressed in.",
        required=False
    )

    organism_tax_id: Optional[str] = Field(
        default=None,
        description="Taxonomy identifier of the expression host.",
        required=False
    )

    boundary: bool = Field(
        default=False,
        description="Whether the protein is under any boundary conditions (SBML Technicality, better leave it to default)",
        required=True
    )

    ontology: Enum = Field(
        default=SBOTerm.PROTEIN,
        description="Ontology describing the characteristic of the protein.",
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

    # Validators

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

    @validator("sequence")
    def clean_sequence(cls, sequence):
        """Cleans a sequence from whitespaces as well as newlines and transforms uppercase"""

        return re.sub(r"\s+", "", sequence).upper()

    @validator("ec_number")
    def validate_ec_number(cls, ec_number: str):
        """Validates whether given EC number complies to the established pattern."""

        pattern = r"(\d+.)(\d+.)(\d+.)(\d+)"
        match = re.search(pattern, ec_number)

        if match is not None:
            return "".join(match.groups())
        else:
            raise ECNumberError(ec_number=ec_number)

    @deprecated_getter("organism_tax_id")
    def getOrganismTaxId(self):
        return self.organism_tax_id

    @deprecated_getter("ec_number")
    def getEcnumber(self):
        return self.ec_number

    @deprecated_getter("uniprot_id")
    def getUniprotID(self):
        return self.uniprot_id

    @deprecated_getter("organism")
    def getOrganism(self):
        return self.organism

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

    @deprecated_getter("sequence")
    def getSequence(self):
        return self.sequence

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
