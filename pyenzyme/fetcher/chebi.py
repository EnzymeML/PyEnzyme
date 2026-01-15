"""
ChEBI fetcher for retrieving chemical entries by ID.

This module provides functionality to fetch chemical entity data from the
ChEBI database by ID and map it to the PyEnzyme data model (v2).
"""

import re
from typing import List, Optional

import httpx
from pydantic import BaseModel, ConfigDict, Field

from pyenzyme.versions import v2

DEFAULT_TIMEOUT = 5.0


class ChEBIError(Exception):
    """Error class for ChEBI-specific errors."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause


class ChebiSearchSource(BaseModel):
    """Source data structure from ChEBI search API result."""

    model_config = ConfigDict(extra="ignore")

    chebi_accession: str
    name: Optional[str] = None
    ascii_name: str
    smiles: Optional[str] = None
    inchi: Optional[str] = None
    inchikey: Optional[str] = None
    definition: Optional[str] = None
    formula: Optional[str] = None
    charge: Optional[int] = None
    mass: Optional[float] = None
    monoisotopicmass: Optional[float] = None
    stars: Optional[int] = None
    default_structure: Optional[int] = None
    structures: Optional[List[int]] = None


class ChebiSearchResult(BaseModel):
    """Individual search result structure."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    source: ChebiSearchSource = Field(alias="_source")


class ChebiSearchResponse(BaseModel):
    """Search response structure from ChEBI search API."""

    results: List[ChebiSearchResult]
    total: int
    number_pages: int


class ChEBIClient:
    """Client for accessing the ChEBI API to fetch chemical entity data."""

    SEARCH_URL = "https://www.ebi.ac.uk/chebi/backend/api/public/es_search/"

    def __init__(self):
        """Initialize the ChEBI client."""
        pass

    def get_entry_by_id(self, chebi_id: str) -> ChebiSearchSource:
        """
        Fetch a ChEBI entry by its ID using the search API.

        Args:
            chebi_id: The ChEBI ID to fetch, can be with or without the 'CHEBI:' prefix

        Returns:
            ChebiSearchSource object with the parsed response data

        Raises:
            ChEBIError: If the ChEBI ID is invalid or not found
            ChEBIError: If the connection to the ChEBI server fails
        """
        if not chebi_id.startswith("CHEBI:"):
            chebi_id = f"CHEBI:{chebi_id}"

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                params = {"term": chebi_id, "page": "1", "size": "1"}
                response = client.get(self.SEARCH_URL, params=params)
                response.raise_for_status()

            if response.status_code == 200:
                try:
                    search_response = ChebiSearchResponse(**response.json())

                    if not search_response.results or len(search_response.results) == 0:
                        raise ChEBIError(f"No data found for ChEBI ID {chebi_id}")

                    return search_response.results[0].source

                except Exception as e:
                    if isinstance(e, ChEBIError):
                        raise e
                    raise ChEBIError(f"Failed to parse ChEBI response: {str(e)}", e)
            else:
                raise ChEBIError(f"HTTP {response.status_code}: {response.text}")

        except httpx.HTTPStatusError as e:
            raise ChEBIError(f"Failed to fetch ChEBI ID {chebi_id}: {str(e)}", e)

    def get_entries_batch(self, chebi_ids: List[str]) -> List[ChebiSearchSource]:
        """
        Fetch multiple ChEBI entries by their IDs using the search API.

        Args:
            chebi_ids: List of ChEBI IDs to fetch

        Returns:
            List of ChebiSearchSource objects with data from ChEBI

        Raises:
            ChEBIError: If any ChEBI ID is invalid or not found
            ChEBIError: If the connection to the ChEBI server fails
        """
        if not chebi_ids:
            return []

        results = []
        for chebi_id in chebi_ids:
            try:
                entry = self.get_entry_by_id(chebi_id)
                results.append(entry)
            except ChEBIError as e:
                # Continue with other IDs even if one fails
                raise ChEBIError(f"Failed to fetch ChEBI ID {chebi_id}: {str(e)}", e)

        return results

    def search_entries(
        self, query: str, size: Optional[int] = None, page: int = 1
    ) -> List[ChebiSearchSource]:
        """
        Search for ChEBI entries by query string.

        Args:
            query: The search query string to find ChEBI entries
            size: The maximum number of search results to return
            page: The page number to retrieve (default: 1)

        Returns:
            List of ChebiSearchSource objects for matching entries

        Raises:
            ChEBIError: If the search request fails or the API is unavailable
        """
        params = {"term": query, "page": str(page)}
        if size:
            params["size"] = str(size)

        try:
            with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
                response = client.get(self.SEARCH_URL, params=params)
            response.raise_for_status()

            if response.status_code == 200:
                try:
                    search_response = ChebiSearchResponse(**response.json())

                    if not search_response.results:
                        return []

                    return [result.source for result in search_response.results]

                except Exception as e:
                    if isinstance(e, ChEBIError):
                        raise e
                    raise ChEBIError(f"Invalid search response format: {str(e)}", e)
            else:
                raise ChEBIError(
                    f"Search failed: HTTP {response.status_code}: {response.text}"
                )

        except httpx.HTTPStatusError as e:
            raise ChEBIError(f"Failed to search ChEBI: {str(e)}", e)


