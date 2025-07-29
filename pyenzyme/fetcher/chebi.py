"""
ChEBI fetcher for retrieving chemical entries by ID.

This module provides functionality to fetch chemical entity data from the
ChEBI database by ID and map it to the PyEnzyme data model (v2).
"""

import requests
import re
from typing import Optional, Union
from pydantic_xml import element, attr, BaseXmlModel
from pyenzyme.versions import v2


class PropertyModel(
    BaseXmlModel,
    tag="property",
    nsmap={"": "https://www.ebi.ac.uk/webservices/chebi"},
):
    """
    Model for a ChEBI entity property.
    """

    name: str = attr(name="name")
    value: str = element(tag="value")


class SynonymModel(
    BaseXmlModel,
    tag="synonym",
    nsmap={"": "https://www.ebi.ac.uk/webservices/chebi"},
):
    """
    Model for a ChEBI synonym.
    """

    data: str = element(tag="data")
    type: str = attr(name="type")
    source: Optional[str] = attr(name="source", default=None)


class FormulaModel(
    BaseXmlModel,
    tag="formula",
    nsmap={"": "https://www.ebi.ac.uk/webservices/chebi"},
):
    """
    Model for a ChEBI chemical formula.
    """

    formula: str = element(tag="data")
    source: Optional[str] = attr(name="source", default=None)


class StructureModel(
    BaseXmlModel,
    tag="structure",
    nsmap={"": "https://www.ebi.ac.uk/webservices/chebi"},
):
    """
    Model for a ChEBI structure representation.
    """

    type: str = attr(name="type")
    structure: str = element(tag="structure")
    dimension: Optional[str] = attr(name="dimension", default=None)
    format: Optional[str] = attr(name="format", default=None)


class ChEBIEntity(
    BaseXmlModel,
    tag="return",
    search_mode="unordered",
    nsmap={"": "https://www.ebi.ac.uk/webservices/chebi"},
):
    """
    Model for a ChEBI entity response.
    """

    chebi_id: str = element(tag="chebiId")
    chebi_ascii_name: str = element(tag="chebiAsciiName")
    definition: Optional[str] = element(tag="definition", default=None)
    status: str = element(tag="status")
    mass: Optional[float] = element(tag="mass", default=None)
    charge: Optional[int] = element(tag="charge", default=None)
    structure: Optional[StructureModel] = element(tag="structure", default=None)
    formula: Optional[FormulaModel] = element(tag="formula", default=None)
    inchi: Optional[str] = element(tag="inchi", default=None)
    inchikey: Optional[str] = element(tag="inchiKey", default=None)
    smiles: Optional[str] = element(tag="smiles", default=None)
    chebiId_version: Optional[str] = element(tag="chebiIdVersion", default=None)


class GetEntityResponse(
    BaseXmlModel,
    tag="getCompleteEntityResponse",
    search_mode="unordered",
    nsmap={"": "https://www.ebi.ac.uk/webservices/chebi"},
):
    """
    Model for the ChEBI API response inside SOAP envelope.
    """

    entity: ChEBIEntity = element(tag="return")


class ChEBIClient:
    """Client for accessing the ChEBI API to fetch chemical entity data."""

    BASE_URL = "https://www.ebi.ac.uk/webservices/chebi/2.0/test/getCompleteEntity"

    def __init__(self):
        """Initialize the ChEBI client."""
        pass

    def get_entry_by_id(self, chebi_id: str) -> Union[ChEBIEntity, None]:
        """
        Fetch a ChEBI entry by its ID.

        Args:
            chebi_id: The ChEBI ID to fetch, can be with or without the 'CHEBI:' prefix

        Returns:
            ChEBIEntity object with the parsed response data

        Raises:
            ValueError: If the ChEBI ID is invalid or not found
            ConnectionError: If the connection to the ChEBI server fails
        """
        # Ensure the CHEBI ID has the correct format
        if not chebi_id.startswith("CHEBI:"):
            chebi_id = f"CHEBI:{chebi_id}"

        # Construct the URL
        url = f"{self.BASE_URL}?chebiId={chebi_id}"

        try:
            response = requests.get(url)
            response.raise_for_status()

            if response.status_code == 200:
                try:
                    # Extract the getCompleteEntityResponse element using regex
                    xml_text = response.text
                    match = re.search(
                        r"<getCompleteEntityResponse.*?</getCompleteEntityResponse>",
                        xml_text,
                        re.DOTALL,
                    )

                    if not match:
                        raise ValueError(
                            "Could not find expected content in ChEBI response"
                        )

                    # Parse only the relevant XML fragment
                    xml_text = match.group(0)
                    entity_response = GetEntityResponse.from_xml(xml_text)
                    return entity_response.entity
                except Exception as e:
                    raise ValueError(f"Failed to parse ChEBI response: {str(e)}")
            else:
                raise ValueError(f"Failed to retrieve ChEBI entry for ID {chebi_id}")

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Connection to ChEBI server failed: {str(e)}")


def fetch_chebi(
    chebi_id: str,
    smallmol_id: Optional[str] = None,
    vessel_id: Optional[str] = None,
) -> v2.SmallMolecule:
    """
    Fetch a ChEBI entry by ID and convert it to a SmallMolecule object.

    Args:
        chebi_id: The ChEBI ID to fetch
        vessel_id: The ID of the vessel to add the small molecule to
    Returns:
        A SmallMolecule object with data from ChEBI

    Raises:
        ValueError: If the ChEBI ID is invalid or not found
        ConnectionError: If the connection to the ChEBI server fails
    """
    client = ChEBIClient()
    chebi_entity = client.get_entry_by_id(chebi_id)

    if not chebi_entity:
        raise ValueError(f"No data found for ChEBI ID {chebi_id}")

    # Create a SmallMolecule instance
    if smallmol_id is None:
        smallmol_id = process_id(chebi_entity.chebi_ascii_name)

    small_molecule = v2.SmallMolecule(
        id=smallmol_id,
        name=chebi_entity.chebi_ascii_name,
        canonical_smiles=chebi_entity.smiles,
        inchi=chebi_entity.inchi,
        inchikey=chebi_entity.inchikey,
        constant=False,  # Default to non-constant
        vessel_id=vessel_id,
    )

    # Add type term for ChEBI source
    small_molecule.add_type_term(
        term=f"OBO:{chebi_entity.chebi_id.replace(':', '_')}",
        prefix="OBO",
        iri="http://purl.obolibrary.org/obo/",
    )

    # Add LD ID
    small_molecule.ld_id = f"OBO:{chebi_entity.chebi_id.replace(':', '_')}"

    # Add full link as reference
    small_molecule.references.append(
        f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId={chebi_entity.chebi_id}"
    )

    return small_molecule


def process_id(name: str) -> str:
    """
    Process the ID of a ChEBI entity.

    Replaces special characters and intial non-alpha characters with an underscore.
    """
    # Replace non-alphanumeric characters with underscore
    # and then replace multiple consecutive underscores with a single one
    return re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9]+", "_", name)).lower().strip("_")
