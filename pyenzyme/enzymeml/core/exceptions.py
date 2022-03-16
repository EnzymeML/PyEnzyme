# File: functionalities.py
# Project: core
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import yaml

from typing import Union, Optional


class SpeciesNotFoundError(Exception):
    """Raised when a species hasnt been found in a specific element"""

    def __init__(
        self,
        species_id: str,
        enzymeml_part: str,
        message: str = "Species ID has not been found",
    ):
        self.species_id = species_id
        self.enzymeml_part = enzymeml_part
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.species_id} in {self.enzymeml_part} -> {self.message}"


class MeasurementDataSpeciesIdentifierError(Exception):
    """Raised when either no ID has been assigned to a measurementData"""

    def __init__(self, both: Optional[list] = None):

        if both:
            self.message = f"Both reactant ({both[0]}) and protein ({both[1]}) have been ID assigned to a measurement. Please specifiy either one of those."
        else:
            self.message = (
                "Neither a reactant not protein has been ID assigned to measurement."
            )

        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class ParticipantIdentifierError(Exception):
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


class ChEBIIdentifierError(Exception):
    """Raised when the CHEBI ID is incorrect."""

    def __init__(self, chebi_id: Union[str, int]) -> None:
        self.chebi_id = chebi_id

    def __str__(self) -> str:
        return f"ChEBI ID {self.chebi_id} is invalid. Please provide a valid ChEBI ID."


class UniProtIdentifierError(Exception):
    """Raised when the UniProt ID is incorrect."""

    def __init__(self, uniprotid: Union[str, int]) -> None:
        self.uniprotid = uniprotid

    def __str__(self) -> str:
        return f"UniProt ID {self.uniprotid} is invalid. Please provide a valid UniProt ID."
