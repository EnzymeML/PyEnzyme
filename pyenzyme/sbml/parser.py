from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import IO

import libsbml as sbml  # type: ignore
import rich
from loguru import logger  # type: ignore

import pyenzyme as pe
from pyenzyme import tools
from pyenzyme.logging import add_logger
from pyenzyme.units import M, s
from . import read_sbml_omex
from .ldutils import parse_sbml_rdf_annotation

MAPPINGS = tools.read_static_file("pyenzyme.sbml", "mappings.toml")
ENZYMEML_NS = "https://www.enzymeml.org/v2"


def read_sbml(cls, path: Path | str):
    """
    Reads an SBML file and initializes an EnzymeML document.

    Args:
        cls: The class to instantiate the EnzymeML document.
        path (Path | str): The path to the OMEX archive containing the SBML file.

    Returns:
        An initialized EnzymeML document with extracted units, species, vessels, equations, parameters, reactions, and measurements.
    """
    add_logger(name="SBML")

    # Create globals to use in the functions
    global units
    global path_prefix
    global tsv_path

    # Read the OMEX archive and extract the SBML and TSV paths
    sbml_path, tsv_path = read_sbml_omex(path)

    # Read the SBML file and init an EnzymeML document
    model = _init_and_read_sbml(open(sbml_path))
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

    enzmldoc.measurements = _parse_measurements(model)

    return enzmldoc


def _init_and_read_sbml(handler: IO):
    """Initialize the SBML reader and read the SBML document."""

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
    """Parse a unit definition from an SBML model into an EnzymeML unit definition."""
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
    """Parse a species from an SBML model into EnzymeML small molecule or protein."""
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
    """Parse a species from an SBML model into an EnzymeML small molecule."""

    annots = _parse_enzymeml_annotations("smallMolecule", species.getAnnotationString())
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
    """Parse a species from an SBML model into an EnzymeML small molecule."""

    annots = _parse_enzymeml_annotations("protein", species.getAnnotationString())
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
    """Parse a species from an SBML model into an EnzymeML complex."""

    annots = _parse_enzymeml_annotations("complex", species.getAnnotationString())
    complex_ = pe.Complex(
        id=species.getId(),
        name=species.getName(),
        **annots,
    )

    parse_sbml_rdf_annotation(species, complex_)

    return complex_


def _parse_vessel(compartment: sbml.Compartment):
    """Parse a compartment from an SBML model into an EnzymeML vessel."""

    vessel = pe.Vessel(
        id=compartment.getId(),
        name=compartment.getName(),
        volume=_check_nan(compartment.getSize()),
        unit=units[compartment.getUnits()],  # type: ignore
    )

    parse_sbml_rdf_annotation(compartment, vessel)

    return vessel


def _parse_parameter(parameter: sbml.Parameter):
    """Parse a parameter from an SBML model into an EnzymeML parameter."""
    annots = _parse_enzymeml_annotations("parameter", parameter.getAnnotationString())
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
    """Parse a rule from an SBML model into an EnzymeML equation."""

    match rule_type:
        case pe.EquationType.INITIAL_ASSIGNMENT:
            equation = sbml.formulaToString(rule.getMath())
            species_id = rule.getSymbol()
        case pe.EquationType.ODE:
            equation = rule.getFormula()
            species_id = rule.getVariable()
        case pe.EquationType.RATE_LAW:
            equation = rule.getMath()
            species_id = None
        case _:
            raise ValueError(f"Unknown rule type: {rule_type}")

    annots = _parse_enzymeml_annotations("variables", rule.getAnnotationString())
    equation = pe.Equation(
        equation_type=rule_type,
        equation=equation,
        species_id=species_id,
        variables=[pe.Variable(**annot) for annot in annots.get("variables", [])],
    )

    return equation


def _parse_reaction(reaction: sbml.Reaction):
    """Parse a reaction from an SBML model into an EnzymeML reaction."""

    # Get the reactants and products
    products = [_parse_element(product, 1) for product in reaction.getListOfProducts()]
    reactants = [
        _parse_element(reactant, -1) for reactant in reaction.getListOfReactants()
    ]

    # Get the modifiers
    modifiers = [modifier.getSpecies() for modifier in reaction.getListOfModifiers()]

    # Get the kinetic law
    kinetic_law = _parse_kinetic_law(reaction)

    # Create the EnzymeML reaction
    reaction = pe.Reaction(
        id=reaction.getId(),
        name=reaction.getName(),
        species=reactants + products,
        modifiers=modifiers,
        kinetic_law=kinetic_law,
    )

    rich.print(reaction)

    return reaction


def _parse_element(species, direction: int):
    return pe.ReactionElement(
        species_id=species.getSpecies(),
        stoichiometry=species.getStoichiometry() * direction,
    )


def _parse_kinetic_law(reaction):
    kinetic_law = reaction.getKineticLaw()

    if not kinetic_law:
        return None

    annots = _parse_enzymeml_annotations("variables", kinetic_law.getAnnotationString())
    kinetic_law = pe.Equation(
        equation=kinetic_law.getFormula(),
        equation_type=pe.EquationType.RATE_LAW,
        unit=M,  # We need to set a default unit here, because SBML does not provide units for kinetic laws
        variables=[pe.Variable(**annot) for annot in annots.get("variables", [])],
    )

    return kinetic_law


