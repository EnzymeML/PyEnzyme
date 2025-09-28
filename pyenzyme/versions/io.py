import json
from pathlib import Path
from typing import Optional

import pandas as pd
import rich
from pydantic import ValidationError

from pyenzyme.petab.io import to_petab
from pyenzyme.petab.petab import PEtab
from pyenzyme.sbml.parser import read_sbml
from pyenzyme.sbml.serializer import to_sbml
from pyenzyme.tabular import from_dataframe, read_csv, read_excel, to_pandas
from pyenzyme.versions import v2

AVAILABLE_VERSIONS = ["v1", "v2"]


class EnzymeMLHandler:
    """Handler for EnzymeML document operations.

    This class provides methods for reading, writing, and converting EnzymeML documents
    between different formats including JSON, SBML, CSV, Excel, and pandas DataFrames.
    """

    @classmethod
    def read_enzymeml(cls, path: str) -> v2.EnzymeMLDocument:  # noqa: F405
        """Read an EnzymeML document from a file.

        Attempts to read the document using different version parsers until successful.

        Args:
            path: Path to the EnzymeML document file

        Returns:
            An EnzymeMLDocument object

        Raises:
            ValueError: If the document cannot be parsed with any available version
        """
        error = None
        for version in AVAILABLE_VERSIONS:
            if version == "v1":
                try:
                    return read_sbml(v2.EnzymeMLDocument, path)
                except Exception:
                    continue
            elif version == "v2":
                try:
                    with open(path, "r") as f:
                        data = json.load(f)

                    return v2.EnzymeMLDocument.model_validate(data)
                except ValidationError as e:
                    error = e
                    continue

        raise ValueError(f"Invalid EnzymeML version: {path}") from error

    @classmethod
    def read_enzymeml_from_string(cls, data: str) -> v2.EnzymeMLDocument:  # noqa: F405
        """Read an EnzymeML document from a string.

        Attempts to read the document using different version parsers until successful.

        Args:
            data: The EnzymeML document as a string

        Returns:
            An EnzymeMLDocument object

        Raises:
            ValueError: If the document cannot be parsed with any available version
        """
        for version in AVAILABLE_VERSIONS:
            if version == "v2":
                try:
                    return v2.EnzymeMLDocument.model_validate(data)
                except ValidationError:
                    continue

        raise ValueError("Could not parse EnzymeML document: Invalid JSON")

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        data_unit: str,
        time_unit: str,
    ) -> list[v2.Measurement]:  # noqa: F405
        """Parse a pandas DataFrame into a list of measurements.

        This function expects the DataFrame to have the following structure:

            - time: The time points of the measurements. Should start at 0.
            - id: The ID of the measurement. Only needed in case of multiple measurements.
            - [species_id]: Per column, the data of a species.

        If there is no 'id' column, the function assumes that there is only one measurement
        in the file. If there is an 'id' column, the function assumes that there are multiple
        measurements in the file. Hence, if you want to have multiple measurements in the same
        file, you need to have an 'id' column. Otherwise, it will return a single measurement.

        Args:
            df (pd.DataFrame): The DataFrame to parse.
            data_unit (str): The unit of the data.
            time_unit (str): The unit of the time.

        Returns:
            list[Measurement]: A list of Measurement objects.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the path is not a file.
        """
        return from_dataframe(df, data_unit, time_unit)

    @classmethod
    def write_enzymeml(
        cls,
        enzmldoc: v2.EnzymeMLDocument,
        path: Path | str | None = None,
    ) -> Optional[str]:  # noqa: F405
        """Write an EnzymeML document to a file or return as a string.

        Args:
            enzmldoc: The EnzymeML document to write
            path: Path to write the document to. If None, returns the document as a string

        Returns:
            The document as a string if path is None, otherwise None
        """
        data = json.loads(enzmldoc.model_dump_json(exclude_none=True, by_alias=True))
        data = json.dumps(sort_by_ld(data), indent=2)

        if path is None:
            return data
        elif isinstance(path, str):
            path = Path(path)

        if path.is_dir():
            path = path / "experiment.json"

        with open(path, "w") as f:
            f.write(data)

        rich.print(
            f"\n  EnzymeML document written to [green][bold]{path}[/bold][/green]\n"
        )

    @classmethod
    def to_sbml(
        cls,
        enzmldoc: v2.EnzymeMLDocument,
        path: Path | str | None = None,
        verbose: bool = False,
    ) -> tuple[str, pd.DataFrame | None]:  # noqa: F405
        """Convert an EnzymeML document to SBML format and write it to a file.

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
            path (Path | str | None, optional): The output file to write the SBML document to. Defaults to None.
            verbose (bool, optional): Whether to print warnings during SBML validation. Defaults to False.

        Returns:
            tuple[str, pd.DataFrame]: The SBML document as a string, and a DataFrame with the measurement data.

        Raises:
            ValueError: If the EnzymeML document is not valid for SBML export.
        """
        return to_sbml(enzmldoc, path, verbose)

    @classmethod
    def to_petab(
        cls,
        enzmldoc: v2.EnzymeMLDocument,
        path: Path | str,
    ) -> PEtab:  # noqa: F405
        """
        Convert an EnzymeML document to a PEtab parameter estimation problem and write to file.

        This function exports an EnzymeML document to the PEtab format, which is a
        standardized format for specifying parameter estimation problems in systems biology.
        The function creates all necessary PEtab files:

        1. SBML model file: Contains the mathematical model specification
        2. Condition table: Specifies experimental conditions
        3. Observable table: Defines model outputs that correspond to measurements
        4. Measurement table: Contains experimental data points
        5. Parameter table: Defines model parameters and their estimation settings
        6. YAML configuration file: Links all files together in a PEtab problem definition

        Args
        ----
        enzmldoc : v2.EnzymeMLDocument
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
        return to_petab(enzmldoc, path)

    @classmethod
    def from_sbml(
        cls,
        path: Path | str,
    ) -> v2.EnzymeMLDocument:  # noqa: F405
        """
        Read an SBML file and initialize an EnzymeML document.

        This function reads an SBML file from an OMEX archive, extracts all relevant
        information, and creates an EnzymeML document with the extracted data. It handles
        different versions of the EnzymeML format and maps SBML elements to their
        corresponding EnzymeML entities.

        Args:
            path (Path | str): The path to the OMEX archive containing the SBML file.

        Returns:
            An initialized EnzymeMLDocument object with extracted units, species, vessels,
            equations, parameters, reactions, and measurements.
        """
        return read_sbml(v2.EnzymeMLDocument, path)

    @classmethod
    def to_pandas(
        cls,
        enzmldoc: v2.EnzymeMLDocument,
        per_measurement: bool = False,
    ) -> pd.DataFrame | dict[str, pd.DataFrame]:  # noqa: F405
        """Convert an EnzymeML document to a pandas DataFrame.

        The resulting DataFrame contains the following columns:

            - time: The time values of the measurement.
            - id: The ID of the measurement.
            - [species]: The species data of the measurement per column.

        Args:
            enzmldoc (EnzymeMLDocument): The EnzymeMLDocument object to convert
            per_measurement (bool): If True, returns a dictionary of DataFrames keyed by measurement ID.
                If False, returns a single DataFrame containing all measurements.

        Returns:
            pd.DataFrame or dictionary of DataFrames containing the measurement data,
                or None if no measurements exist
        """
        df = to_pandas(enzmldoc)

        if per_measurement and df is not None:
            return split_by_measurement(df)

        if df is None:
            return pd.DataFrame()

        return df

    @classmethod
    def from_csv(
        cls,
        path: Path | str,
        data_unit: str,
        time_unit: str,
        data_type: v2.DataTypes = v2.DataTypes.CONCENTRATION,
        sep: str = "\t",
    ) -> list[v2.Measurement]:  # noqa: F405
        """Reads a CSV file from the specified path into a measurement.

        This function expects the CSV file to have the following structure:

            - time: The time points of the measurements. Should start at 0.
            - id: The ID of the measurement. Only needed in case of multiple measurements.
            - [species_id]: Per column, the data of a species.

        If there is no 'id' column, the function assumes that there is only one measurement
        in the file. If there is an 'id' column, the function assumes that there are multiple
        measurements in the file. Hence, if you want to have multiple measurements in the same
        file, you need to have an 'id' column. Otherwise it will return a single measurement.

        Args:
            path (str, pathlib.Path): The path to the CSV file.
            data_unit (str): The unit of the data.
            time_unit (str): The unit of the time.
            data_type (DataTypes): The type of the data. Default is DataTypes.CONCENTRATION.
            sep (str): The separator of the CSV file. Default is '\t'.

        Returns:
            list[Measurement]: A list of Measurement objects.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the path is not a file.
        """
        return read_csv(path, data_unit, time_unit, data_type, sep)

    @classmethod
    def from_excel(
        cls,
        path: Path | str,
        data_unit: str,
        time_unit: str,
        data_type: v2.DataTypes = v2.DataTypes.CONCENTRATION,
    ) -> list[v2.Measurement]:  # noqa: F405
        """Reads an Excel file from the specified path into Measurement objects.

        This function expects the Excel file to have the following structure:

            - time: The time points of the measurements. Should start at 0.
            - id: The ID of the measurement. Only needed in case of multiple measurements.
            - [species_id]: Per column, the data of a species.

        If there is no 'id' column, the function assumes that there is only one measurement
        in the file. If there is an 'id' column, the function assumes that there are multiple
        measurements in the file. Hence, if you want to have multiple measurements in the same
        file, you need to have an 'id' column. Otherwise it will return a single measurement.

        Args:
            path (str, pathlib.Path): The path to the Excel file.
            data_unit (str): The unit of the data.
            time_unit (str): The unit of the time.
            data_type (DataTypes): The type of the data. Default is DataTypes.CONCENTRATION.

        Returns:
            list[Measurement]: A list of measurements.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the path is not a file.
        """
        return read_excel(path, data_unit, time_unit, data_type)


def sort_by_ld(d: dict) -> dict:
    """Sort a dictionary according to JSON-LD conventions.

    Sorts keys so that @context, @id, and @type appear first, followed by other keys.

    Args:
        d: Dictionary to sort

    Returns:
        Sorted dictionary
    """
    keys = sorted(d.keys(), key=_pattern)
    data = {}

    for key in keys:
        value = d[key]

        if isinstance(value, dict):
            data[key] = sort_by_ld(value)
        elif isinstance(value, list) and all(isinstance(v, dict) for v in value):
            data[key] = [sort_by_ld(v) for v in value]
        else:
            data[key] = value

    return data


def _pattern(s: str):
    """Helper function for sorting JSON-LD keys.

    Args:
        s: Key string

    Returns:
        Priority value for sorting (lower values come first)
    """
    if s.startswith("@context"):
        return 0
    elif s.startswith("@id"):
        return 1
    elif s.startswith("@type"):
        return 2
    else:
        return 3


def split_by_measurement(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Split a pandas DataFrame by measurement ID.

    Args:
        df: DataFrame to split

    Returns:
        Dictionary of DataFrames, keyed by measurement ID
    """
    measurement_dfs = {}
    for measurement_id in df["id"].unique():
        measurement = df[df["id"] == measurement_id].reset_index(drop=True)

        # Remove ID column
        measurement = measurement.drop(columns=["id"])

        measurement_dfs[measurement_id] = measurement

    return measurement_dfs
