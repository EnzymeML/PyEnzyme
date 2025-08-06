from pathlib import Path
from typing import Union

import pandas as pd
import yaml

from pyenzyme.sbml.serializer import to_sbml
from pyenzyme.versions import v2

from .conditions import ConditionRow
from .measurements import MeasurementRow
from .observables import ObservableRow
from .parameters import ParameterRow
from .petab import PEtab, Problem

# Default filenames for PEtab format components
PARAMETER_FILENAME = "parameters.tsv"
CONDITION_FILENAME = "conditions.tsv"
OBSERVABLE_FILENAME = "observables.tsv"
MEASUREMENT_FILENAME = "measurements.tsv"
SBML_FILENAME = "model.xml"


def to_petab(doc: v2.EnzymeMLDocument, path: Union[Path, str]) -> PEtab:
    """
    Convert an EnzymeML document to a PEtab parameter estimation problem.

    This function exports an EnzymeML document to the PEtab format, which is a
    standardized format for specifying parameter estimation problems in systems biology.
    The function creates all necessary PEtab files:

    1. SBML model file: Contains the mathematical model specification
    2. Condition table: Specifies experimental conditions
    3. Observable table: Defines model outputs that correspond to measurements
    4. Measurement table: Contains experimental data points
    5. Parameter table: Defines model parameters and their estimation settings
    6. YAML configuration file: Links all files together in a PEtab problem definition

    Parameters
    ----------
    doc : v2.EnzymeMLDocument
        The EnzymeML document to convert, containing all model information,
        measurements, and parameters.
    path : Union[Path, str]
        Directory path where PEtab files will be written. If the directory
        doesn't exist, it will be created.

    Returns
    -------
    None
        Files are written to the specified path.

    Notes
    -----
    The file naming convention is based on the EnzymeML document name,
    with spaces replaced by underscores and converted to lowercase.
    """

    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        path.mkdir(parents=True)

    # Create paths for all PEtab files
    name = doc.name.replace(" ", "_").lower()
    meta_path = path / f"{name}.yaml"

    condition_name = f"{name}_{CONDITION_FILENAME}"
    condition_path = path / condition_name

    observable_name = f"{name}_{OBSERVABLE_FILENAME}"
    observable_path = path / observable_name

    measurement_name = f"{name}_{MEASUREMENT_FILENAME}"
    measurement_path = path / measurement_name

    parameter_name = f"{name}_{PARAMETER_FILENAME}"
    parameter_path = path / parameter_name

    sbml_name = f"{name}_{SBML_FILENAME}"
    sbml_path = path / sbml_name

    # Write SBML model file
    with open(sbml_path, "w") as f:
        sbml, _ = to_sbml(doc)
        f.write(sbml)

    # Generate and write conditions table
    pd.DataFrame(
        [row.to_row() for row in ConditionRow.from_measurements(doc.measurements)],
    ).to_csv(condition_path, index=False, sep="\t")

    # Generate and write observables table
    pd.DataFrame(
        [row.to_row() for row in ObservableRow.from_enzymeml(doc)],
    ).to_csv(observable_path, index=False, sep="\t")

    # Generate and write measurements table
    pd.DataFrame(
        [row.to_row() for row in MeasurementRow.from_measurements(doc.measurements)],
    ).to_csv(measurement_path, index=False, sep="\t")

    # Generate and write parameters table
    pd.DataFrame(
        [row.to_row() for row in ParameterRow.from_parameters(doc.parameters)],
    ).to_csv(parameter_path, index=False, sep="\t")

    # Create PEtab configuration object
    meta = PEtab(
        format_version=1,
        parameter_file=parameter_path,
        problems=[
            Problem(
                sbml_files=[sbml_path],
                measurement_files=[measurement_path],
                condition_files=[condition_path],
                observable_files=[
                    observable_path,
                ],
            )
        ],
    )

    # Serialize configuration to YAML
    with open(meta_path, "w") as f:
        yaml.dump(
            meta.model_dump(
                mode="json",
                by_alias=True,
                exclude_none=True,
            ),
            f,
        )

    return meta
