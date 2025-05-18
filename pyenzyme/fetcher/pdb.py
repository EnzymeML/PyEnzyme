"""
PDB fetcher for retrieving protein entries by ID and mapping them to the PyEnzyme data model.

This module provides functionality to fetch protein data from the
Protein Data Bank by ID and map it to the PyEnzyme data model (v2).
"""

import requests
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pyenzyme.fetcher.chebi import process_id
from pyenzyme.versions import v2


class Citation(BaseModel):
    """Model for PDB citation data"""

    title: Optional[str] = None
    authors: Optional[List[str]] = None
    journal_name: Optional[str] = Field(default=None, alias="journal_abbrev")
    year: Optional[int] = None
    doi: Optional[str] = None
    pubmed_id: Optional[str] = Field(default=None, alias="pdbx_database_id_PubMed")


class StructInfo(BaseModel):
    """Model for PDB structure information"""

    title: Optional[str] = None
    experimental_method: Optional[str] = None
    resolution: Optional[float] = None


class EntityInfo(BaseModel):
    """Model for PDB entity information"""

    description: Optional[str] = None
    polymer_type: Optional[str] = None
    ec_number: Optional[str] = None
    sequence: Optional[str] = None
    organism_scientific_name: Optional[str] = None
    organism_taxid: Optional[int] = None


class PDBResponse(BaseModel):
    """Model for PDB API response"""

    pdb_id: str
    citation: List[Citation] = []
    struct: Optional[StructInfo] = None
    polymer_entities: Optional[Dict[str, EntityInfo]] = None
    rcsb_primary_citation: Optional[Dict[str, Any]] = None
    rcsb_entry_info: Optional[Dict[str, Any]] = None


class PDBClient:
    """Client for accessing the PDB API"""

    BASE_URL = "https://data.rcsb.org/rest/v1/core"

    def get_entry_by_id(self, pdb_id: str) -> Optional[PDBResponse]:
        """
        Fetch a PDB entry by its ID.

        Args:
            pdb_id: The PDB ID to fetch (e.g., '4HHB')

        Returns:
            PDBResponse object with parsed data or None if not found

        Raises:
            ValueError: If the PDB ID is invalid or not found
            ConnectionError: If the connection to the PDB server fails
        """
        # Ensure PDB ID is uppercase
        pdb_id = pdb_id.upper()

        try:
            # Fetch main entry data
            entry_data = self._fetch_json(f"{self.BASE_URL}/entry/{pdb_id}")

            # Get polymer entity information
            polymer_entities = {}

            # If we have polymer entity IDs, fetch their details
            if entity_ids := entry_data.get("rcsb_entry_container_identifiers", {}).get(
                "polymer_entity_ids"
            ):
                for entity_id in entity_ids:
                    entity_data = self._fetch_json(
                        f"{self.BASE_URL}/polymer_entity/{pdb_id}/{entity_id}"
                    )

                    # Extract entity information
                    polymer_entities[entity_id] = EntityInfo(
                        description=entity_data.get("struct", {}).get(
                            "pdbx_descriptor"
                        ),
                        polymer_type=entity_data.get("entity_poly", {}).get("type"),
                        ec_number=entity_data.get("rcsb_polymer_entity", {}).get(
                            "enzyme_class"
                        ),
                        sequence=entity_data.get("entity_poly", {}).get(
                            "pdbx_seq_one_letter_code"
                        ),
                        organism_scientific_name=entity_data.get(
                            "rcsb_polymer_entity_container_identifiers", {}
                        ).get("taxonomy_organism_scientific_name"),
                        organism_taxid=entity_data.get(
                            "rcsb_polymer_entity_container_identifiers", {}
                        ).get("taxonomy_id"),
                    )

            # Get citation data
            citation = [
                Citation.model_validate(c) for c in entry_data.get("citation", [])
            ]

            # Construct the PDBResponse
            return PDBResponse(
                pdb_id=pdb_id,
                citation=citation,
                struct=StructInfo(
                    title=entry_data.get("struct", {}).get("title"),
                    experimental_method=entry_data.get("rcsb_entry_info", {}).get(
                        "experimental_method"
                    ),
                    resolution=entry_data.get("rcsb_entry_info", {}).get(
                        "resolution_combined", [None]
                    )[0],
                ),
                polymer_entities=polymer_entities,
                rcsb_primary_citation=entry_data.get("rcsb_primary_citation"),
                rcsb_entry_info=entry_data.get("rcsb_entry_info"),
            )

        except ValueError as e:
            raise ValueError(f"Failed to retrieve PDB entry: {str(e)}")
        except ConnectionError as e:
            raise ValueError(f"Connection to PDB server failed: {str(e)}")

    def _fetch_json(self, url: str) -> dict:
        """
        Helper method to fetch and parse JSON from a URL.

        Args:
            url: The URL to fetch data from

        Returns:
            Parsed JSON as a dictionary

        Raises:
            ValueError: If the request fails or returns non-200 status
            ConnectionError: If the connection to the server fails
        """
        try:
            response = requests.get(url)
            response.raise_for_status()

            if response.status_code == 200:
                return response.json()
            else:
                raise ValueError(
                    f"Request failed with status code {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Connection failed: {str(e)}")
        except ValueError as e:
            raise ValueError(f"Failed to parse response: {str(e)}")


