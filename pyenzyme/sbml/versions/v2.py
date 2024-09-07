"""
This module contains the classes for the EnzymeML version 2 format annotations
used to map the EnzymeML JSON schema to SBML.
"""

from __future__ import annotations

import pandas as pd
from pydantic import field_validator
from pydantic_xml import element, attr, BaseXmlModel

from pyenzyme import UnitDefinition, DataTypes, Measurement


class BaseAnnot(BaseXmlModel):
    """
    Base class for annotations in the EnzymeML format.
    """

    def is_empty(self):
        return all(value is None or value == [] for _, value in self)


class V2Annotation(
    BaseAnnot,
    tag="annotation",
    search_mode="unordered",
    nsmap={"enzymeml": "https://www.enzymeml.org/v2"},
):
    small_molecule: SmallMoleculeAnnot | None = element(
        tag="smallMolecule",
        default=None,
    )

    protein: ProteinAnnot | None = element(
        tag="protein",
        default=None,
    )

    complex: ComplexAnnot | None = element(
        tag="complex",
        default=None,
    )

    data: DataAnnot | None = element(
        tag="data",
        default=None,
    )

    parameter: ParameterAnnot | None = element(
        tag="parameter",
        default=None,
    )

    variables: VariablesAnnot | None = element(
        tag="variables",
        default=None,
    )


