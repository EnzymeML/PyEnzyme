from enum import Enum
from typing import List, Optional
from pydantic import ConfigDict, Field, field_serializer, field_validator

from pyenzyme.versions import v2
from .baserow import BaseRow


class ParameterScale(Enum):
    """
    Enumeration of parameter scaling options.

    Defines how parameters are scaled for optimization and fitting.
    """

    LOG = "log"
    LOG10 = "log10"
    LIN = "lin"


class PriorType(Enum):
    """
    Enumeration of available prior distribution types.

    Defines the types of prior distributions that can be used for parameters
    in Bayesian parameter estimation.
    """

    NORMAL = "normal"
    UNIFORM = "uniform"
    LAPLACE = "laplace"
    LOGNORMAL = "lognormal"
    LOGLAPLACE = "loglaplace"
    PARAMETER_SCALE_UNIFORM = "parameterScaleUniform"
    PARAMETER_SCALE_NORMAL = "parameterScaleNormal"
    PARAMETER_SCALE_LAPLACE = "parameterScaleLaplace"


class ParameterRow(BaseRow):
    """
    Represents a row in a PEtab parameters table.

    This class models parameter information including bounds, scales, and prior
    distributions used for parameter estimation and optimization.
    """

    model_config = ConfigDict(use_enum_values=True)

    parameter_id: str = Field(alias="parameterId")
    parameter_name: Optional[str] = Field(alias="parameterName", default=None)
    parameter_scale: ParameterScale = Field(
        default=ParameterScale.LIN,
        alias="parameterScale",
    )
    lower_bound: float = Field(alias="lowerBound")
    upper_bound: float = Field(alias="upperBound")
    nominal_value: Optional[float] = Field(alias="nominalValue", default=None)
    estimate: bool = Field(alias="estimate", default=True)
    initialization_prior_type: PriorType = Field(
        default=PriorType.PARAMETER_SCALE_UNIFORM,
        alias="initializationPriorType",
    )
    initialization_prior_parameters: List[float] = Field(
        default_factory=list,
        alias="initializationPriorParameters",
    )
    objective_prior_type: PriorType = Field(
        default=PriorType.PARAMETER_SCALE_UNIFORM,
        alias="objectivePriorType",
    )
    objective_prior_parameters: List[float] = Field(
        default_factory=list,
        alias="objectivePriorParameters",
    )

    @field_serializer(
        "objective_prior_parameters",
        "initialization_prior_parameters",
    )
    def serialize_prior_parameters(self, v: List[float]) -> str:
        """
        Serializes a list of prior parameters into a semicolon-separated string.

        Args:
            v: List of float values representing prior parameters

        Returns:
            Semicolon-separated string of parameter values
        """
        return ";".join(map(str, v))

    @field_validator(
        "objective_prior_parameters",
        "initialization_prior_parameters",
        mode="before",
    )
    @classmethod
    def validate_prior_parameters(cls, v: str) -> List[float]:
        """
        Validates and converts a string of prior parameters into a list of floats.

        Args:
            v: Semicolon-separated string of parameter values

        Returns:
            List of float values parsed from the input string
        """
        return [float(x) for x in v.split(";")]

    @classmethod
    def from_parameters(cls, parameters: List[v2.Parameter]) -> List["ParameterRow"]:
        """
        Creates a list of ParameterRow objects from a list of PyEnzyme Parameter objects.
        """
        return [cls.from_parameter(parameter) for parameter in parameters]

    @classmethod
    def from_parameter(cls, parameter: v2.Parameter) -> "ParameterRow":
        """
        Creates a ParameterRow from a PyEnzyme Parameter object.
        """
        if parameter.lower_bound is None or parameter.upper_bound is None:
            raise ValueError("Parameter bounds are required")

        return cls(
            parameterId=parameter.id,
            parameterName=parameter.name,
            parameterScale=ParameterScale.LIN,
            lowerBound=parameter.lower_bound,
            upperBound=parameter.upper_bound,
            nominalValue=parameter.value,
        )
