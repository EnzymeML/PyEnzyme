from __future__ import annotations

import pandas as pd
from pydantic import computed_field
from pydantic_xml import element, BaseXmlModel, attr, wrapped

from pyenzyme import Measurement, UnitDefinition, DataTypes
from pyenzyme.sbml.versions.v2 import VariableAnnot


class V1Annotation(
    BaseXmlModel,
    tag="annotation",
    search_mode="unordered",
):
    small_molecule: ReactantAnnot | None = element(
        tag="smallMolecule",
        default=None,
        nsmap={"enzymeml": "https://www.enzymeml.org/v2"},
    )

    protein: ProteinAnnot | None = element(
        tag="protein",
        default=None,
        nsmap={"enzymeml": "https://www.enzymeml.org/v2"},
    )

    complex: ComplexAnnot | None = element(
        tag="complex",
        default=None,
        nsmap={"enzymeml": "https://www.enzymeml.org/v2"},
    )

    data: DataAnnot | None = element(
        tag="data",
        default=None,
        nsmap={"enzymeml": "https://www.enzymeml.org/v2"},
    )

    parameter: ParameterAnnot | None = element(
        tag="parameter",
        default=None,
        nsmap={"enzymeml": "https://www.enzymeml.org/v2"},
    )

    variables: VariableAnnot | None = element(
        tag="variables",
        default=None,
        nsmap={"enzymeml": "https://www.enzymeml.org/v2"},
    )


class ParameterAnnot(
    BaseXmlModel,
    tag="parameter",
    nsmap={"": "https://www.enzymeml.org/v2"},
):
    """
    Represents the annotation for a parameter in the EnzymeML format.

    Attributes:
        initial (float | None): The initial value of the parameter.
        upper (float | None): The upper bound of the parameter.
        lower (float | None): The lower bound of the parameter.
    """

    initial: float | None = element(tag="initialValue", default=None)
    upper: float | None = element(tag="upperBound", default=None)
    lower: float | None = element(tag="lowerBound", default=None)


class ComplexAnnot(
    BaseXmlModel,
    tag="complex",
    nsmap={"": "http://sbml.org/enzymeml/version2"},
):
    """
    Represents the annotation for a complex in the EnzymeML format.

    Attributes:
        participants (list[str]): A list of participants in the complex.
    """

    participants: list[str] = element(tag="participant", default_factory=list)


class ReactantAnnot(
    BaseXmlModel,
    tag="reactant",
    nsmap={"": "http://sbml.org/enzymeml/version2"},
):
    """
    Represents the annotation for a reactant in the EnzymeML format.

    Attributes:
        inchi (str | None): The InChI of the reactant.
        smiles (str | None): The SMILES representation of the reactant.
        chebi_id (str | None): The ChEBI ID of the reactant.
    """

    inchi: str | None = element(tag="inchi", default=None)
    smiles: str | None = element(tag="smiles", default=None)
    chebi_id: str | None = element(tag="chebiID", default=None)


class ProteinAnnot(
    BaseXmlModel,
    tag="protein",
    nsmap={"": "http://sbml.org/enzymeml/version2"},
):
    """
    Represents the annotation for a protein in the EnzymeML format.

    Attributes:
        sequence (str | None): The amino acid sequence of the protein.
        ecnumber (str | None): The EC number of the protein.
        uniprotid (str | None): The UniProt ID of the protein.
        organism (str | None): The organism from which the protein is derived.
        organism_tax_id (str | None): The taxonomic ID of the organism.
    """

    sequence: str | None = element(tag="sequence", default=None)
    ecnumber: str | None = element(tag="ECnumber", default=None)
    uniprotid: str | None = element(tag="uniprotID", default=None)
    organism: str | None = element(tag="organism", default=None)
    organism_tax_id: str | None = element(tag="organismTaxID", default=None)


