from __future__ import annotations

import math
import re
from pathlib import Path
from typing import IO

import libsbml as sbml  # type: ignore
import pandas as pd
from loguru import logger

import pyenzyme as pe

from pyenzyme import xmlutils
from pyenzyme.logging import add_logger

from . import read_sbml_omex
from .ldutils import parse_sbml_rdf_annotation
from .versions.handler import VersionHandler, SupportedVersions
from .utils import _get_unit


def read_sbml(cls, path: Path | str):
    """
    Reads an SBML file and initializes an EnzymeML document.

    This function reads an SBML file from an OMEX archive, extracts all relevant
    information, and creates an EnzymeML document with the extracted data. It handles
    different versions of the EnzymeML format and maps SBML elements to their
    corresponding EnzymeML entities.

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
    enzmldoc.parameters = [
        _parse_parameter(param) for param in model.getListOfParameters()
    ]  # type: ignore
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

    This function creates an SBML reader, reads the SBML document from the provided
    file handler, and returns the model contained in the document.

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

    This function extracts information from an SBML unit definition and creates
    an equivalent EnzymeML unit definition with the same properties.

    Args:
        unit (sbml.UnitDefinition): The SBML unit definition.

    Returns:
        An EnzymeML unit definition with the same ID, name, and base units.
    """
    enzml_unit = pe.UnitDefinition(
        id=unit.getId(),  # type: ignore
        name=unit.getName(),  # type: ignore
    )

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

    This function determines the type of species based on its SBO term and calls
    the appropriate parsing function to create the corresponding EnzymeML entity.

    Args:
        species (sbml.Species): The SBML species.

    Returns:
        An EnzymeML small molecule, protein, or complex based on the SBO term.

    Logs:
        Error: If the SBO term is unknown or not supported.
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

    This function extracts information from an SBML species with an SBO term
    indicating it's a small molecule and creates an equivalent EnzymeML small
    molecule entity.

    Args:
        species (sbml.Species): The SBML species with SBO term for small molecule.

    Returns:
        An EnzymeML small molecule with properties extracted from the SBML species
        and its annotations.
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

    This function extracts information from an SBML species with an SBO term
    indicating it's a protein and creates an equivalent EnzymeML protein entity.

    Args:
        species (sbml.Species): The SBML species with SBO term for protein.

    Returns:
        An EnzymeML protein with properties extracted from the SBML species
        and its annotations.
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

    This function extracts information from an SBML species with an SBO term
    indicating it's a complex and creates an equivalent EnzymeML complex entity.

    Args:
        species (sbml.Species): The SBML species with SBO term for complex.

    Returns:
        An EnzymeML complex with properties extracted from the SBML species
        and its annotations.
    """
    parsed = version.parse_annotation(annotation=species.getAnnotationString())
    annots = version.extract(parsed, "complex")

    complex_ = pe.Complex(
        id=species.getId(),
        name=species.getName(),
        vessel_id=species.getCompartment(),
        **annots,
    )

    parse_sbml_rdf_annotation(species, complex_)

    return complex_


def _parse_vessel(compartment: sbml.Compartment):
    """
    Parse a compartment from an SBML model into an EnzymeML vessel.

    This function extracts information from an SBML compartment and creates
    an equivalent EnzymeML vessel entity.

    Args:
        compartment (sbml.Compartment): The SBML compartment.

    Returns:
        An EnzymeML vessel with properties extracted from the SBML compartment.

    Note:
        The function prints the unit of the compartment for debugging purposes.
    """

    vessel = pe.Vessel(
        id=compartment.getId(),
        name=compartment.getName(),
        volume=_check_nan(compartment.getSize()),  # type: ignore
        unit=_get_unit(compartment.getUnits(), units),  # type: ignore
    )

    parse_sbml_rdf_annotation(compartment, vessel)

    return vessel


def _parse_parameter(parameter: sbml.Parameter):
    """
    Parse a parameter from an SBML model into an EnzymeML parameter.

    This function extracts information from an SBML parameter and creates
    an equivalent EnzymeML parameter entity.

    Args:
        parameter (sbml.Parameter): The SBML parameter.

    Returns:
        An EnzymeML parameter with properties extracted from the SBML parameter
        and its annotations.

    Note:
        The function prints the parameter annotation string for debugging purposes.
    """
    parsed = version.parse_annotation(annotation=parameter.getAnnotationString())
    annots = version.extract(parsed, "parameter")

    parameter = pe.Parameter(
        id=parameter.getId(),
        name=parameter.getName(),
        symbol=parameter.getId(),
        value=_check_nan(parameter.getValue()),
        constant=parameter.getConstant(),
        unit=_get_unit(parameter.getUnits(), units),  # type: ignore
        **annots,
    )

    return parameter


def _parse_equation(rule: sbml.Rule, rule_type: pe.EquationType):
    """
    Parse a rule from an SBML model into an EnzymeML equation.

    This function extracts information from an SBML rule and creates an equivalent
    EnzymeML equation entity based on the specified equation type.

    Args:
        rule (sbml.Rule): The SBML rule.
        rule_type (pe.EquationType): The type of the equation (INITIAL_ASSIGNMENT, ODE, or RATE_LAW).

    Returns:
        An EnzymeML equation with properties extracted from the SBML rule.

    Raises:
        ValueError: If the rule type is unknown or not supported.
    """
    match rule_type:
        case pe.EquationType.INITIAL_ASSIGNMENT:
            equation = sbml.formulaToString(rule.getMath())
            species_id = rule.getSymbol()  # type: ignore
        case pe.EquationType.ODE:
            equation = rule.getFormula()
            species_id = rule.getVariable()
        case pe.EquationType.RATE_LAW:
            equation = rule.getFormula()
            species_id = "v"
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

    This function identifies variables in the equation string that correspond to
    species in the EnzymeML document and adds them to the annotations.

    Args:
        annots (dict): The annotations dictionary to update with variables.
        equation (str): The equation string to search for variables.
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

    This function extracts information from an SBML reaction, including reactants,
    products, modifiers, and kinetic law, and creates an equivalent EnzymeML reaction.

    Args:
        reaction (sbml.Reaction): The SBML reaction.

    Returns:
        An EnzymeML reaction with properties extracted from the SBML reaction.
    """
    products = [_parse_element(product) for product in reaction.getListOfProducts()]
    reactants = [_parse_element(reactant) for reactant in reaction.getListOfReactants()]
    modifiers = [
        _parse_modifier(modifier) for modifier in reaction.getListOfModifiers()
    ]

    # Get the kinetic law
    kinetic_law = _parse_equation(reaction.getKineticLaw(), pe.EquationType.RATE_LAW)

    # Create the EnzymeML reaction
    enzml_reaction = pe.Reaction(
        id=reaction.getId(),
        name=reaction.getName(),
        reactants=reactants,
        products=products,
        modifiers=modifiers,
        kinetic_law=kinetic_law,
    )

    return enzml_reaction


