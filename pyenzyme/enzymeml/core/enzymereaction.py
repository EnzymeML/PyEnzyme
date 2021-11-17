'''
File: enzymereaction.py
Project: core
Author: Jan Range
License: BSD-2 clause
-----
Last Modified: Wednesday June 23rd 2021 9:06:54 pm
Modified By: Jan Range (<jan.range@simtech.uni-stuttgart.de>)
-----
Copyright (c) 2021 Institute of Biochemistry and Technical Biochemistry Stuttgart
'''

from typing import List, Optional, TYPE_CHECKING, Any
from enum import Enum
from dataclasses import dataclass
from pydantic import (
    BaseModel,
    PositiveFloat,
    validator,
    validate_arguments,
    Field
)

from pyenzyme.enzymeml.core.enzymemlbase import EnzymeMLBase
from pyenzyme.enzymeml.models.kineticmodel import KineticModel
from pyenzyme.enzymeml.core.ontology import SBOTerm
from pyenzyme.enzymeml.core.exceptions import (
    ValidationError,
    SpeciesNotFoundError,
)

from pyenzyme.enzymeml.core.utils import (
    type_checking,
    deprecated_getter
)

if TYPE_CHECKING:  # pragma: no cover
    static_check_init_args = dataclass
else:
    static_check_init_args = type_checking


@static_check_init_args
class ReactionElement(BaseModel):
    """Describes an element of a chemical reaction."""

    species_id: str = Field(
        description="Internal identifier to either a protein or reactant defined in the EnzymeMLDocument.",
        required=True
    )

    stoichiometry: PositiveFloat = Field(
        description="Positive float number representing the associated stoichiometry.",
        required=True
    )

    is_constant: bool = Field(
        description="Whether or not the concentration of this species remains constant.",
        required=True
    )

    ontology: Enum = Field(
        description="Ontology defining the role of the given species.",
        required=True
    )


