from pathlib import Path
import libsbml
from loguru import logger
import pandas as pd
import xml.etree.ElementTree as ET
from typing import Callable
from pydantic import BaseModel

import pyenzyme.model as pe
from pyenzyme.sbml.validation import validate_sbml_export
from pyenzyme.tabular import to_pandas
import pyenzyme.tools as tools

from pyenzyme import xmlutils as _xml
from pyenzyme import rdf
from pyenzyme.units.units import UnitDefinition
from pyenzyme.logging import add_logger

MAPPINGS = tools.read_static_file("pyenzyme.sbml", "mappings.toml")
NSMAP = {"enzymeml": "https://www.enzymeml.org/v2"}


def to_sbml(
    enzmldoc: pe.EnzymeMLDocument,
    out: Path | str | None = None,
    verbose: bool = False,
) -> tuple[str, pd.DataFrame] | None:
    """This function converts an EnzymeML document to an SBML document.

    The systems biology markup language (SBML) is a machine-readable format for
    representing models of biochemical reaction networks. This function converts
    an EnzymeML document to an SBML document. Prior to serialization the EnzymeML
    document is validated for SBML export.

    Example:
        >> import pyenzyme as pe
        >> doc = pe.EnzymeMLDocument()
        >> [add entities to doc]
        >> pe.to_sbml(doc, "example.xml")

    Args:
        enzmldoc (pe.EnzymeMLDocument): The EnzymeML document to convert.
        out (Path | str | None, optional): The output file to write the SBML document to. Defaults to None.

    Returns:
        tuple[str, pd.DataFrame] | None: The SBML document as a string and a DataFrame with the RDF triples.

    Raises:
        ValueError: If the EnzymeML document is not valid for SBML export.
    """

    add_logger(name="SBML")

    if not validate_sbml_export(enzmldoc):
        raise ValueError("EnzymeML document is not valid for SBML export")

    global print_warnings
    global units
    global model
    global doc

    doc = enzmldoc.copy()
    sbmldoc = libsbml.SBMLDocument()
    model = sbmldoc.createModel()
    units = tools.find_unique(enzmldoc, pe.UnitDefinition)
    print_warnings = verbose

    _xml.register_namespaces(nsmap=NSMAP)

    # Add entities
    [_add_unit_definitions(unit, i) for i, unit in enumerate(units)]
    [_add_vessel(vessel) for vessel in doc.vessels]
    [_add_protein(protein) for protein in doc.proteins]
    [_add_small_mol(small_mol) for small_mol in doc.small_molecules]
    [_add_parameter(param) for param in doc.parameters]
    [_add_equation(equation) for equation in doc.equations]
    [_add_reaction(reaction, i) for i, reaction in enumerate(doc.reactions)]

    if doc.measurements:
        _add_measurements(doc.measurements)

    if out is None:
        return libsbml.writeSBMLToString(sbmldoc), to_pandas(doc)

    if isinstance(out, str):
        out = Path(out)

    if out.is_dir():
        out = out / "enzymeml_doc.xml"
    else:
        out = out.with_suffix(".xml")

    _validate_sbml(sbmldoc)

    libsbml.writeSBML(sbmldoc, str(out))

    if doc.measurements:
        to_pandas(doc).to_csv(out.with_name("data.tsv"), sep="\t", index=False)

    logger.info(f"SBML document written to {out}")


def _add_unit_definitions(unit: UnitDefinition, index: int):
    """Add unit definitions to the SBML model."""

    sbml_unitdef = model.createUnitDefinition()
    sbml_unitdef.setName(unit.name)
    sbml_unitdef.setId(f"u{index}")
    sbml_unitdef.setAnnotation(rdf.to_rdf_xml(unit))

    for base_unit in unit.base_units:
        sbml_unit = sbml_unitdef.createUnit()
        sbml_unit.setKind(_get_sbml_kind(base_unit.kind))
        sbml_unit.setExponent(base_unit.exponent)

        if base_unit.scale:
            sbml_unit.setScale(int(base_unit.scale))
        if base_unit.multiplier:
            sbml_unit.setMultiplier(base_unit.multiplier)


def _add_vessel(vessel: pe.Vessel):
    """Add vessels to the SBML model."""

    compartment = model.createCompartment()
    compartment.setId(vessel.id)
    compartment.setName(vessel.name)
    compartment.setConstant(True)
    compartment.setSize(vessel.volume)
    compartment.setAnnotation(rdf.to_rdf_xml(vessel))

    if vessel.unit in units:
        compartment.setUnits(_get_unit(vessel.unit, units))
    else:
        raise ValueError(f"Unit {vessel.unit} not found in units")