class SmallMoleculeAnnot(
    BaseAnnot,
    tag="smallMolecule",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for a small molecule in the EnzymeML format.

    Attributes:
        inchikey (str | None): The InChIKey of the small molecule.
        canonical_smiles (str | None): The canonical SMILES representation of the small molecule.
    """

    inchikey: str | None = element(tag="inchiKey", default=None)
    canonical_smiles: str | None = element(tag="smiles", default=None)


class ProteinAnnot(
    BaseAnnot,
    tag="protein",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for a protein in the EnzymeML format.

    Attributes:
        ecnumber (str | None): The EC number of the protein.
        organism (str | None): The organism from which the protein is derived.
        organism_tax_id (str | None): The taxonomic ID of the organism.
        sequence (str | None): The amino acid sequence of the protein.
    """

    ecnumber: str | None = element(tag="ecnumber", default=None)
    organism: str | None = element(tag="organism", default=None)
    organism_tax_id: str | None = element(tag="organismTaxId", default=None)
    sequence: str | None = element(tag="sequence", default=None)


class ComplexAnnot(
    BaseAnnot,
    tag="complex",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for a complex in the EnzymeML format.

    Attributes:
        participants (list[str]): A list of participants in the complex.
    """

    participants: list[str] = element(
        tag="participants",
        default_factory=list,
    )


class DataAnnot(
    BaseAnnot,
    tag="data",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for data in the EnzymeML format.

    Attributes:
        file (str): The file associated with the data.
        measurements (list[MeasurementAnnot]): A list of measurements associated with the data.
    """

    file: str = attr(name="file")
    measurements: list[MeasurementAnnot] = element(
        tag="measurement",
        default_factory=list,
    )

    @field_validator("file")
    @classmethod
    def _check_file_path(cls, value):
        if not value.startswith("./"):
            return "./" + value
        return value

    def to_measurements(
        self,
        meas_data: dict[str, pd.DataFrame],
        units: dict[str, UnitDefinition],
    ) -> list[Measurement]:
        assert self.file in meas_data, f"Data file '{self.file}' not found in data"

        return [
            meas.to_measurement(
                meas_data=meas_data[self.file],
                units=units,
            )
            for meas in self.measurements
        ]


class MeasurementAnnot(
    BaseAnnot,
    tag="measurement",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for a measurement in the EnzymeML format.

    Attributes:
        id (str): The ID of the measurement.
        name (str | None): The name of the measurement.
        time_unit (str): The unit of time.
        conditions (ConditionsAnnot | None): The conditions associated with the measurement.
        species_data (list[SpeciesDataAnnot]): A list of species data associated with the measurement.
    """

    id: str = attr(name="id")
    name: str | None = attr(name="name", default=None)
    time_unit: str = attr(name="timeUnit")
    conditions: ConditionsAnnot | None = element(tag="conditions", default=None)
    species_data: list[SpeciesDataAnnot] = element(
        tag="speciesData",
        default_factory=list,
    )

    def to_measurement(
        self,
        meas_data: pd.DataFrame,
        units: dict[str, UnitDefinition],
    ):
        df_sub = meas_data[meas_data.id == self.id]
        measurement = Measurement(
            id=self.id,
            name=self.name,
            temperature=self.conditions.temperature.value,
            temperature_unit=units.get(self.conditions.temperature.unit),
            ph=self.conditions.ph.value,
        )

        if df_sub.empty:
            raise ValueError(f"No data found for measurement with ID '{self.id}'")

        for species in self.species_data:
            self._map_species_data(df_sub, measurement, species, units)

        return measurement

    def _map_species_data(
        self,
        df_sub: pd.DataFrame,
        measurement: Measurement,
        species: SpeciesDataAnnot,
        units: dict[str, UnitDefinition],
    ):
        if species.species_id in df_sub.columns:
            data = df_sub[species.species_id].to_list()
            time = df_sub["time"].to_list()
        else:
            data, time = None, None
        measurement.add_to_species_data(
            data=data,
            time=time,
            species_id=species.species_id,
            data_unit=units[species.unit],
            time_unit=units[self.time_unit],
            initial=species.initial,
            data_type=self._map_data_type(species.type),
        )

    @staticmethod
    def _map_data_type(dtype: str):
        if data_type := getattr(DataTypes, dtype, None):
            return data_type
        else:
            raise ValueError(f"Data type '{dtype}' not supported")


class SpeciesDataAnnot(
    BaseAnnot,
    tag="speciesData",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for species data in the EnzymeML format.

    Attributes:
        species_id (str): The ID of the species.
        initial (float): The value associated with the species.
        type (str | None): The type of data (default is "CONCENTRATION").
        unit (str): The unit of the value.
    """

    species_id: str = attr(name="species")
    initial: float = attr(name="value", default=0.0)
    type: str | None = attr(name="type", default="CONCENTRATION")
    unit: str = attr(name="unit")


class ConditionsAnnot(
    BaseAnnot,
    tag="conditions",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for conditions in the EnzymeML format.

    Attributes:
        ph (PHAnnot | None): The pH conditions.
        temperature (TemperatureAnnot | None): The temperature conditions.
    """

    ph: PHAnnot | None = element(tag="ph")
    temperature: TemperatureAnnot | None = element(tag="temperature", default=None)


class PHAnnot(
    BaseAnnot,
    tag="ph",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for pH in the EnzymeML format.

    Attributes:
        value (float): The pH value.
    """

    value: float = attr(name="value")


class TemperatureAnnot(
    BaseAnnot,
    tag="temperature",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for temperature in the EnzymeML format.

    Attributes:
        value (float): The temperature value.
        unit (str): The unit of the temperature value.
    """

    value: float = attr(name="value")
    unit: str = attr(name="unit")


class ParameterAnnot(
    BaseAnnot,
    tag="parameter",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for a parameter in the EnzymeML format.

    Attributes:
        lower (float | None): The lower bound of the parameter.
        upper (float | None): The upper bound of the parameter.
        stderr (float | None): The standard deviation of the parameter.
    """

    lower: float | None = element(tag="lowerBound", default=None)
    upper: float | None = element(tag="upperBound", default=None)
    stderr: float | None = element(tag="stdDeviation", default=None)


class VariablesAnnot(
    BaseAnnot,
    tag="variables",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for variables in the EnzymeML format.

    Attributes:
        variables (list[Variable]): A list of variables.
    """

    variables: list[VariableAnnot] = element(tag="variable", default_factory=list)


class VariableAnnot(
    BaseAnnot,
    tag="variable",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents a variable in the EnzymeML format.

    Attributes:
        id (str | None): The ID of the variable.
        name (str | None): The name of the variable.
        symbol (str | None): The symbol of the variable.
    """

    id: str | None = attr(name="id")
    name: str | None = attr(name="name")
    symbol: str | None = attr(name="symbol")


# Rebuild all the classes within this file
for cls in [
    SmallMoleculeAnnot,
    ProteinAnnot,
    ComplexAnnot,
    DataAnnot,
    MeasurementAnnot,
    SpeciesDataAnnot,
    ConditionsAnnot,
    PHAnnot,
    TemperatureAnnot,
    ParameterAnnot,
    VariablesAnnot,
    VariableAnnot,
    V2Annotation,
]:
    cls.model_rebuild()
