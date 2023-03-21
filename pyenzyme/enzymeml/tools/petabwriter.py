# File: petabwriter.py
# Project: tools
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import io
import os
import zipfile
from typing import List, Dict

import pandas as pd
import numpy as np
import yaml


PARAMETER_MAPPING = {
    "name": "parameterId",
    "constant": "estimate",
    "upper": "upperBound",
    "lower": "lowerBound",
    "initial_value": "nominalValue",
    "value": "parameterScale",
}

PARAMETER_DEFAULTS = {
    "upperBound": lambda value: value if value else 1.0e6,
    "lowerBound": lambda value: value if value else 1.0e-6,
    "estimate": lambda value: int(not value),
    "parameterScale": lambda _: "lin",
}


def enzymeml_to_petab(enzmldoc, name: str, path: str) -> None:
    """Converts an EnzymeML document to the petab format

    Args:
        enzmldoc (EnzymeMLDocument): The EnzymeML document to be converted
        name (str): Name of the resulting file
        path (str): Path to which the resulting file will be written

    Raises:
        ValueError: Raised when models are incomplete.
    """

    if not all(
        reaction.model is not None for reaction in enzmldoc.reaction_dict.values()
    ):
        raise ValueError("Not all reactions have a model, yet this is necessary")

    # Move all local parameters from local to global
    for reaction in enzmldoc.reaction_dict.values():
        for parameter in reaction.model.parameters:
            parameter.is_global = True
            enzmldoc.global_parameters[parameter.name] = parameter

    # Convert to DataFrames
    condition_table, set_species = build_condition_table(enzmldoc)
    parameter_table = build_parameters_table(enzmldoc)
    measurement_table, ob_ids = build_measurement_table(enzmldoc)
    observable_table = build_observable_table(enzmldoc, ob_ids)

    # Check if every species that has not been set an IC
    # within the measurements actually has one. If not, set
    # to zero IC.
    check_and_set_initials(enzmldoc, set_species)

    # Build YAML file
    petab_yaml = {
        "format_version": 1,
        "parameter_file": "parameter_table.tsv",
        "problems": [
            {
                "sbml_files": ["model.xml"],
                "measurement_files": ["measurement_table.tsv"],
                "condition_files": ["condition_table.tsv"],
                "observable_files": ["observable_table.tsv"],
            }
        ],
    }

    # Build table data
    content = [
        ("condition_table.tsv", condition_table.to_csv(sep="\t", index=False)),
        ("measurement_table.tsv", measurement_table.to_csv(sep="\t", index=False)),
        ("observable_table.tsv", observable_table.to_csv(sep="\t", index=False)),
        ("parameter_table.tsv", parameter_table.to_csv(sep="\t", index=False)),
        ("model.xml", enzmldoc.toXMLString()),
        ("problems.yaml", yaml.safe_dump(petab_yaml)),
    ]

    # Write everything to a ZIP file
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_name, data in content:
            zip_file.writestr(file_name, data)

    fpath = os.path.join(path, f"{name}.zip")
    with open(fpath, "wb") as file:
        file.write(zip_buffer.getvalue())


def build_condition_table(enzmldoc):
    """Builds the condition table that is necessary for the PETab format"""
    condition_table = []
    set_species = set()

    for measurement in enzmldoc.measurement_dict.values():
        all_species = measurement._getAllSpecies()

        # Keep track of species that have been
        # specified with an IC
        set_species.update(all_species.keys())

        init_concs = {id: meas_data.init_conc for id, meas_data in all_species.items()}

        condition_name = {"conditionName": measurement.name}

        condition_table.append(
            {"conditionId": measurement.id, **condition_name, **init_concs}
        )

    return pd.DataFrame(condition_table), set_species


def build_measurement_table(enzmldoc):
    """Builds the measurement table that is necessary for the PETab format"""
    meas_table = []
    observable_ids, species_ids = [], []
    for measurement in enzmldoc.measurement_dict.values():
        all_species = measurement._getAllSpecies()

        for meas_data in all_species.values():
            for replicate in meas_data.replicates:
                observable_id, species_id = _add_replicate_to_table(
                    replicate, meas_table
                )
                observable_ids.append(observable_id)
                species_ids.append(species_id)

    return pd.DataFrame(meas_table), observable_ids


