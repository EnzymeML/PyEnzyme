import re

import rich
from loguru import logger
from sympy import sympify

from pyenzyme.logging import add_logger
from pyenzyme.model import (
    EnzymeMLDocument,
    Equation,
    EquationType,
    UnitDefinition,
    Variable,
    Parameter,
)

INIT_ASSIGNMENT_PATTERN = r"^[A-Za-z][A-Za-z\_]*"
DERIVATIVE_PATTERN = r"([A-Za-z0-9\_]+)\'\(t\)"
VARIABLE_PATTERN = r"([A-Za-z0-9\_]+)\'?\(t\)"
PARAMETER_PATTERN = r"([A-Za-z0-9\_]+)"
REPLACE_PATTERN = r"\(t\)|\'"
ELEMENTAL_FUNCTIONS = ["exp", "log", "sin", "cos", "tan", "sqrt", "abs"]


def build_equations(
    *equations: str,
    unit_mapping: dict[str, UnitDefinition] | None = None,
) -> list[Equation]:
    """Builds a list of Equation objects from a list of string representations.

    Args:
        *equations (list[str]): A list of string representations of the ODEs
        unit_mapping: A dictionary mapping parameter names to their respective

    Returns:
        list[ODE]: A list of ODE objects

    Example:
        >> build_equations("s1'(t) = 2 * s2(t)", "s2'(t) = 3 * s1(t)")
    """

    if unit_mapping is None:
        unit_mapping = {}

    assert all(isinstance(eq, str) for eq in equations), "All equations must be strings"

    return [build_equation(eq, unit_mapping) for eq in equations]  # type: ignore


def build_equation(
    equation: str,
    unit_mapping: dict[str, UnitDefinition] | None = None,
) -> Equation:
    """Builds an equation object from a string

    This function takes an equation string and converts it into an ODE object.
    The equation string should be in the form of "s1'(t) = 2 * s2(t)" where
    there is a left and right side of the equation.

    Args:
        equation (str): The equation to be converted into an ODE object
        unit_mapping: A dictionary mapping parameter names to their respective units

    Returns:
        ODE: The ODE object

    Example:

        >> eq = "s1'(t) = 2 * s2(t)"
        >> ode = ode(eq)

    """

    if unit_mapping is None:
        unit_mapping = {}

    left, right = _extract_sides(equation)
    variables = set(re.findall(VARIABLE_PATTERN, right))

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
                    "There are three types equations that follow a certain pattern:\n",
                    "  [bold]1. ODE: y'(t) = 2 * x(t)[/bold]",
                    "  [bold]2. Assignment: y(t) = 2 * x(t)[/bold]",
                    "  [bold]3. Initial Assignment: y = 2 * x(t)[/bold]",
                    "\nPlease make sure your equation follows one of these patterns.\n",
                ]
            )
        )
        raise ValueError("Equation type not recognized")

    right = sympify(_clean_and_trim(right))
    left = _clean_and_trim(left)
    parameters = {str(symbol) for symbol in right.free_symbols} - variables  # type: ignore

    if equation_type == EquationType.ASSIGNMENT:
        parameters = parameters.union({left})

    eq = Equation(
        species_id=left if left else None,
        equation=str(right),
        variables=[_create_variable(name) for name in variables],
        equation_type=equation_type,
        parameters=[
            _create_parameter(name, unit_mapping.get(name)) for name in parameters
        ],
    )

    # Left out for now, but could be re-used by decision upon change to include
    # parameters on the top-level document.
    # if enzmldoc:
    #     [_add_to_parameters(enzmldoc, param.name, param.id) for param in eq.parameters]
    #     _add_units_to_parameters(enzmldoc, unit_mapping)

    return eq


def _extract_sides(equation: str) -> tuple[str, str]:
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
    vars = re.findall(VARIABLE_PATTERN, eq)
    for var in vars:
        var = var.replace("'", "")
        if var not in ELEMENTAL_FUNCTIONS:
            eq = re.sub(rf"{var}\'?\(t\)", var, eq)

    return eq.strip()


def _create_parameter(name: str, unit: UnitDefinition | None) -> Parameter:
    return Parameter(id=name, name=name, symbol=name, unit=unit)


def _create_variable(name: str) -> Variable:
    return Variable(id=name, name=name, symbol=name)


def _add_to_parameters(enzmldoc: EnzymeMLDocument, name: str, id: str):
    """Adds a parameter to the EnzymeMLDocument"""

    add_logger("ENZML")

    if enzmldoc.filter_parameters(name=name):
        logger.info(f"Parameter {name} already exists in EnzymeMLDocument. Skipping...")

        return

    enzmldoc.add_to_parameters(name=name, id=name)  # type: ignore


def _add_units_to_parameters(
    doc: EnzymeMLDocument,
    unit_mapping: dict[str, UnitDefinition],
):
    """Adds units to the parameters in the EnzymeMLDocument"""

    add_logger("ENZML")

    has_error = False

    for param, unit in unit_mapping.items():
        if unit.__class__.__name__ != "UnitDefinition":
            logger.error(f"Unit {unit} is not a UnitDefinition object. Skipping...")
            has_error = True
            continue

        doc.filter_parameters(name=param)[0].unit = unit

    if has_error:
        raise ValueError(
            "Assigning units to parameters failed. Check the logs for more info."
        )
