import re
from enum import Enum

from pyenzyme.model import Equation, ReactionElement, Reaction

ELEMENT_PATTERN = r"(\d*)\s?([A-Za-z\d]+)"


class EquationSide(Enum):
    LEFT = -1
    RIGHT = 1


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

    Returns:
        list[Reaction]: A list of reaction objects

    Example:
        >> reactions("2A --> B", "A + B <=> C")

    Raises:
        ValueError: If the reaction direction is not valid
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

        reaction.modifiers = modifier

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
        id (str): The id of the reaction
        name (str): The name of the reaction
        scheme (str): The equation of the reaction
        modifiers (list[str], optional): A list of modifiers for the reaction. Defaults to [].

    Returns:
        Reaction: A reaction object

    Example:

        >> reaction("R1", "Reaction 1", "2A --> B") # Irrversible reaction
        >> reaction("R2", "Reaction 2", "A + B <=> C") # Reversible reaction
        >> reaction("R2", "Reaction 2", "A + B <-> C") # Reversible reaction

    Raises:
        ValueError: If the reaction direction is not valid
        AssertionError: If the species is not set

    """

    if not id:
        id = name

    left, right, reversible = _extract_left_right(scheme)

    # Initialize and build the reaction object
    reaction = Reaction(
        name=name,
        id=id,
        reversible=reversible,
        modifiers=modifiers,
    )
    reaction.species += _extract_elements(left, EquationSide.LEFT)
    reaction.species += _extract_elements(right, EquationSide.RIGHT)

    return reaction


def _extract_left_right(reaction: str) -> tuple[str, str, bool]:
    """Extracts the left and right side of a reaction string.

    Args:
        reaction (str): The reaction string

    Returns:
        tuple[str, str, bool]: A tuple containing the left side, right side, and the reaction direction
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


def _extract_elements(side_string: str, side: EquationSide) -> list[ReactionElement]:
    """Extracts the elements from a reaction string."""
    elements = []
    for element in side_string.split("+"):
        element = re.search(ELEMENT_PATTERN, element.strip())
        stoich, species = element.groups()  # type: ignore

        elements.append(_create_reaction_element(stoich, species, side))

    return elements


def _create_reaction_element(
    stoich: str | float,
    species: str,
    side: EquationSide,
) -> ReactionElement:
    assert species, "Species must be set"

    if stoich == "":
        stoich = 1.0

    return ReactionElement(
        stoichiometry=float(stoich) * side.value,
        species_id=species,
    )
