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

from typing import TYPE_CHECKING, Optional
from enum import Enum
from pydantic import Field
from dataclasses import dataclass

from libsbml import parseL3Formula, Reaction
from pydantic.fields import PrivateAttr

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
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

    value: float = Field(
        ...,
        description="Numerical value of the estimated parameter.",
    )

    unit: str = Field(
        ...,
        description="Unit of the estimated parameter.",
    )

    ontology: Optional[Enum] = Field(
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

    ontology: Optional[Enum] = Field(
        ...,
        description="Type of the estimated parameter.",
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

    # ! Getters
    @deprecated_getter("equation")
    def getEquation(self):
        return self.equation

    @deprecated_getter("parameters")
    def getParameters(self):
        return self.parameters

    @deprecated_getter("name")
    def getName(self):
        return self.name