@static_check_init_args
class EnzymeReaction(EnzymeMLBase):
    """
        Describes an enzyme reaction by combining already defined
        reactants/proteins of an EnzymeML document. In addition,
        this class provides ways to integrate reaction conditions
        as well. It is also possible to add a kinetic law to this
        object by using the KineticModel class.
    """

    name: str = Field(
        description="Name of the reaction.",
        required=True
    )

    temperature: float = Field(
        description="Numeric value of the temperature of the reaction.",
        required=True
    )

    temperature_unit: str = Field(
        description="Unit of the temperature of the reaction.",
        required=True,
        regex=r"kelvin|Kelvin|k|K|celsius|Celsius|C|c"
    )

    ph: float = Field(
        description="PH value of the reaction.",
        required=True,
        inclusiveMinimum=0,
        inclusiveMaximum=14
    )

    reversible: bool = Field(
        description="Whether the reaction is reversible or irreversible",
        required=True
    )

    id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the reaction.",
        required=False,
        regex=r"r[\d]+"
    )

    meta_id: Optional[str] = Field(
        default=None,
        description="Unique meta identifier for the reaction.",
        required=False
    )

    uri: Optional[str] = Field(
        default=None,
        description="URI of the reaction.",
        required=False
    )

    creator_id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the author.",
        required=False
    )

    model: Optional[Any] = Field(
        default=None,
        description="Kinetic model decribing the reaction.",
        required=False
    )

    educts: List[ReactionElement] = Field(
        default_factory=list,
        description="List of educts containing ReactionElement objects.",
        required=True
    )

    products: List[ReactionElement] = Field(
        default_factory=list,
        description="List of products containing ReactionElement objects.",
        required=True
    )

    modifiers: List[ReactionElement] = Field(
        default_factory=list,
        description="List of modifiers (Proteins, snhibitors, stimulators) containing ReactionElement objects.",
        required=False
    )

    # Validators
    @validator("temperature_unit")
    def check_temperature_unit(cls, temperature_unit: str):
        valid_units = ["C", "c", "celsius", "K", "kelvin"]
        if temperature_unit not in valid_units:
            raise ValidationError(
                f"Temperature unit {temperature_unit} is not a valid unit - {valid_units}"
            )

        return temperature_unit

    # Utility methods
    def getEduct(self, id: str) -> ReactionElement:
        """
        Returns a ReactionElement including information about the following properties:

            - Reactant/Protein Identifier
            - Stoichiometry of the element
            - Whether or not the element's concentration is constant

        Args:
            id (string): Reactant/Protein ID

        Raises:
            SpeciesNotFoundError: If species ID is unfindable

        Returns:
            ReactionElement: Object including species ID, stoichiometry, constant)
        """

        return self._getReactionElement(
            id=id, element_list=self.educts, element_type="Educts"
        )

    def getProduct(self, id: str) -> ReactionElement:
        """
        Returns a ReactionElement including information about the following properties:

            - Reactant/Protein Identifier
            - Stoichiometry of the element
            - Whether or not the element's concentration is constant

        Args:
            id (string): Reactant/Protein ID

        Raises:
            SpeciesNotFoundError: If species ID is unfindable

        Returns:
            ReactionElement: Object including species ID, stoichiometry, constant)
        """

        return self._getReactionElement(
            id=id, element_list=self.products, element_type="Products"
        )

    def getModifier(self, id: str) -> ReactionElement:
        """
        Returns a ReactionElement including information about the following properties:

            - Reactant/Protein Identifier
            - Stoichiometry of the element
            - Whether or not the element's concentration is constant

        Args:
            id (string): Reactant/Protein ID

        Raises:
            SpeciesNotFoundError: If species ID is unfindable

        Returns:
            ReactionElement: Object including species ID, stoichiometry, constant)
        """

        return self._getReactionElement(
            id=id, element_list=self.modifiers, element_type="Modifiers"
        )

    @validate_arguments
    def _getReactionElement(
        self,
        id: str,
        element_list: list[ReactionElement],
        element_type: str,
    ) -> ReactionElement:

        try:
            return next(filter(
                lambda element: element.species_id == id,
                element_list
            ))
        except StopIteration:
            raise SpeciesNotFoundError(
                species_id=id, enzymeml_part=element_type
            )

    @validate_arguments
    def __addElement(
        self,
        species_id: str,
        stoichiometry: PositiveFloat,
        is_constant: bool,
        element_list: List[ReactionElement],
        ontology: Enum,
        enzmldoc
    ) -> None:

        # Check if species is part of document already
        all_species = [
            list(enzmldoc.getProteinDict.keys()),
            list(enzmldoc.getReactantDict.keys()),
        ]

        if species_id not in all_species:
            raise SpeciesNotFoundError(
                species_id=species_id, enzymeml_part="EnzymeMLDocument"
            )

        # Add element to the respecticve list
        element_list.append(ReactionElement(
            species_id=species_id,
            stoichiometry=stoichiometry,
            is_constant=is_constant,
            ontology=ontology
        ))

    def addEduct(
        self,
        species_id: str,
        stoichiometry: PositiveFloat,
        is_constant: bool,
        enzmldoc,
        ontology: Enum = SBOTerm.SUBSTRATE
    ) -> None:
        """
        Adds element to EnzymeReaction object. Replicates as well
        as initial concentrations are optional.

        Args:
            species_id: str (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            is_constant:  (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs

        Raises:
            SpeciesNotFoundError: If Reactant/Protein hasnt been defined yet
        """

        self.__addElement(
            species_id=species_id,
            stoichiometry=stoichiometry,
            is_constant=is_constant,
            element_list=self.educts,
            ontology=ontology,
            enzmldoc=enzmldoc
        )

    def addProduct(
        self,
        species_id: str,
        stoichiometry: PositiveFloat,
        is_constant: bool,
        enzmldoc,
        ontology: Enum = SBOTerm.PRODUCT
    ) -> None:
        """
        Adds element to EnzymeReaction object. Replicates as well
        as initial concentrations are optional.

        Args:
            species_id: str (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            is_constant:  (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs

        Raises:
            SpeciesNotFoundError: If Reactant/Protein hasnt been defined yet
        """

        self.__addElement(
            species_id=species_id,
            stoichiometry=stoichiometry,
            is_constant=is_constant,
            element_list=self.products,
            ontology=ontology,
            enzmldoc=enzmldoc
        )

    def addModifier(
        self,
        species_id: str,
        stoichiometry: PositiveFloat,
        is_constant: bool,
        enzmldoc,
        ontology: Enum = SBOTerm.CATALYST
    ) -> None:
        """
        Adds element to EnzymeReaction object. Replicates as well
        as initial concentrations are optional.

        Args:
            species_id: str (string): Reactant/Protein ID - Needs to be pre-defined!
            stoichiometry (float): Stoichiometric coefficient
            is_constant:  (bool): Whether constant or not
            enzmldoc (EnzymeMLDocument): Checks and adds IDs

        Raises:
            SpeciesNotFoundError: If Reactant/Protein hasnt been defined yet
        """

        self.__addElement(
            species_id=species_id,
            stoichiometry=stoichiometry,
            is_constant=is_constant,
            element_list=self.modifiers,
            ontology=ontology,
            enzmldoc=enzmldoc
        )

    @deprecated_getter("temperature")
    def getTemperature(self) -> float:
        return self.temperature

    @deprecated_getter("temperature_unit")
    def getTempunit(self) -> str:
        return self.temperature_unit

    @deprecated_getter("ph")
    def getPh(self) -> PositiveFloat:
        return self.ph

    @deprecated_getter("name instead")
    def getName(self) -> str:
        return self.name

    @deprecated_getter("reveserible")
    def getReversible(self) -> bool:
        return self.reversible

    @deprecated_getter("id")
    def getId(self) -> Optional[str]:
        return self.id

    @deprecated_getter("meta_id")
    def getMetaid(self) -> Optional[str]:
        return self.meta_id

    @deprecated_getter("model")
    def getModel(self) -> Optional[KineticModel]:
        return self.model

    @deprecated_getter("educts")
    def getEducts(self):
        return self.educts

    @deprecated_getter("products")
    def getProducts(self):
        return self.products

    @deprecated_getter("modifier")
    def getModifiers(self):
        return self.modifiers
