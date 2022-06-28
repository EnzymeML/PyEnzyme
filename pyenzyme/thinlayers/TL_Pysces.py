# File: TL_Pysces.py
# Project: ThinLayers
# Author: Johann Rohwer (j.m.rohwer@gmail.com)
# License: BSD-2 clause
# Copyright (c) 2022 Stellenbosch University

import numpy as np
import pandas as pd
import os
import yaml

from typing import Union, Optional, List
from pyenzyme.thinlayers.TL_Base import BaseThinLayer
from pyenzyme.enzymeml.core.exceptions import SpeciesNotFoundError
from pyenzyme.enzymeml.core.measurement import Measurement
from pyenzyme.enzymeml.core.replicate import Replicate

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

        if self.experimental_data is None:
            raise ValueError(
                "The given experiment has no data which is mandatory to perform an optimization. "
            )

        # Initialize the model parameters
        parameters = self._initialize_parameters()

        # Perform optimization
        self.minimizer = lmfit.Minimizer(self._calculate_residual, parameters)

        # Set estiomated parameters to self
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

    def simulate(
        self,
        time: Union[List[float], int],
        step: int = 1,
        init_file: Optional[str] = None,
        name: Optional[str] = None,
        to_measurement: bool = False,
        **kwargs,
    ):
        """Simulates a given model over a time period"""

        if isinstance(time, list):
            # Convert to Series to maintain functionality
            # in helper function '_simulate_experiment'
            time = pd.Series(time)
        elif isinstance(time, int):
            # Generate a series to a certain point of time
            time = pd.Series(list(range(0, time, step)))
        else:
            raise TypeError(
                f"Expected either a list or number of timesteps. Got '{type(time)}' instead."
            )

        if init_file:
            inits = yaml.safe_load(open(init_file).read())
            initials = {
                species_id: config["init_conc"] for species_id, config in inits.items()
            }
        else:
            initials = {**kwargs}

        self.inits = [{"time": time, **initials}]

        # Perform simulation
        output = self._simulate_experiment()
        output.index.name = "Time"

        if to_measurement:
            name = name if name is not None else "Unnamed"
            self._add_to_measurements(name=name, time=time, data=output)

        return output

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

            if global_param.value:
                parameters.add(
                    f"{global_param.name}",
                    global_param.value,
                    vary=not global_param.constant,
                    min=global_param.lower,
                    max=global_param.upper,
                )

            elif global_param.initial_value:
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

                if parameter.value:
                    parameters.add(
                        f"{reaction_id}_{parameter.name}",
                        parameter.value,
                        vary=not parameter.constant,
                        min=parameter.lower,
                        max=parameter.upper,
                    )
                elif parameter.initial_value:
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
        if raw_data:
            self.experimental_data = pd.concat(raw_data)
            self.experimental_data.reset_index(drop=True, inplace=True)
            self.cols = list(self.experimental_data.columns)
        else:
            self.experimental_data = None

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
            sbmlfile_name, sbmldir=model_dir, pscdir=model_dir
        )

        # Finally, load the PSC model
        self.model = pysces.model(sbmlfile_name, dir=model_dir)

    def _calculate_residual(self, parameters) -> np.ndarray:
        """Function that will be optimized"""

        simulated_data = self._simulate_experiment(parameters)
        simulated_data = simulated_data.drop(
            simulated_data.columns.difference(self.cols), axis=1
        )

        return np.array(self.experimental_data - simulated_data)

    def _simulate_experiment(self, parameters=None):
        """Performs simulation based on the PySCeS model"""

        self.model.SetQuiet()

        if parameters:
            # Used for optimization only
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
                [getattr(self.model.sim, species) for species in self.model.species]
            )

        return pd.DataFrame(np.hstack(output).T, columns=self.model.species)

    def _add_to_measurements(self, name: str, time, data):
        """Adds simulation outputs to measurements"""

        FUNCTIONAL_FIELDS = ["reaction", "time"]

        # Create the measurement
        time_unit = self._infer_time_unit()
        measurement = Measurement(
            name=name,
            global_time=time.to_list(),
            global_time_unit=time_unit,
        )

        for init in self.inits:
            for species, init_conc in init.items():

                if species in FUNCTIONAL_FIELDS:
                    continue

                unit = self.enzmldoc.getAny(species).unit

                if species in data:
                    repls = [
                        Replicate(
                            id=f"simu_{name}_{species}_{init_conc}",
                            species_id=species,
                            data_unit=unit,
                            time_unit=time_unit,
                            data=data[species].to_list(),
                            time=time.to_list(),
                            is_calculated=True,
                        )
                    ]

                else:
                    repls = []

                measurement.addData(
                    reactant_id=species,
                    init_conc=init_conc,
                    unit=unit,
                    replicates=repls,
                )

            self.enzmldoc.addMeasurement(measurement)

    def _infer_time_unit(self):
        """Retrieves the time unit for the simulation from the parameter unit definitions"""

        params = self.enzmldoc.exportKineticParameters()
        unit_defs = [
            self.enzmldoc._unit_dict[self.enzmldoc._convertToUnitDef(unit)]
            for unit in params.unit
            if unit is not None
        ]

        # Filter time units and create a unique set
        time_units = set()
        for unit in unit_defs:
            # Find the time part and safe in a list

            filtered_units = list(
                filter(lambda base: base.kind == "second", unit.units)
            )

            time_units.update([unit.get_name() for unit in filtered_units])

        if len(time_units):
            return list(time_units)[0]

        # Raise an error if there are either no time units
        # or different ones -> Bot scenarios do not make sense
        raise ValueError(
            "Either found none or different time units in the document. ({time_units})"
        )
