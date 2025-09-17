"""
ChEBI fetcher for retrieving chemical entries by ID.

This module provides functionality to fetch chemical entity data from the
ChEBI database by ID and map it to the PyEnzyme data model (v2).
"""

import requests
import re
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, RootModel
from pyenzyme.versions import v2


class ChEBIError(Exception):
    """Error class for ChEBI-specific errors."""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause


class ChEBIName(BaseModel):
    """Individual name/synonym entry."""

    name: str
    status: str
    type: str
    source: str
    ascii_name: str
    adapted: bool
    language_code: str


class ChEBINames(BaseModel):
    """Names and synonyms structure. All name types are optional."""

    SYNONYM: Optional[List[ChEBIName]] = None
    IUPAC_NAME: Optional[List[ChEBIName]] = Field(None, alias="IUPAC NAME")
    INN: Optional[List[ChEBIName]] = None


class ChEBIChemicalData(BaseModel):
    """Chemical formula and mass data."""

    formula: str
    charge: int
    mass: str
    monoisotopic_mass: str


class ChEBIStructure(BaseModel):
    """Chemical structure information. All structure fields may be null."""

    id: int
    smiles: Optional[str] = None
    standard_inchi: Optional[str] = None
    standard_inchi_key: Optional[str] = None
    wurcs: Optional[str] = None
    is_r_group: bool


class ChEBIEntryData(BaseModel):
    """Core data structure for a ChEBI entry."""

    id: int
    chebi_accession: str
    name: str
    ascii_name: str
    stars: int
    definition: str
    names: ChEBINames
    chemical_data: ChEBIChemicalData
    default_structure: Optional[ChEBIStructure] = None
    modified_on: str
    secondary_ids: List[str]
    is_released: bool


class ChEBIEntryResult(BaseModel):
    """Individual ChEBI entry result."""

    standardized_chebi_id: str
    primary_chebi_id: str
    exists: bool
    id_type: str
    data: ChEBIEntryData


class ChEBIApiResponse(RootModel[Dict[str, ChEBIEntryResult]]):
    """Top-level response structure from ChEBI API. Maps ChEBI IDs to their corresponding entry data."""

    root: Dict[str, ChEBIEntryResult]


class ChebiSearchResult(BaseModel):
    """Individual search result structure."""

    _source: Dict[str, str]  # Contains chebi_accession field


class ChebiSearchResponse(BaseModel):
    """Search response structure from ChEBI search API."""

    results: List[ChebiSearchResult]


