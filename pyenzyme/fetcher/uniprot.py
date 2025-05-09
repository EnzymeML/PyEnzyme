"""
UniProt fetcher for retrieving protein entries by ID.

This module provides functionality to fetch protein data from the
UniProt database by ID and map it to the PyEnzyme data model (v2).
"""

import requests
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from pyenzyme.fetcher.chebi import process_id
from pyenzyme.versions import v2


class ECNumber(BaseModel):
    """Model for EC number in UniProt API"""

    value: str


class ProteinName(BaseModel):
    """Model for protein name in UniProt API"""

    value: str


class RecommendedName(BaseModel):
    """Model for recommended protein name in UniProt API"""

    full_name: ProteinName = Field(alias="fullName")
    ec_numbers: Optional[List[ECNumber]] = Field(alias="ecNumbers")


class ProteinDescription(BaseModel):
    """Model for protein description in UniProt API"""

    recommended_name: Optional[RecommendedName] = Field(alias="recommendedName")


class Organism(BaseModel):
    """Model for organism in UniProt API"""

    scientific_name: Optional[str] = Field(alias="scientificName")
    taxon_id: Optional[int] = Field(alias="taxonId")


class Sequence(BaseModel):
    """Model for protein sequence in UniProt API"""

    value: str
    length: int
    mol_weight: Optional[int] = Field(alias="molWeight")


class UniProtEntry(BaseModel):
    """
    Model for a UniProt entry response.
    """

    id: str = Field(alias="uniProtkbId")
    protein_description: ProteinDescription = Field(alias="proteinDescription")
    organism: Optional[Organism] = None
    sequence: Optional[Sequence] = None
    accession: str = Field(alias="primaryAccession")
    annotation_score: Optional[float] = Field(alias="annotationScore")


class UniProtClient:
    """Client for accessing the UniProt API to fetch protein data."""

    BASE_URL = "https://rest.uniprot.org/uniprotkb"

    def __init__(self):
        """Initialize the UniProt client."""
        pass

    def get_entry_by_id(self, uniprot_id: str) -> Union[UniProtEntry, None]:
        """
        Fetch a UniProt entry by its ID.

        Args:
            uniprot_id: The UniProt ID to fetch

        Returns:
            UniProtEntry object with the parsed response data

        Raises:
            ValueError: If the UniProt ID is invalid or not found
            ConnectionError: If the connection to the UniProt server fails
        """
        # Construct the URL
        url = f"{self.BASE_URL}/{uniprot_id}.json"

        try:
            response = requests.get(url)
            response.raise_for_status()

            if response.status_code == 200:
                try:
                    data = response.json()
                    return UniProtEntry.model_validate(data)
                except Exception as e:
                    raise ValueError(f"Failed to parse UniProt response: {str(e)}")
            else:
                raise ValueError(
                    f"Failed to retrieve UniProt entry for ID {uniprot_id}"
                )

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Connection to UniProt server failed: {str(e)}")


def fetch_uniprot(
    uniprot_id: str,
    protein_id: Optional[str] = None,
    vessel_id: Optional[str] = None,
) -> v2.Protein:
    """
    Fetch a UniProt entry by ID and convert it to a Protein object.

    Args:
        uniprot_id: The UniProt ID to fetch
        vessel_id: The ID of the vessel to add the protein to
    Returns:
        A Protein object with data from UniProt

    Raises:
        ValueError: If the UniProt ID is invalid or not found
        ConnectionError: If the connection to the UniProt server fails
    """
    client = UniProtClient()

    # Allow prefixing with 'uniprot:'
    if uniprot_id.lower().startswith("uniprot:"):
        uniprot_id = uniprot_id.split(":", 1)[-1]

    uniprot_entry = client.get_entry_by_id(uniprot_id)

    if not uniprot_entry:
        raise ValueError(f"No data found for UniProt ID {uniprot_id}")

    # Extract protein name
    name = uniprot_id
    if (
        uniprot_entry.protein_description
        and uniprot_entry.protein_description.recommended_name
        and uniprot_entry.protein_description.recommended_name.full_name
    ):
        name = uniprot_entry.protein_description.recommended_name.full_name.value

    # Extract sequence if available
    sequence = None
    if uniprot_entry.sequence:
        sequence = uniprot_entry.sequence.value

    # Extract organism data
    organism = None
    organism_tax_id = None
    if uniprot_entry.organism:
        organism = uniprot_entry.organism.scientific_name
        if uniprot_entry.organism.taxon_id is not None:
            organism_tax_id = str(uniprot_entry.organism.taxon_id)

    # Extract EC number
    ecnumber = None
    if (
        uniprot_entry.protein_description
        and uniprot_entry.protein_description.recommended_name
        and uniprot_entry.protein_description.recommended_name.ec_numbers
        and len(uniprot_entry.protein_description.recommended_name.ec_numbers) > 0
    ):
        ecnumber = uniprot_entry.protein_description.recommended_name.ec_numbers[
            0
        ].value

    # Create a Protein instance
    if protein_id is None:
        if (
            uniprot_entry.protein_description
            and uniprot_entry.protein_description.recommended_name
            and uniprot_entry.protein_description.recommended_name.full_name
        ):
            protein_id = process_id(
                uniprot_entry.protein_description.recommended_name.full_name.value
            )
        else:
            protein_id = uniprot_entry.accession

    protein = v2.Protein(
        id=protein_id,
        name=name,
        sequence=sequence,
        organism=organism,
        organism_tax_id=organism_tax_id,
        ecnumber=ecnumber,
        constant=True,  # Default to constant
        vessel_id=vessel_id,
    )

    # Add type term for UniProt source
    protein.add_type_term(
        f"uniprot:{uniprot_entry.accession}",
        "uniprot",
        "https://www.uniprot.org/uniprotkb/",
    )

    # Add LD ID
    protein.ld_id = f"uniprot:{uniprot_entry.accession}"

    # Add full link as reference
    protein.references.append(
        f"https://www.uniprot.org/uniprotkb/{uniprot_entry.accession}"
    )

    return protein
