'''
File: functionalities.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Tuesday June 15th 2021 6:43:34 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''


class ValidationError(Exception):
    """Raised when a Dataverse validation has failed"""
    pass


class DataverseError(Exception):
    """Raised when a Dataverse validation has failed"""
    pass


def TypeChecker(value, obj):
    if isinstance(value, obj):
        return value
    else:
        raise TypeError(
            "Expected %s got %s"
            % (str(obj), str(type(value)))
        )
