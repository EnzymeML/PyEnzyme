from typing import List, Union
from pydantic import Field

from pyenzyme.versions import v2
from .baserow import BaseRow


class MeasurementRow(BaseRow):
    """
    Represents a row in a PEtab measurements table.

    This class models experimental measurements with species initial concentrations
    and other measurement-specific parameters.

    Attributes:
        observable_id (str): The identifier of the observable being measured.
            Maps to 'observableId' in the PEtab specification.
        preequilibration_condition_id (str | None): The identifier of the preequilibration condition.
            Maps to 'preequilibrationConditionId' in the PEtab specification.
            Defaults to None if no preequilibration was performed.
        condition_id (str): The identifier of the simulation condition.
            Maps to 'simulationConditionId' in the PEtab specification.
        measurement (float): The measured value of the observable.
            Maps to 'measurement' in the PEtab specification.
        time (float): The time point at which the measurement was taken.
            Maps to 'time' in the PEtab specification.
        observable_parameters (Union[str, float, None]): Parameters for the observable transformation.
            Maps to 'observableParameters' in the PEtab specification.
            Can be a parameter ID, a numeric value, or None if not applicable.
        noise_parameters (Union[str, float, None]): Parameters for the noise model.
            Maps to 'noiseParameters' in the PEtab specification.
            Can be a parameter ID, a numeric value, or None if not applicable.
        dataset_id (str | None): An identifier for the dataset this measurement belongs to.
            Maps to 'datasetId' in the PEtab specification.
            Useful for grouping measurements from the same experiment.
        replicate_id (str | None): An identifier for the replicate this measurement belongs to.
            Maps to 'replicateId' in the PEtab specification.
            Useful for identifying repeated measurements under identical conditions.
    """

    observable_id: str = Field(alias="observableId")
    preequilibration_condition_id: str | None = Field(
        default=None,
        alias="preequilibrationConditionId",
    )
    condition_id: str = Field(alias="simulationConditionId")
    measurement: float = Field(alias="measurement")
    time: float = Field(alias="time")
    observable_parameters: Union[str, float, None] = Field(
        default=None,
        alias="observableParameters",
    )
    noise_parameters: Union[str, float, None] = Field(
        default=None,
        alias="noiseParameters",
    )
    dataset_id: str | None = Field(alias="datasetId", default=None)
    replicate_id: str | None = Field(alias="replicateId", default=None)

    @classmethod
    def from_measurements(
        cls, measurements: list[v2.Measurement]
    ) -> List["MeasurementRow"]:
        """
        Convert a list of EnzymeML Measurement objects to a list of PEtab MeasurementRow objects.
        """
        return [
            row
            for measurement in measurements
            for row in cls.from_measurement(measurement)
        ]

    @classmethod
    def from_measurement(cls, measurement: v2.Measurement) -> List["MeasurementRow"]:
        """
        Convert an EnzymeML Measurement object to a list of PEtab MeasurementRow objects.

        This method extracts the time series data from a Measurement object and creates
        individual MeasurementRow entries for each time point and corresponding data value.

        Args:
            measurement (v2.Measurement): An EnzymeML Measurement object containing
                species concentration time series data.

        Returns:
            List["MeasurementRow"]: A list of MeasurementRow objects, each representing a single
                data point from the original measurement. Each row contains the species ID,
                measurement condition ID, the measured value, and the time point.

        Example:
            If a Measurement contains data for species 'S1' with time points [0, 10, 20]
            and corresponding values [1.0, 0.8, 0.6], this method will return three
            MeasurementRow objects, one for each time-value pair.
        """
        meas_rows = []
        for meas_data in measurement.species_data:
            for t, x in zip(meas_data.time, meas_data.data):
                meas_rows.append(
                    cls(
                        observableId=meas_data.species_id,
                        simulationConditionId=measurement.id,
                        measurement=x,
                        time=t,
                    )
                )
        return meas_rows
