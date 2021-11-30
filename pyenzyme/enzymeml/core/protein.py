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
from typing import Optional, TYPE_CHECKING, Any
from enum import Enum
from dataclasses import dataclass

from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.exceptions import ECNumberError, UniProtIdentifierError
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

    name: Optional[str] = Field(
        default=None,
        description="Name of the protein",
        required=True
    )

    sequence: Optional[str] = Field(
        default=None,
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

    ecnumber: Optional[str] = Field(
        default=None,
        description="EC number of the protein.",
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

    uniprotid: Optional[str] = Field(
        default=None,
        description="Unique identifier referencing a protein entry at UniProt. Use this identifier to initialize the object from the UniProt database.",
        required=False
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

    @validator("ecnumber")
    def validate_ecnumber(cls, ecnumber: Optional[str]):
        """Validates whether given EC number complies to the established pattern."""

        if ecnumber is None:
            return ecnumber

        pattern = r"(\d+.)(\d+.)(\d+.)(\d+)"
        match = re.search(pattern, ecnumber)

        if match is not None:
            return "".join(match.groups())
        else:
            raise ECNumberError(ecnumber=ecnumber)

    @validator("uniprotid")
    def fetch_uniprot_parameters(cls, uniprotid, values):
        """PYDANTIC VALIDATOR: Automatically fills out fields present in the UniProt database with appropriate values.

        Caution, this function will overwrite any values in name, seqence and ecnumber that were given to the constructor!!

        Args:
            uniprotid (Union[str, int]): The UniProt ID from which the data will be fetched.
            values (dict): Already initialiized values from teh constructor.
        """

        # Guard clauses
        if uniprotid is None:
            if values.get("name") is None:
                raise NameError(
                    "Please provide a name for the protein if there is no UniProt ID to fetch it from."
                )
            else:
                return uniprotid

        # Get chebi parameters
        parameters = cls._getUniProtParameters(uniprotid=uniprotid)

        # Override already given parameters in the data model
        for key, item in parameters.items():
            values[key] = str(item)

        return uniprotid

    # ! Initializers
    @classmethod
    def fromUniProtID(
        cls,
        uniprotid: str,
        init_conc: float,
        unit: str,
        vessel_id: str,
        constant: bool = False
    ) -> 'Protein':
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
            **parameters
        )

    @staticmethod
    def _getUniProtParameters(uniprotid: str) -> dict[str, Any]:
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
    @ deprecated_getter("organism_tax_id")
    def getOrganismTaxId(self):
        return self.organism_tax_id

    @ deprecated_getter("ecnumber")
    def getEcnumber(self):
        return self.ecnumber

    @ deprecated_getter("uniprotid")
    def getUniprotID(self):
        return self.uniprotid

    @ deprecated_getter("organism")
    def getOrganism(self):
        return self.organism

    @ deprecated_getter("init_conc")
    def getInitConc(self):
        return self.init_conc

    @ deprecated_getter("name")
    def getName(self):
        return self.name

    @ deprecated_getter("id")
    def getId(self):
        return self.id

    @ deprecated_getter("meta_id")
    def getMetaid(self):
        return self.meta_id

    @ deprecated_getter("sequence")
    def getSequence(self):
        return self.sequence

    @ deprecated_getter("ontology")
    def getSboterm(self):
        return self.ontology

    @ deprecated_getter("vessel_id")
    def getVessel(self):
        return self.vessel_id

    @ deprecated_getter("unit")
    def getSubstanceUnits(self):
        return self.unit

    @ deprecated_getter("boundary")
    def getBoundary(self):
        return self.boundary

    @ deprecated_getter("constant")
    def getConstant(self):
        return self.constant
