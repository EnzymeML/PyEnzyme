# File: TL_Pysces.py
# Project: ThinLayers
# Author: Johann Rohwer (j.m.rohwer@gmail.com)
# License: BSD-2 clause
# Copyright (c) 2022 Stellenbosch University

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import os
import math

from typing import Union, Optional
from pyenzyme.thinlayers.TL_Base import BaseThinLayer
from pyenzyme.enzymeml.core.exceptions import SpeciesNotFoundError

import io
from contextlib import redirect_stdout

_PYSCES_IMPORT_ERROR = None
_PYSCES_IMPORT_STREAM = io.StringIO()
try:
    with redirect_stdout(_PYSCES_IMPORT_STREAM):
        import pysces
    import lmfit
except ModuleNotFoundError as e:
    _PYSCES_IMPORT_ERROR = """
    ThinLayerPysces is not available. 
    To use it, please install the following dependencies:
    {}
    """.format(
        e
    )


class ThinLayerPysces(BaseThinLayer):
    def __init__(
        self,
        path,
        model_dir: str,
        measurement_ids: Union[str, list] = "all",
        init_file: Optional[str] = None,
    ):
        # first time a pysces thinlayer is created, print the import messages
        global _PYSCES_IMPORT_STREAM
        if _PYSCES_IMPORT_STREAM is not None:
            print(_PYSCES_IMPORT_STREAM.getvalue())
            _PYSCES_IMPORT_STREAM = None
        
        # check dependencies
        if _PYSCES_IMPORT_ERROR:
            raise RuntimeError(_PYSCES_IMPORT_ERROR)

        super().__init__(path, measurement_ids, init_file)

        # Convert model to PSC and get experimental data
        self._get_pysces_model(model_dir)
        self._get_experimental_data()

    # ! Interface
    def optimize(self, method="leastsq"):
        """Performs optimization of the given parameters

        Args:
            method (str): lmfit optimization algorithm, see https://lmfit.github.io/lmfit-py/fitting.html#choosing-different-fitting-methods
        """

        # Initialize the model parameters
        parameters = self._initialize_parameters()

        # Perform optimization
        self.minimizer = lmfit.Minimizer(self._calculate_residual, parameters)

        # Set estimated parameters to self
        self.parameters = parameters

        return self.minimizer.minimize(method=method)

    def write(self):
        """Writes the estimated parameters to a copy of the EnzymeMLDocument"""

        nu_enzmldoc = self.enzmldoc.copy(deep=True)
        results = self.minimizer.result.params.valuesdict()

        for name, value in results.items():
            # names contain information about reaction and parameter
            # Pattern: rX_name

            splitted = name.split("_")
            reaction_id = splitted[0]
            parameter_id = "_".join(splitted[1::])

            # Fetch reaction and parameter
            try:
                reaction = nu_enzmldoc.getReaction(reaction_id)
            except SpeciesNotFoundError:
                global_param = nu_enzmldoc.global_parameters.get(name)
                global_param.value = value
                continue

            if reaction.model:
                parameter = reaction.model.getParameter(parameter_id)
                parameter.value = value
            else:
                raise TypeError(f"Reaction {reaction_id} has no model to add values to")

        return nu_enzmldoc

    # ! Helper methods
    def _initialize_parameters(self):
        """Adds all parameters to an lmfit Parameters instance.

        Raises:
            ValueError: Raised when parameter posesses neither an initial value or value attribute
        """

        # Initialize lmfit parameters
        parameters = lmfit.Parameters()

        # Add global parameters
        for global_param in self.global_parameters.values():

            # need to also catch zero initial values
            if global_param.value is not None:
                parameters.add(
                    f"{global_param.name}",
                    global_param.value,
                    vary=not global_param.constant,
                    min=global_param.lower,
                    max=global_param.upper,
                )

            elif global_param.initial_value is not None:
                parameters.add(
                    f"{global_param.name}",
                    global_param.initial_value,
                    vary=not global_param.constant,
                    min=global_param.lower,
                    max=global_param.upper,
                )

            else:  # parameter is
                raise ValueError(
                    f"Neither initial_value nor value given for parameter {global_param.name} in global parameters"
                )

        # Consistency check
        for reaction_id, (model, _) in self.reaction_data.items():

            # Apply parameters to lmfit parameters
            for parameter in model.parameters:

                if parameter.is_global:
                    continue

                # need to also catch zero initial values
                if parameter.value is not None:
                    parameters.add(
                        f"{reaction_id}_{parameter.name}",
                        parameter.value,
                        vary=not parameter.constant,
                        min=parameter.lower,
                        max=parameter.upper,
                    )
                elif parameter.initial_value is not None:
                    parameters.add(
                        f"{reaction_id}_{parameter.name}",
                        parameter.initial_value,
                        vary=not parameter.constant,
                        min=parameter.lower,
                        max=parameter.upper,
                    )
                else:  # parameter is
                    raise ValueError(
                        f"Neither initial_value nor value given for parameter {parameter.name} in reaction {reaction_id}"
                    )

        return parameters

    def _get_experimental_data(self):
        """Extract measurement data from the EnzymeML document"""

        # Initialize data structure to store experimental data
        raw_data, self.inits = [], []

        for measurement_data in self.data.values():

            # Gather data
            data: pd.DataFrame = measurement_data["data"]
            init_concs: dict = measurement_data["initConc"]

            # Collect raw_data
            raw_data.append(data.drop("time", axis=1))

            # Collect initial concentrations for simulation
            init_mapping = {
                "time": data.time,
                **{species_id: value for species_id, (value, _) in init_concs.items()},
            }

            self.inits.append(init_mapping)

        # Concatenate and clean all DataFrames
        self.experimental_data = pd.concat(raw_data)
        self.experimental_data.reset_index(drop=True, inplace=True)
        self.cols = list(self.experimental_data.columns)

    def _get_pysces_model(self, model_dir: str):
        """Converts an EnzymeMLDocument to a PySCeS model."""

        # Set up the PySCeS directory structure
        model_dir = os.path.join(model_dir)
        os.makedirs(model_dir, exist_ok=True)

        # Write the raw XMLString to the dir
        sbmlfile_name = f"{self.enzmldoc.name.replace(' ', '_')}.xml"
        sbmlfile_path = os.path.join(model_dir, sbmlfile_name)
        with open(sbmlfile_path, "w") as file:
            file.write(self.sbml_xml)

        # First, convert the EnzymeML model to a PySCeS model
        pscfile_path = sbmlfile_path + ".psc"
        if not (
            (os.path.exists(pscfile_path))
            and (os.path.getmtime(pscfile_path) > os.path.getmtime(self.filepath))
        ):
            pysces.interface.convertSBML2PSC(sbmlfile_name, sbmldir=model_dir, pscdir=model_dir)

        # Finally, load the PSC model
        self.model = pysces.model(sbmlfile_name, dir=model_dir)

        # work around https://github.com/PySCeS/pysces/issues/79
        if (
            self.model.__KeyWords__["Species_In_Conc"]
            and self.model.__KeyWords__["Output_In_Conc"]
        ):
            for comp in self.model.__compartments__:
                self.model.__compartments__[comp]["size"] = 1.0
                setattr(self.model, comp, 1.0)
                setattr(self.model, f"{comp}_init", 1.0)

    def _calculate_residual(self, parameters) -> np.ndarray:
        """Function that will be optimized"""

        simulated_data = self._simulate_experiment(parameters)
        simulated_data = simulated_data.drop(
            simulated_data.columns.difference(self.cols), axis=1
        )

        return np.array(self.experimental_data - simulated_data)

    def _simulate_experiment(self, parameters):
        """Performs simulation based on the PySCeS model"""

        self.model.SetQuiet()
        self.model.__dict__.update(parameters.valuesdict())

        # intialize collection
        output = []

        # Now iterate over all initial concentrations and simulate accordingly
        for init_concs in self.inits:
            for species_id, value in init_concs.items():

                if type(value) in [float, int] and value == 0:
                    # Catch initial values with zero and set them ot a small number
                    value = 1.0e-9

                if species_id in self.model.species:
                    # Add if given in the model
                    setattr(self.model, f"{species_id}_init", value)
                elif species_id == "time":
                    # Add time to the model
                    time_values, num_reps = self._get_replicate_info(value)
                    self.model.sim_time = time_values
                else:
                    setattr(self.model, species_id, value)

            # Simulate the experiment and save results
            self.model.Simulate(userinit=1)
            for i in range(num_reps):
                output.append(
                    [getattr(self.model.sim, species) for species in self.model.species]
                )

        return pd.DataFrame(np.hstack(output).T, columns=self.model.species)

    def _get_replicate_info(self, time):
        i = 1
        # get index in time series where 2nd replicate starts
        while i < len(time) and time[i] > time[i - 1]:
            i += 1
        num_reps = len(time) // i
        if num_reps > 1:
            for k in range(1, num_reps):
                assert np.allclose(
                    time[:i], time[k * i : k * i + i]
                ), "Time points of replicates don't match!"
        return (time[:i].values, num_reps)

    def plot_fit(self):
        """Plots the simulation and data for the fitted parameters."""

        # check that optimization has been done
        assert hasattr(self, "minimizer") and hasattr(
            self.minimizer, "result"
        ), "Please run optimize() first."

        measurements = list(self.data.keys())
        num = len(measurements)
        numcols = 3
        numrows = math.ceil(num / numcols)
        fig, ax = plt.subplots(nrows=numrows, ncols=numcols, figsize=(9, 2.8 * numrows))
        for i in range(num):
            if num <= numcols:
                theax = ax[i]
            else:
                theax = ax[i // numcols, i % numcols]
            self._plot_measurement(measurements[i], i, ax=theax)
        # remove empty axes
        if num % numcols != 0:
            empty = numcols - num % numcols
            for i in range(-empty, 0):
                if num <= numcols:
                    ax[i].set_visible(False)
                else:
                    ax[num // numcols, i].set_visible(False)
        fig.tight_layout()

    def _plot_measurement(self, meas_id, i=0, ax=None):
        """Plots a single measurement with simulation."""
        time_unit = self.enzmldoc.measurement_dict[meas_id].global_time_unit
        conc_unit = self.enzmldoc.reactant_dict[self.cols[0]].unit
        if not ax:
            fig, ax = plt.subplots()
        sim = self._simulate_measurement(meas_id, self.minimizer.result.params, self.model)
        sim.plot("Time", self.cols, ax=ax, legend=False)
        if i == 0:
            ax.figure.legend(loc='upper left', bbox_to_anchor=(1.0, 0.96))
        ax.set_prop_cycle(None)
        self.data[meas_id]["data"].plot("time", self.cols, style="^", legend=False, ax=ax)
        ax.set_title(meas_id)
        ax.set_xlabel(f"Time ({time_unit})")
        ax.set_ylabel(f"Concentration ({conc_unit})")

    def _simulate_measurement(self, meas_id, parameters, model):
        """Performs simulation based on the PySCeS model"""

        data = self.data[meas_id]["data"]
        model.SetQuiet()
        model.__dict__.update(parameters.valuesdict())

        # Now iterate over all initial concentrations and simulate accordingly
        init_concs = self._map_inits(meas_id)
        for species_id, value in init_concs.items():
            if species_id in model.species:
                # Add if given in the model
                setattr(model, f"{species_id}_init", value)
            else:
                setattr(model, species_id, value)

        # Simulate the experiment and save results
        end_time = data.time.iloc[-1]
        # simulate 200 points for smooth curve
        model.doSim(end=end_time, points=200)
        result = pd.DataFrame(
            np.array([getattr(model.sim, species) for species in self.cols]).T,
            columns=self.cols,
        )
        result["Time"] = self.model.sim.Time
        return result

    def _map_inits(self, meas_id):
        init_concs = self.data[meas_id]["initConc"]
        return {species_id: value for species_id, (value, _) in init_concs.items()}
