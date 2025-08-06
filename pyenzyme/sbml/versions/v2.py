"""
This module contains the classes for the EnzymeML version 2 format annotations
used to map the EnzymeML JSON schema to SBML.

The classes in this module define the structure for annotating SBML models with
EnzymeML-specific information. These annotations allow for the representation of
enzymatic reactions, experimental data, and associated metadata in a standardized format.

Each annotation class corresponds to a specific aspect of enzymatic data, such as
small molecules, proteins, complexes, experimental measurements, and parameters.
"""

from __future__ import annotations

import pandas as pd
from mdmodels.units.unit_definition import UnitDefinition
from pydantic import field_validator
from pydantic_xml import BaseXmlModel, attr, element

from pyenzyme.sbml.utils import _get_unit
from pyenzyme.versions.v2 import DataTypes, Measurement


class BaseAnnot(BaseXmlModel):
    """
    Base class for annotations in the EnzymeML format.

    This class provides common functionality for all annotation classes,
    including methods to check if an annotation is empty.
    """

    def is_empty(self):
        """
        Check if the annotation is empty.

        Returns:
            bool: True if all attributes are None or empty lists, False otherwise.
        """
        return all(value is None or value == [] for _, value in self)


class V2Annotation(
    BaseAnnot,
    tag="annotation",
    search_mode="unordered",
    nsmap={"enzymeml": "https://www.enzymeml.org/v2"},
):
    """
    Top-level annotation class for EnzymeML version 2.

    This class serves as a container for all other annotation types and
    is attached to SBML elements to provide EnzymeML-specific information.

    Attributes:
        small_molecule (SmallMoleculeAnnot | None): Annotation for small molecules.
        protein (ProteinAnnot | None): Annotation for proteins.
        complex (ComplexAnnot | None): Annotation for complexes.
        data (DataAnnot | None): Annotation for experimental data.
        parameter (ParameterAnnot | None): Annotation for parameters.
        variables (VariablesAnnot | None): Annotation for variables.
    """

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

    This class contains chemical identifiers that help uniquely identify
    small molecules involved in enzymatic reactions.

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

    This class contains biological information about proteins, including
    their enzymatic classification, origin, and sequence.

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

    This class describes molecular complexes formed by multiple components,
    such as protein-protein or protein-substrate complexes.

    Attributes:
        participants (list[str]): A list of participants in the complex.
    """

    participants: list[str] = element(
        tag="participants",
        default_factory=list,
    )


class ModifierAnnot(
    BaseAnnot,
    tag="modifier",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for a modifier in the EnzymeML format.

    This class describes the modifier of a reaction, including its ID and name.
    """

    modifier_role: str = attr(name="modifierRole")


