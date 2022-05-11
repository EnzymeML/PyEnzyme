# File: kineticmodel.py
# Project: models
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import ast
import re
import numexpr

from typing import Any, List, TYPE_CHECKING, Optional
from pydantic import Field
from dataclasses import dataclass

from pydantic.fields import PrivateAttr

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.utils import type_checking, deprecated_getter

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

    initial_value: Optional[float] = Field(
        None, description="Initial value that was used for the parameter estimation."
    )

    upper: Optional[float] = Field(
        None, description="Upper bound of the estimated parameter."
    )

    lower: Optional[float] = Field(
        None, description="Lower bound of the estimated parameter."
    )

    is_global: bool = Field(
        False, description="Specifies if this parameter is a global parameter."
    )

    stdev: Optional[float] = Field(
        None, description="Standard deviation of the estimated parameter."
    )

    constant: bool = Field(False, description="Specifies if this parameter is constant")

    ontology: Optional[SBOTerm] = Field(
        None,
        description="Type of the estimated parameter.",
    )

    # * Private attributes
    _unit_id: Optional[str] = PrivateAttr(None)
    _enzmldoc = PrivateAttr(default=None)

    def get_id(self):
        """For logging. Dont bother."""
        return self.name

    # ! Utilities
    def update(self, **kwargs):
        """Adds attributes to this parameter based in kwargs"""
        self.__dict__.update(kwargs)

    # ! Getters
    def unitdef(self):
        """Returns the appropriate unitdef if an enzmldoc is given"""

        if not self._enzmldoc:
            return None

        return self._enzmldoc._unit_dict[self._unit_id]


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

    parameters: List[KineticParameter] = Field(
        default_factory=list,
        description="List of estimated parameters.",
    )

    ontology: Optional[SBOTerm] = Field(
        None,
        description="Type of the estimated parameter.",
    )

    # ! Add methods
    def addParameter(
        self,
        name: str,
        value: Optional[float] = None,
        unit: Optional[str] = None,
        initial_value: Optional[float] = None,
        upper: Optional[float] = None,
        lower: Optional[float] = None,
        is_global: bool = False,
        stdev: Optional[float] = None,
        constant: bool = False,
        ontology: Optional[SBOTerm] = None,
    ):
        """Adds a parameter to the KineticModel object

        Args:
            name (str): Name of the estimated parameter.
            value (Optional[float], optional): Numerical value of the estimated parameter.. Defaults to None.
            unit (Optional[str], optional): Unit of the estimated parameter.. Defaults to None.
            initial_value (Optional[float], optional): Initial value that was used for the parameter estimation. Defaults to None.
            upper (Optional[float], optional): Upper bound of the estimated parameter.. Defaults to None.
            lower (Optional[float], optional): Lower bound of the estimated parameter.. Defaults to None.
            is_global (bool, optional): Specifies if this parameter is a global parameter.. Defaults to False.
            stdev (Optional[float], optional): Standard deviation of the estimated parameter.. Defaults to None.
            constant (bool, optional): Specifies if this parameter is constant. Defaults to False.
            ontology (Optional[SBOTerm], optional): Type of the estimated parameter.. Defaults to None.
        """

        self.parameters.append(
            KineticParameter(
                name=name,
                value=value,
                unit=unit,
                initial_value=initial_value,
                upper=upper,
                lower=lower,
                is_global=is_global,
                stdev=stdev,
                constant=constant,
                ontology=ontology,
            )
        )

        self.__dict__["_" + self.parameters[-1].name] = self.parameters[-1]

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

        return ModelFactory(name=name, equation=equation, **parameters)

    @classmethod
    def fromEquation(cls, name: str, equation: str, enzmldoc: Optional[Any] = None):
        """Creates a Kinetic Model instance from an equation

        Args:
            equation (str): Mathematical equation decribing the model.

        Returns:
            KineticModel: Resulting kinetic model
        """

        if enzmldoc:
            # Convert an equation with names to one with IDs

            class_name = enzmldoc.__class__.__name__
            if class_name != "EnzymeMLDocument":
                # Guard clause
                raise TypeError(
                    f"Expected type 'EnzymeMLDocument' for argument 'enzmldoc'. Got '{class_name}' instead."
                )

            # Now perform the actual conversion
            equation = cls._convert_names_to_ids(enzmldoc, equation)

        # Create a new instance
        cls = cls(name=name, equation=equation)

        # Parse equation and add parameters
        used_species = []
        for node in ast.walk(ast.parse(equation)):
            if isinstance(node, ast.Name):
                name = node.id
                regex = re.compile(r"[s|p|c]\d*")
                if not bool(regex.match(name)) and "_" + name not in cls.__dict__:
                    cls.addParameter(name=name)
                else:
                    used_species.append(name)

        if not used_species:
            raise TypeError(
                "It seems like you have included no species (Protein, Reactant, Complex) in your equation. "
                "Are you using names? Please set your 'EnzymeMLDocument' to the argument 'enzmldoc' in order to proceed"
            )

        return cls

    @staticmethod
    def _convert_names_to_ids(enzmldoc, equation: str):
        """Converts names in an equation to appropriate IDs given in an EnzymeMLDocument"""

        all_species = {
            **enzmldoc.protein_dict,
            **enzmldoc.reactant_dict,
            **enzmldoc.complex_dict,
        }

        for id, species in all_species.items():
            equation = equation.replace(species.name, id)

        return equation

    # ! Utilities

    def get_id(self) -> str:
        return self.name

    def evaluate(self, **kwargs):
        """Calculates the the reaction velocity given the internal parameters and variable concentrations handed as keyword arguments.

        Examples:

            model = KineticModel(...) <- Lets assume this is a Menten Model with already estimated parameters
            print(model.evaluate(protein=10.0, substrate=1.0))

            >> 1.002 <- This is the resulting velocity

        Returns:
            float: Corresponding reaction velocity given the internal parameters and variables.
        """

        # Initialize a dictionary which will take care to create an eval string
        params = {}

        # Get the values for the parameters
        for parameter in self.parameters:
            if parameter.value:
                params.update({parameter.name: parameter.value})

        # Now replace the strings in the equation to evaluate it using numexpr
        eval_string = self.equation
        for key, value in {**kwargs, **params}.items():

            eval_string = eval_string.replace(key, str(value))

        return numexpr.evaluate(eval_string).tolist()

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
            return next(filter(lambda parm: parm.name == name, self.parameters))
        except StopIteration:
            raise KeyError(f"Parameter {name} not found in the model.")

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
    parameters: List[str]
    name: str

    def __init__(
        self, name: str, equation: str, ontology: Optional[SBOTerm] = None, **parameters
    ) -> None:

        # Parse the eqation and get all names and variables
        self.variables = self.parse_equation(equation)

        # Initialize the model
        self.model = KineticModel(name=name, equation=equation, ontology=None)

        for name, options in parameters.items():

            # Remove parameter from variables
            self.variables.remove(name)

            # Get all teh options for the parameter
            init_value = options.get("init_value")
            value = options.get("value")
            unit = options.get("unit")
            ontology = options.get("ontology")
            stdev = options.get("stdev")
            upper = options.get("upper")
            lower = options.get("lower")
            constant = options.get("constant")

            # Convert constant to bool if not set
            if not constant:
                constant = False

            parameter = KineticParameter(
                name=name,
                value=value,
                unit=unit,
                initial_value=init_value,
                stdev=stdev,
                ontology=ontology,
                upper=upper,
                lower=lower,
                is_global=False,
                constant=constant,
            )

            self.model.parameters.append(parameter)

    def __call__(self, mapping: dict = {}, **variables) -> KineticModel:
        """Returns a KineticModel that is suited for the given parameters."""

        # Copy the internal object and modify it to the needs
        model = KineticModel(**self.model.dict())

        # Replace everything
        for stock_variable in self.variables:

            try:
                identifier = variables[stock_variable]

                if isinstance(identifier, list):
                    # Allow multiple species
                    identifier = [repr(name) for name in identifier]
                    identifier = f"({' * '.join(identifier)})"
                else:
                    identifier = repr(identifier)

                model.equation = model.equation.replace(stock_variable, identifier)

            except KeyError:
                raise KeyError(
                    f"Variable {stock_variable} has not been given. Please make sure to cover all variables: [{repr(self.variables)}]"
                )

        # Apply mapping
        if mapping:
            self._apply_mapping(mapping, model)

        return model

    def _apply_mapping(self, mapping: dict, model: KineticModel):
        """Applies a mapping that has been given to the model."""

        for param_old, param_new in mapping.items():
            model.equation = model.equation.replace(param_old, param_new)

            # Variable to control when a parameter has found
            found = False

            for index, parameter in enumerate(model.parameters):
                if parameter.name == param_old:

                    # Copy old and add new parameter
                    nu_param = parameter.copy()
                    nu_param.name = param_new
                    model.parameters.append(nu_param)

                    found = True

                    # Remove old one
                    del model.parameters[index]
                    continue

            if not found:
                raise KeyError(f"Parameter {param_old} is not part of the model.")

    @staticmethod
    def parse_equation(equation: str):
        return list(
            set(
                [
                    node.id
                    for node in ast.walk(ast.parse(equation))
                    if isinstance(node, ast.Name)
                ]
            )
        )
