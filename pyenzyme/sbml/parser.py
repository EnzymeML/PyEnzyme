from __future__ import annotations

import math
import re
from pathlib import Path
from typing import IO

import libsbml as sbml  # type: ignore
import pandas as pd
from loguru import logger  # type: ignore

import pyenzyme as pe
from pyenzyme import xmlutils
from pyenzyme.logging import add_logger
from . import read_sbml_omex
from .ldutils import parse_sbml_rdf_annotation
from .versions.handler import VersionHandler, SupportedVersions


def read_sbml(cls, path: Path | str):
    """
    Reads an SBML file and initializes an EnzymeML document.

    Args:
        cls: The class to instantiate the EnzymeML document.
        path (Path | str): The path to the OMEX archive containing the SBML file.

    Returns:
        An initialized EnzymeML document with extracted units, species, vessels,
        equations, parameters, reactions, and measurements.
    """
    add_logger(name="SBML")

    # Create globals to use in the functions
    global units
    global path_prefix
    global version
    global enzmldoc

    # Read the OMEX archive and extract the SBML and TSV paths
    sbml_handler, data = read_sbml_omex(path)

    # Find out which version of the SBML file we are dealing with
    namespaces = xmlutils.extract_namespaces(sbml_handler.read())
    version = VersionHandler.from_uri(namespaces)
    sbml_handler.seek(0)

    # Read the SBML file and init an EnzymeML document
    model = _init_and_read_sbml(sbml_handler)
    enzmldoc = cls(name=model.getName())

    # Extract units to map these to the EnzymeML entities
    units = {  # type: ignore
        unit.getId(): _parse_unit(unit) for unit in model.getListOfUnitDefinitions()
    }

    # Extract and sort species
    species = [_parse_species(species) for species in model.getListOfSpecies()]
    enzmldoc.small_molecules = [s for s in species if isinstance(s, pe.SmallMolecule)]
    enzmldoc.proteins = [s for s in species if isinstance(s, pe.Protein)]
    enzmldoc.complexes = [s for s in species if isinstance(s, pe.Complex)]

    # Extract vessels
    enzmldoc.vessels = [_parse_vessel(comp) for comp in model.getListOfCompartments()]

    # Extract equations and parameters
    enzmldoc.parameters = [_parse_parameter(param) for param in model.getListOfParameters()]  # type: ignore
    enzmldoc.equations += [
        _parse_equation(rule, pe.EquationType.INITIAL_ASSIGNMENT)
        for rule in model.getListOfInitialAssignments()
    ]

    enzmldoc.equations += [
        _parse_equation(rule, pe.EquationType.ODE)
        for rule in model.getListOfRules()
        if rule.isRate()
    ]

    enzmldoc.reactions = [
        _parse_reaction(reaction) for reaction in model.getListOfReactions()
    ]

    enzmldoc.measurements = _parse_measurements(
        model=model,
        list_of_reactions=model.getListOfReactions(),
        meas_data=data,
    )

    return enzmldoc


def _init_and_read_sbml(handler: IO):
    """
    Initialize the SBML reader and read the SBML document.

    Args:
        handler (IO): The file handler for the SBML document.

    Returns:
        The SBML model.

    Raises:
        ValueError: If the SBML document or model cannot be read.
    """
    reader = sbml.SBMLReader()
    sbmldoc = reader.readSBMLFromString(handler.read())
    if not sbmldoc:
        logger.error("Could not read SBML document")
        raise ValueError("Could not read SBML document")

    # Get the model
    model = sbmldoc.getModel()
    if not model:
        logger.error("Could not get model from SBML file")
        raise ValueError("Could not get model from SBML file")

    return model


def _parse_unit(unit: sbml.UnitDefinition):
    """
    Parse a unit definition from an SBML model into an EnzymeML unit definition.

    Args:
        unit (sbml.UnitDefinition): The SBML unit definition.

    Returns:
        An EnzymeML unit definition.
    """
    enzml_unit = pe.UnitDefinition(
        id=unit.getId(),
        name=unit.getName(),
    )

    parse_sbml_rdf_annotation(unit, enzml_unit)

    for base_unit in unit.getListOfUnits():
        multiplier = base_unit.getMultiplier()
        kind = sbml.UnitKind_toString(base_unit.getKind())

        if math.isnan(multiplier):
            multiplier = None

        enzml_unit.add_to_base_units(
            kind=kind,
            exponent=base_unit.getExponent(),
            scale=base_unit.getScale(),
            multiplier=multiplier,
        )

    return enzml_unit