def _add_small_mol(small_mol: pe.SmallMolecule):
    """Add small molecules to the SBML model."""

    species = model.createSpecies()
    species.setId(small_mol.id)
    species.setName(small_mol.name)
    species.setCompartment(small_mol.vessel_id)
    species.setConstant(small_mol.constant)
    species.appendAnnotation(rdf.to_rdf_xml(small_mol))

    init_conc = _get_first_meas_init_conc(small_mol)

    if init_conc is not None:
        species.setInitialConcentration(init_conc)
        species.setHasOnlySubstanceUnits(False)

    root = ET.Element("enzymeml")
    annot = _xml.serialize_to_pretty_xml_string(
        _extract_create_annot("smallMolecule", small_mol, root)
    )

    if annot is not None:
        species.appendAnnotation(annot)


def _add_protein(protein: pe.Protein):
    """Add proteins to the SBML model."""

    species = model.createSpecies()
    species.setId(protein.id)
    species.setName(protein.name)
    species.setConstant(protein.constant)
    species.setCompartment(protein.vessel_id)
    species.appendAnnotation(rdf.to_rdf_xml(protein))

    init_conc = _get_first_meas_init_conc(protein)

    if init_conc is not None:
        species.setInitialConcentration(init_conc)
        species.setHasOnlySubstanceUnits(False)

    annot = _xml.serialize_to_pretty_xml_string(
        _extract_create_annot("protein", protein)
    )

    if annot is not None:
        species.appendAnnotation(annot)


def _get_first_meas_init_conc(species: pe.SmallMolecule | pe.Protein):
    """Extracts the initial concentration of a species from the first measurement

    SBML requires the initial concentration to be set for species that are measured,
    even if there are multiple measurements. This function extracts the initial
    concentration from the first measurement of the species to fulfill this requirement.
    """

    if not doc.measurements:
        return None

    measurement = doc.measurements[0]
    meas_species = measurement.filter_species(species_id=species.id)

    if meas_species:
        return meas_species[0].init_conc
    else:
        return None


def _add_reaction(reaction: pe.Reaction, index: int):
    """Add reactions to the SBML model."""

    sbml_reaction = model.createReaction()
    sbml_reaction.setName(reaction.name)
    sbml_reaction.setId(f"r{index}")
    sbml_reaction.setReversible(reaction.reversible)

    for species in reaction.species:
        assert species.stoichiometry, f"Stoichiometry of species {species} is not set"

        species_ref = _get_create_fun(
            species.stoichiometry,
            sbml_reaction,
            species.species_id,
        )()

        species_ref.setSpecies(species.species_id)
        species_ref.setStoichiometry(abs(species.stoichiometry))

    for modifier in reaction.modifiers:
        modifier_ref = sbml_reaction.createModifier()
        modifier_ref.setSpecies(modifier)

    if reaction.kinetic_law:
        _add_rate_law(reaction.kinetic_law, sbml_reaction)


def _add_rate_law(equation: pe.Equation, reac: libsbml.Reaction):
    """Add rate laws to the SBML Reaction."""

    law = reac.createKineticLaw()
    law.setMath(libsbml.parseL3Formula(equation.equation))

    for parameter in equation.parameters:
        param = law.createParameter()
        param.setId(parameter.id)


def _get_create_fun(
    stoichiometry: float,
    reaction: libsbml.Reaction,
    species: str,
) -> Callable[[], libsbml.SpeciesReference]:
    """Helper function to retrieve the appropriate create function"""
    if stoichiometry > 0:
        return reaction.createProduct
    elif stoichiometry < 0:
        return reaction.createReactant

    raise ValueError(f"Stoichiometry of species {species} is 0")


def _add_parameter(parameter: pe.Parameter):
    """Add parameters to the SBML model."""

    sbml_param = model.createParameter()
    sbml_param.setId(parameter.id)
    sbml_param.setName(parameter.name)
    sbml_param.setConstant(parameter.constant)
    sbml_param.appendAnnotation(rdf.to_rdf_xml(parameter))

    if parameter.value:
        sbml_param.setValue(parameter.value)
    if parameter.unit:
        sbml_param.setUnits(_get_unit(parameter.unit, units))

    annot = _xml.serialize_to_pretty_xml_string(
        _extract_create_annot("parameter", parameter)
    )

    if annot is not None:
        sbml_param.appendAnnotation(annot)


def _add_equation(equation: pe.Equation):
    """Add equations to the SBML model."""

    if equation.equation_type == pe.EquationType.ODE:
        sbml_rule = model.createRateRule()
        sbml_rule.setVariable(equation.species_id)
        sbml_rule.setUnits(_get_unit(equation.unit, units))
    elif equation.equation_type == pe.EquationType.ASSIGNMENT:
        sbml_rule = model.createAssignmentRule()
        sbml_rule.setVariable(equation.species_id)
        sbml_rule.setUnits(_get_unit(equation.unit, units))
    elif equation.equation_type == pe.EquationType.INITIAL_ASSIGNMENT:
        sbml_rule = model.createInitialAssignment()
        sbml_rule.setSymbol(equation.species_id)
    else:
        raise ValueError(f"Equation type {equation.equation_type} not supported")

    sbml_rule.setMath(libsbml.parseL3Formula(equation.equation))


