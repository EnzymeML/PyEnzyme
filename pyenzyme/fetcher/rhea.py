"""
Rhea database fetcher for retrieving reaction entries by ID.

This module provides functionality to fetch reaction data from the
Rhea database by ID and map it to the PyEnzyme data model (v2).
"""

from io import StringIO
import pandas as pd
from pydantic import BaseModel, ConfigDict
from typing import List, ClassVar, Optional, Tuple

import requests

from pyenzyme.fetcher.chebi import fetch_chebi
from pyenzyme.versions import v2
import re


class RheaResult(BaseModel):
    """
    Result for Rhea database.

    Attributes:
        id: The Rhea ID of the reaction
        equation: The chemical equation of the reaction
        balanced: Whether the reaction is balanced
        transport: Whether the reaction is a transport reaction
    """

    id: str
    equation: str
    balanced: bool
    transport: bool


class RheaQuery(BaseModel):
    """
    Query for Rhea database.

    Attributes:
        count: The number of results returned
        results: List of RheaResult objects
    """

    count: int
    results: List[RheaResult]


class RheaClient(BaseModel):
    """
    Client for Rhea database.

    This class handles communication with the Rhea database API
    and parses the responses into structured data.

    Attributes:
        json_content: The parsed JSON response from Rhea
        chebi_ids: List of ChEBI IDs associated with the reaction
        BASE_URL: The base URL for the Rhea API
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    json_content: RheaResult
    chebi_ids: List[str]

    BASE_URL: ClassVar[str] = (
        "https://www.rhea-db.org/rhea/?query=RHEA:{0}&columns=rhea-id,equation,chebi-id&format={1}&limit=10"
    )

    @classmethod
    def from_id(cls, rhea_id: str) -> "RheaClient":
        """
        Create a RheaClient instance from a Rhea ID.

        Args:
            rhea_id: The Rhea ID to fetch, can be with or without the 'RHEA:' prefix

        Returns:
            A RheaClient instance with the fetched data

        Raises:
            ValueError: If no results are found for the given Rhea ID
        """
        if rhea_id.startswith("RHEA:"):
            rhea_id = rhea_id.split(":")[-1]

        tsv_content = cls.fetch_tsv(rhea_id)
        json_content = cls.fetch_json(rhea_id)

        if len(json_content.results) == 0:
            raise ValueError(f"No results found for RHEA ID: {rhea_id}")

        # Get first row of tsv_content
        entry = tsv_content.iloc[0]

        return cls(
            json_content=json_content.results[0],
            chebi_ids=entry["ChEBI identifier"].split(";"),
        )

    @staticmethod
    def fetch_tsv(query: str) -> pd.DataFrame:
        """
        Fetch TSV data from the Rhea API.

        Args:
            query: The Rhea ID to query

        Returns:
            A pandas DataFrame containing the TSV response

        Raises:
            HTTPError: If the request to the Rhea API fails
        """
        response = requests.get(RheaClient.BASE_URL.format(query, "tsv"))
        response.raise_for_status()

        return pd.read_csv(StringIO(response.text), sep="\t")

    @staticmethod
    def fetch_json(query: str) -> RheaQuery:
        """
        Fetch JSON data from the Rhea API.

        Args:
            query: The Rhea ID to query

        Returns:
            A RheaQuery object containing the parsed JSON response

        Raises:
            HTTPError: If the request to the Rhea API fails
        """
        response = requests.get(RheaClient.BASE_URL.format(query, "json"))
        response.raise_for_status()

        return RheaQuery.model_validate(response.json())


def fetch_rhea(
    rhea_id: str,
    vessel_id: Optional[str] = None,
) -> Tuple[v2.Reaction, List[v2.SmallMolecule]]:
    """
    Fetch a Rhea entry by ID and convert it to a Reaction object.

    This function retrieves reaction data from the Rhea database and
    converts it to the PyEnzyme data model, including fetching all
    associated small molecules from ChEBI.

    Args:
        rhea_id: The Rhea ID to fetch, can be with or without the 'RHEA:' prefix
        vessel_id: The ID of the vessel to add the small molecules to
    Returns:
        A tuple containing:
            - A Reaction object with data from Rhea
            - A list of SmallMolecule objects for all reactants and products

    Raises:
        ValueError: If the Rhea ID is invalid or not found
        ConnectionError: If the connection to the Rhea server fails
    """
    client = RheaClient.from_id(rhea_id)
    rhea_id = client.json_content.id

    equation = client.json_content.equation

    # Split equation into reactants and products sides
    equation_sides = equation.split("=")
    reactant_species = _split_chemical_equation_side(equation_sides[0])
    product_species = _split_chemical_equation_side(equation_sides[1])

    n_reactants = len(reactant_species)
    n_products = len(product_species)

    small_molecules = []
    reactants = []
    products = []

    # Process each chemical species in the reaction
    for i in range(n_reactants + n_products):
        small_molecule = fetch_chebi(
            client.chebi_ids[i],
            vessel_id=vessel_id,
        )
        small_molecules.append(small_molecule)

        if i < n_reactants:
            reaction_element = v2.ReactionElement(
                species_id=small_molecule.id,
                stoichiometry=1,
            )
            reactants.append(reaction_element)
        else:
            reaction_element = v2.ReactionElement(
                species_id=small_molecule.id,
                stoichiometry=1,
            )
            products.append(reaction_element)

    reaction = v2.Reaction(
        id=f"RHEA:{client.json_content.id}",
        name=f"RHEA:{rhea_id}",
        reactants=reactants,
        products=products,
        reversible=client.json_content.balanced,
    )

    # Add semantic annotations
    reaction.add_type_term(
        term=f"rhea:{rhea_id}",
        prefix="rhea",
        iri="http://www.rhea-db.org/rhea/",
    )

    # Set linked data identifier
    reaction.ld_id = f"rhea:{rhea_id}"

    return reaction, small_molecules


def _split_chemical_equation_side(equation_side: str) -> List[str]:
    """
    Split a chemical equation side on '+' while respecting parentheses.

    This function properly handles chemical formulas like 'NAD(+)' and 'H(+)'
    where the '+' is part of the chemical formula, not a separator.

    Args:
        equation_side: One side of a chemical equation (e.g., "ethanol + NAD(+)")

    Returns:
        List of chemical species as strings
    """
    # Use regex to split on '+' that are not inside parentheses
    # This pattern matches '+' that are not preceded by an opening parenthesis
    # without a closing parenthesis in between
    pattern = r"\+(?![^()]*\))"
    species = re.split(pattern, equation_side)
    return [species.strip() for species in species if species.strip()]