class ChEBIClient:
    """Client for accessing the ChEBI API to fetch chemical entity data."""

    BASE_URL = "https://www.ebi.ac.uk/chebi/backend/api/public/compounds/"
    SEARCH_URL = "https://www.ebi.ac.uk/chebi/backend/api/public/es_search/"

    def __init__(self):
        """Initialize the ChEBI client."""
        pass

    def get_entry_by_id(self, chebi_id: str) -> ChEBIEntryResult:
        """
        Fetch a ChEBI entry by its ID.

        Args:
            chebi_id: The ChEBI ID to fetch, can be with or without the 'CHEBI:' prefix

        Returns:
            ChEBIEntryResult object with the parsed response data

        Raises:
            ChEBIError: If the ChEBI ID is invalid or not found
            ChEBIError: If the connection to the ChEBI server fails
        """
        if not chebi_id.startswith("CHEBI:"):
            chebi_id = f"CHEBI:{chebi_id}"

        try:
            response = requests.get(self.BASE_URL, params={"chebi_ids": chebi_id})
            response.raise_for_status()

            if response.status_code == 200:
                try:
                    raw_response_data = response.json()

                    if not raw_response_data or len(raw_response_data) == 0:
                        raise ChEBIError(f"No data found for ChEBI ID {chebi_id}")

                    chebi_response = ChEBIApiResponse(raw_response_data)

                    entry = list(chebi_response.root.values())[0]
                    return entry

                except Exception as e:
                    if isinstance(e, ChEBIError):
                        raise e
                    raise ChEBIError(f"Failed to parse ChEBI response: {str(e)}", e)
            else:
                raise ChEBIError(f"HTTP {response.status_code}: {response.reason}")

        except requests.exceptions.RequestException as e:
            raise ChEBIError(f"Failed to fetch ChEBI ID {chebi_id}: {str(e)}", e)

    def get_entries_batch(self, chebi_ids: List[str]) -> List[ChEBIEntryResult]:
        """
        Fetch multiple ChEBI entries by their IDs.

        Args:
            chebi_ids: List of ChEBI IDs to fetch

        Returns:
            List of ChEBIEntryResult objects with data from ChEBI

        Raises:
            ChEBIError: If any ChEBI ID is invalid or not found
            ChEBIError: If the connection to the ChEBI server fails
        """
        if not chebi_ids:
            return []

        formatted_ids = []
        for chebi_id in chebi_ids:
            if not chebi_id.startswith("CHEBI:"):
                formatted_ids.append(f"CHEBI:{chebi_id}")
            else:
                formatted_ids.append(chebi_id)

        try:
            response = requests.get(
                self.BASE_URL, params={"chebi_ids": ",".join(formatted_ids)}
            )
            response.raise_for_status()

            if response.status_code == 200:
                try:
                    raw_response_data = response.json()
                    chebi_response = ChEBIApiResponse(raw_response_data)
                    return list(chebi_response.root.values())

                except Exception as e:
                    raise ChEBIError(
                        f"Failed to parse ChEBI batch response: {str(e)}", e
                    )
            else:
                raise ChEBIError(f"HTTP {response.status_code}: {response.reason}")

        except requests.exceptions.RequestException as e:
            raise ChEBIError(f"Failed to fetch ChEBI batch: {str(e)}", e)

    def search_entries(
        self, query: str, size: Optional[int] = None
    ) -> List[ChEBIEntryResult]:
        """
        Search for ChEBI entries by query string.

        Args:
            query: The search query string to find ChEBI entries
            size: The maximum number of search results to return

        Returns:
            List of ChEBIEntryResult objects for matching entries

        Raises:
            ChEBIError: If the search request fails or the API is unavailable
        """
        params = {"term": query}
        if size:
            params["size"] = str(size)

        try:
            response = requests.get(self.SEARCH_URL, params=params)
            response.raise_for_status()

            if response.status_code == 200:
                try:
                    search_results = ChebiSearchResponse(**response.json())

                    if not search_results.results:
                        return []

                    chebi_ids = [
                        result._source["chebi_accession"]
                        for result in search_results.results
                    ]

                    return self.get_entries_batch(chebi_ids)

                except Exception as e:
                    if isinstance(e, ChEBIError):
                        raise e
                    raise ChEBIError(f"Invalid search response format: {str(e)}", e)
            else:
                raise ChEBIError(
                    f"Search failed: HTTP {response.status_code}: {response.reason}"
                )

        except requests.exceptions.RequestException as e:
            raise ChEBIError(f"Failed to search ChEBI: {str(e)}", e)


def process_chebi_entry(entry: ChEBIEntryResult) -> v2.SmallMolecule:
    """
    Process a ChEBI entry result and convert it to a SmallMolecule object.

    Args:
        entry: The ChEBI entry result from the API

    Returns:
        A SmallMolecule object with mapped data
    """
    smallmol_id = process_id(entry.data.ascii_name)

    structure = entry.data.default_structure
    canonical_smiles = structure.smiles if structure else None
    inchi = structure.standard_inchi if structure else None
    inchikey = structure.standard_inchi_key if structure else None

    small_molecule = v2.SmallMolecule(
        id=smallmol_id,
        name=entry.data.ascii_name,
        canonical_smiles=canonical_smiles,
        inchi=inchi,
        inchikey=inchikey,
        constant=False,
        vessel_id=None,
        synonymous_names=[],
        references=[
            f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId={entry.standardized_chebi_id}"
        ],
    )

    small_molecule.add_type_term(
        term=f"OBO:{entry.standardized_chebi_id.replace(':', '_')}",
        prefix="OBO",
        iri="http://purl.obolibrary.org/obo/",
    )

    small_molecule.ld_id = f"OBO:{entry.standardized_chebi_id.replace(':', '_')}"

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
        chebi_entry = client.get_entry_by_id(chebi_id)

        small_molecule = process_chebi_entry(chebi_entry)

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
    chebi_entries = client.get_entries_batch(chebi_ids)

    return [process_chebi_entry(entry) for entry in chebi_entries]


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
    chebi_entries = client.search_entries(query, size)

    return [process_chebi_entry(entry) for entry in chebi_entries]


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