def _add_replicate_to_table(replicate, meas_table):
    """Parses a Replicate object and adds it to a measurement table"""

    observable_id = replicate.species_id + f"_{replicate.data_type.value}"
    condition_id = replicate.measurement_id
    replicate_id = replicate.id
    species_id = replicate.species_id

    for time_i, data_i in zip(replicate.time, replicate.data):
        meas_table.append(
            {
                "observableId": observable_id,
                "simulationConditionId": condition_id,
                "replicateId": replicate_id,
                "measurement": data_i,
                "time": time_i,
                "noiseParameters": f"sd_{species_id}",
            }
        )

    return (observable_id, replicate.species_id)


def build_parameters_table(enzmldoc):
    """Builds the parameters table that is necessary for the PETab format"""

    observable_species = set(
        [
            species
            for measurement in enzmldoc.exportMeasurementData().values()
            for species in measurement["data"].columns
            if species != "time"
        ]
    )

    parameter_table = []
    parameter_table += _extract_parameters_from_model(
        enzmldoc.exportKineticParameters()
    )
    parameter_table += [
        _create_noise_parameters(species_id, enzmldoc)
        for species_id in observable_species
    ]

    return pd.DataFrame(parameter_table).drop_duplicates()


def _create_noise_parameters(species_id: str, enzmldoc):
    """Creates noise parameter and calculates the stdev for each species"""

    row = {
        "parameterId": f"sd_{species_id}",
        "parameterScale": "lin",
        "nominalValue": _calculate_stdev_by_id(species_id, enzmldoc),
        "estimate": 0,
        "upperBound": 1e6,
        "lowerBound": 1e-6,
    }

    if not row["nominalValue"]:
        row["estimate"] = 1
        row["nominalValue"] = None

    return row


def _calculate_stdev_by_id(species_id: str, enzmldoc):
    """Takes a species ID and calculates the standard deviation for all replicates"""

    stdevs = []
    replicates = enzmldoc.exportMeasurementData(species_ids=[species_id]).values()

    for replicate in replicates:

        data = replicate["data"]

        if species_id not in data.columns:
            continue

        stdevs += [
            np.std(list(data[data.time == time][species_id])) for time in data.time
        ]

    if stdevs:
        return np.std(stdevs)
    else:
        return 0.0


def _extract_parameters_from_model(kinetic_parameters: pd.DataFrame) -> List[Dict]:
    """Takes a kinetic parameter DataFrame and extracts these according to PeTAB"""

    kinetic_parameters.columns = _convert_columns(kinetic_parameters.columns)
    parameters = kinetic_parameters.drop(
        [
            col
            for col in kinetic_parameters.columns
            if col not in PARAMETER_MAPPING.values()
        ],
        axis=1,
    ).to_dict("records")

    return list(map(_apply_defaults, parameters))


def _convert_columns(cols: List[str]) -> List[str]:
    """Converts columns found in the parameter dataframe to PeTab compliant names"""

    nu_cols = []

    for col in cols:
        if col in PARAMETER_MAPPING:
            nu_cols.append(PARAMETER_MAPPING[col])
        else:
            nu_cols.append(col)

    return nu_cols


def _apply_defaults(record: Dict) -> Dict:
    """Applies all functions that optionally assign defaul values"""

    for key, value in record.items():
        if key not in PARAMETER_DEFAULTS:
            continue

        record[key] = PARAMETER_DEFAULTS[key](value)

    if record["estimate"]:
        record["nominalValue"] = None

    return record


def build_observable_table(enzmldoc, observable_ids):
    """Builds the observable table that is necessary for the PETab format"""

    observable_names = []
    observable_ids = list(set(observable_ids))

    for observable_id in observable_ids:
        observable_names.append(enzmldoc.getAny(observable_id.split("_")[0]).name)

    return pd.DataFrame(
        [
            {
                "observableId": observable_id,
                "observableName": observable_name,
                "observableFormula": observable_id.split("_")[0],
                "noiseFormula": f"noiseParameter1_{observable_id}",
                "noiseDistribution": "normal",
            }
            for observable_id, observable_name in zip(observable_ids, observable_names)
        ]
    ).drop_duplicates()


def check_and_set_initials(enzmldoc, set_species: set) -> None:
    """
    Checks whether species that have not been set within a measurement obatin
    an IC and set those that do not have one to 0.0
    """

    all_species = [
        *list(enzmldoc.reactant_dict.keys()),
        *list(enzmldoc.protein_dict.keys()),
        *list(enzmldoc.complex_dict.keys()),
    ]

    for species_id in all_species:
        if species_id in set_species:
            continue

        species = enzmldoc.getAny(species_id)

        if species.init_conc is None:
            species.init_conc = 0
            species.unit = "mmole / l"
