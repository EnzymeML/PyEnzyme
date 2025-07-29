import re
from typing import List, Optional, Tuple, Callable, Any

from rich.console import Console

from pyenzyme.fetcher.chebi import fetch_chebi
from pyenzyme.fetcher.pdb import fetch_pdb
from pyenzyme.fetcher.pubchem import fetch_pubchem
from pyenzyme.fetcher.rhea import fetch_rhea
from pyenzyme.fetcher.uniprot import fetch_uniprot
from pyenzyme.versions import v2

PROTEIN_FETCHERS = [
    fetch_uniprot,
    fetch_pdb,
]

SMALL_MOLECULE_FETCHERS = [
    fetch_pubchem,
    fetch_chebi,
]

REACTION_FETCHERS = [
    fetch_rhea,
]

console = Console()


def compose(
    name: str,
    proteins: Optional[list[str]] = None,
    small_molecules: Optional[list[str]] = None,
    reactions: Optional[list[str]] = None,
    vessel: Optional[v2.Vessel] = None,
    id_mapping: Optional[dict[str, str]] = None,
) -> v2.EnzymeMLDocument:
    """
    Compose an EnzymeML document from proteins, small molecules, and reactions.

    Args:
        name: Name of the EnzymeML document
        proteins: List of protein identifiers to fetch
        small_molecules: List of small molecule identifiers to fetch
        reactions: List of reaction identifiers to fetch
        vessel: Optional vessel to associate with the entities

    Returns:
        A complete EnzymeML document with fetched entities
    """

    proteins = proteins or []
    small_molecules = small_molecules or []
    reactions = reactions or []

    protein_objects = []
    small_molecule_objects = []
    reaction_objects = []
    small_molecule_reaction_objects = []

    # Fetch proteins
    if proteins:
        with console.status("[bold cyan]Fetching proteins...") as status:
            protein_objects = [_fetch_protein(p) for p in proteins]
            status.update("[bold cyan]Proteins fetched successfully")
        console.print("[bold green]Proteins fetched successfully")

    # Fetch small molecules
    if small_molecules:
        with console.status("[bold cyan]Fetching small molecules...") as status:
            small_molecule_objects = [
                _fetch_small_molecule(sm) for sm in small_molecules
            ]
            status.update("[bold cyan]Small molecules fetched successfully")
        console.print("[bold green]Small molecules fetched successfully")

    # Fetch reactions
    if reactions:
        with console.status("[bold cyan]Fetching reactions...") as status:
            for r in reactions:
                reaction, smallmols = _fetch_reaction(r)
                reaction_objects.append(reaction)
                small_molecule_reaction_objects.extend(smallmols)
            status.update("[bold cyan]Reactions fetched successfully")
        console.print("[bold green]Reactions fetched successfully")

    # Merge small molecules from reactions with explicitly provided ones
    small_molecule_objects.extend(small_molecule_reaction_objects)

    # Remove duplicates
    small_molecule_objects = _remove_duplicates(small_molecule_objects)
    protein_objects = _remove_duplicates(protein_objects)
    reaction_objects = _remove_duplicates(reaction_objects)

    # Sort by ID
    small_molecule_objects.sort(key=lambda x: x.id)
    protein_objects.sort(key=lambda x: x.id)
    reaction_objects.sort(key=lambda x: x.id)

    if id_mapping:
        small_molecule_objects = _apply_id_mapping(
            small_molecule_objects,
            id_mapping,
            r"CHEBI|PUBCHEM",
        )
        protein_objects = _apply_id_mapping(
            protein_objects,
            id_mapping,
            r"UNIPROT|PDB",
        )
        reaction_objects = _apply_id_mapping(
            reaction_objects,
            id_mapping,
            r"RHEA",
        )

    # Set vessel IDs if vessel is provided
    vessels = []
    if vessel:
        for item in small_molecule_objects + protein_objects:
            item.vessel_id = vessel.id
        vessels = [vessel]

    return v2.EnzymeMLDocument(
        name=name,
        proteins=protein_objects,
        small_molecules=small_molecule_objects,
        reactions=reaction_objects,
        vessels=vessels,
    )


def _fetch_protein(protein_id: str) -> v2.Protein:
    """
    Fetch protein information using available fetchers.

    Args:
        protein_id: Identifier for the protein to fetch

    Returns:
        Protein object with fetched data

    Raises:
        ValueError: If no fetcher can handle the given protein ID
    """
    return _fetch_with_fetchers(protein_id, PROTEIN_FETCHERS, "protein")


def _fetch_small_molecule(small_molecule_id: str) -> v2.SmallMolecule:
    """
    Fetch small molecule information using available fetchers.

    Args:
        small_molecule_id: Identifier for the small molecule to fetch

    Returns:
        SmallMolecule object with fetched data

    Raises:
        ValueError: If no fetcher can handle the given small molecule ID
    """
    return _fetch_with_fetchers(
        small_molecule_id, SMALL_MOLECULE_FETCHERS, "small molecule"
    )


def _fetch_reaction(reaction_id: str) -> Tuple[v2.Reaction, List[v2.SmallMolecule]]:
    """
    Fetch reaction information using available fetchers.

    Args:
        reaction_id: Identifier for the reaction to fetch

    Returns:
        Tuple containing the Reaction object and a list of associated SmallMolecule objects

    Raises:
        ValueError: If no fetcher can handle the given reaction ID
    """
    return _fetch_with_fetchers(reaction_id, REACTION_FETCHERS, "reaction")


def _fetch_with_fetchers(
    entity_id: str, fetchers: List[Callable], entity_type: str
) -> Any:
    """
    Generic function to attempt fetching with multiple fetchers.

    Args:
        entity_id: Identifier for the entity to fetch
        fetchers: List of fetcher functions to try
        entity_type: Type of entity being fetched (for error message)

    Returns:
        Fetched entity data

    Raises:
        ValueError: If no fetcher can handle the given entity ID
    """
    for fetcher in fetchers:
        try:
            return fetcher(entity_id)
        except Exception:
            continue

    fetcher_names = ", ".join(f.__name__ for f in fetchers)
    raise ValueError(
        f"No {entity_type} fetcher found for {entity_id}. "
        f"Supported fetchers: {fetcher_names}"
    )


def _remove_duplicates(objects: List[Any]) -> List[Any]:
    """
    Remove duplicate objects based on their ID attribute.

    Args:
        objects: List of objects to deduplicate

    Returns:
        List of unique objects
    """
    ids = set()
    unique_objects = []

    for obj in objects:
        if not hasattr(obj, "id"):
            continue

        if obj.id not in ids:
            ids.add(obj.id)
            unique_objects.append(obj)

    return unique_objects


def _apply_id_mapping(
    objects: List[Any],
    id_mapping: dict[str, str],
    prefix: str,
) -> List[Any]:
    """
    Apply ID mapping to objects based on the provided mapping.

    Args:
        objects: List of objects to apply ID mapping to
        id_mapping: Dictionary mapping old IDs to new IDs
        prefix: Regex pattern to match ID prefixes

    Returns:
        List of objects with updated IDs
    """
    for obj in objects:
        key = next(
            (
                k
                for k in id_mapping
                if re.sub(prefix + ":", "", k) in obj.ld_id.replace("_", ":")
            ),
            None,
        )
        if key:
            obj.id = id_mapping[key]

    return objects
