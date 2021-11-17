'''
File: baseclass.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 15th 2021 7:48:31 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from typing import TYPE_CHECKING
from pydantic import BaseModel
from dataclasses import dataclass
from typing import Optional

from pyenzyme.enzymeml.core.utils import type_checking

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class EnzymeMLBase(BaseModel):
    class Config:
        validate_assignment = True
        validate_all = True