def _parse_element(species: sbml.SpeciesReference):
    """
    Parse a species element from an SBML model into an EnzymeML reaction element.

    This function creates an EnzymeML reaction element from an SBML species reference,
    applying the specified direction to determine if it's a reactant or product.

    Args:
        species: The SBML species element (SpeciesReference).

    Returns:
        An EnzymeML reaction element with the species ID and stoichiometry.
    """
    return pe.ReactionElement(
        species_id=species.getSpecies(),
        stoichiometry=species.getStoichiometry(),
    )


def _parse_modifier(modifier: sbml.SpeciesReference):
    """
    Parse a modifier from an SBML model into an EnzymeML modifier.

    This function extracts information from an SBML modifier and creates an equivalent
    EnzymeML modifier entity.

    Args:
        modifier (sbml.SpeciesReference): The SBML modifier.

    Returns:
        An EnzymeML modifier with properties extracted from the SBML modifier.
    """
    parsed = version.parse_annotation(annotation=modifier.getAnnotationString())
    annots = version.extract(parsed, "modifier")

    return pe.ModifierElement(
        species_id=modifier.getSpecies(),
        role=pe.ModifierRole.CATALYST,
        **annots,
    )


def _parse_measurements(
    model: sbml.Model,
    list_of_reactions: sbml.ListOfReactions,
    meas_data: dict[str, pd.DataFrame],
):
    """
    Parse measurements from an SBML model into EnzymeML measurements.

    This function extracts measurement data from the SBML model based on the
    EnzymeML version and creates EnzymeML measurement objects.

    Args:
        model (sbml.Model): The SBML model.
        list_of_reactions (sbml.ListOfReactions): The list of reactions in the SBML model.
        meas_data (dict[str, pd.DataFrame]): The measurement data extracted from the OMEX archive.

    Returns:
        A list of EnzymeML measurements.

    Raises:
        ValueError: If the EnzymeML version is unknown or not supported.
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
    Check if a value is NaN and return None if it is.

    This utility function checks if a floating-point value is NaN (Not a Number)
    and returns None in that case, otherwise it returns the original value.

    Args:
        value (float): The value to check.

    Returns:
        float | None: The original value if it is not NaN, otherwise None.
    """
    if math.isnan(value):
        return None

    return value
