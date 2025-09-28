import re
from enum import Enum

from pyenzyme import Equation, Reaction, ReactionElement
from pyenzyme.versions.v2 import ModifierElement, ModifierRole

ELEMENT_PATTERN = r"(\d*)\s?([A-Za-z\d]+)"


class EqDirection(Enum):
    """Enum for the type of reaction.

    Returns true if the reaction is reversible, false otherwise.

    Attributes:
        IRREVERSIBLE: A reaction that only goes in one direction.
        REVERSIBLE: A reaction that can go in both directions.
    """

    IRREVERSIBLE = False
    REVERSIBLE = True


def build_reactions(
    *equations: str,
    modifiers: dict[str, list[str]] = {},
) -> list[Reaction]:
    """Builds a list of reaction objects from a list of string representations.

    Args:
        *equations (list[str]): A list of string representations of the reactions
        modifiers (dict[str, list[str]], optional): A dictionary mapping reaction IDs to lists of modifier species IDs.
            Defaults to an empty dictionary.

    Returns:
        list[Reaction]: A list of reaction objects

    Example:
        >>> build_reactions("2A --> B", "A + B <=> C")
        >>> build_reactions("2A --> B", modifiers={"r1": ["E"]})

    Raises:
        ValueError: If the reaction direction is not valid or if a specified modifier reaction ID is not found
        AssertionError: If the species is not set
    """

    reactions = [
        build_reaction(
            id=f"r{i}",
            name=f"Reaction {i}",
            scheme=equation,
        )  # type: ignore
        for i, equation in enumerate(equations, start=1)
    ]

    for id, modifier in modifiers.items():
        try:
            reaction = next(r for r in reactions if r.id == id)
        except StopIteration:
            raise ValueError(f"Reaction with id {id} not found in list of reactions")

        if isinstance(modifier, list):
            reaction.modifiers = [
                ModifierElement(
                    species_id=m,
                    role=ModifierRole.CATALYST,
                )
                for m in modifier
            ]
        else:
            reaction.modifiers = [
                ModifierElement(
                    species_id=modifier,
                    role=ModifierRole.CATALYST,
                )
            ]

    return reactions


def build_reaction(
    name: str,
    scheme: str,
    id: str | None = None,
    kinetic_law: Equation | None = None,
    modifiers: list[str] = [],
):
    """Builds a reaction object from a string representation.

    Args:
        name (str): The name of the reaction
        scheme (str): The equation of the reaction in string format (e.g., "2A --> B")
        id (str | None, optional): The ID of the reaction. If None, the name is used as ID. Defaults to None.
        kinetic_law (Equation | None, optional): The kinetic law associated with the reaction. Defaults to None.
        modifiers (list[str], optional): A list of modifiers (e.g., enzyme IDs) for the reaction. Defaults to [].

    Returns:
        Reaction: A reaction object

    Example:
        >>> build_reaction("Reaction 1", "2A --> B", id="R1") # Irreversible reaction
        >>> build_reaction("Reaction 2", "A + B <=> C", id="R2") # Reversible reaction
        >>> build_reaction("Reaction 2", "A + B <-> C", id="R2") # Reversible reaction

    Raises:
        ValueError: If the reaction direction is not valid
        AssertionError: If the species is not set
    """

    if not id:
        id = name

    left, right, reversible = _extract_left_right(scheme)

    # Initialize and build the reaction object
    mod_objs = [
        ModifierElement(
            species_id=m,
            role=ModifierRole.CATALYST,
        )
        for m in modifiers
    ]
    reaction = Reaction(
        name=name,
        id=id,
        reversible=reversible,
        modifiers=mod_objs,
        kinetic_law=kinetic_law,
    )
    reaction.reactants += _extract_elements(left)
    reaction.products += _extract_elements(right)

    return reaction


def _extract_left_right(reaction: str) -> tuple[str, str, bool]:
    """Extracts the left and right side of a reaction string.

    Args:
        reaction (str): The reaction string (e.g., "A + B -> C")

    Returns:
        tuple[str, str, bool]: A tuple containing the left side, right side, and whether the reaction is reversible

    Raises:
        ValueError: If no valid reaction direction symbol is found in the equation
    """

    if "->" in reaction:
        direction = EqDirection.IRREVERSIBLE
        sep = "->"
    elif "<=>" in reaction:
        direction = EqDirection.REVERSIBLE
        sep = "<=>"
    else:
        raise ValueError(
            "No valid reaction direction found in equation. Use ->, <->, or <=>."
        )

    left, right = reaction.split(sep, 1)

    return left.strip(), right.strip(), direction.value


def _extract_elements(side_string: str) -> list[ReactionElement]:
    """Extracts the elements from a reaction string.

    Args:
        side_string (str): The string representing one side of the reaction (e.g., "2A + B")

    Returns:
        list[ReactionElement]: A list of ReactionElement objects representing the species and their stoichiometries
    """
    elements = []
    for element in side_string.split("+"):
        element = re.search(ELEMENT_PATTERN, element.strip())
        stoich, species = element.groups()  # type: ignore

        elements.append(_create_reaction_element(stoich, species))

    return elements


def _create_reaction_element(
    stoich: str | float,
    species: str,
) -> ReactionElement:
    """Creates a ReactionElement object from stoichiometry, species ID, and equation side.

    Args:
        stoich (str | float): The stoichiometric coefficient (can be a string or float)
        species (str): The species ID

    Returns:
        ReactionElement: A ReactionElement object with the appropriate stoichiometry and species ID

    Raises:
        AssertionError: If the species is not set
    """
    assert species, "Species must be set"

    if stoich == "":
        stoich = 1.0

    return ReactionElement(
        stoichiometry=float(stoich),
        species_id=species,
    )