def fetch_pdb(
    pdb_id: str,
    protein_id: Optional[str] = None,
    entity_id: str = "1",
    vessel_id: Optional[str] = None,
) -> v2.Protein:
    """
    Fetch a PDB entry by ID and convert it to a Protein object.

    Args:
        pdb_id: The PDB ID to fetch (e.g., '4HHB')
        protein_id: Optional custom ID for the protein (derived from PDB if not provided)
        entity_id: The entity ID within the PDB structure (default is "1")
        vessel_id: The ID of the vessel to add the protein to

    Returns:
        A Protein object with data from PDB

    Raises:
        ValueError: If the PDB ID is invalid or not found
        ConnectionError: If the connection to the PDB server fails
    """
    # Get PDB data
    client = PDBClient()

    # Allow prefixing with 'PDB:'
    if pdb_id.lower().startswith("pdb:"):
        pdb_id = pdb_id.split(":", 1)[-1]

    pdb_response = client.get_entry_by_id(pdb_id)

    if not pdb_response:
        raise ValueError(f"No data found for PDB ID {pdb_id}")

    # Get the entity data
    if not pdb_response.polymer_entities:
        raise ValueError("No polymer entries to fetch from.")

    entity_data = pdb_response.polymer_entities.get(entity_id)

    if not entity_data:
        raise ValueError(f"Entity ID {entity_id} not found in PDB {pdb_id}")

    # Prepare data for Protein object
    # Use entity description or structure title for name
    name = entity_data.description or (
        pdb_response.struct.title
        if pdb_response.struct and pdb_response.struct.title
        else f"PDB {pdb_id}"
    )

    # Generate protein_id if not provided
    if protein_id is None:
        protein_id = (
            process_id(entity_data.description)
            if entity_data.description
            else f"{pdb_id.lower()}_{entity_id}"
        )

    # Create Protein instance
    protein = v2.Protein(
        id=protein_id,
        name=name,
        sequence=entity_data.sequence,
        organism=entity_data.organism_scientific_name,
        organism_tax_id=str(entity_data.organism_taxid)
        if entity_data.organism_taxid
        else None,
        ecnumber=entity_data.ec_number,
        constant=True,
        vessel_id=vessel_id,
    )

    # Add metadata
    protein.add_type_term(
        f"pdb:{pdb_id.upper()}", "pdb", "https://www.rcsb.org/structure/"
    )
    protein.ld_id = f"pdb:{pdb_id.upper()}"

    # Add references
    protein.references.append(f"https://www.rcsb.org/structure/{pdb_id.upper()}")

    # Add citation if available
    if pdb_response.citation and pdb_response.citation[0].doi:
        protein.references.append(f"https://doi.org/{pdb_response.citation[0].doi}")

    if pdb_response.citation and pdb_response.citation[0].pubmed_id:
        protein.references.append(
            f"https://pubmed.ncbi.nlm.nih.gov/{pdb_response.citation[0].pubmed_id}"
        )

    return protein
