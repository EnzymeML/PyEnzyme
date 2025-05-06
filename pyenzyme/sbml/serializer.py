from __future__ import annotations

from copy import deepcopy
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Callable, List

import libsbml
import pandas as pd
from loguru import logger

import pyenzyme as pe
import pyenzyme.tools as tools
from pyenzyme import rdf
from pyenzyme import xmlutils as _xml
from pyenzyme.logging import add_logger
from pyenzyme.sbml import create_sbml_omex
from pyenzyme.sbml.validation import validate_sbml_export
from pyenzyme.sbml.versions import v2
from pyenzyme.tabular import to_pandas
from pyenzyme.units.units import UnitDefinition

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
        >> to_sbml(doc, "example.xml")

    Args:
        enzmldoc (pe.EnzymeMLDocument): The EnzymeML document to convert.
        out (Path | str | None, optional): The output file to write the SBML document to. Defaults to None.
        verbose (bool, optional): Whether to print warnings during SBML validation. Defaults to False.

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

    doc = deepcopy(enzmldoc)
    sbmldoc = libsbml.SBMLDocument()
    model = sbmldoc.createModel()
    model.setName(doc.name)
    units = _assign_ids_to_units(tools.find_unique(doc, pe.UnitDefinition))

    # Add units that have been defined by the custom UnitDefinition
    convert_unit_classes(doc, units)

    print_warnings = verbose

    _xml.register_namespaces(nsmap=NSMAP)

    # Add entities
    [_add_unit_definitions(unit) for unit in units]
    [_add_vessel(vessel) for vessel in doc.vessels]
    [_add_protein(protein) for protein in doc.proteins]
    [_add_complex(complex_) for complex_ in doc.complexes]
    [_add_small_mol(small_mol) for small_mol in doc.small_molecules]
    [_add_equation(equation) for equation in doc.equations]
    [_add_reaction(reaction, i) for i, reaction in enumerate(doc.reactions)]

    if doc.measurements:
        _add_measurements(doc.measurements)

    for parameter in enzmldoc.parameters:
        _add_parameter(parameter)

    if out is None:
        return libsbml.writeSBMLToString(sbmldoc), to_pandas(doc)

    if isinstance(out, str):
        out = Path(out)

    if out.is_dir():
        out = out / "enzymeml_doc.omex"
    else:
        out = out.with_suffix(".omex")

    _validate_sbml(sbmldoc)
    create_sbml_omex(
        sbml_doc=libsbml.writeSBMLToString(sbmldoc),
        data=to_pandas(doc),
        out=out,
    )

    logger.info(f"OMEX archive written to {out}")


def convert_unit_classes(doc: pe.EnzymeMLDocument, custom_units: list[UnitDefinition]):
    custom_units.extend(
        [
            pe.UnitDefinition(**unit.model_dump())
            for unit in _assign_ids_to_units(tools.find_unique(doc, pe.UnitDefinition))
            if unit.id not in [unit.id for unit in custom_units]
        ]
    )


def _add_unit_definitions(unit: UnitDefinition):
    """Add unit definitions to the SBML model."""

    sbml_unitdef = model.createUnitDefinition()

    sbml_unitdef.setId(unit.id)
    sbml_unitdef.setName(unit.name)

    for base_unit in unit.base_units:
        sbml_unit = sbml_unitdef.createUnit()
        sbml_unit.initDefaults()
        sbml_unit.setKind(_get_sbml_kind(base_unit.kind))
        sbml_unit.setExponent(base_unit.exponent)

        if base_unit.scale:
            sbml_unit.setScale(int(base_unit.scale))
        if base_unit.multiplier:
            sbml_unit.setMultiplier(base_unit.multiplier)


def _add_vessel(vessel: pe.Vessel):
    """Add vessels to the SBML model."""

    compartment = model.createCompartment()
    compartment.initDefaults()
    compartment.setId(vessel.id)
    compartment.setName(vessel.name)
    compartment.setConstant(True)
    compartment.setSize(vessel.volume)
    compartment.setAnnotation(rdf.to_rdf_xml(vessel))

    if vessel.unit:
        compartment.setUnits(_get_unit_id(vessel.unit))
        model.setVolumeUnits(_get_unit_id(vessel.unit))
    else:
        raise ValueError(f"Unit {vessel.unit} not found in units")