def _add_measurements(measurements: list[pe.Measurement]):
    """Adds measurements to the SBML model."""

    annotation = ET.Element(f"{{{NSMAP['enzymeml']}}}data")
    annotation.attrib["file"] = "data.csv"

    for measurement in measurements:
        meas_element = _extract_create_annot("measurement", measurement)
        meas_element.attrib["timeUnit"] = _get_unit(  # type: ignore
            measurement.species[0].time_unit,
            units,
        )

        assert meas_element is not None, "Measurement element is None"

        conditions = _create_condition_element(
            ph=measurement.ph,
            temperature=measurement.temperature,
            temperature_unit=measurement.temperature_unit,  # type: ignore
        )

        if conditions:
            meas_element.append(conditions)

        for species in measurement.species:
            _extract_create_annot("initConc", species, meas_element)

        annotation.append(meas_element)

    annot = _xml.serialize_to_pretty_xml_string(annotation)

    if annot is not None:
        model.appendAnnotation(annot)


def _create_condition_element(
    ph: float | None,
    temperature: float | None,
    temperature_unit: UnitDefinition | None,
):
    """Set the conditions of the reaction in the SBML model."""

    element = ET.Element(f"{{{NSMAP['enzymeml']}}}conditions")
    mappings = {
        "ph": {"@value": ph},
        "temperature": {"@value": temperature, "@unit": temperature_unit},
    }

    _xml.map_to_xml(
        root=element,
        mappings=mappings,
        namespace=NSMAP["enzymeml"],
    )

    return element


def _extract_create_annot(
    name: str,
    obj: BaseModel,
    element: ET.Element | None = None,
) -> ET.Element | None:
    """Extracts the data from the object and creates an annotation element.

    This function makes use of the "mappings.toml" file which orchestrates
    the mapping of the data from the object to the XML element.

    Args:
        name (str): The name of the object.
        obj (BaseModel): The object to extract the data from.
        element (ET.Element, optional): The element to append the annotation to. Defaults to None.

    Returns:
        ET.Element: The annotation element.
    """
    mappings = _extract(obj, MAPPINGS[name])

    if element is None:
        element = ET.Element(f"{{{NSMAP['enzymeml']}}}{name}")

    _xml.map_to_xml(
        root=element,
        mappings=mappings,
        namespace=NSMAP["enzymeml"],
    )

    if len(element) == 0 and not element.attrib:
        return None

    return element


def _extract(obj: BaseModel, mapping: dict) -> dict:
    """Based on the mapping, extract the data from the object and return it as a dictionary.

    Args:
        obj (BaseModel): The object to extract the data from.
        mapping (dict): The mapping to use for extraction.

    Returns:
        dict: The extracted data.
    """

    data = {}

    for trgt_key, enzml_key in mapping.items():
        if isinstance(enzml_key, dict):
            data[trgt_key] = _extract(obj, enzml_key)
        elif "unit" in enzml_key:
            value = getattr(obj, enzml_key)
            data[trgt_key] = _get_unit(value, units)
        else:
            data[trgt_key] = getattr(obj, enzml_key)

    return data


def _get_sbml_kind(unit_type: pe.UnitType):
    try:
        return getattr(libsbml, f"UNIT_KIND_{unit_type.name}")
    except AttributeError:
        raise ValueError(f"Unit type {unit_type} not found in libsbml")


def _get_unit(unit: pe.UnitDefinition, units: list[pe.UnitDefinition]) -> str | None:
    """Helper function to get the unit from the list of units."""
    try:
        index = units.index(unit)
    except ValueError:
        return None

    return f"u{index}"


def _validate_sbml(sbmldoc: libsbml.SBMLDocument) -> None:
    """Validate the SBML document using the libSBML function."""
    sbml_errors = sbmldoc.checkConsistency()
    valid = True

    if sbml_errors and not print_warnings:
        logger.warning(
            "The SBML document has warnings that should be checked. Set the `warnings` argument to true to see them."
        )

    for error in range(sbml_errors):
        severity = sbmldoc.getError(error).getSeverity()

        if severity == libsbml.LIBSBML_SEV_ERROR:
            valid = False
            logger.error(
                sbmldoc.getError(error).getMessage().strip().replace("\n", " ")
            )
        elif severity == libsbml.LIBSBML_SEV_WARNING and print_warnings:
            logger.warning(
                sbmldoc.getError(error).getMessage().strip().replace("\n", " ")
            )

    if not valid:
        raise ValueError("SBML model is not valid")