def _parse_species(species: sbml.Species):
    """
    Parse a species from an SBML model into EnzymeML small molecule or protein.

    Args:
        species (sbml.Species): The SBML species.

    Returns:
        An EnzymeML small molecule, protein, or complex.
    """
    sbo_term = species.getSBOTermID()

    if sbo_term == "SBO:0000247":
        return _parse_small_molecule(species)
    elif sbo_term == "SBO:0000252":
        return _parse_protein(species)
    elif sbo_term == "SBO:0000296":
        return _parse_complex(species)
    else:
        logger.error(
            f"Unknown SBO term for species '{species.getId()}': {sbo_term}. Unable to parse species."
        )


def _parse_small_molecule(species: sbml.Species):
    """
    Parse a species from an SBML model into an EnzymeML small molecule.

    Args:
        species (sbml.Species): The SBML species.

    Returns:
        An EnzymeML small molecule.
    """
    parsed = version.parse_annotation(annotation=species.getAnnotationString())
    annots = version.extract(parsed, "small_molecule")

    small_molecule = pe.SmallMolecule(
        id=species.getId(),
        name=species.getName(),
        vessel_id=species.getCompartment(),
        constant=species.getConstant(),
        **annots,
    )

    parse_sbml_rdf_annotation(species, small_molecule)

    return small_molecule


def _parse_protein(species: sbml.Species):
    """
    Parse a species from an SBML model into an EnzymeML protein.

    Args:
        species (sbml.Species): The SBML species.

    Returns:
        An EnzymeML protein.
    """
    parsed = version.parse_annotation(annotation=species.getAnnotationString())
    annots = version.extract(parsed, "protein")

    protein = pe.Protein(
        id=species.getId(),
        name=species.getName(),
        vessel_id=species.getCompartment(),
        constant=species.getConstant(),
        **annots,
    )

    parse_sbml_rdf_annotation(species, protein)

    return protein


def _parse_complex(species: sbml.Species):
    """
    Parse a species from an SBML model into an EnzymeML complex.

    Args:
        species (sbml.Species): The SBML species.

    Returns:
        An EnzymeML complex.
    """
    parsed = version.parse_annotation(annotation=species.getAnnotationString())
    annots = version.extract(parsed, "complex")

    complex_ = pe.Complex(
        id=species.getId(),
        name=species.getName(),
        **annots,
    )

    parse_sbml_rdf_annotation(species, complex_)

    return complex_


def _parse_vessel(compartment: sbml.Compartment):
    """
    Parse a compartment from an SBML model into an EnzymeML vessel.

    Args:
        compartment (sbml.Compartment): The SBML compartment.

    Returns:
        An EnzymeML vessel.
    """
    vessel = pe.Vessel(
        id=compartment.getId(),
        name=compartment.getName(),
        volume=_check_nan(compartment.getSize()),
        unit=units[compartment.getUnits()],  # type: ignore
    )

    parse_sbml_rdf_annotation(compartment, vessel)

    return vessel


def _parse_parameter(parameter: sbml.Parameter):
    """
    Parse a parameter from an SBML model into an EnzymeML parameter.

    Args:
        parameter (sbml.Parameter): The SBML parameter.

    Returns:
        An EnzymeML parameter.
    """
    parsed = version.parse_annotation(annotation=parameter.getAnnotationString())
    annots = version.extract(parsed, "parameter")

    parameter = pe.Parameter(
        id=parameter.getId(),
        name=parameter.getName(),
        symbol=parameter.getId(),
        value=_check_nan(parameter.getValue()),
        constant=parameter.getConstant(),
        unit=units.get(parameter.getUnits()),  # type: ignore
        **annots,
    )

    return parameter


