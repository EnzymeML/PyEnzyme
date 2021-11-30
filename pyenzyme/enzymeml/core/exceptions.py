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

from typing import Union


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


class IdentifierNameError(Exception):
    """Raised when an ID does not match the expected format"""

    def __init__(self, id: str, prefix: str) -> None:
        self.prefix = prefix
        self.id = id

    def __str__(self) -> str:
        return f"Identifier '{self.id}' does not match the expected format of '{self.prefix}[digits]'."


class ECNumberError(Exception):
    """Raised when an EC number does not match the pattern convenrtion"""

    def __init__(self, ecnumber: str):
        self.ecnumber = ecnumber

    def __str__(self) -> str:
        return f"EC number {self.ecnumber} does not match the pattern. Please specifify as X.X.X.X"


class DataError(Exception):
    """Raised when incomplete data has been assigned to a replicate"""
    pass


class UnitKindError(Exception):
    """Raised when an to SBML unknown unit kind has been given"""

    def __str__(self) -> str:
        return (
            "The unit kind integer that has been given is not supported. Please check 'libsbml' for the supported ones."
        )


class MissingUnitError(Exception):
    """Raised when a unit is missing """


class ChEBIIdentifierError(Exception):
    """Raised when the CHEBI ID is incorrect."""

    def __init__(self, chebi_id: Union[str, int]) -> None:
        self.chebi_id = chebi_id

    def __str__(self) -> str:
        return (
            f"ChEBI ID {self.chebi_id} is invalid. Please provide a valid ChEBI ID."
        )


class UniProtIdentifierError(Exception):
    """Raised when the UniProt ID is incorrect."""

    def __init__(self, uniprotid: Union[str, int]) -> None:
        self.uniprotid = uniprotid

    def __str__(self) -> str:
        return (
            f"UniProt ID {self.uniprotid} is invalid. Please provide a valid UniProt ID."
        )
