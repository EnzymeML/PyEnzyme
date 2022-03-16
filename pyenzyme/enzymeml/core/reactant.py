# File: reactant.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

from pydantic import Field
from typing import Dict, TYPE_CHECKING, Optional, Union, Any
from dataclasses import dataclass

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.abstract_classes import AbstractSpecies
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.exceptions import ChEBIIdentifierError
from pyenzyme.enzymeml.core.utils import type_checking, deprecated_getter

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class Reactant(EnzymeMLBase, AbstractSpecies):

    name: Optional[str] = Field(
        None, description="Name of the reactant.", template_alias="Name"
    )

    vessel_id: str = Field(
        ...,
        description="Identifier of the vessel in which the reactant was stored.",
        template_alias="Vessel",
    )

    init_conc: Optional[float] = Field(
        None,
        description="Initial concentration of the reactant.",
    )

    unit: Optional[str] = Field(
        None,
        description="Unit of the reactant intial concentration.",
    )

    constant: bool = Field(
        False,
        description="Whether the reactants concentration remains constant or not.",
        template_alias="Constant",
    )

    id: Optional[str] = Field(
        None,
        description="Unique identifier of the protein.",
        template_alias="ID",
        regex=r"s[\d]+",
    )

    meta_id: Optional[str] = Field(
        None,
        description="Unique meta identifier of the protein.",
    )

    smiles: Optional[str] = Field(
        None,
        description="Simplified Molecular Input Line Entry System (SMILES) encoding of the reactant.",
        template_alias="SMILES",
    )

    inchi: Optional[str] = Field(
        None,
        description="International Chemical Identifier (InChI) encoding of the reactant.",
        template_alias="InCHI",
    )

    boundary: bool = Field(
        False,
        description="Whether the reactant is under any boundary conditions (SBML Technicality, better leave it to default)",
    )

    ontology: SBOTerm = Field(
        SBOTerm.SMALL_MOLECULE,
        description="Ontology describing the characteristic of the reactant.",
    )

    uri: Optional[str] = Field(
        None,
        description="URI of the protein.",
    )

    creator_id: Optional[str] = Field(
        None,
        description="Unique identifier of the author.",
    )

    chebi_id: Optional[str] = Field(
        None,
        description="Unique identifier of the CHEBI database. Use this identifier to initialize the object from the CHEBI database.",
    )

    # ! Initializers
    @classmethod
    def fromChebiID(
        cls,
        chebi_id: str,
        vessel_id: str,
        constant: bool = False,
        init_conc: Optional[float] = None,
        unit: Optional[str] = None,
    ) -> "Reactant":
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
            chebi_id=chebi_id,
            **parameters,
        )

    @staticmethod
    def _getChEBIParameters(chebi_id: Union[str, int]) -> Dict[str, Any]:
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
