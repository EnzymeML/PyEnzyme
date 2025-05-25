from typing import Dict, Any
from pydantic import Field

from pyenzyme.versions import v2
from .baserow import BaseRow


class ConditionRow(BaseRow):
    """
    Represents a row in a PEtab conditions table.

    This class models experimental conditions with species initial concentrations
    and other condition-specific parameters.

    Attributes:
        condition_id: Unique identifier for the condition
        condition_name: Human-readable name for the condition
        species: Dictionary mapping species IDs to their initial concentrations
    """

    condition_id: str = Field(alias="conditionId")
    condition_name: str = Field(alias="conditionName")
    species: dict[str, float] = Field(default_factory=dict)

    def to_row(self) -> Dict[str, Any]:
        """
        Converts the condition to a dictionary suitable for a PEtab conditions table row.

        Returns:
            Dictionary with condition ID, name, and species initial concentrations
        """
        return {
            **self.model_dump(exclude={"species"}, by_alias=True),
            **self.species,
        }

    @classmethod
    def from_measurements(
        cls, measurements: list[v2.Measurement]
    ) -> list["ConditionRow"]:
        """
        Creates a list of ConditionRow objects from a list of PyEnzyme Measurement objects.
        """
        return [cls.from_measurement(measurement) for measurement in measurements]

    @classmethod
    def from_measurement(cls, measurement: v2.Measurement) -> "ConditionRow":
        """
        Creates a ConditionRow from a PyEnzyme Measurement object.

        This method extracts species initial concentrations from the measurement
        and creates a corresponding condition row.

        Args:
            measurement: PyEnzyme Measurement object containing species data

        Returns:
            A new ConditionRow instance with data from the measurement
        """
        inits = {
            str(meas_data.species_id): meas_data.initial
            for meas_data in measurement.species_data
            if meas_data.initial is not None
        }

        return cls(
            conditionId=measurement.id,
            conditionName=measurement.name,
            species=inits,
        )
