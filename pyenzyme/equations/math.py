import re

import rich
from loguru import logger
from sympy import sympify

from pyenzyme.logging import add_logger
from mdmodels.units.unit_definition import UnitDefinition
from pyenzyme.versions.v2 import (
    EnzymeMLDocument,
    Equation,
    EquationType,
    Variable,
)

# Regular expression patterns for parsing different parts of equations
INIT_ASSIGNMENT_PATTERN = (
    r"^[A-Za-z][A-Za-z\_]*"  # Pattern for initial assignment variables
)
DERIVATIVE_PATTERN = r"([A-Za-z0-9\_]+)\'\(t\)"  # Pattern for derivatives like x'(t)
VARIABLE_PATTERN = (
    r"([A-Za-z0-9\_]+)\'?\(t\)"  # Pattern for variables like x(t) or x'(t)
)
PARAMETER_PATTERN = r"([A-Za-z0-9\_]+)"  # Pattern for parameter names
REPLACE_PATTERN = r"\(t\)|\'"  # Pattern for replacing (t) or ' in variables
ELEMENTAL_FUNCTIONS = [
    "exp",
    "log",
    "sin",
    "cos",
    "tan",
    "sqrt",
    "abs",
]  # Built-in mathematical functions


def build_equations(
    *equations: str,
    unit_mapping: dict[str, str] | None = None,
    enzmldoc: EnzymeMLDocument,
    equation_type: EquationType | None = None,
) -> list[Equation]:
    """Builds a list of Equation objects from a list of string representations.

    This function takes multiple equation strings and converts each one into an Equation object.
    It handles different types of equations including ODEs, assignments, and initial assignments.

    Args:
        *equations (list[str]): A list of string representations of the equations
        unit_mapping: A dictionary mapping parameter names to their respective units
        enzmldoc (EnzymeMLDocument): The EnzymeMLDocument to add the parameters to

    Returns:
        list[Equation]: A list of Equation objects

    Example:
        >>> build_equations("s1'(t) = 2 * s2(t)", "s2'(t) = 3 * s1(t)")
    """

    if unit_mapping is None:
        unit_mapping = {}

    assert all(isinstance(eq, str) for eq in equations), "All equations must be strings"

    return [
        build_equation(
            equation=eq,
            unit_mapping=unit_mapping,
            enzmldoc=enzmldoc,
            equation_type=equation_type,
        )
        for eq in equations
    ]  # type: ignore


def build_equation(
    equation: str,
    enzmldoc: EnzymeMLDocument,
    equation_type: EquationType | None = None,
    unit_mapping: dict[str, str] | None = None,
) -> Equation:
    """Builds an equation object from a string representation.

    This function takes an equation string and converts it into an Equation object.
    It identifies the equation type (ODE, assignment, or initial assignment) based on the pattern,
    extracts variables and parameters, and creates the appropriate Equation object.

    Equation types can be explicitly provided, otherwise they will be inferred from the equation, following the following rules:

    - ODE: y'(t) = 2 * x
    - Assignment: y(t) = 2 * x
    - Initial Assignment: y = 2 * x
    - Rate Law: 2 * x (no left-hand side)

    Args:
        equation (str): The equation to be converted into an Equation object
        enzmldoc (EnzymeMLDocument): The EnzymeMLDocument to add the parameters to
        unit_mapping: A dictionary mapping parameter names to their respective units

    Returns:
        Equation: The created Equation object

    Example:
        >>> eq = "s1'(t) = 2 * s2(t)"
        >>> equation = build_equation(eq, enzmldoc)

    Raises:
        ValueError: If the equation type is not recognized or if the equation is malformed
    """

    if unit_mapping is None:
        unit_mapping = {}

    left, right = _extract_sides(equation)

    if equation_type is None:
        if bool(re.match(DERIVATIVE_PATTERN, left)):
            equation_type = EquationType.ODE
        elif bool(re.match(VARIABLE_PATTERN, left)):
            equation_type = EquationType.ASSIGNMENT
        elif bool(re.match(INIT_ASSIGNMENT_PATTERN, left)):
            equation_type = EquationType.INITIAL_ASSIGNMENT
        elif left.strip() == "":
            equation_type = EquationType.RATE_LAW
        else:
            rich.print(
                "\n".join(
                    [
                        "Cannot infer equation type. There are three types equations that follow a certain pattern:\n",
                        "  [bold]1. ODE: y'(t) = 2 * x[/bold]",
                        "  [bold]2. Assignment: y(t) = 2 * x[/bold]",
                        "  [bold]3. Initial Assignment: y = 2 * x[/bold]",
                        "\nPlease make sure your equation follows one of these patterns or explicitly provide the equation type.\n",
                    ]
                )
            )
            raise ValueError("Equation type not recognized")

    right = sympify(_clean_and_trim(right))
    left = _clean_and_trim(left)
    all_ids = _extract_all_ids(enzmldoc)
    variables = {str(symbol) for symbol in right.free_symbols if str(symbol) in all_ids}
    parameters = {
        str(symbol) for symbol in right.free_symbols if str(symbol) not in all_ids
    }

    if equation_type == EquationType.ASSIGNMENT:
        parameters = parameters.union({left})

    eq = Equation(
        species_id=left,
        equation=str(right),
        variables=[_create_variable(name) for name in variables],
        equation_type=equation_type,
    )

    [
        _add_to_parameters(
            enzmldoc,
            param,
            unit_mapping.get(param, None),
        )
        for param in parameters
    ]

    return eq


