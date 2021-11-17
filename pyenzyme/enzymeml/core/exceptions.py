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


class ValidationError(Exception):
    """Raised when a Dataverse validation has failed"""
    pass


class DataverseError(Exception):
    """Raised when a Dataverse validation has failed"""
    pass


class SpeciesNotFoundError(Exception):
    """Raised when a species hasnt been found in a specific element"""

    def __init__(self, species_id: str, enzymeml_part: str, message: str = "Species ID has not been found in "):
        self.species_id = species_id
        self.enzymeml_part = enzymeml_part
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f'{self.species_id} in {self.enzymeml_part} -> {self.message}'


class MissingSpeciesError(Exception):
    """Raised when a species has not yet been assigned to a measurement"""
    pass


class IdentifierError(Exception):
    """Raised when either no ID has been assigned to a measurementData"""
    pass


class ECNumberError(Exception):
    """Raised when an EC number does not match the pattern convenrtion"""

    def __init__(self, ec_number: str):
        self.ec_number = ec_number

    def __str__(self) -> str:
        return f"EC number {self.ec_number} does not match the pattern. Please specifify as X.X.X.X"


class DataError(Exception):
    """Raised when incomplete data has been assigned to a replicate"""
    pass


class UnitKindError(Exception):
    """Raised when an to SBML unknown unit kind has been given"""

    def __str__(self) -> str:
        return (
            "The unit kind integer that has been given is not supported. Please check 'libsbml' for the supported ones."
        )
