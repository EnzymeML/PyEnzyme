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


from deprecation import deprecated


def type_checking(cls):
    """Used to enable pyDantic type checking, since it is not supported yet by Pylance"""
    return cls


def deprecated_getter(name: str):
    """Decorator used to indicate that a deprecated method has been used"""
    return deprecated(
        details=f"Use the attribute `{name}` instead.",
    )


def deprecated_method(name: str):
    """Decorator used to indicate that a deprecated method has been used"""
    return deprecated(
        details=f"Use the method `{name}` instead.",
    )
