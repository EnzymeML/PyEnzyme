# File: baseclass.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import json
import logging

from pydantic import BaseModel, PrivateAttr
from pyenzyme.utils.log import log_change
from typing import Optional

logger = logging.getLogger("pyenzyme")


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
                "protein_dict": {"Protein": {"__all__": {"_unit_id"}}},
            },
            by_alias=True,
            **kwargs,
        )

    @classmethod
    def fromJSON(cls, json_string):
        return cls.parse_obj(json.loads(json_string))

    def __setattr__(self, name, value):
        """Modified attribute setter to document changes in the EnzymeML document"""

        # Check for changing units and assign a new one
        if "unit" in name and not name.startswith("_") and hasattr(self, "_enzmldoc"):
            if self._enzmldoc and value:
                # When the object has already been assigned to a document
                # use this to set and add the new unit

                # Create a new UnitDef and get the ID
                new_unit_id = self._enzmldoc._convertToUnitDef(value)
                value = self._enzmldoc.unit_dict[new_unit_id]._get_unit_name()

                # Set the unit ID to the object
                attr_name = f"_{name}_id"
                super().__setattr__(attr_name, new_unit_id)

        # Perform logging of the new attribute to history
        old_value = getattr(self, name)

        # Whenever a new ID is assigned, make sure the names are compliant with our standards
        if "unit_id" in name and hasattr(self, "_enzmldoc"):
            if self._enzmldoc:
                unit_name = self._enzmldoc.unit_dict[value]._get_unit_name()
                attr_name = name.replace("_id", "")[1::]
                super().__setattr__(attr_name, unit_name)

        if (
            isinstance(old_value, list) is False
            and name.startswith("_") is False
            and name != "id"
            and old_value
        ):

            if type(self).__name__ != "EnzymeMLDocument":

                try:
                    log_change(
                        logger,
                        type(self).__name__,
                        getattr(self, "id"),
                        name,
                        old_value,
                        value,
                    )

                except AttributeError:
                    log_change(
                        logger,
                        type(self).__name__,
                        self.get_id(),
                        name,
                        old_value,
                        value,
                    )

        # Finally, set the new attribute's value
        super().__setattr__(name, value)
