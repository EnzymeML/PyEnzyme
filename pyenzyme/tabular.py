from __future__ import annotations

import pathlib as pl

import pandas as pd

from mdmodels.units.unit_definition import UnitDefinition

from .versions.v2 import (
    DataTypes,
    Measurement,
    EnzymeMLDocument,
    MeasurementData,
)


def to_pandas(
    enzmldoc: EnzymeMLDocument,
    ignore: list[str] | None = None,
) -> pd.DataFrame | None:
    """This function converts an EnzymeMLDocument object to a pandas DataFrame.

    The resulting DataFrame contains the following columns:

        - time: The time values of the measurement.
        - id: The ID of the measurement.
        - [species]: The species data of the measurement per column.

    Args:
        enzmldoc (EnzymeMLDocument): The EnzymeMLDocument object to convert.
        ignore (list[str], optional): A list of measurement IDs to ignore. Defaults to [].

    Returns:
        pd.DataFrame: The EnzymeMLDocument object as a pandas DataFrame.

    Raises:
        ValueError: If the input is not an EnzymeMLDocument object.
        ValueError: If the measurements are not of type Measurement.
        ValueError: If the measurement does not contain species data.
    """

    if not _has_measurement_data(enzmldoc):
        return None

    if ignore is None:
        ignore = []

    assert isinstance(enzmldoc, EnzymeMLDocument), (
        "The input must be an EnzymeMLDocument object"
    )

    dfs = []
    for meas in enzmldoc.measurements:
        if meas.id in ignore:
            continue

        if not isinstance(meas, Measurement):
            raise ValueError("The measurements must be of type Measurement")
        if meas.species_data is None:
            raise ValueError("The measurement must contain species data")

        df = _measurement_to_pandas(meas)
        df["id"] = [meas.id] * len(df)
        dfs.append(df)

    if dfs:
        return pd.concat(dfs, ignore_index=True).reset_index(drop=True)
    else:
        return pd.DataFrame()


def _has_measurement_data(enzmldoc: EnzymeMLDocument) -> bool:
    """Checks if the measurement contains species data."""
    for meas in enzmldoc.measurements:
        for meas_data in meas.species_data:
            if meas_data.data is not None and len(meas_data.data) > 0:
                return True
    return False


def read_excel(
    path: pl.Path | str,
    data_unit: str,
    time_unit: str,
    data_type: DataTypes = DataTypes.CONCENTRATION,
):
    """Reads an Excel file from the specified path into a measurement.

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

    if isinstance(path, str):
        path = pl.Path(path)

    if not path.exists():
        raise FileNotFoundError(f"The file '{path}' does not exist.")
    elif not path.is_file():
        raise ValueError(f"The path '{path}' is not a file.")

    df = pd.read_excel(path)

    return from_dataframe(
        df=df,
        meas_id=path.stem,
        data_unit=data_unit,
        time_unit=time_unit,
        data_type=data_type,
    )


def read_csv(
    path: pl.Path | str,
    data_unit: str,
    time_unit: str,
    data_type: DataTypes = DataTypes.CONCENTRATION,
    sep: str = "\t",
):
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
        list[Measurement]: A list of measurements.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a file.
    """

    if isinstance(path, str):
        path = pl.Path(path)

    if not path.exists():
        raise FileNotFoundError(f"The file '{path}' does not exist.")
    elif not path.is_file():
        raise ValueError(f"The path '{path}' is not a file.")

    df = pd.read_csv(path, sep=sep)

    return from_dataframe(
        df=df,
        meas_id=path.stem,
        data_unit=data_unit,
        time_unit=time_unit,
        data_type=data_type,
    )


