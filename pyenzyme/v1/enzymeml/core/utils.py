# File: functionalities.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart


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
