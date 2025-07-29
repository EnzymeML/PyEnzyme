import json
from pathlib import Path
from typing import Optional

import pandas as pd

from pydantic import ValidationError
import rich
from pyenzyme.petab.io import to_petab
from pyenzyme.petab.petab import PEtab
from pyenzyme.sbml.serializer import to_sbml
from pyenzyme.tabular import from_dataframe, read_csv, read_excel, to_pandas
from pyenzyme.versions import v2
from pyenzyme.sbml.parser import read_sbml

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
                except ValidationError:
                    continue

        raise ValueError(f"Invalid EnzymeML version: {path}")

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
        """Create measurements from a pandas DataFrame.

        Args:
            df: DataFrame containing measurement data
            data_unit: Unit for the measurement data
            time_unit: Unit for the time data

        Returns:
            List of Measurement objects
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
    ) -> tuple[str, pd.DataFrame | None]:  # noqa: F405
        """Convert an EnzymeML document to SBML format and write to a file.

        Args:
            enzmldoc: The EnzymeML document to convert
            path: Path to write the SBML document to

        Returns:
            Tuple of the SBML document and the measurement data, or None if path is None
        """
        return to_sbml(enzmldoc, path)

    @classmethod
    def to_petab(
        cls,
        enzmldoc: v2.EnzymeMLDocument,
        path: Path | str,
    ) -> PEtab:  # noqa: F405
        """Convert an EnzymeML document to PEtab format and write to a file.

        Args:
            enzmldoc: The EnzymeML document to convert
            path: Path to write the PEtab document to

        Returns:
            The PEtab object
        """
        return to_petab(enzmldoc, path)

    @classmethod
    def from_sbml(
        cls,
        path: Path | str,
    ) -> v2.EnzymeMLDocument:  # noqa: F405
        """Read an EnzymeML document from an SBML file.

        Args:
            path: Path to the SBML file

        Returns:
            An EnzymeMLDocument object
        """
        return read_sbml(v2.EnzymeMLDocument, path)

    @classmethod
    def to_pandas(
        cls,
        enzmldoc: v2.EnzymeMLDocument,
        per_measurement: bool = False,
    ) -> pd.DataFrame | dict[str, pd.DataFrame]:  # noqa: F405
        """Convert an EnzymeML document to a pandas DataFrame.

        Args:
            enzmldoc: The EnzymeML document to convert

        Returns:
            DataFrame containing the measurement data, or None if no measurements exist
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
        """Create measurements from a CSV file.

        Args:
            path: Path to the CSV file
            data_unit: Unit for the measurement data
            time_unit: Unit for the time data
            data_type: Type of data (default: CONCENTRATION)
            sep: Separator used in the CSV file (default: tab)

        Returns:
            List of Measurement objects
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
        """Create measurements from an Excel file.

        Args:
            path: Path to the Excel file
            data_unit: Unit for the measurement data
            time_unit: Unit for the time data
            data_type: Type of data (default: CONCENTRATION)

        Returns:
            List of Measurement objects
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
