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

from builtins import isinstance


def TypeChecker(value, obj):
    if isinstance(value, obj):
        return value
    else:
        raise TypeError(
            "Expected %s got %s"
            % (str(obj), str(type(value)))
        )