class DataAnnot(
    BaseXmlModel,
    tag="data",
    nsmap={"": "http://sbml.org/enzymeml/version2"},
):
    """
    Represents the annotation for data in the EnzymeML format.

    Attributes:
        formats (list[FormatAnnot]): A list of format annotations.
        measurements (list[MeasurementAnnot]): A list of measurement annotations.
        files (list[FileAnnot]): A list of file annotations.
    """

    formats: list[FormatAnnot] = wrapped(
        "formats",
        element(
            tag="format",
            default_factory=list,
        ),
    )

    measurements: list[MeasurementAnnot] = wrapped(
        "listOfMeasurements",
        element(
            tag="measurement",
            default_factory=list,
        ),
    )

    files: list[FileAnnot] = wrapped(
        "files",
        element(
            tag="file",
            default_factory=list,
        ),
    )

    def to_measurements(
        self,
        meas_data: dict[str, pd.DataFrame],
        units: dict[str, UnitDefinition],
    ) -> list[Measurement]:
        """
        Converts the data annotation to version 2 format.

        Args:
            meas_data (dict[str, pd.DataFrame]): A dictionary of dataframes.
            units (dict[str, UnitDefinition]): A dictionary of unit definitions.

        Returns:
            list[Measurement]: A list of measurements.
        """

        # Create a mapping from fileid to filepath
        file_map = {file.id: meas_data[file.location] for file in self.files}

        measurements: list[Measurement] = list()

        for meas_v1 in self.measurements:
            measurement = Measurement(id=meas_v1.id, name=meas_v1.name)

            for init_conc in meas_v1.init_concs:
                measurement.add_to_species_data(
                    data_unit=units[init_conc.unit],
                    species_id=init_conc.species_id,
                    initial=init_conc.value,
                    data_type=DataTypes.CONCENTRATION,
                )

            # Extract the format information
            file = next(f for f in self.files if f.id == meas_v1.file)
            file_format = next(f for f in self.formats if f.id == file.format)

            self._map_columns(file_map[meas_v1.file], file_format, measurement, units)

            for species_data in measurement.species_data:
                if not species_data.data:
                    species_data.time = []

            measurements.append(measurement)

        return measurements

    def _map_columns(
        self,
        df: pd.DataFrame,
        file_format: FormatAnnot,
        measurement: Measurement,
        units: dict[str, UnitDefinition],
    ) -> None:
        """
        Maps columns from the dataframe to the measurement.

        Args:
            df (pd.DataFrame): The dataframe containing the data.
            file_format (FormatAnnot): The format annotation.
            measurement (Measurement): The measurement to map the columns to.
            units (dict[str, UnitDefinition]): A dictionary of unit definitions.
        """

        for col in file_format.columns:
            unit = units[col.unit]
            values = df.iloc[:, col.index].values.tolist()

            if col.type == "time":
                self._map_time_values(measurement, unit, values)
            else:
                self._map_species_values(col, measurement, unit, values)

    @staticmethod
    def _map_species_values(
        col: ColumnAnnot,
        measurement: Measurement,
        unit: UnitDefinition,
        values: list[float],
    ):
        """
        Maps species values to the measurement.

        Args:
            col (ColumnAnnot): The column annotation.
            measurement (Measurement): The measurement to map the values to.
            unit (UnitDefinition): The unit definition.
            values (list[float]): The list of values.
        """
        species_data = measurement.filter_species_data(species_id=col.species_id)

        assert len(species_data) == 1, f"Species data not found for {col.species_id}"

        species_data = species_data[0]
        species_data.data_unit = unit
        species_data.data = values

    @staticmethod
    def _map_time_values(measurement, unit, values):
        """
        Maps time values to the measurement.

        Args:
            measurement (Measurement): The measurement to map the values to.
            unit (UnitDefinition): The unit definition.
            values (list[float]): The list of time values.
        """
        # Map time to all species data
        for species_data in measurement.species_data:
            species_data.time = values
            species_data.time_unit = unit


class FormatAnnot(
    BaseXmlModel,
    tag="format",
    nsmap={"": "http://sbml.org/enzymeml/version2"},
):
    """
    Represents the format annotation in the EnzymeML format.

    Attributes:
        id (str): The ID of the format.
        columns (list[ColumnAnnot]): A list of column annotations.
    """

    id: str = attr(name="id")
    columns: list[ColumnAnnot] = element(
        tag="column",
        default_factory=list,
    )


class ColumnAnnot(
    BaseXmlModel,
    tag="column",
    nsmap={"": "http://sbml.org/enzymeml/version2"},
):
    """
    Represents the column annotation in the EnzymeML format.

    Attributes:
        species_id (str | None): The ID of the species.
        type (str): The type of the column.
        unit (str): The unit of the column.
        index (int): The index of the column.
        replica (str | None): The replica of the column.
        is_calculated (bool): Whether the column is calculated.
    """

    species_id: str | None = attr(name="species", default=None)
    type: str = attr(name="type")
    unit: str = attr(name="unit")
    index: int = attr(name="index")
    replica: str | None = attr(name="replica", default=None)
    is_calculated: bool = attr(name="isCalculated", default=False)


class MeasurementAnnot(
    BaseXmlModel,
    tag="measurement",
    nsmap={"": "http://sbml.org/enzymeml/version2"},
):
    """
    Represents the measurement annotation in the EnzymeML format.

    Attributes:
        id (str): The ID of the measurement.
        name (str): The name of the measurement.
        file (str): The file associated with the measurement.
        init_concs (list[InitConcAnnot]): A list of initial concentration annotations.
    """

    id: str = attr(name="id")
    name: str = attr(name="name")
    file: str = attr(name="file")
    init_concs: list[InitConcAnnot] = element(
        tag="initConc",
        default_factory=list,
    )


class InitConcAnnot(
    BaseXmlModel,
    tag="initConc",
    nsmap={"": "http://sbml.org/enzymeml/version2"},
):
    """
    Represents the initial concentration annotation in the EnzymeML format.

    Attributes:
        protein (str | None): The protein associated with the initial concentration.
        reactant (str | None): The reactant associated with the initial concentration.
        value (float): The value of the initial concentration.
        unit (str): The unit of the initial concentration.
    """

    protein: str | None = attr(name="protein", default=None)
    reactant: str | None = attr(name="reactant", default=None)
    value: float = attr(name="value", default=0.0)
    unit: str = attr(name="unit")

    @computed_field
    @property
    def species_id(self) -> str:
        """
        Computes the species ID based on the protein or reactant.

        Returns:
            str: The species ID.
        """
        assert bool(self.protein) != bool(
            self.reactant
        ), "Either protein or reactant must be set"
        return self.protein or self.reactant


class FileAnnot(
    BaseXmlModel,
    tag="file",
    nsmap={"": "http://sbml.org/enzymeml/version2"},
):
    """
    Represents the file annotation in the EnzymeML format.

    Attributes:
        id (str): The ID of the file.
        location (str): The file path.
        format (str): The format of the file.
    """

    id: str = attr(name="id")
    location: str = attr(name="file")
    format: str = attr(name="format")


# Rebuild all the classes within this file
for cls in [
    DataAnnot,
    FormatAnnot,
    ColumnAnnot,
    MeasurementAnnot,
    InitConcAnnot,
    ProteinAnnot,
    ReactantAnnot,
    ParameterAnnot,
    V1Annotation,
]:
    cls.model_rebuild()
