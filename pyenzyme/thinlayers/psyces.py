# File: pysces.py
# Project: ThinLayers
# Authors: Johann Rohwer (j.m.rohwer@gmail.com), Jan Range (jan.range@simtech.uni-stuttgart.de)
# License: BSD-2 clause
# Copyright (c) 2025 Stellenbosch University, University of Stuttgart

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from joblib import Parallel, delayed
import dill
import numpy as np
import pandas as pd
import os
import contextlib
import io

from typing import Dict, List, Optional, Tuple

from pyenzyme.thinlayers.base import BaseThinLayer, SimResult, Time, InitCondDict
from pyenzyme.versions import v2

try:
    # Suppress PySCeS import output by redirecting stdout and stderr
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        import pysces
    import lmfit
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "ThinLayerPySces is not available. "
        "To use it, please install the following dependencies: "
        f"{e}"
    )


class ThinLayerPysces(BaseThinLayer):
    """
    PySCeS implementation of the BaseThinLayer for kinetic modeling.

    This class provides integration with the Python Simulator for Cellular Systems (PySCeS)
    for simulating and optimizing kinetic models from EnzymeML documents.

    Attributes:
        model (pysces.model): The PySCeS model instance.
        model_dir (Path | str): Directory for storing model files.
        inits (list[InitMap]): Initial conditions for each measurement.
        cols (list[str]): Column names for the experimental data.
        parameters (lmfit.Parameters): Optimizable parameters for the model.
    """

    model: pysces.model
    model_dir: Path | str
    inits: list[InitMap]
    cols: list[str]
    parameters: lmfit.Parameters
    nu_enzmldoc: v2.EnzymeMLDocument

    def __init__(
        self,
        enzmldoc: v2.EnzymeMLDocument,
        model_dir: Path | str = "./pysces_models",
        measurement_ids: Optional[List[str]] = None,
    ):
        """
        Initialize the ThinLayerPysces instance.

        Args:
            enzmldoc (v2.EnzymeMLDocument): EnzymeML document containing the model.
            model_dir (Path | str): Directory where PySCeS model files will be stored.
            measurement_ids (Optional[List[str]]): IDs of measurements to include in the analysis.
                If None, all measurements will be used.

        Examples:
            >>> import pyenzyme as pe
            >>> import pyenzyme.thinlayers as tls
            >>> doc = pe.read_enzymeml("path/to/enzmldoc.json")
            >>> tl = tls.ThinLayerPysces(doc)
        """

        # Currently, the ThinLayerPysces only supports the reaction model
        # TODO: Add support for Rate Rules
        self._check_compliance(enzmldoc)

        super().__init__(
            enzmldoc=enzmldoc,
            measurement_ids=measurement_ids,
            df_per_measurement=False,
            exclude_unmodeled_species=True,
        )

        if not isinstance(model_dir, Path):
            model_dir = Path(model_dir)

        if not model_dir.exists():
            # Create model directory if it doesn't exist
            os.makedirs(model_dir, exist_ok=True)

        # Convert model to PSC
        self._get_pysces_model(model_dir)

    def _check_compliance(self, enzmldoc: v2.EnzymeMLDocument):
        """
        Check if the EnzymeML document is compliant with the PySCeS model.
        """
        has_kinetic_laws = any(m.kinetic_law is not None for m in enzmldoc.reactions)

        has_odes = any(
            m.equation_type == v2.EquationType.ODE for m in enzmldoc.equations
        )

        if not has_kinetic_laws:
            raise ValueError("EnzymeML document must contain kinetic laws")

        if has_odes:
            raise ValueError(
                "The PySCeS thinlayer only supports Kinetic Laws, not ODEs",
                "Support for ODEs will be added in the future.",
            )

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
                "Model must be the same as the one used to initialize the ThinLayerPysces. Otherwise, rerun the Thin Layer optimization with the new model."
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

    def optimize(self, method="leastsq"):
        """
        Optimizes model parameters to fit experimental data.

        This method performs parameter estimation to minimize the difference
        between simulated and experimental data.

        Args:
            method (str, optional): Optimization algorithm to use from lmfit. Defaults to "leastsq".
                Available methods include:
                - leastsq: Levenberg-Marquardt (default)
                - least_squares: Least-Squares minimization, using Trust Region Reflective method
                - differential_evolution: differential evolution
                - brute: brute force method
                - basinhopping: basinhopping
                - ampgo: Adaptive Memory Programming for Global Optimization
                - nelder: Nelder-Mead
                - lbfgsb: L-BFGS-B
                - powell: Powell
                - cg: Conjugate-Gradient
                - newton: Newton-CG
                - cobyla: Cobyla
                - bfgs: BFGS
                - tnc: Truncated Newton
                - trust-ncg: Newton-CG trust-region
                - trust-exact: nearly exact trust-region
                - trust-krylov: Newton GLTR trust-region
                - trust-constr: trust-region for constrained optimization
                - dogleg: Dog-leg trust-region
                - slsqp: Sequential Linear Squares Programming
                - emcee: Maximum likelihood via Monte-Carlo Markov Chain
                - shgo: Simplicial Homology Global Optimization
                - dual_annealing: Dual Annealing optimization

        Returns:
            lmfit.MinimizerResult: Result of the optimization.

        Examples:
            >>> # Optimize model parameters
            >>> tl = ThinLayerPysces(doc, ".")
            >>> result = tl.optimize()
            >>> print(f"Optimization success: {result.success}")
        """
        # Get experimental data from the EnzymeML document
        self._get_experimental_data()

        # Initialize the model parameters
        parameters = self._initialize_parameters()

        # Perform optimization
        self.minimizer = lmfit.Minimizer(self._calculate_residual, parameters)

        self.parameters = parameters

        result = self.minimizer.minimize(method=method)
        # add standard error if available in enzmldoc and if param.fit=False
        # (e.g. if parameter was fitted before)
        for param in self.enzmldoc.parameters:
            if not param.fit and param.stderr is not None:
                if param.symbol in result.params:
                    result.params[param.symbol].stderr = param.stderr

        return result


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
            >>> tl = ThinLayerPysces(doc)
            >>> tl.optimize()
            >>> optimized_doc = tl.write()
            >>> pe.write_enzymeml(optimized_doc, "optimized_model.json")
        """
        nu_enzmldoc = self.enzmldoc.model_copy(deep=True)
        results = self.minimizer.result.params  # type: ignore

        for name in results:
            query = nu_enzmldoc.filter_parameters(symbol=name)

            if len(query) == 0:
                raise ValueError(f"Parameter {name} not found")

            parameter = query[0]
            parameter.value = results[name].value
            if results[name].stderr is not None:
                parameter.stderr = results[name].stderr

        return nu_enzmldoc

    # ! Helper methods
    def _initialize_parameters(self):
        """
        Initializes lmfit Parameters instance with model parameters.

        Returns:
            lmfit.Parameters: Parameters object ready for optimization.

        Raises:
            ValueError: If a parameter has neither an initial value nor a value attribute.
        """
        # Initialize lmfit parameters
        parameters = lmfit.Parameters()

        # Add global parameters
        for param in self.enzmldoc.parameters:
            # Build kwargs dictionary with conditional assignments
            kwargs = {
                **({'min': param.lower_bound} if param.lower_bound is not None else {}),
                **({'max': param.upper_bound} if param.upper_bound is not None else {}),
                **({'vary': param.fit}),
            }

            # Determine parameter value
            if param.value:
                kwargs["value"] = param.value
            elif param.initial_value:
                kwargs["value"] = param.initial_value
            else:
                raise ValueError(
                    f"Neither initial_value nor value given for parameter {param.name} in global parameters"
                )

            parameters.add(param.symbol, **kwargs)

        return parameters

    def _get_experimental_data(self):
        """
        Extracts measurement data from the EnzymeML document.

        Populates the inits, experimental_data, and cols attributes.
        """
        enzmldoc = self._remove_unmodeled_species(self.enzmldoc)
        self.inits = [
            InitMap.from_measurement(measurement, self.df_map[measurement.id])
            for measurement in enzmldoc.measurements
            if measurement.id in self.measurement_ids
        ]

        self.experimental_data = self.df.drop(columns=["id", "time"])
        self.cols = list(self.experimental_data.columns)

    def _get_pysces_model(self, model_dir: Path | str):
        """
        Converts an EnzymeML document to a PySCeS model.

        Args:
            model_dir (Path | str): Directory for storing model files.
        """
        model_dir = self._prepare_model_directory(model_dir)
        sbmlfile_name = self._create_sbml_file(model_dir)

        self._convert_to_pysces_format(sbmlfile_name, model_dir)
        self._load_pysces_model(sbmlfile_name, model_dir)
        self._fix_compartment_sizes()

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

    def _convert_to_pysces_format(self, sbmlfile_name: str, model_dir: str):
        """
        Converts SBML to PySCeS format if needed.

        Args:
            sbmlfile_name (str): Name of the SBML file.
            model_dir (str): Directory containing the file.
        """
        sbmlfile_path = os.path.join(model_dir, sbmlfile_name)
        pscfile_path = f"{sbmlfile_path}.psc"
        sbml_file_modified = os.path.getmtime(sbmlfile_path)

        # Check if PSC file needs to be regenerated
        psc_needs_update = (
            not os.path.exists(pscfile_path)
            or os.path.getmtime(pscfile_path) <= sbml_file_modified
        )

        if psc_needs_update:
            pysces.interface.convertSBML2PSC(
                sbmlfile_name,
                sbmldir=model_dir,
                pscdir=model_dir,
            )

    def _load_pysces_model(self, sbmlfile_name: str, model_dir: str):
        """
        Loads the PySCeS model.

        Args:
            sbmlfile_name (str): Name of the SBML/PSC file.
            model_dir (str): Directory containing the file.
        """
        self.model = pysces.model(sbmlfile_name, dir=model_dir)

    def _fix_compartment_sizes(self):
        """
        Fixes compartment sizes to work around a PySCeS issue (#79).

        Sets compartment sizes to 1.0 when working with concentrations.
        See: https://github.com/PySCeS/pysces/issues/79
        """
        if (
            self.model.__KeyWords__["Species_In_Conc"]
            and self.model.__KeyWords__["Output_In_Conc"]
        ):
            for comp in self.model.__compartments__:
                self.model.__compartments__[comp]["size"] = 1.0
                setattr(self.model, comp, 1.0)
                setattr(self.model, f"{comp}_init", 1.0)

    def _calculate_residual(self, parameters) -> np.ndarray:
        """
        Calculates residuals between experimental and simulated data.

        Args:
            parameters: The parameter values to use for simulation.

        Returns:
            np.ndarray: Array of residuals.
        """
        simulated_data = self._simulate_experiment(parameters)
        simulated_data = simulated_data.drop(
            simulated_data.columns.difference(self.cols), axis=1
        )

        return np.array(self.experimental_data - simulated_data)

    def _simulate_experiment(self, parameters):
        """
        Simulates the entire experiment with all measurements.

        Args:
            parameters: Parameter values for the simulation.

        Returns:
            pd.DataFrame: DataFrame with simulation results.
        """
        self.model.SetQuiet()
        self.model.__dict__.update(parameters.valuesdict())

        # Now iterate over all initial concentrations and simulate in parallel
        output = Parallel(n_jobs=-1)(
            delayed(lambda x: self._simulate_condition(x)[0])(init_conc)
            for init_conc in self.inits
        )

        return pd.DataFrame(np.hstack(output).T, columns=self.model.species)  # type: ignore

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
        model = init_concs.to_pysces_model(self.model)
        model.Simulate(userinit=1)
        return (
            [getattr(model.sim, species) for species in model.species],
            [str(species) for species in model.species],
        )


@dataclass
class InitMap:
    """
    Helper class for managing species initial concentrations.

    This class provides type-safe handling of initial concentrations and
    time points for PySCeS model simulations.

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

    def to_pysces_model(self, model: pysces.model):
        """
        Apply initial conditions to a PySCeS model.

        This method sets the simulation time and initial species concentrations
        in the PySCeS model, ensuring zero values are replaced with small positive values.

        Args:
            model (pysces.model): The PySCeS model to update.

        Returns:
            pysces.model: The updated model with initial conditions set.
        """
        model = dill.loads(dill.dumps(model))
        model.sim_time = np.array(self.time)
        model.__dict__.update(
            {
                f"{species_id}_init": value if value != 0 else 1.0e-9
                for species_id, value in self.species.items()
            }
        )
        return model
