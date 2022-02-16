"""
File: TL_Pysces.py
Project: ThinLayers
Author: Johann Rohwer (j.m.rohwer@gmail.com)
License: BSD-2 clause
-----
Copyright (c) 2021 Stellenbosch University
"""

import numpy as np
import pandas as pd
import os
import pysces
import lmfit
import copy

from pyenzyme.thinlayers.TL_Base import BaseThinLayer


class ThinLayerPysces(BaseThinLayer):

    # ! Interface
    def optimize(self, model_dir: str):
        """Performs optimization of the given parameters"""

        # Prepare the model
        self._get_pysces_model(model_dir)
        self._initialize_parameters()
        self._get_experimental_data()

        # Perform optimization
        self.minimizer = lmfit.Minimizer(
            self._calculate_residual, self.parameters
        )

        return self.minimizer.minimize()

    def write(self):
        """Writes the estimated parameters to a copy of the EnzymeMLDocument"""

        nu_enzmldoc = self.enzmldoc.copy(deep=True)
        parameters = self.parameters.valuesdict()

        for name, value in parameters.items():
            # names contain information about reaction and parameter
            # Pattern: rX_name

            splitted = name.split("_")
            reaction_id = splitted[0]
            parameter_id = "_".join(splitted[1::])

            # Fetch reaction and parameter
            reaction = nu_enzmldoc.getReaction(reaction_id)

            if reaction.model:
                parameter = reaction.model.getParameter(parameter_id)
                parameter.value = value
            else:
                raise TypeError(
                    f"Reaction {reaction_id} has no model to add values to"
                )

        return nu_enzmldoc

    # ! Helper methods
    def _initialize_parameters(self) -> None:
        """Adds all parameters to an lmfit Parameters instance.

        Raises:
            ValueError: Raised when parameter posesses neither an initial value or value attribute
        """

        # Initialize lmfit parameters
        self.parameters = lmfit.Parameters()

        # Add global parameters
        for global_param in self.global_parameters.values():

            if global_param.value:
                self.parameters.add(
                    f"{global_param.name}", global_param.value, vary=not global_param.constant,
                    min=global_param.lower, max=global_param.upper
                )

            elif global_param.initial_value:
                self.parameters.add(
                    f"{global_param.name}", global_param.initial_value, vary=not global_param.constant,
                    min=global_param.lower, max=global_param.upper
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

                if parameter.value:
                    self.parameters.add(
                        f"{reaction_id}_{parameter.name}", parameter.value, vary=not parameter.constant,
                        min=parameter.lower, max=parameter.upper
                    )
                elif parameter.initial_value:
                    self.parameters.add(
                        f"{reaction_id}_{parameter.name}", parameter.initial_value, vary=not parameter.constant,
                        min=parameter.lower, max=parameter.upper
                    )
                else:  # parameter is
                    raise ValueError(
                        f"Neither initial_value nor value given for parameter {parameter.name} in reaction {reaction_id}"
                    )

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
                **{species_id: value
                   for species_id, (value, _) in init_concs.items()
                   }
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
            file.write(self.enzmldoc.toXMLString())

        # First, convert the EnzymeML model to a PySCeS model
        pysces.interface.convertSBML2PSC(
            sbmlfile_name,
            sbmldir=model_dir,
            pscdir=model_dir
        )

        # Finally, load the PSC model
        self.model = pysces.model(sbmlfile_name, dir=model_dir)

    def _calculate_residual(self, parameters: lmfit.Parameters) -> np.ndarray:
        """Function that will be optimized"""

        simulated_data = self._simulate_experiment(parameters)
        simulated_data = simulated_data.drop(
            simulated_data.columns.difference(self.cols), axis=1
        )

        return np.array(self.experimental_data - simulated_data)

    def _simulate_experiment(self, parameters: lmfit.Parameters):
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
                    value = 1.0e-6

                if species_id in self.model.species:
                    # Add if given in the model
                    setattr(self.model, f"{species_id}_init", value)
                elif species_id == "time":
                    # Add time to the model
                    self.model.sim_time = value.values
                else:
                    setattr(self.model, species_id, value)

            # Simulate the experiment and save results
            self.model.Simulate(userinit=1)
            output.append(
                [getattr(self.model.sim, species)
                 for species in self.model.species]
            )

        return pd.DataFrame(np.hstack(output).T, columns=self.model.species)
