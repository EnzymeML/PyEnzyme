from loguru import logger
from mdmodels.units.unit_definition import UnitDefinition

import pyenzyme.tools as tools
from pyenzyme.versions.v2 import (
    EnzymeMLDocument,
    EquationType,
    MeasurementData,
    Parameter,
    ReactionElement,
)


def validate_sbml_export(doc: EnzymeMLDocument) -> bool:
    """This function validates the SBML export of an EnzymeML document.

    Args:
        doc (pe.EnzymeMLDocument): The EnzymeML document to validate.

    Returns:
        bool: True if the document is valid, False otherwise.
    """

    result = all(
        [
            _check_consistent_vessel_ids(doc),
            _check_equation_either_rule_or_reaction(doc),
            _check_units_exist(doc),
            _check_assigned_params_are_not_constant(doc),
        ]
    )

    return result


def _check_consistent_vessel_ids(doc: EnzymeMLDocument) -> bool:
    """This validator checks whether all species have a vessel id that exists in the document.

    SBML documents require that all species have a vessel id that exists in the document and
    this validator checks for that. Otherwise, an error message will be logged and the validity
    set to False.

    Args:
        doc (pe.EnzymeMLDocument): The EnzymeML document to validate.

    Returns:
        bool: True if all species have valid vessel IDs, False otherwise.
    """

    vessel_ids = {v.id for v in doc.vessels}
    all_species = doc.small_molecules + doc.proteins + doc.complexes
    result = []

    for species in all_species:
        if species.vessel_id is None:
            logger.error(
                f"Species '{species.id}' of type '{type(species).__name__}' does not have a vessel id."
            )
            result.append(False)
        elif species.vessel_id not in vessel_ids:
            logger.error(
                f"Species '{species.id}' of type '{type(species).__name__}' has a vessel id that does not exist in "
                f"the document."
            )
            result.append(False)
        else:
            result.append(True)

    return all(result)


def _check_equation_either_rule_or_reaction(doc: EnzymeMLDocument) -> bool:
    """This validator checks whether there are either rules or reactions in the document.

    SBML documents require that there are either rules or reactions in the document. For instance,
    there cannot be a rate equation and reaction element at the same time, since the latter is
    used to derive the former. This validator checks for that and logs an error message if the
    document is invalid.

    Args:
        doc (pe.EnzymeMLDocument): The EnzymeML document to validate.

    Returns:
        bool: True if all species have either rules or reactions but not both, False otherwise.
    """

    species_w_rate = {
        eq.species_id for eq in doc.equations if eq.equation_type == EquationType.ODE
    }

    all_reaction_elements = tools.extract(obj=doc, target=ReactionElement)
    result, validated = [], set()

    for element in all_reaction_elements:
        if element.species_id in species_w_rate and element.species_id not in validated:
            logger.error(
                f"Species '{element.species_id}' is part of a reaction and has a rate equation. This is not allowed "
                f"in SBML."
            )
            validated.add(element.species_id)
            result.append(False)
        else:
            result.append(True)

    return all(result)


def _check_units_exist(doc: EnzymeMLDocument) -> bool:
    """This validator checks whether all units in the document are defined in the SBML standard.

    Args:
        doc (pe.EnzymeMLDocument): The EnzymeML document to validate.

    Returns:
        bool: True if all mandatory objects have units defined, False otherwise.
    """

    mandatory_unit_objects = [
        *tools.extract(obj=doc, target=MeasurementData),
    ]

    optional_unit_objects = [
        *tools.extract(obj=doc, target=Parameter),
    ]

    result = []

    for unit_obj in mandatory_unit_objects:
        units = tools.extract(obj=unit_obj, target=UnitDefinition)

        if len(units) == 0:
            logger.error(
                f"Object of type '{type(unit_obj).__name__}' with id '{unit_obj.species_id}' does not have a unit defined."
            )
            result.append(False)

    for unit_obj in optional_unit_objects:
        units = tools.extract(obj=unit_obj, target=UnitDefinition)

        if len(units) == 0:
            logger.warning(
                f"{type(unit_obj).__name__} with id '{unit_obj.id}' should ideally have a unit defined."
            )

        result.append(True)

    return all(result)


def _check_assigned_params_are_not_constant(doc: EnzymeMLDocument) -> bool:
    """This validator checks whether all assigned parameters are not constant.

    If a parameter is assigned a value through an assignment rule, it should not be constant.
    This validator checks for that and logs a warning if a parameter is constant but has
    an assignment rule and sets the parameter to non-constant.

    Args:
        doc (pe.EnzymeMLDocument): The EnzymeML document to validate.

    Returns:
        bool: True if all assigned parameters are valid, False otherwise.
    """

    assignments = doc.filter_equations(equation_type=EquationType.ASSIGNMENT)
    result = []

    for assignment in assignments:
        params = doc.filter_parameters(id=assignment.species_id)

        if len(params) == 0:
            logger.error(
                f"Assignment '{assignment.species_id}' does not have a parameter defined."
            )
            result.append(False)
        elif len(params) > 1:
            logger.error(
                f"Assignment '{assignment.species_id}' has multiple parameters defined."
            )
            result.append(False)

        if params[0].constant:
            params[0].constant = False
            logger.warning(
                f"Parameter '{params[0].id}' has an assignment rule, but is set to constant. The parameter is now set "
                f"to non-constant."
            )

            result.append(True)

    return all(result)
