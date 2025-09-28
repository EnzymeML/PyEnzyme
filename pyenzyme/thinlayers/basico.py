# File: pysces.py
# Project: ThinLayers
# Authors: Frank T. Bergmann (frankbergmann@live.com), Jan Range (jan.range@simtech.uni-stuttgart.de)
# License: BSD-2 clause
# Copyright (c) 2025 Heidelberg University, University of Stuttgart

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
import os

from typing import Dict, List, Optional, Tuple

from pyenzyme.thinlayers.base import BaseThinLayer, SimResult, Time, InitCondDict
from pyenzyme.versions import v2

try:
    import basico
    import COPASI
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "ThinLayerCopasi is not available. "
        "To use it, please install the following dependencies: "
        f"{e}"
    )


class ThinLayerCopasi(BaseThinLayer):
    """
    COPASI implementation of the BaseThinLayer for kinetic modeling.

    This class provides integration with the COPASI (COmplex PAthway SImulator)
    for simulating and optimizing kinetic models from EnzymeML documents.

    Attributes:
        model (basico.COPASI.CDataModel): The COPASI model instance.
        model_dir (Path | str): Directory for storing model files.
        inits (list[InitMap]): Initial conditions for each measurement.
        cols (list[str]): Column names for the experimental data.
        parameters (list[dict[str, float]]): Optimizable parameters for the model.
    """

    model: basico.COPASI.CDataModel
    model_dir: Path | str
    inits: dict[str, InitMap]
    cols: list[str]
    parameters: list
    nu_enzmldoc: v2.EnzymeMLDocument

    def __init__(
        self,
        enzmldoc: v2.EnzymeMLDocument,
        model_dir: Path | str = "./copasi_models",
        measurement_ids: Optional[List[str]] = None,
    ):
        """
        Initialize the ThinLayerCopasi instance.

        Args:
            enzmldoc (v2.EnzymeMLDocument): EnzymeML document containing the model.
            model_dir (Path | str): Directory where COPASI model files will be stored.
            measurement_ids (Optional[List[str]]): IDs of measurements to include in the analysis.
                If None, all measurements will be used.

        Examples:
            >>> import pyenzyme as pe
            >>> import pyenzyme.thinlayers as tls
            >>> doc = pe.read_enzymeml("path/to/enzmldoc.json")
            >>> tl = tls.ThinLayerCopasi(doc)
        """

        # not sure this is needed, everything ought to be supported
        self._check_compliance(enzmldoc)

        super().__init__(
            enzmldoc=enzmldoc,
            measurement_ids=measurement_ids,
            df_per_measurement=False,
        )

        if not isinstance(model_dir, Path):
            model_dir = Path(model_dir)

        if not model_dir.exists():
            # Create model directory if it doesn't exist
            os.makedirs(model_dir, exist_ok=True)

        self.model_dir = model_dir

        # load the model into COPASI
        self._get_copasi_model(model_dir)

    def _check_compliance(self, enzmldoc: v2.EnzymeMLDocument):
        """
        Check if the EnzymeML document is compliant with COPASI model.
        """
        has_kinetic_laws = any(m.kinetic_law is not None for m in enzmldoc.reactions)

        has_odes = any(
            m.equation_type == v2.EquationType.ODE for m in enzmldoc.equations
        )

        if not has_kinetic_laws and not has_odes:
            raise ValueError("EnzymeML document must contain kinetic laws or ODEs")

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

        This method simulates the model dynamics within the specified time range
        and returns trajectories for all species.

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

        Raises:
            ValueError: If the provided model is different from the one used for initialization.

        Examples:
            >>> # Get initial conditions from a measurement
            >>> initial_conditions = {
            ...     s.species_id: s.initial for s in measurement.species_data
            ...     if s.initial is not None
            ... }
            >>> # Simulate from time 0 to 10
            >>> results, time = tl.integrate(doc, initial_conditions, 0, 10)
        """
        if model != self.enzmldoc:
            raise ValueError(
                "Model must be the same as the one used to initialize the ThinLayerCopasi. Otherwise, rerun the Thin Layer optimization with the new model."
            )

        # Convert the initial conditions to a InitMap
        time = np.linspace(t0, t1, nsteps).tolist()
        init_map = InitMap(
            time=time,
            species=initial_conditions,
        )

        out, species_order = self._simulate_condition(init_map)

        return (
            {species: traj.tolist() for species, traj in zip(species_order, out)},
            time,
        )

    def optimize(self, method="Levenberg - Marquardt"):
        """
        Optimizes model parameters to fit experimental data.

        This method performs parameter estimation to minimize the difference
        between simulated and experimental data.

        Args:
            method (str, optional): Optimization algorithm to use from COPASI. Defaults to "Levenberg - Marquard".
                Available methods include:
                - 'Levenberg - Marquardt': Levenberg-Marquardt (default)
                - 'Hooke & Jeeves': Hooke & Jeeves
                - 'Nelder - Mead': Nelder-Mead
                - 'Steepest Descent': Steepest Descent
                - 'NL2SOL': NL2SOL
                - 'Praxis': Praxis
                - 'Current Solution Statistics': just return the current solution
                - 'Particle Swarm': Particle Swarm Optimization
                - 'Evolution Strategy (SRES)': Evolution Strategy with Stochastic Ranking
                - 'Genetic Algorithm SR': Genetic Algorithm with Stochastic Ranking
                - 'Evolutionary Programming': Evolutionary Programming
                - 'Genetic Algorithm': Genetic Algorithm
                - 'Scatter Search': Scatter Search
                - 'Differential Evolution': Differential Evolution
                - 'Simulated Annealing': Simulated Annealing
                - 'Random Search': Random Search

        Returns:
            {}: Result of the optimization.

        Examples:
            >>> # Optimize model parameters
            >>> tl = ThinLayerCopasi(doc, ".")
            >>> result = tl.optimize()
            >>> print(f"Optimization success: {result.success}")
        """
        # Get experimental data from the EnzymeML document
        self._get_experimental_data()

        # Initialize the model parameters
        parameters = self._initialize_parameters()
        basico.set_fit_parameters(parameters, model=self.model)

        # Perform optimization
        basico.run_parameter_estimation(method=method, update_model=True, model=self.model)
        return basico.get_fit_statistic(include_parameters=True, model=self.model)

    def write(self) -> v2.EnzymeMLDocument:
        """
        Creates a new EnzymeML document with optimized parameter values.

        This method updates parameter values in a copy of the original EnzymeML document
        based on optimization results.

        Returns:
            v2.EnzymeMLDocument: A new EnzymeML document with optimized parameters.

        Raises:
            ValueError: If a parameter in the optimization results is not found in the document.

        Examples:
            >>> # Optimize and save optimized document
            >>> tl = ThinLayerCopasi(doc)
            >>> tl.optimize()
            >>> optimized_doc = tl.write()
            >>> pe.write_enzymeml(optimized_doc, "optimized_model.json")
        """
        nu_enzmldoc = self.enzmldoc.model_copy(deep=True)
        results = basico.get_fit_statistic(include_parameters=True)  # type: ignore

        # update the parameters in the enzmldoc
        for parameter in nu_enzmldoc.parameters:
            for fitted_param in results['parameters']:
                if fitted_param['name'] == f'Values[{parameter.symbol}].InitialValue':
                    parameter.value = fitted_param['value']
                    break
        return nu_enzmldoc

    # ! Helper methods
    def _initialize_parameters(self):
        """
        Initializes Parameters instance with model parameters.

        Returns:
            list[dict[str, float]]: Parameters object ready for optimization.

        Raises:
            ValueError: If a parameter has neither an initial value nor a value attribute.
        """
        # Initialize parameters
        parameters = []

        # Add global parameters
        for param in self.enzmldoc.parameters:
            # Build kwargs dictionary with conditional assignments
            param_dict = {}

            if param.lower_bound is not None:
                param_dict["lower"] = param.lower_bound

            if param.upper_bound is not None:
                param_dict["upper"] = param.upper_bound

            # Determine parameter value
            if param.value:
                param_dict["start"] = param.value
            elif param.initial_value:
                param_dict["start"] = param.initial_value
            else:
                raise ValueError(
                    f"Neither initial_value nor value given for parameter {param.name} in global parameters"
                )

            param_dict["name"] = 'Values[' + param.symbol + ']'
            parameters.append(param_dict)

        return parameters

    def _get_experimental_data(self):
        """
        Extracts measurement data from the EnzymeML document.

        Populates the inits, experimental_data, and cols attributes.
        """
        self.inits = {
            measurement.id: InitMap.from_measurement(measurement, self.df_map[measurement.id])
            for measurement in self.enzmldoc.measurements
            if measurement.id in self.measurement_ids
        }

        # get all species
        species_df = basico.get_species(model=self.model).reset_index()

        # loop over 'id' colum of self.df and create a new experiment for each id
        for id in self.df['id'].unique():
            # get the dataframe for the id
            df = self.df[self.df['id'] == id]
            # drop id column
            df = df.drop(columns=["id"])
            # initializations
            inits = self.inits[id]

            # loop over remaining columns
            for col in df.columns:
                # if col is 'time' rename to Time and continue
                if col == 'time':
                    df = df.rename(columns={"time": "Time"})
                    continue
                # otherwise find in species_df and rename to '[col]' 
                if col in species_df['name'].values:
                    df = df.rename(columns={col: f"[{col}]"})
                    continue
                # otherwise raise error
                else:
                    raise ValueError(f"Column {col} not found in species_df")

            # finally add all the initial concentrations to the dataframe with the
            # initial value at Time == 0
            for species in inits.species.keys():
                df.loc[df.index[0], f"[{species}]_0"] = inits.species[species]

            # now add as experiment to basico
            basico.add_experiment(name=id, data=df, data_dir=self.model_dir)

    def _get_copasi_model(self, model_dir: Path | str):
        """
        Converts an EnzymeML document to a COPASI model.

        Args:
            model_dir (Path | str): Directory for storing model files.
        """
        model_dir = self._prepare_model_directory(model_dir)
        sbmlfile_name = self._create_sbml_file(model_dir)

        self._load_copasi_model(sbmlfile_name, model_dir)
        # TODO: check whether this is really needed!!!
        #self._fix_compartment_sizes()

    def _load_copasi_model(self, sbmlfile_name: str, model_dir: Path | str):
        """
        Loads a COPASI model from an SBML file.
        """
        self.model = basico.load_model(os.path.join(model_dir, sbmlfile_name))

    def _prepare_model_directory(self, model_dir: Path | str) -> str:
        """
        Ensures the model directory exists and returns it as a string.

        Args:
            model_dir (Path | str): Directory path for model files.

        Returns:
            str: Path to the model directory as a string.
        """
        model_dir = str(model_dir)
        os.makedirs(model_dir, exist_ok=True)

        return model_dir

    def _create_sbml_file(self, model_dir: str) -> str:
        """
        Creates an SBML file from the EnzymeML document.

        Args:
            model_dir (str): Directory to save the SBML file.

        Returns:
            str: Name of the created SBML file.
        """
        sbmlfile_name = f"{self.enzmldoc.name.replace(' ', '_')}.xml"
        sbmlfile_path = os.path.join(model_dir, sbmlfile_name)

        with open(sbmlfile_path, "w") as file:
            file.write(self.sbml_xml)

        return sbmlfile_name

    def _simulate_condition(
        self, init_concs: InitMap
    ) -> Tuple[List[np.ndarray], List[str]]:
        """
        Simulates a single experimental condition.

        Args:
            init_concs (InitMap): Initial concentrations for the simulation.

        Returns:
            Tuple[List[np.ndarray], List[str]]:
                - List of arrays containing trajectory data for each species
                - List of species IDs
        """

        # apply initial conditions to model
        init_concs.to_copasi_model(self.model)
        result = basico.run_time_course_with_output(output_selection=[f'[{species}]' for species in init_concs.species.keys()], values=init_concs.time, model=self.model)

        # result is a pandas dataframe with the columns as the species and the rows as the time points
        # enzymeml needs it separated by columns and converted to np.ndarray
        # build a tuple of the result and the species
        data = []
        ids = []
        for species in init_concs.species.keys():
            data.append(result[f'[{species}]'].values)
            ids.append(species)
        return (data, ids)


@dataclass
class InitMap:
    """
    Helper class for managing species initial concentrations.

    This class provides type-safe handling of initial concentrations and
    time points for COPASI model simulations.

    Attributes:
        time (List[float]): List of time points for simulation.
        species (Dict[str, float]): Dictionary mapping species IDs to initial concentrations.
    """

    time: List[float]
    species: Dict[str, float]

    @classmethod
    def from_measurement(cls, meas: v2.Measurement, df: pd.DataFrame) -> "InitMap":
        """
        Create an InitMap instance from a measurement and its dataframe.

        Args:
            meas (v2.Measurement): The measurement containing species data.
            df (pd.DataFrame): DataFrame with time data for the measurement.

        Returns:
            InitMap: Initialized instance with time points and species initial values.
        """
        return cls(
            time=df["time"].tolist(),
            species={
                s.species_id: s.initial
                for s in meas.species_data
                if s.initial is not None
            },
        )

    def to_copasi_model(self, model: COPASI.CDataModel):
        """
        Apply initial conditions to a COPASI model.

        This method sets the simulation time and initial species concentrations
        in the COPASI model, ensuring zero values are replaced with small positive values.

        Args:
            model (COPASI.CDataModel): The COPASI model to update.

        Returns:
            COPASI.CDataModel: The updated model with initial conditions set.
        """

        for species_id, value in self.species.items():
            # seems odd to be doing this here, but it is the same for the PySCeS thin layer
            if value == 0:
                value = 1.0e-9  # is this really needed?
            basico.set_species(species_id, exact=True, initial_concentration=value, model=model)