class DataAnnot(
    BaseAnnot,
    tag="data",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for data in the EnzymeML format.

    This class links experimental data files to measurements and provides
    methods to convert the data into Measurement objects.

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
        """
        Ensures that file paths start with './'.

        Args:
            value (str): The file path to validate.

        Returns:
            str: The validated file path.
        """
        if not value.startswith("./"):
            return "./" + value
        return value

    def to_measurements(
        self,
        meas_data: dict[str, pd.DataFrame],
        units: dict[str, UnitDefinition],
    ) -> list[Measurement]:
        """
        Converts data annotations to Measurement objects.

        This method processes the measurement annotations and associated data
        to create fully-populated Measurement objects.

        Args:
            meas_data (dict[str, pd.DataFrame]): Dictionary mapping file paths to data frames.
            units (dict[str, UnitDefinition]): Dictionary mapping unit IDs to UnitDefinition objects.

        Returns:
            list[Measurement]: List of created Measurement objects.

        Raises:
            AssertionError: If the specified data file is not found in the provided data.
        """
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

    This class describes experimental measurements, including conditions,
    time units, and species data.

    Attributes:
        id (str): The ID of the measurement.
        name (str | None): The name of the measurement.
        time_unit (str): The unit of time.
        conditions (ConditionsAnnot | None): The conditions associated with the measurement.
        species_data (list[SpeciesDataAnnot]): A list of species data associated with the measurement.
    """

    id: str = attr(name="id")
    name: str | None = attr(name="name", default=None)
    time_unit: str | None = attr(name="timeUnit", default=None)
    conditions: ConditionsAnnot | None = element(tag="conditions", default=None)
    species_data: list[SpeciesDataAnnot] = element(
        tag="speciesData",
        default_factory=list,
    )

    @field_validator("conditions")
    @classmethod
    def _check_conditions(cls, value: ConditionsAnnot):
        """
        Check if the conditions are empty.
        """
        if value.ph is None and value.temperature is None:
            return None
        return value

    def to_measurement(
        self,
        meas_data: pd.DataFrame,
        units: dict[str, UnitDefinition],
    ):
        """
        Converts a measurement annotation to a Measurement object.

        This method processes the measurement data, conditions, and species data
        to create a fully-populated Measurement object.

        Args:
            meas_data (pd.DataFrame): The data frame containing measurement data.
            units (dict[str, UnitDefinition]): Dictionary mapping unit IDs to UnitDefinition objects.

        Returns:
            Measurement: The created Measurement object.

        Raises:
            ValueError: If no data is found for the measurement ID.
        """
        df_sub = meas_data[meas_data.id == self.id]

        # Extract conditions data
        ph = None
        temperature = None
        temperature_unit = None

        # Python ☕️ Love it...
        if self.conditions:
            if self.conditions.ph:
                ph = self.conditions.ph.value

            if self.conditions.temperature:
                temperature = self.conditions.temperature.value
                if self.conditions.temperature.unit:
                    temperature_unit = _get_unit(
                        self.conditions.temperature.unit, units
                    )

        if not self.name:
            name = self.id
        else:
            name = self.name

        measurement = Measurement(
            id=self.id,
            name=name,
            temperature=temperature,
            temperature_unit=temperature_unit,  # type: ignore
            ph=ph,
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
        """
        Maps species data from a data frame to a Measurement object.

        This method extracts species-specific data from the data frame and
        adds it to the Measurement object.

        Args:
            df_sub (pd.DataFrame): The filtered data frame for the current measurement.
            measurement (Measurement): The Measurement object to add data to.
            species (SpeciesDataAnnot): The species data annotation.
            units (dict[str, UnitDefinition]): Dictionary mapping unit IDs to UnitDefinition objects.
        """
        if species.species_id in df_sub.columns:
            data = df_sub[species.species_id].to_list()
            time = df_sub["time"].to_list()
        else:
            data, time = [], []

        measurement.add_to_species_data(
            data=data,
            time=time,
            species_id=species.species_id,
            data_unit=_get_unit(species.unit, units),  # type: ignore
            time_unit=_get_unit(self.time_unit, units) if self.time_unit else None,  # type: ignore
            initial=species.initial,
            data_type=self._map_data_type(species.type),  # type: ignore
        )

    @staticmethod
    def _map_data_type(dtype: str) -> str:
        """
        Maps a string data type to a DataTypes enum value.

        Args:
            dtype (str): The string representation of the data type.

        Returns:
            DataTypes: The corresponding DataTypes enum value.

        Raises:
            ValueError: If the data type is not supported.
        """
        for data_type in DataTypes:
            if data_type.value == dtype or data_type.name == dtype:
                return data_type.value
        raise ValueError(f"Data type '{dtype}' not supported")


class SpeciesDataAnnot(
    BaseAnnot,
    tag="speciesData",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for species data in the EnzymeML format.

    This class describes data associated with a specific species, including
    its initial value, data type, and unit.

    Attributes:
        species_id (str): The ID of the species.
        initial (float): The value associated with the species.
        type (str | None): The type of data (default is "CONCENTRATION").
        unit (str): The unit of the value.
    """

    species_id: str = attr(name="species")
    initial: float | None = attr(name="value", default=None)
    type: str | None = attr(name="type", default=DataTypes.CONCENTRATION.value)
    unit: str = attr(name="unit")


class ConditionsAnnot(
    BaseAnnot,
    tag="conditions",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for conditions in the EnzymeML format.

    This class describes experimental conditions such as pH and temperature
    under which measurements were taken.

    Attributes:
        ph (PHAnnot | None): The pH conditions.
        temperature (TemperatureAnnot | None): The temperature conditions.
    """

    ph: PHAnnot | None = element(tag="ph", default=None)
    temperature: TemperatureAnnot | None = element(tag="temperature", default=None)

    @field_validator("ph")
    @classmethod
    def _check_ph(cls, value: PHAnnot):
        """
        Check if the conditions are empty.
        """
        if value.value is None:
            return None
        return value

    @field_validator("temperature")
    @classmethod
    def _check_temperature(cls, value: TemperatureAnnot):
        """
        Check if the temperature is empty.
        """
        if value.value is None and value.unit is None:
            return None
        return value


class PHAnnot(
    BaseAnnot,
    tag="ph",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for pH in the EnzymeML format.

    This class describes the pH value of an experimental condition.

    Attributes:
        value (float): The pH value.
    """

    value: float | None = attr(name="value")


class TemperatureAnnot(
    BaseAnnot,
    tag="temperature",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for temperature in the EnzymeML format.

    This class describes the temperature value and unit of an experimental condition.

    Attributes:
        value (float): The temperature value.
        unit (str): The unit of the temperature value.
    """

    value: float | None = attr(name="value", default=None)
    unit: str | None = attr(name="unit", default=None)


class ParameterAnnot(
    BaseAnnot,
    tag="parameter",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for a parameter in the EnzymeML format.

    This class describes statistical properties of parameters used in
    kinetic models, such as bounds and standard error.

    Attributes:
        lower (float | None): The lower bound of the parameter.
        upper (float | None): The upper bound of the parameter.
        stderr (float | None): The standard deviation of the parameter.
    """

    lower_bound: float | None = element(tag="lowerBound", default=None)
    upper_bound: float | None = element(tag="upperBound", default=None)
    stderr: float | None = element(tag="stdDeviation", default=None)


class VariablesAnnot(
    BaseAnnot,
    tag="variables",
    nsmap={"": "https://www.enzymeml.org/v2"},
    search_mode="unordered",
):
    """
    Represents the annotation for variables in the EnzymeML format.

    This class serves as a container for variable annotations used in
    kinetic models and equations.

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

    This class describes variables used in kinetic models and equations,
    including their identifiers and symbols.

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
    ModifierAnnot,
    VariableAnnot,
    V2Annotation,
]:
    cls.model_rebuild()
