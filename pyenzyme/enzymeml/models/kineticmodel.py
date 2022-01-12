'''
File: kineticmodel.py
Project: models
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 22nd 2021 9:55:38 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

import ast

from typing import TYPE_CHECKING, Optional
from pydantic import Field
from dataclasses import dataclass

from libsbml import parseL3Formula, Reaction
from pydantic.fields import PrivateAttr

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class KineticParameter(EnzymeMLBase):

    name: str = Field(
        ...,
        description="Name of the estimated parameter.",
    )

    value: Optional[float] = Field(
        None,
        description="Numerical value of the estimated parameter.",
    )

    unit: Optional[str] = Field(
        None,
        description="Unit of the estimated parameter.",
    )

    stdev: Optional[float] = Field(
        None,
        description="Standard deviation of the estimated parameter."
    )

    initial_value: Optional[float] = Field(
        None,
        description="Initial value that was used for the parameter estimation."
    )

    ontology: Optional[SBOTerm] = Field(
        None,
        description="Type of the estimated parameter.",
    )

    # * Private attributes
    _unit_id: Optional[str] = PrivateAttr(None)


@static_check_init_args
class KineticModel(EnzymeMLBase):

    name: str = Field(
        ...,
        description="Name of the kinetic law.",
    )

    equation: str = Field(
        ...,
        description="Equation for the kinetic law.",
    )

    parameters: list[KineticParameter] = Field(
        default_factory=list,
        description="List of estimated parameters.",
    )

    ontology: Optional[SBOTerm] = Field(
        None,
        description="Type of the estimated parameter.",
    )

    # ! Initializers
    @staticmethod
    def createGenerator(name: str, equation: str, **parameters):
        """Creates an abstract model generator to generated specific models.

        Args:
            name (str): Name of the model.
            equation (str): Equation

        Returns:
            [type]: [description]
        """

        return ModelFactory(
            name=name,
            equation=equation,
            **parameters
        )

    # ! Utilities
    def addToReaction(self, reaction: Reaction) -> None:
        '''
        Adds kinetic law to SBML reaction.
        Only relevant for EnzymeML > SBML conversion.

        Args:
            reaction (libsbml.Reaction): SBML reaciton class
        '''

        # Set up SBML kinetic law node
        kl = reaction.createKineticLaw()

        for kinetic_parameter in self.parameters:

            local_param = kl.createLocalParameter()
            local_param.setId(kinetic_parameter.name)
            local_param.setValue(kinetic_parameter.value)
            local_param.setUnits(kinetic_parameter._unit_id)

            if kinetic_parameter.ontology:
                local_param.setSBOTerm(kinetic_parameter.ontology)

        kl.setMath(parseL3Formula(self.equation))
        kl.setName(self.name)

        if self.ontology:
            kl.setSBOTerm(self.ontology)

    def get_id(self) -> str:
        return self.name

    # ! Getters
    def getParameter(self, name: str) -> KineticParameter:
        """Returns a parameter of choice from the model.

        Args:
            name (str): Name of the parameter.

        Raises:
            KeyError: If the parameter does not exist.

        Returns:
            KineticParameter: The desired parameter.
        """

        try:
            return next(filter(
                lambda parm: parm.name == name, self.parameters
            ))
        except StopIteration:
            raise KeyError(
                f"Parameter {name} not found in the model."
            )

    @deprecated_getter("equation")
    def getEquation(self):
        return self.equation

    @deprecated_getter("parameters")
    def getParameters(self):
        return self.parameters

    @deprecated_getter("name")
    def getName(self):
        return self.name


class ModelFactory:

    equation: str
    parameters: list[str]
    name: str

    def __init__(self, name: str, equation: str, **parameters) -> None:

        # Parse the eqation and get all names and variables
        self.variables = self.parse_equation(equation)

        # Initialize the model
        self.model = KineticModel(
            name=name,
            equation=equation,
            ontology=None
        )

        for name, options in parameters.items():

            # Remove parameter from variables
            self.variables.remove(name)

            # Get all teh options for the parameter
            init_value = options.get("init_value")
            value = options.get("value")
            unit = options.get("unit")
            ontology = options.get("ontology")
            stdev = options.get("stdev")

            parameter = KineticParameter(
                name=name,
                value=value,
                unit=unit,
                initial_value=init_value,
                stdev=stdev,
                ontology=ontology
            )

            self.model.parameters.append(parameter)

    def __call__(self, **variables) -> KineticModel:
        """Returns a KineticModel that is suited for the given parameters.
        """

        # Copy the internal object and modify it to the needs
        model = self.model.copy()

        # Replace everything
        for stock_variable in self.variables:

            try:
                identifier: str = variables[stock_variable]
                model.equation = model.equation.replace(
                    stock_variable, identifier)
            except KeyError:
                raise KeyError(
                    f"Variable {stock_variable} has not been given. Please make sure to cover all variables: [{repr(self.variables)}]"
                )

        return model

    @staticmethod
    def parse_equation(equation: str):
        return [
            node.id for node in ast.walk(ast.parse(equation))
            if isinstance(node, ast.Name)
        ]