def _parse_measurements(model: sbml.Model):
    # Extract metadata from the model
    meas_metadata, file_path = _get_meas_metadata(model)
    meas_metadata = _extract_measurement_metadata(meas_metadata)

    # Read the CSV file into measurement objects
    # We need to set defaults for the units here,
    # but we will overwrite them with the units from the EnzymeML annotations
    measurements = pe.read_csv(
        tsv_path,
        data_unit=M,
        time_unit=s,
    )

    for meas_id, metadata in meas_metadata.items():
        _assign_units_and_initials(meas_id, measurements, metadata)

    return measurements


def _assign_units_and_initials(meas_id, measurements, metadata):
    measurement = [m for m in measurements if m.id == meas_id][0]
    conditions = metadata.get("condition", {})
    init_concs = metadata.get("speciesData", [])
    measurement.ph = _cast(conditions.get("ph"), float)
    measurement.temperature = _cast(conditions.get("temperature"), float)
    measurement.temperature_unit = conditions.get("temperature_unit")

    for init_conc in init_concs:
        species_id = _get_species_id(init_conc)
        meas_data = _get_species_data(measurement, species_id)

        meas_data.initial = float(init_conc.get("initial", 0.0))
        meas_data.time_unit = init_conc["time_unit"]
        meas_data.data_unit = init_conc["data_unit"]


def _cast(value, data_type):
    if value is None:
        return None

    return data_type(value)


def _get_species_id(init_conc):
    species_id = init_conc.get("species_id")
    assert species_id, "No species ID found in the EnzymeML data annotation"
    return species_id


def _get_species_data(measurement, species_id):
    try:
        return [d for d in measurement.species_data if d.species_id == species_id][0]
    except IndexError:
        raise ValueError(f"No species data found for species ID {species_id}")


def _get_meas_metadata(model):
    root = ET.fromstring(model.getAnnotationString())
    data = root.find(f"{{{ENZYMEML_NS}}}data")
    meas_metadata = data.findall(f"{{{ENZYMEML_NS}}}measurement")
    file_path = data.attrib.get("file")

    assert file_path, "No file path found in the EnzymeML data annotation"

    return meas_metadata, file_path


def _extract_measurement_metadata(meas_metadata):
    measurements = {}

    for meas_meta in meas_metadata:
        meas_id = meas_meta.attrib.get("id")
        data = _process_measurement(meas_meta)
        measurements[meas_id] = data

    return measurements


def _process_measurement(meas_meta):
    data = {}
    time_unit = units.get(meas_meta.attrib.get("timeUnit"))

    assert (
        time_unit
    ), f"Time unit not found for measurement {meas_meta.attrib.get('id')}"

    species_data = _parse_enzymeml_annotations("speciesData", meas_meta).get(
        "speciesData", []
    )
    conditions = _parse_enzymeml_annotations("conditions", meas_meta).get(
        "conditions", []
    )

    if conditions:
        data["condition"] = _assign_temp_unit(conditions[0])
    if species_data:
        data["speciesData"] = _assign_meas_units(species_data, time_unit)

    return data


def _assign_temp_unit(conditions):
    if temp_unit := conditions.get("temperature_unit"):
        conditions["temperature_unit"] = units.get(temp_unit)

    return conditions


def _assign_meas_units(species_data, time_unit):
    for data in species_data:
        data["data_unit"] = units.get(data["data_unit"])
        data["time_unit"] = time_unit
        data["data_type"] = pe.DataTypes.__members__.get(data["data_type"])

    return species_data


def _parse_enzymeml_annotations(
    root_key: str, annotation: str | ET.Element | None
) -> dict:
    """Parse the RDF annotation of an SBML object."""

    if not annotation:
        return {}

    mappings = MAPPINGS[root_key]

    match annotation:
        case str():
            root = ET.fromstring(annotation).find(f".//{{{ENZYMEML_NS}}}{root_key}")
        case _ if isinstance(annotation, ET.Element):
            root = annotation
        case _:
            raise ValueError(f"Unknown annotation type: {type(annotation)}")

    if not root:
        return {}

    return _map_values(mappings, root, root_key)


def _map_values(mappings, root, root_key=None):
    """Map the values from the XML root to the EnzymeML entities."""

    data = {}
    for xml_key, enzml_key in mappings.items():
        match enzml_key:
            case dict():
                if value := _process_nested_keys(
                    enzml_key=enzml_key,
                    root=root,
                    xml_key=xml_key,
                ):
                    if root_key in data and len(value) == 1:
                        # Special case for conditions
                        data[root_key][0].update(value[0])
                    else:
                        data[root_key] = value

            case str():
                if value := _process_simple(
                    root=root,
                    xml_key=xml_key,
                ):
                    data[enzml_key] = value
            case _:
                raise ValueError(f"Unknown value type for key '{enzml_key}'")

    return data


def _process_simple(
    root: ET.Element,
    xml_key: str,
):
    if xml_key.startswith("@"):
        value = root.attrib.get(xml_key[1:])
    else:
        value = root.findall(f"{{{ENZYMEML_NS}}}{xml_key}")

        if len(value) == 1:
            value = value[0].text
        elif len(value) > 1:
            value = [v.text for v in value]
    return value


def _process_nested_keys(
    enzml_key: dict,
    root: ET.Element,
    xml_key: str,
):
    value = root.findall(f".//{{{ENZYMEML_NS}}}{xml_key}")
    if len(value) == 1:
        value = [_map_values(enzml_key, value[0])]
    elif len(value) > 1:
        value = [_map_values(enzml_key, v) for v in value]
    else:
        return None

    return value


def _check_nan(value: float):
    """Check if a value is NaN."""

    if math.isnan(value):
        return None

    return value
