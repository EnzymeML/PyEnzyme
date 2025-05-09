from functools import cached_property
from typing import Optional, List

import pandas as pd
from pydantic import BaseModel, ConfigDict, computed_field, field_validator

from pyenzyme.versions import v2
from pyenzyme import to_pandas, to_sbml


class BaseThinLayer(BaseModel):
    """
    Base class for thin layers that wrap EnzymeML documents.

    This class provides a foundation for creating specialized interfaces to EnzymeML documents,
    with built-in conversion to SBML and pandas DataFrames. It allows filtering measurements
    by their IDs.

    Attributes:
        enzmldoc (v2.EnzymeMLDocument): The EnzymeML document to wrap.
        measurement_ids (Optional[List[str]]): Optional list of measurement IDs to filter by.
            If None, all measurements are included.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    enzmldoc: v2.EnzymeMLDocument
    measurement_ids: Optional[List[str]] = None

    @field_validator("enzmldoc")
    @classmethod
    def check_measurement_ids(cls, enzmldoc: v2.EnzymeMLDocument):
        """
        Validates that the EnzymeML document contains at least one measurement.

        Args:
            enzmldoc (v2.EnzymeMLDocument): The EnzymeML document to validate.

        Returns:
            v2.EnzymeMLDocument: The validated EnzymeML document.

        Raises:
            ValueError: If the EnzymeML document has no measurements.
        """
        if len(enzmldoc.measurements) == 0:
            raise ValueError("EnzymeMLDocument has no measurements")

        return enzmldoc

    @computed_field(return_type=str)
    @cached_property
    def sbml_xml(self) -> str:
        """
        Converts the EnzymeML document to SBML XML format.

        Returns:
            str: The SBML XML representation of the EnzymeML document.
        """
        return to_sbml(self.enzmldoc)[0]

    @computed_field(return_type=dict[str, pd.DataFrame])
    @cached_property
    def data(self) -> dict[str, pd.DataFrame]:
        """
        Converts the EnzymeML document to pandas DataFrames, organized by measurement ID.

        If measurement_ids is specified, only those measurements are included in the result.

        Returns:
            dict[str, pd.DataFrame]: A dictionary mapping measurement IDs to their corresponding
                pandas DataFrames containing time series data.

        Raises:
            ValueError: If the conversion doesn't return a dictionary or if specified
                measurement IDs are not found in the document.
        """
        df_map = to_pandas(self.enzmldoc, per_measurement=True)

        if not isinstance(df_map, dict):
            raise ValueError("Expected a dictionary of dataframes")

        if self.measurement_ids is None:
            return df_map

        missing_ids = set(self.measurement_ids) - set(df_map.keys())
        if missing_ids:
            raise ValueError(f"Measurement ids {missing_ids} not found in data")

        return {k: v for k, v in df_map.items() if k in self.measurement_ids}
