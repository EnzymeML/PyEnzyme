# File: protein.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import re

from pydantic import validator, Field
from typing import Dict, Optional, TYPE_CHECKING, Any
from dataclasses import dataclass

from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.exceptions import UniProtIdentifierError
from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies
from pyenzyme.enzymeml.core.utils import type_checking, deprecated_getter

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class Protein(EnzymeMLBase, AbstractSpecies):

    name: Optional[str] = Field(
        None, description="Name of the protein", template_alias="Name"
    )

    sequence: Optional[str] = Field(
        None,
        description="Amino acid sequence of the protein",
        template_alias="Sequence",
    )

    vessel_id: str = Field(
        ...,
        description="Identifier of the vessel in which the protein was stored.",
        template_alias="Vessel",
        regex=r"v[\d.]+",
    )

    init_conc: Optional[float] = Field(
        default=None,
        description="Initial concentration of the protein.",
    )

    unit: Optional[str] = Field(
        None,
        description="Unit of the proteins intial concentration.",
    )

    constant: bool = Field(
        True,
        description="Whether the proteins concentration remains constant or not.",
        template_alias="Constant",
    )

    id: Optional[str] = Field(
        None,
        description="Unique identifier of the protein.",
        template_alias="ID",
        regex=r"p[\d]+",
    )

    meta_id: Optional[str] = Field(
        None,
        description="Unique meta identifier of the protein.",
    )

    ecnumber: Optional[str] = Field(
        None,
        description="EC number of the protein.",
        template_alias="EC Number",
        regex=r"(\d+.)(\d+.)(\d+.)(\d+)",
    )

    organism: Optional[str] = Field(
        None,
        description="Organism the protein was expressed in.",
        template_alias="Source organism",
    )

    organism_tax_id: Optional[str] = Field(
        None,
        description="Taxonomy identifier of the expression host.",
    )

    boundary: bool = Field(
        False,
        description="Whether the protein is under any boundary conditions (SBML Technicality, better leave it to default)",
    )

    ontology: SBOTerm = Field(
        SBOTerm.PROTEIN,
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

    uniprotid: Optional[str] = Field(
        None,
        description="Unique identifier referencing a protein entry at UniProt. Use this identifier to initialize the object from the UniProt database.",
        template_alias="UniProt ID",
    )

    # ! Validators
    @validator("id")
    def set_meta_id(cls, id: Optional[str], values: dict):
        """Sets the meta ID when an ID is provided"""

        if id:
            # Set Meta ID with ID
            values["meta_id"] = f"METAID_{id.upper()}"

        return id

    @validator("sequence")
    def clean_sequence(cls, sequence):
        """Cleans a sequence from whitespaces as well as newlines and transforms uppercase"""

        if sequence:
            return re.sub(r"\s+", "", sequence).upper()
        else:
            return sequence

    # ! Initializers
    @classmethod
    def fromUniProtID(
        cls,
        uniprotid: str,
        vessel_id: str,
        init_conc: Optional[float] = None,
        unit: Optional[str] = None,
        constant: bool = False,
    ) -> "Protein":
        """Initializes a protein based on the UniProt database.

        Raises:
            UniProtIdentifierError: Raised when the UniProt identifier is invalid.

        Returns:
            Protein: The initialiized Protein object.
        """

        # Get UniProt Parameters
        parameters = cls._getUniProtParameters(uniprotid=uniprotid)

        return cls(
            init_conc=init_conc,
            unit=unit,
            vessel_id=vessel_id,
            constant=constant,
            uniprotid=uniprotid,
            **parameters,
        )

    @staticmethod
    def _getUniProtParameters(uniprotid: str) -> Dict[str, Any]:
        import requests
        import xml.etree.ElementTree as ET

        # Send request to CHEBI database
        endpoint = f"https://www.uniprot.org/uniprot/{uniprotid}.xml"

        # Fetch data
        response = requests.get(endpoint)

        # Check if the UniProt ID is correct
        if response.status_code == 404:
            raise UniProtIdentifierError(uniprotid=uniprotid)

        # Create XML Tree
        tree = ET.ElementTree(ET.fromstring(response.text))

        # Set prefix to match tag
        prefix = r"{http://uniprot.org/uniprot}"

        # Define mapping for the used attributes
        attribute_mapping = {
            prefix + "sequence": "sequence",
            prefix + "fullName": "name",
            prefix + "ecNumber": "ecnumber",
        }

        # Collect parameters
        parameters = {}
        for elem in tree.iter():
            if elem.tag in attribute_mapping and parameters.get(elem.tag) is None:
                parameters[attribute_mapping[elem.tag]] = elem.text

        return parameters

    # ! Getters
    @deprecated_getter("organism_tax_id")
    def getOrganismTaxId(self):
        return self.organism_tax_id

    @deprecated_getter("ecnumber")
    def getEcnumber(self):
        return self.ecnumber

    @deprecated_getter("uniprotid")
    def getUniprotID(self):
        return self.uniprotid

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
