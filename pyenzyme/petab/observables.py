from enum import Enum
from typing import List, Optional
from pydantic import ConfigDict, Field

from pyenzyme.versions import v2
from .baserow import BaseRow


class Transformation(Enum):
    LIN = "lin"
    LOG = "log"
    LOG10 = "log10"


class NoiseDistribution(Enum):
    NORMAL = "normal"
    LAPLACE = "laplace"


class ObservableRow(BaseRow):
    model_config = ConfigDict(use_enum_values=True)

    observable_id: str = Field(alias="observableId")
    observable_name: Optional[str] = Field(alias="observableName", default=None)
    observable_formula: str = Field(alias="observableFormula")
    observable_noise: Optional[float] = Field(alias="observableNoise", default=0.0)
    observable_transformation: Transformation = Field(
        alias="observableTransformation",
        default=Transformation.LIN,
    )
    noise_formula: Optional[str] = Field(
        default=None,
        alias="noiseFormula",
    )
    noise_distribution: Optional[NoiseDistribution] = Field(
        default=None,
        alias="noiseDistribution",
    )

    @classmethod
    def from_enzymeml(cls, enzmldoc: v2.EnzymeMLDocument) -> List["ObservableRow"]:
        """Extract observable rows from an EnzymeML document.

        Collects all species with data across measurements and creates observable rows.
        """
        if not enzmldoc.measurements:
            return []

        # Get observables from first measurement
        first_measurement = enzmldoc.measurements[0]
        observables = {
            meas_data.species_id
            for meas_data in first_measurement.species_data
            if meas_data.data
        }

        for measurement in enzmldoc.measurements[1:]:
            current_observables = {
                meas_data.species_id
                for meas_data in measurement.species_data
                if meas_data.data
            }

            missing = current_observables - observables
            if missing:
                raise ValueError(
                    f"Observable(s) {missing} not present in all measurements"
                )

        # Create observable rows
        return [
            cls(
                observableId=obs,
                observableName=obs,
                observableFormula=obs,
                observableNoise=0.0,
                observableTransformation=Transformation.LIN,
            )
            for obs in observables
        ]