def _extract_sides(equation: str) -> tuple[str, str]:
    """Extracts the left and right sides of an equation.

    Args:
        equation (str): The equation string to parse

    Returns:
        tuple[str, str]: A tuple containing the left and right sides of the equation

    Raises:
        ValueError: If the equation is missing a left or right side
    """
    if "=" not in equation:
        # Will be handled as a kinetic law
        return "", equation

    left, right, *_ = equation.split("=")

    if right == "":
        raise ValueError("Equation must contain a right-hand side")
    if left == "":
        raise ValueError("Equation must contain a left-hand side")

    return left, right


def _clean_and_trim(eq: str) -> str:
    """Cleans and trims an equation string by removing time dependencies.

    This function removes the time dependency notation (t) from variables
    and simplifies the equation representation.

    Args:
        eq (str): The equation string to clean

    Returns:
        str: The cleaned equation string
    """
    vars = re.findall(VARIABLE_PATTERN, eq)
    for var in vars:
        var = var.replace("'", "")
        if var not in ELEMENTAL_FUNCTIONS:
            eq = re.sub(rf"{var}\'?\(t\)", var, eq)

    return eq.strip()


def _create_variable(name: str) -> Variable:
    """Creates a Variable object with the given name.

    Args:
        name (str): The name of the variable

    Returns:
        Variable: The created Variable object
    """
    return Variable(id=name, name=name, symbol=name)


def _add_to_parameters(
    enzmldoc: EnzymeMLDocument,
    name: str,
    unit: str | UnitDefinition | None,
):
    """Adds a parameter to the EnzymeMLDocument if it doesn't already exist.

    Args:
        enzmldoc (EnzymeMLDocument): The document to add the parameter to
        name (str): The name of the parameter
        unit (str | UnitDefinition | None): The unit of the parameter
    """
    add_logger("ENZML")

    if enzmldoc.filter_parameters(name=name):
        logger.info(f"Parameter {name} already exists in EnzymeMLDocument. Skipping...")
        return

    enzmldoc.add_to_parameters(
        name=name,
        id=name,
        symbol=name,
        unit=unit,  # type: ignore
    )  # type: ignore


def _extract_all_ids(enzmldoc: EnzymeMLDocument) -> set[str]:
    """Extracts all IDs from the EnzymeMLDocument.

    Args:
        enzmldoc (EnzymeMLDocument): The document to extract the IDs from

    Returns:
        list[str]: A list of all IDs in the EnzymeMLDocument
    """
    assignments = [
        eq.species_id
        for eq in enzmldoc.equations
        if eq.equation_type != EquationType.ODE
    ]
    species = [
        obj.id
        for obj in enzmldoc.small_molecules + enzmldoc.proteins + enzmldoc.complexes
    ]
    return set(assignments + species)
