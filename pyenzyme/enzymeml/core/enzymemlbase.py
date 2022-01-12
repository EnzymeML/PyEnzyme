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

import logging

from typing import TYPE_CHECKING
from pydantic import BaseModel
from dataclasses import dataclass

from pyenzyme.enzymeml.core.utils import type_checking
from pyenzyme.utils.log import log_change

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


logger = logging.getLogger("pyenzyme")


@static_check_init_args
class EnzymeMLBase(BaseModel):
    class Config:
        validate_assignment = True
        validate_all = True

    def json(self, indent: int = 2, **kwargs):
        return super().json(
            indent=indent,
            exclude_none=True,
            exclude={
                "log": ...,
                "unit_dict": ...,
                "file_dict": ...,
                "protein_dict":
                    {
                        "Protein": {"__all__": {"_unit_id"}}
                    }
            },
            by_alias=True,
            **kwargs
        )

    def __setattr__(self, name, value):
        """Modified attribute setter to document changes in the EnzymeML document"""
        old_value = getattr(self, name)
        if isinstance(old_value, list) is False and name.startswith("_") is False and name != "id" and old_value:

            if type(self).__name__ != "EnzymeMLDocument":

                try:
                    log_change(
                        logger,
                        type(self).__name__,
                        getattr(self, 'id'),
                        name,
                        old_value,
                        value
                    )

                except AttributeError:
                    log_change(
                        logger,
                        type(self).__name__,
                        self.get_id(),
                        name,
                        old_value,
                        value
                    )

        super().__setattr__(name, value)