def _add_small_mol(small_mol: pe.SmallMolecule):
    """Add small molecules to the SBML model."""

    species = model.createSpecies()
    species.initDefaults()
    species.setId(small_mol.id)
    species.setName(small_mol.name)
    species.setCompartment(small_mol.vessel_id)
    species.setConstant(small_mol.constant)
    species.setSBOTerm("SBO:0000247")  # Simple chemical
    species.appendAnnotation(rdf.to_rdf_xml(small_mol))

    init_conc = _get_first_meas_init_conc(small_mol)

    if init_conc is not None:
        species.setInitialConcentration(init_conc)
        species.setHasOnlySubstanceUnits(False)

    annot = v2.SmallMoleculeAnnot(
        canonical_smiles=small_mol.canonical_smiles,
        inchikey=small_mol.inchikey,
    )

    if not annot.is_empty():
        species.appendAnnotation(annot.to_xml(encoding="unicode"))


def _add_protein(protein: pe.Protein):
    """Add proteins to the SBML model."""

    species = model.createSpecies()
    species.initDefaults()
    species.setId(protein.id)
    species.setName(protein.name)
    species.setConstant(protein.constant)
    species.setCompartment(protein.vessel_id)
    species.setSBOTerm("SBO:0000252")  # Protein
    species.appendAnnotation(rdf.to_rdf_xml(protein))

    init_conc = _get_first_meas_init_conc(protein)

    if init_conc is not None:
        species.setInitialConcentration(init_conc)
        species.setHasOnlySubstanceUnits(False)

    annot = v2.ProteinAnnot(
        ecnumber=protein.ecnumber,
        organism=protein.organism,
        sequence=protein.sequence,
        organism_tax_id=protein.organism_tax_id,
    )

    if not annot.is_empty():
        species.appendAnnotation(annot.to_xml(encoding="unicode"))


def _add_complex(complex_: pe.Complex):
    """Add complexes to the SBML model."""

    species = model.createSpecies()
    species.initDefaults()
    species.setId(complex_.id)
    species.setName(complex_.name)
    species.setCompartment(complex_.vessel_id)
    species.setConstant(True)
    species.setSBOTerm("SBO:0000296")  # Complex
    species.appendAnnotation(rdf.to_rdf_xml(complex_))

    annot = v2.ComplexAnnot(participants=complex_.participants)

    if not annot.is_empty():
        species.appendAnnotation(annot.to_xml(encoding="unicode"))


def _get_first_meas_init_conc(species: pe.SmallMolecule | pe.Protein):
    """Extracts the initial concentration of a species from the first measurement

    SBML requires the initial concentration to be set for species that are measured,
    even if there are multiple measurements. This function extracts the initial
    concentration from the first measurement of the species to fulfill this requirement.
    """

    if not doc.measurements:
        return None

    measurement = doc.measurements[0]
    meas_species = measurement.filter_species_data(species_id=species.id)

    if meas_species:
        return meas_species[0].initial
    else:
        return None


def _add_reaction(reaction: pe.Reaction, index: int):
    """Add reactions to the SBML model."""

    sbml_reaction = model.createReaction()
    sbml_reaction.initDefaults()
    sbml_reaction.setName(reaction.name)
    sbml_reaction.setId(reaction.id)
    sbml_reaction.setReversible(reaction.reversible)

    for species in reaction.species:
        assert species.stoichiometry, f"Stoichiometry of species {species} is not set"

        species_ref = _get_create_fun(
            species.stoichiometry,
            sbml_reaction,
            species.species_id,
        )()

        species_ref.initDefaults()
        species_ref.setConstant(True)
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

    annot = v2.VariablesAnnot(
        variables=[v2.VariableAnnot(**var.model_dump()) for var in equation.variables],
    )

    if not annot.is_empty():
        law.setAnnotation(annot.to_xml(encoding="unicode"))


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
    elif parameter.initial_value:
        sbml_param.setValue(parameter.initial_value)

    if parameter.unit:
        sbml_param.setUnits(_get_unit_id(parameter.unit))

    annot = v2.ParameterAnnot(
        lower_bound=parameter.lower_bound,
        upper_bound=parameter.upper_bound,
        stderr=parameter.stderr,
    )

    if not annot.is_empty():
        sbml_param.appendAnnotation(annot.to_xml(encoding="unicode"))