def from_dataframe(
    df: pd.DataFrame,
    data_unit: str,
    time_unit: str,
    data_type: DataTypes = DataTypes.CONCENTRATION,
    meas_id: str | None = None,
) -> list[Measurement]:
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
        meas_id (str | None): The ID of the measurement. Default is None.
        data_unit (str): The unit of the data.
        time_unit (str): The unit of the time.
        data_type (DataTypes): The type of the data. Default is DataTypes.CONCENTRATION.

    Returns:
        list[Measurement]: A list of measurements.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a file.
    """

    _validate_data(df)

    if "id" in df:
        return _process_multiple_measurements(
            df=df,
            data_unit=data_unit,
            time_unit=time_unit,
            data_type=data_type,
        )
    else:
        assert meas_id is not None, (
            "The 'meas_id' argument must be provided when parsing a single measurement"
        )
        return [
            _create_single_measurement(
                df=df,
                id=meas_id,
                data_unit=data_unit,
                time_unit=time_unit,
                data_type=data_type,
            )
        ]


def _create_single_measurement(
    df: pd.DataFrame,
    id: str,
    data_unit: str | UnitDefinition,
    time_unit: str | UnitDefinition,
    data_type: DataTypes,
) -> Measurement:
    data = df.to_dict(orient="list")
    time = data.pop("time")
    meas_data = []

    if isinstance(data_unit, UnitDefinition):
        data_unit = data_unit.name  # type: ignore
    if isinstance(time_unit, UnitDefinition):
        time_unit = time_unit.name  # type: ignore

    for species_id, species_data in data.items():
        if species_id == "id":
            continue

        meas_data.append(
            MeasurementData(
                species_id=str(species_id),
                data=species_data,
                time=time,
                data_unit=data_unit,  # type: ignore
                time_unit=time_unit,  # type: ignore
                initial=float(species_data[0]),
                data_type=data_type,
            )
        )

    return Measurement(name=id, id=id, species_data=meas_data)


def _process_multiple_measurements(
    df: pd.DataFrame,
    data_unit: str,
    time_unit: str,
    data_type: DataTypes,
) -> list[Measurement]:
    ids = df["id"].unique()
    measurements = []

    for id in ids:
        sub_df = df[df["id"] == id]
        measurements.append(
            _create_single_measurement(
                df=sub_df,  # type: ignore
                id=id,
                data_unit=data_unit,
                time_unit=time_unit,
                data_type=data_type,
            )
        )

    return measurements


def _validate_data(data: pd.DataFrame) -> None:
    """Validates the data from a CSV file"""
    assert "time" in data, "The CSV file must contain a 'time' column"
    assert data["time"][0] == 0, "The time column must start at 0"

    for col in data.columns:
        if col == "id":
            continue
        assert data[col].dtype == "float64" or data[col].dtype == "int64", (
            f"The column '{col}' must contain only numerical values"
        )


def _measurement_to_pandas(measurement: Measurement) -> pd.DataFrame:
    """Converts a Measurement object to a pandas DataFrame"""

    _validate_measurement(measurement)

    data = {"time": _get_time_array(measurement)}
    for species in measurement.species_data:
        if len(species.data) > 0:
            data[species.species_id] = species.data

    return pd.DataFrame(data)


def _get_time_array(measurement: Measurement):
    for meas_data in measurement.species_data:
        if len(meas_data.time) > 0:
            return meas_data.time


def _validate_measurement(meas: Measurement) -> None:
    """Validates a Measurement object"""

    # Check if the length of time is consistent
    try:
        times = pd.DataFrame(
            {
                species.species_id + "_time": species.time
                for species in meas.species_data
                if len(species.time) > 0
            }
        )
    except ValueError:
        time_lengths = {
            species.species_id: len(species.time) for species in meas.species_data
        }
        raise ValueError(
            f"Export to pandas not possible, the time lengths are inconsistent. Got different time arrays per species: {time_lengths}"
        )

    # Check if the time arrays are the same
    all_columns_same = bool(times.apply(lambda col: col.equals(times.iloc[:, 0])).all())
    if not all_columns_same:
        raise ValueError(
            f"Export to pandas not possible, the time arrays are inconsistent. Got different time arrays per species: \n\n {times.T} \n\n"
        )
