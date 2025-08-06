from __future__ import annotations

import pandas as pd
from mdmodels.units.unit_definition import UnitDefinition
from pydantic import computed_field
from pydantic_xml import BaseXmlModel, attr, element, wrapped

from pyenzyme.sbml.utils import _get_unit
from pyenzyme.sbml.versions.v2 import VariableAnnot
from pyenzyme.versions.v2 import DataTypes, Measurement


class V1Annotation(
    BaseXmlModel,
    tag="annotation",
    search_mode="unordered",
):
    """
    Represents the top-level annotation in the EnzymeML v1 format.

    This class contains all the different types of annotations that can be
    attached to elements in an SBML model using EnzymeML v1 format.

    Attributes:
        small_molecule (ReactantAnnot | None): Annotation for small molecules.
        protein (ProteinAnnot | None): Annotation for proteins.
        complex (ComplexAnnot | None): Annotation for complexes.
        data (DataAnnot | None): Annotation for experimental data.
        parameter (ParameterAnnot | None): Annotation for parameters.
        variables (VariableAnnot | None): Annotation for variables.
    """

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
    search_mode="unordered",
    nsmap={"": "https://www.enzymeml.org/v2"},
):
    """
    Represents the annotation for a parameter in the EnzymeML format.

    This class contains information about parameter bounds and initial values
    that can be used in parameter estimation or simulation.

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

    A complex is formed by multiple participants (species) that interact
    with each other.

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

    This class contains chemical identifiers for small molecules that
    participate in reactions.

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

    This class contains biological identifiers and properties of proteins,
    particularly enzymes that catalyze reactions.

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
    Represents the annotation for experimental data in the EnzymeML format.

    This class contains information about experimental measurements, including
    file formats, measurement metadata, and file references.

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

        This method transforms v1 data annotations into v2 Measurement objects,
        mapping file data and units appropriately.

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
                if init_conc.species_id:
                    measurement.add_to_species_data(
                        data_unit=_get_unit(init_conc.unit, units),  # type: ignore
                        species_id=init_conc.species_id,
                        initial=init_conc.value,
                        data_type=DataTypes.CONCENTRATION,
                    )

            # Extract the format information
            file = next(f for f in self.files if f.id == meas_v1.file)
            file_format = next(f for f in self.formats if f.id == file.format)

            self._map_columns(
                file_map[meas_v1.file],
                file_format,
                measurement,
                units,
            )

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

        This method processes each column in the format definition, extracts
        the corresponding data from the dataframe, and adds it to the measurement
        object with appropriate units.

        Args:
            df (pd.DataFrame): The dataframe containing the data.
            file_format (FormatAnnot): The format annotation.
            measurement (Measurement): The measurement to map the columns to.
            units (dict[str, UnitDefinition]): A dictionary of unit definitions.
        """

        for col in file_format.columns:
            unit = _get_unit(col.unit, units)
            values = df.iloc[:, col.index].values.tolist()

            if col.type == "time":
                self._map_time_values(
                    measurement,
                    unit,  # type: ignore
                    values,
                )
            else:
                self._map_species_values(
                    col,
                    measurement,
                    unit,  # type: ignore
                    values,
                )

    @staticmethod
    def _map_species_values(
        col: ColumnAnnot,
        measurement: Measurement,
        unit: UnitDefinition,
        values: list[float],
    ):
        """
        Maps species values to the measurement.

        This method finds the appropriate species data object in the measurement
        and adds the concentration or other data values to it.

        Args:
            col (ColumnAnnot): The column annotation.
            measurement (Measurement): The measurement to map the values to.
            unit (UnitDefinition): The unit definition.
            values (list[float]): The list of values.
        """
        species_data = measurement.filter_species_data(species_id=col.species_id)

        assert len(species_data) == 1, f"Species data not found for {col.species_id}"

        species_data = species_data[0]
        species_data.data_unit = unit  # type: ignore
        species_data.data = values

    @staticmethod
    def _map_time_values(
        measurement: Measurement,
        unit: str,
        values: list[float],
    ):
        """
        Maps time values to the measurement.

        This method adds time values to all species data objects in the measurement,
        ensuring that time series data is properly associated with each species.

        Args:
            measurement (Measurement): The measurement to map the values to.
            unit (UnitDefinition): The unit definition.
            values (list[float]): The list of time values.
        """
        # Map time to all species data
        for species_data in measurement.species_data:
            species_data.time = values
            species_data.time_unit = unit  # type: ignore


class FormatAnnot(
    BaseXmlModel,
    tag="format",
    nsmap={"": "http://sbml.org/enzymeml/version2"},
):
    """
    Represents the format annotation in the EnzymeML format.

    This class defines the structure of data files, specifying how columns
    in data files map to species, time, or other measurements.

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

    This class defines how a specific column in a data file should be interpreted,
    including what species it refers to, what type of data it contains, and its units.

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

    This class contains metadata about a specific measurement, including
    its identifier, name, associated file, and initial concentrations.

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

    This class defines the initial concentration of a species (either a protein
    or reactant) in a specific measurement.

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
    def species_id(self) -> str | None:
        """
        Computes the species ID based on the protein or reactant.

        This property returns either the protein or reactant ID, ensuring
        that exactly one of them is set.

        Returns:
            str | None: The species ID.
        """
        assert bool(self.protein) != bool(self.reactant), (
            "Either protein or reactant must be set"
        )
        return self.protein or self.reactant


class FileAnnot(
    BaseXmlModel,
    tag="file",
    nsmap={"": "http://sbml.org/enzymeml/version2"},
):
    """
    Represents the file annotation in the EnzymeML format.

    This class contains metadata about a data file, including its identifier,
    location, and format.

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