def _parse_equation(rule: sbml.Rule, rule_type: pe.EquationType):
    """
    Parse a rule from an SBML model into an EnzymeML equation.

    Args:
        rule (sbml.Rule): The SBML rule.
        rule_type (pe.EquationType): The type of the equation.

    Returns:
        An EnzymeML equation.

    Raises:
        ValueError: If the rule type is unknown.
    """
    match rule_type:
        case pe.EquationType.INITIAL_ASSIGNMENT:
            equation = sbml.formulaToString(rule.getMath())
            species_id = rule.getSymbol()
        case pe.EquationType.ODE:
            equation = rule.getFormula()
            species_id = rule.getVariable()
        case pe.EquationType.RATE_LAW:
            equation = rule.getFormula()
            species_id = None
        case _:
            raise ValueError(f"Unknown rule type: {rule_type}")

    parsed = version.parse_annotation(annotation=rule.getAnnotationString())
    annots = version.extract(parsed, "variables")

    if version.version == SupportedVersions.VERSION1:
        _map_v1_variables(annots, equation)

    equation = pe.Equation(
        equation_type=rule_type,
        equation=equation,
        species_id=species_id,
        variables=[pe.Variable(**annot) for annot in annots.get("variables", [])],
    )

    return equation


def _map_v1_variables(annots: dict, equation: str):
    """
    Map variables for version 1 of the EnzymeML format.

    Args:
        annots (dict): The annotations.
        equation (str): The equation string.
    """
    if "variables" not in annots:
        annots["variables"] = []

    all_species = [
        *[s.id for s in enzmldoc.small_molecules],
        *[p.id for p in enzmldoc.proteins],
        *[c.id for c in enzmldoc.complexes],
    ]
    for species in all_species:
        if bool(re.search(rf"\b{species}\b", equation)):
            annots["variables"].append(
                pe.Variable(
                    id=species,
                    name=species,
                    symbol=species,
                ).model_dump()
            )


def _parse_reaction(reaction: sbml.Reaction):
    """
    Parse a reaction from an SBML model into an EnzymeML reaction.

    Args:
        reaction (sbml.Reaction): The SBML reaction.

    Returns:
        An EnzymeML reaction.
    """
    # Get the reactants and products
    products = [_parse_element(product, 1) for product in reaction.getListOfProducts()]
    reactants = [
        _parse_element(reactant, -1) for reactant in reaction.getListOfReactants()
    ]

    # Get the modifiers
    modifiers = [modifier.getSpecies() for modifier in reaction.getListOfModifiers()]

    # Get the kinetic law
    kinetic_law = _parse_equation(reaction.getKineticLaw(), pe.EquationType.RATE_LAW)

    # Create the EnzymeML reaction
    reaction = pe.Reaction(
        id=reaction.getId(),
        name=reaction.getName(),
        species=reactants + products,
        modifiers=modifiers,
        kinetic_law=kinetic_law,
    )

    return reaction


def _parse_element(species, direction: int):
    """
    Parse a species element from an SBML model into an EnzymeML reaction element.

    Args:
        species: The SBML species element.
        direction (int): The direction of the reaction (1 for product, -1 for reactant).

    Returns:
        An EnzymeML reaction element.
    """
    return pe.ReactionElement(
        species_id=species.getSpecies(),
        stoichiometry=species.getStoichiometry() * direction,
    )


def _parse_measurements(
    model: sbml.Model,
    list_of_reactions: sbml.ListOfReactions,
    meas_data: dict[str, pd.DataFrame],
):
    """
    Parse measurements from an SBML model into EnzymeML measurements.

    Args:
        model (sbml.Model): The SBML model.
        list_of_reactions (sbml.ListOfReactions): The list of reactions in the SBML model.
        meas_data (dict[str, pd.DataFrame]): The measurement data.

    Returns:
        EnzymeML measurements.

    Raises:
        ValueError: If the version is unknown.
    """
    match version.version:
        case SupportedVersions.VERSION1:
            parsed = version.parse_annotation(list_of_reactions.getAnnotationString())
            if parsed.data:
                return parsed.data.to_measurements(meas_data, units)
        case SupportedVersions.VERSION2:
            parsed = version.parse_annotation(model.getAnnotationString())
            if parsed.data:
                return parsed.data.to_measurements(meas_data, units)
        case _:
            raise ValueError(f"Unknown version: {version.version}")


def _check_nan(value: float):
    """
    Check if a value is NaN.

    Args:
        value (float): The value to check.

    Returns:
        The value if it is not NaN, otherwise None.
    """
    if math.isnan(value):
        return None

    return value