def _add_equation(equation: pe.Equation):
    """Add equations to the SBML model."""

    if equation.equation_type == pe.EquationType.ODE:
        sbml_rule = model.createRateRule()  # type: ignore
        sbml_rule.setVariable(equation.species_id)
    elif equation.equation_type == pe.EquationType.ASSIGNMENT:
        sbml_rule = model.createAssignmentRule()  # type: ignore
        sbml_rule.setVariable(equation.species_id)
    elif equation.equation_type == pe.EquationType.INITIAL_ASSIGNMENT:
        sbml_rule = model.createInitialAssignment()  # type: ignore
        sbml_rule.setSymbol(equation.species_id)
    else:
        raise ValueError(f"Equation type {equation.equation_type} not supported")

    sbml_rule.setMath(libsbml.parseL3Formula(equation.equation))

    annot = v2.VariablesAnnot(
        variables=[v2.VariableAnnot(**var.model_dump()) for var in equation.variables],
    )

    if not annot.is_empty():
        sbml_rule.setAnnotation(annot.to_xml(encoding="unicode"))


def _add_measurements(measurements: list[pe.Measurement]):
    """Adds measurements to the SBML model."""

    annot = v2.DataAnnot(file="./data.tsv")

    for measurement in measurements:
        if not measurement.species_data:
            continue

        time_unit = _get_unit_id(measurement.species_data[0].time_unit)
        conditions = v2.ConditionsAnnot(
            ph=v2.PHAnnot(
                value=measurement.ph,
            ),
            temperature=v2.TemperatureAnnot(
                value=measurement.temperature,
                unit=_get_unit_id(measurement.temperature_unit),
            ),
        )

        meas_annot = v2.MeasurementAnnot(
            id=measurement.id,
            time_unit=time_unit,
            name=measurement.name,
            conditions=conditions,
        )

        for species_data in measurement.species_data:
            species_annot = v2.SpeciesDataAnnot(
                species_id=species_data.species_id,
                initial=species_data.initial,
                type=species_data.data_type.name,
                unit=_get_unit_id(species_data.data_unit),
            )

            meas_annot.species_data.append(species_annot)

        annot.measurements.append(meas_annot)

    if not annot.is_empty():
        model.appendAnnotation(annot.to_xml(encoding="unicode"))


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


def _get_sbml_kind(unit_type: pe.UnitType):
    try:
        return getattr(libsbml, f"UNIT_KIND_{unit_type.name}")
    except AttributeError:
        raise ValueError(f"Unit type {unit_type} not found in libsbml")


def _get_unit_id(unit: pe.UnitDefinition | None) -> str | None:
    """Helper function to get the unit from the list of units."""

    if unit is None:
        return None

    for unit2 in units:
        if _same_unit(unit, unit2):
            return unit2.id

    raise ValueError(f"Unit {unit.name} not found in the list of units")


def _same_unit(unit1: pe.UnitDefinition, unit2: pe.UnitDefinition) -> bool:
    """Check if two units are the same."""

    return unit1.model_dump(exclude={"id"}) == unit2.model_dump(exclude={"id"})


def _validate_sbml(sbmldoc: libsbml.SBMLDocument) -> None:
    """Validate the SBML document using the libSBML function."""

    sbml_errors = sbmldoc.checkConsistency()

    if sbml_errors and not print_warnings:
        logger.warning(
            "The SBML document has warnings that should be checked. Set the `warnings` argument to true to see them."
        )

    for error in range(sbml_errors):
        severity = sbmldoc.getError(error).getSeverity()

        if severity == libsbml.LIBSBML_SEV_ERROR:
            logger.error(
                sbmldoc.getError(error).getMessage().strip().replace("\n", " ")
            )
        elif severity == libsbml.LIBSBML_SEV_WARNING and print_warnings:
            logger.warning(
                sbmldoc.getError(error).getMessage().strip().replace("\n", " ")
            )


def _assign_ids_to_units(doc_units: List[UnitDefinition]) -> List[UnitDefinition]:
    ids = [unit.id for unit in doc_units if unit.id]
    unique_units = []

    for unit in doc_units:
        if any(_same_unit(unit, u) for u in unique_units):
            continue

        new_id = next(_id_generator(ids))
        unit.id = new_id

        unique_units.append(unit)

    return unique_units


def _id_generator(ids: list[str]):
    """Generator for creating unique IDs that are not in unit_ids."""
    i = 0
    while True:
        potential_id = f"u{i}"
        if potential_id not in ids:
            ids.append(potential_id)
            yield potential_id
        i += 1
