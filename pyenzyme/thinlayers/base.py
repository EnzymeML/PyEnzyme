from abc import ABC, abstractmethod
from functools import cached_property
from typing import Dict, List, Optional, Tuple, TypeAlias

import pandas as pd

import pyenzyme as pe
from pyenzyme.versions import v2

# Type aliases for usage across the thinlayers
# Easier to read and understand than using type hints
InitCondDict: TypeAlias = Dict[str, float]
SimResult: TypeAlias = Dict[str, List[float]]
Time: TypeAlias = List[float]


class BaseThinLayer(ABC):
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

    enzmldoc: v2.EnzymeMLDocument
    measurement_ids: List[str]
    exclude_unmodeled_species: bool = True

    def __init__(
        self,
        enzmldoc: v2.EnzymeMLDocument,
        measurement_ids: Optional[List[str]] = None,
        df_per_measurement: bool = False,
        exclude_unmodeled_species: bool = True,
    ):
        assert isinstance(enzmldoc, v2.EnzymeMLDocument)
        assert isinstance(measurement_ids, list) or measurement_ids is None

        # Remove empty measurements
        enzmldoc.measurements = [
            meas for meas in enzmldoc.measurements if meas.species_data
        ]

        if measurement_ids is None:
            measurement_ids = [meas.id for meas in enzmldoc.measurements]

        self.enzmldoc = enzmldoc.model_copy(deep=True)
        self.fitted_doc = enzmldoc.model_copy(deep=True)
        self.measurement_ids = measurement_ids
        self.df_per_measurement = df_per_measurement
        self.exclude_unmodeled_species = exclude_unmodeled_species

    @staticmethod
    def _remove_unmodeled_species(enzmldoc: v2.EnzymeMLDocument) -> v2.EnzymeMLDocument:
        """
        Removes species that are not modeled from the EnzymeML document.

        This method filters out species that are not referenced in any reactions or ODEs,
        cleaning up the document to only include modeled species. It also removes
        measurements that have no remaining species data after filtering.

        Args:
            enzmldoc (v2.EnzymeMLDocument): The EnzymeML document to filter.

        Returns:
            v2.EnzymeMLDocument: A deep copy of the document with unmodeled species removed.

        Note:
            - Creates a deep copy to avoid modifying the original document
            - Removes measurements that become empty after species filtering
            - Only considers species from reactions (reactants/products) and ODE equations
        """
        enzmldoc = enzmldoc.model_copy(deep=True)

        # Collect all species that are explicitly modeled
        modeled_species = set()

        # Add species from reactions (reactants and products)
        for reaction in enzmldoc.reactions:
            modeled_species.update(
                reactant.species_id for reactant in reaction.reactants
            )
            modeled_species.update(product.species_id for product in reaction.products)

        # Add species from ODE equations
        modeled_species.update(
            equation.species_id
            for equation in enzmldoc.equations
            if equation.equation_type == v2.EquationType.ODE
        )

        if not modeled_species:
            enzmldoc.measurements = []
            enzmldoc.small_molecules = []
            enzmldoc.proteins = []
            enzmldoc.complexes = []
            return enzmldoc

        filtered_measurements = []
        for measurement in enzmldoc.measurements:
            # Filter species data to only include modeled species
            filtered_species_data = [
                data
                for data in measurement.species_data
                if data.species_id in modeled_species
            ]

            # Only keep measurements that still have species data
            if filtered_species_data:
                measurement.species_data = filtered_species_data
                filtered_measurements.append(measurement)

        # Update all collections to only include modeled species
        enzmldoc.measurements = filtered_measurements
        enzmldoc.small_molecules = [
            species
            for species in enzmldoc.small_molecules
            if species.id in modeled_species
        ]
        enzmldoc.proteins = [
            protein for protein in enzmldoc.proteins if protein.id in modeled_species
        ]
        enzmldoc.complexes = [
            complex for complex in enzmldoc.complexes if complex.id in modeled_species
        ]

        return enzmldoc

    @abstractmethod
    def integrate(
        self,
        model: v2.EnzymeMLDocument,
        initial_conditions: InitCondDict,
        t0: float,
        t1: float,
        nsteps: int = 100,
    ) -> Tuple[SimResult, Time]:
        """
        Integrates the model from t0 to t1 with the given initial conditions.

        Args:
            model (v2.EnzymeMLDocument): EnzymeML document containing the model.
            initial_conditions (InitCondDict): Dictionary mapping species IDs to initial concentrations.
            t0 (float): Start time for integration.
            t1 (float): End time for integration.
            nsteps (int, optional): Number of time points to generate. Defaults to 100.

        Returns:
            Tuple[SimResult, Time]: A tuple containing:
                - Dict mapping species IDs to concentration trajectories.
                - List of time points.

        Examples:
            >>> # Simulate model with initial conditions
            >>> species_data, time_points = thinlayer.integrate(
            ...     model=doc,
            ...     initial_conditions={"S1": 10.0, "S2": 0.0},
            ...     t0=0.0,
            ...     t1=100.0,
            ...     nsteps=200
            ... )
        """
        pass

    @abstractmethod
    def optimize(self, **kwargs):
        """
        Optimizes the model parameters.

        This method should implement parameter optimization for the model,
        typically fitting to experimental data contained in the EnzymeML document.

        Args:
            **kwargs: Implementation-specific keyword arguments.

        Returns:
            Implementation-specific optimization results.

        Examples:
            >>> # Optimize model parameters
            >>> result = thinlayer.optimize(**kwargs)
            >>> print(f"Optimization success: {result.success}")
        """
        pass

    @abstractmethod
    def write(self) -> v2.EnzymeMLDocument:
        """
        Writes the optimized model parameters to a copy of the EnzymeMLDocument.

        This method creates a new EnzymeML document with updated parameter values
        based on optimization results.

        Returns:
            v2.EnzymeMLDocument: A new EnzymeML document with optimized parameters.

        Examples:
            >>> # Get optimized document after parameter fitting
            >>> thinlayer.optimize()
            >>> optimized_doc = thinlayer.write()
            >>> pe.write_enzymeml(optimized_doc, "optimized_model.json")
        """
        pass

    @staticmethod
    def _check_measurement_ids(enzmldoc: v2.EnzymeMLDocument):
        """
        Validates that the EnzymeML document contains at least one measurement.

        Args:
            enzmldoc (v2.EnzymeMLDocument): The EnzymeML document to validate.

        Returns:
            v2.EnzymeMLDocument: The validated EnzymeML document.

        Raises:
            ValueError: If the EnzymeML document has no measurements.

        Examples:
            >>> # Validate document has measurements
            >>> validated_doc = BaseThinLayer.check_measurement_ids(doc)
        """
        if len(enzmldoc.measurements) == 0:
            raise ValueError("EnzymeMLDocument has no measurements")

        return enzmldoc

    @cached_property
    def sbml_xml(self) -> str:
        """
        Converts the EnzymeML document to SBML XML format.

        Returns:
            str: The SBML XML representation of the EnzymeML document.

        Examples:
            >>> # Export model as SBML
            >>> sbml_string = thinlayer.sbml_xml
            >>> with open("model.xml", "w") as f:
            ...     f.write(sbml_string)
        """
        return pe.to_sbml(self.enzmldoc)[0]

    @cached_property
    def df(self) -> pd.DataFrame:
        """
        Converts the EnzymeML document to a pandas DataFrame.

        If measurement_ids is specified, only those measurements are included in the result.

        Returns:
            pd.DataFrame: A DataFrame containing time series data for all measurements
                or only the specified measurements.

        Raises:
            ValueError: If the conversion doesn't return a DataFrame.
        """
        if self.exclude_unmodeled_species:
            enzmldoc = self._remove_unmodeled_species(self.enzmldoc)
        else:
            enzmldoc = self.enzmldoc

        df = pe.to_pandas(enzmldoc, per_measurement=False)

        # Drop all this rows where "id" is within measurement_ids
        df = (
            df
            if self.measurement_ids is None
            else df[df["id"].isin(self.measurement_ids)]  # type: ignore
        )

        if not isinstance(df, pd.DataFrame):
            raise ValueError("Expected a single dataframe")

        return df

    @cached_property
    def df_map(self) -> dict[str, pd.DataFrame]:
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

        df_map = pe.to_pandas(self.enzmldoc, per_measurement=True)

        if not isinstance(df_map, dict):
            raise ValueError("Expected a dictionary of dataframes")

        if self.measurement_ids is None:
            return df_map

        missing_ids = set(self.measurement_ids) - set(df_map.keys())
        if missing_ids:
            raise ValueError(f"Measurement ids {missing_ids} not found in data")

        return {k: v for k, v in df_map.items() if k in self.measurement_ids}
