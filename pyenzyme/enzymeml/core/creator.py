'''
File: creator.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 15th 2021 6:28:16 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from pydantic import BaseModel, Field
from typing import TYPE_CHECKING
from dataclasses import dataclass
from deprecation import deprecated

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
class Creator(EnzymeMLBase):

    given_name: str = Field(
        description='Given name of the author or contributor.',
        required=True
    )

    family_name: str = Field(
        description='Family name of the author or contributor.',
        required=True
    )

    mail: str = Field(
        description='Email address of the author or contributor.',
        required=True
    )

    @deprecated_getter("family_name")
    def getFname(self) -> str:
        return self.family_name

    @deprecated_getter("given_name")
    def getGname(self) -> str:
        return self.given_name

    @deprecated_getter("mail")
    def getMail(self) -> str:
        return self.mail
