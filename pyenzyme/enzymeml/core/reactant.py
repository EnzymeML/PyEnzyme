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
from typing import TYPE_CHECKING, Optional, Union, Any
from enum import Enum
from dataclasses import dataclass

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.exceptions import ChEBIIdentifierError
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

    name: Optional[str] = Field(
        default=None,
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
        default=False,
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

    chebi_id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the CHEBI database. Use this identifier to initialize the object from the CHEBI database.",
        required=False
    )

    # ! Validators
    @validator("chebi_id")
    def fetch_chebi_parameters(cls, chebi_id, values):
        """PYDANTIC VALIDATOR: Automatically fills out fields present in the ChEBI database with appropriate values.

        Caution, this function will overwrite any values in smiles, inchi and name that were given to the constructor!!

        Args:
            chebi_id (Union[str, int]): The ChEBI ID from which the data will be fetched.
            values ([type]): Already initialiized values from teh constructor.
        """

        # Guard clauses
        if chebi_id is None:
            if values.get("name") is None:
                raise NameError(
                    "Please provide a name for the reactant if there is no ChEBI ID to fetch it from."
                )
            else:
                return chebi_id

        # Get chebi parameters
        parameters = cls._getChEBIParameters(chebi_id=chebi_id)

        # Override already given parameters in the data model
        for key, item in parameters.items():
            values[key] = item

        return chebi_id

    # ! Initializers
    @classmethod
    def fromChebiID(
        cls,
        chebi_id: Union[str, int],
        init_conc: float,
        unit: str,
        vessel_id: str,
        constant: bool = False
    ) -> 'Reactant':
        """Initializes a reactant based

        Raises:
            ChEBIIdentifierError: [description]

        Returns:
            [type]: [description]
        """

        # Get Chebi Parameters
        parameters = cls._getChEBIParameters(chebi_id=chebi_id)

        return cls(
            init_conc=init_conc,
            unit=unit,
            vessel_id=vessel_id,
            constant=constant,
            **parameters
        )

    @staticmethod
    def _getChEBIParameters(chebi_id: Union[str, int]) -> dict[str, Any]:
        import requests
        import xml.etree.ElementTree as ET

        # Send request to CHEBI database
        endpoint = f"https://www.ebi.ac.uk/webservices/chebi/2.0/test/getCompleteEntity?chebiId={chebi_id}"

        # Fetch data
        response = requests.get(endpoint)
        tree = ET.ElementTree(ET.fromstring(response.text))

        # Set prefix to match tag
        prefix = r"{https://www.ebi.ac.uk/webservices/chebi}"

        # Check if the CHEBI ID is correct
        if "faultcode" in response.text:
            raise ChEBIIdentifierError(chebi_id=chebi_id)

        # Define mapping for the used attributes
        attribute_mapping = {
            prefix + "inchi": "inchi",
            prefix + "smiles": "smiles",
            prefix + "chebiAsciiName": "name",
        }

        # Collect parameters
        parameters = {
            attribute_mapping[elem.tag]: elem.text
            for elem in tree.iter()
            if elem.tag in attribute_mapping
        }

        return parameters

    # ! Getters

    @ deprecated_getter("inchi")
    def getInchi(self):
        return self.inchi

    @ deprecated_getter("smiles")
    def getSmiles(self):
        return self.smiles

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
