# File: measurementData.py
# Project: thinlayers
# Author: Jan Range, Dr. Frank Bergmann, Prof. Dr. Johann Rohwer
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

from abc import ABC, abstractmethod
from typing import Union, Optional

from pyenzyme.enzymeml.core.enzymemldocument import EnzymeMLDocument


class BaseThinLayer(ABC):
    def __init__(
        self,
        path,
        measurement_ids: Union[str, list] = "all",
        init_file: Optional[str] = None,
    ):

        if isinstance(measurement_ids, str) and measurement_ids != "all":
            raise TypeError("Measurements must either be a list of IDs or 'all'")

        # Load the EnzymeML document to gather data
        self.filepath = path
        self.enzmldoc = EnzymeMLDocument.fromFile(path)

        # If an initialization schema is given, apply it here
        if init_file:
            self.enzmldoc.applyModelInitialization(init_file, to_values=True)

        # The following will extract the tim course data found in all measurements
        self.sbml_xml = self.enzmldoc.toXMLString()
        self.data = self.enzmldoc.exportMeasurementData(measurement_ids=measurement_ids)

        # Get all rate laws and store them in a dictionary
        self.reaction_data = {
            reaction.id: (reaction.model, reaction.getStoichiometricCoefficients())
            for reaction in self.enzmldoc.reaction_dict.values()
            if reaction.model
        }

        # Store global parameters if given
        self.global_parameters = self.enzmldoc.global_parameters

    @abstractmethod
    def optimize(self):
        """
        The optimize method should only utilize the objects attributes 'data' and 'models' since these
        should cover all necessary informations to run the optimization. In addition, the method could
        also utilize the XML string if based in SBML.

        Finally, if an optimization has been performed the method should enter all estimated values as
        well as optional statistics such as stdev or AKAIKE for instance to each parameter. Since the
        models found in 'self.models' are immutable objects and thus references, the estimated parameters
        will already be inserted to the model.

        See the example class below to see how the optimization could be implemented.
        """
        raise NotImplementedError()

    @abstractmethod
    def write(self) -> EnzymeMLDocument:
        """Writes the estimated parameters back to a new EnzymeMLDocument"""
        raise NotImplementedError()