def process_search_result(source: ChebiSearchSource) -> v2.SmallMolecule:
    """
    Process a ChEBI search result source and convert it to a SmallMolecule object.

    Args:
        source: The ChEBI search result source from the API

    Returns:
        A SmallMolecule object with mapped data
    """
    smallmol_id = process_id(source.ascii_name)

    small_molecule = v2.SmallMolecule(
        id=smallmol_id,
        name=source.ascii_name,
        canonical_smiles=source.smiles,
        inchi=source.inchi,
        inchikey=source.inchikey,
        constant=False,
        vessel_id=None,
        synonymous_names=[],
        references=[
            f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId={source.chebi_accession}"
        ],
    )

    small_molecule.add_type_term(
        term=f"OBO:{source.chebi_accession.replace(':', '_')}",
        prefix="OBO",
        iri="http://purl.obolibrary.org/obo/",
    )

    small_molecule.ld_id = f"OBO:{source.chebi_accession.replace(':', '_')}"

    return small_molecule


def fetch_chebi(
    chebi_id: str,
    smallmol_id: Optional[str] = None,
    vessel_id: Optional[str] = None,
) -> v2.SmallMolecule:
    """
    Fetch a ChEBI entry by ID and convert it to a SmallMolecule object.

    Args:
        chebi_id: The ChEBI ID to fetch
        smallmol_id: Optional custom ID for the small molecule
        vessel_id: The ID of the vessel to add the small molecule to

    Returns:
        A SmallMolecule object with data from ChEBI

    Raises:
        ValueError: If the ChEBI ID is invalid or not found
        ConnectionError: If the connection to the ChEBI server fails
    """
    try:
        client = ChEBIClient()
        chebi_source = client.get_entry_by_id(chebi_id)

        small_molecule = process_search_result(chebi_source)

        if smallmol_id is not None:
            small_molecule.id = smallmol_id
        if vessel_id is not None:
            small_molecule.vessel_id = vessel_id

        return small_molecule
    except ChEBIError as e:
        if "Connection" in str(e) and "400" not in str(e) and "404" not in str(e):
            raise ConnectionError(str(e)) from e
        else:
            raise ValueError(str(e)) from e


def fetch_chebi_batch(chebi_ids: List[str]) -> List[v2.SmallMolecule]:
    """
    Fetch multiple ChEBI entries by their IDs and convert them to SmallMolecule objects.

    Args:
        chebi_ids: List of ChEBI IDs to fetch

    Returns:
        List of SmallMolecule objects with data from ChEBI

    Raises:
        ChEBIError: If any ChEBI ID is invalid or not found
        ChEBIError: If the connection to the ChEBI server fails
    """
    if not chebi_ids:
        return []

    client = ChEBIClient()
    chebi_sources = client.get_entries_batch(chebi_ids)

    return [process_search_result(source) for source in chebi_sources]


def search_chebi(query: str, size: Optional[int] = None) -> List[v2.SmallMolecule]:
    """
    Search for ChEBI entries by query string.

    This function searches the ChEBI database using the EBI search API and returns
    a list of SmallMolecule objects for each matching entry.

    Args:
        query: The search query string to find ChEBI entries
        size: The maximum number of search results to return

    Returns:
        A list of SmallMolecule objects

    Raises:
        ChEBIError: If the search request fails or the API is unavailable

    Example:
        # Search for glucose entries
        glucose_results = search_chebi('glucose', 10)

        # Search for ATP entries
        atp_results = search_chebi('ATP', 5)
    """
    client = ChEBIClient()
    chebi_sources = client.search_entries(query, size)

    return [process_search_result(source) for source in chebi_sources]


def process_id(name: str) -> str:
    """
    Process a name string to create a valid identifier.

    Replaces non-alphanumeric characters with underscores, removes consecutive
    underscores, converts to lowercase, and trims leading/trailing underscores.

    Args:
        name: The name string to process

    Returns:
        A processed identifier string
    """
    return re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9]+", "_", name)).lower().strip("_")
