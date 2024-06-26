## This is a generated file. Do not modify it manually!

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Generic, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

# Filter Wrapper definition used to filter a list of objects
# based on their attributes
Cls = TypeVar("Cls")


class FilterWrapper(Generic[Cls]):
    """Wrapper class to filter a list of objects based on their attributes"""

    def __init__(self, collection: list[Cls], **kwargs):
        self.collection = collection
        self.kwargs = kwargs

    def filter(self) -> list[Cls]:
        for key, value in self.kwargs.items():
            self.collection = [
                item for item in self.collection if self._fetch_attr(key, item) == value
            ]
        return self.collection

    def _fetch_attr(self, name: str, item: Cls):
        try:
            return getattr(item, name)
        except AttributeError:
            raise AttributeError(f"{item} does not have attribute {name}")


# JSON-LD Helper Functions
def add_namespace(obj, prefix: str | None, iri: str | None):
    """Adds a namespace to the JSON-LD context

    Args:
        prefix (str): The prefix to add
        iri (str): The IRI to add
    """
    if prefix is None and iri is None:
        return
    elif prefix and iri is None:
        raise ValueError("If prefix is provided, iri must also be provided")
    elif iri and prefix is None:
        raise ValueError("If iri is provided, prefix must also be provided")

    obj.ld_context[prefix] = iri  # type: ignore


def validate_prefix(term: str | dict, prefix: str):
    """Validates that a term is prefixed with a given prefix

    Args:
        term (str): The term to validate
        prefix (str): The prefix to validate against

    Returns:
        bool: True if the term is prefixed with the prefix, False otherwise
    """

    if isinstance(term, dict) and not term["@id"].startswith(prefix + ":"):
        raise ValueError(f"Term {term} is not prefixed with {prefix}")
    elif isinstance(term, str) and not term.startswith(prefix + ":"):
        raise ValueError(f"Term {term} is not prefixed with {prefix}")


# Model Definitions


class EnzymeMLDocument(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    name: str
    references: list[str] = Field(default_factory=list)
    created: Optional[str] = Field(default=None)
    modified: Optional[str] = Field(default=None)
    creators: list[Creator] = Field(default_factory=list)
    vessels: list[Vessel] = Field(default_factory=list)
    proteins: list[Protein] = Field(default_factory=list)
    complexes: list[Complex] = Field(default_factory=list)
    small_molecules: list[SmallMolecule] = Field(default_factory=list)
    reactions: list[Reaction] = Field(default_factory=list)
    measurements: list[Measurement] = Field(default_factory=list)
    equations: list[Equation] = Field(default_factory=list)
    parameters: list[Parameter] = Field(default_factory=list)

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:EnzymeMLDocument/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:EnzymeMLDocument",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "name": "schema:title",
            "references": {
                "@id": "schema:citation",
                "@type": "@id",
            },
            "created": "schema:dateCreated",
            "modified": "schema:dateModified",
            "creators": "schema:creator",
        },
    )

    def filter_creators(self, **kwargs) -> list[Creator]:
        """Filters the creators attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Creator]: The filtered list of Creator objects
        """

        return FilterWrapper[Creator](self.creators, **kwargs).filter()

    def filter_vessels(self, **kwargs) -> list[Vessel]:
        """Filters the vessels attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Vessel]: The filtered list of Vessel objects
        """

        return FilterWrapper[Vessel](self.vessels, **kwargs).filter()

    def filter_proteins(self, **kwargs) -> list[Protein]:
        """Filters the proteins attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Protein]: The filtered list of Protein objects
        """

        return FilterWrapper[Protein](self.proteins, **kwargs).filter()

    def filter_complexes(self, **kwargs) -> list[Complex]:
        """Filters the complexes attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Complex]: The filtered list of Complex objects
        """

        return FilterWrapper[Complex](self.complexes, **kwargs).filter()

    def filter_small_molecules(self, **kwargs) -> list[SmallMolecule]:
        """Filters the small_molecules attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[SmallMolecule]: The filtered list of SmallMolecule objects
        """

        return FilterWrapper[SmallMolecule](self.small_molecules, **kwargs).filter()

    def filter_reactions(self, **kwargs) -> list[Reaction]:
        """Filters the reactions attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Reaction]: The filtered list of Reaction objects
        """

        return FilterWrapper[Reaction](self.reactions, **kwargs).filter()

    def filter_measurements(self, **kwargs) -> list[Measurement]:
        """Filters the measurements attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Measurement]: The filtered list of Measurement objects
        """

        return FilterWrapper[Measurement](self.measurements, **kwargs).filter()

    def filter_equations(self, **kwargs) -> list[Equation]:
        """Filters the equations attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Equation]: The filtered list of Equation objects
        """

        return FilterWrapper[Equation](self.equations, **kwargs).filter()

    def filter_parameters(self, **kwargs) -> list[Parameter]:
        """Filters the parameters attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Parameter]: The filtered list of Parameter objects
        """

        return FilterWrapper[Parameter](self.parameters, **kwargs).filter()

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)

    def add_to_creators(
        self,
        given_name: str,
        family_name: str,
        mail: str,
        **kwargs,
    ):
        params = {"given_name": given_name, "family_name": family_name, "mail": mail}

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.creators.append(Creator(**params))

        return self.creators[-1]

    def add_to_vessels(
        self,
        id: str,
        name: str,
        volume: float,
        unit: UnitDefinition,
        constant: bool = True,
        **kwargs,
    ):
        params = {
            "id": id,
            "name": name,
            "volume": volume,
            "unit": unit,
            "constant": constant,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.vessels.append(Vessel(**params))

        return self.vessels[-1]

    def add_to_proteins(
        self,
        id: str,
        name: str,
        constant: bool = False,
        sequence: Optional[str] = None,
        vessel_id: Optional[str] = None,
        ecnumber: Optional[str] = None,
        organism: Optional[str] = None,
        organism_tax_id: Optional[str] = None,
        references: list[str] = [],
        **kwargs,
    ):
        params = {
            "id": id,
            "name": name,
            "constant": constant,
            "sequence": sequence,
            "vessel_id": vessel_id,
            "ecnumber": ecnumber,
            "organism": organism,
            "organism_tax_id": organism_tax_id,
            "references": references,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.proteins.append(Protein(**params))

        return self.proteins[-1]

    def add_to_complexes(
        self,
        id: str,
        participants: list[str] = [],
        **kwargs,
    ):
        params = {"id": id, "participants": participants}

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.complexes.append(Complex(**params))

        return self.complexes[-1]

    def add_to_small_molecules(
        self,
        id: str,
        name: str,
        constant: bool = False,
        vessel_id: Optional[str] = None,
        canonical_smiles: Optional[str] = None,
        inchikey: Optional[str] = None,
        references: list[str] = [],
        **kwargs,
    ):
        params = {
            "id": id,
            "name": name,
            "constant": constant,
            "vessel_id": vessel_id,
            "canonical_smiles": canonical_smiles,
            "inchikey": inchikey,
            "references": references,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.small_molecules.append(SmallMolecule(**params))

        return self.small_molecules[-1]

    def add_to_reactions(
        self,
        id: str,
        name: str,
        reversible: bool = False,
        kinetic_law: Optional[Equation] = None,
        species: list[ReactionElement] = [],
        modifiers: list[str] = [],
        **kwargs,
    ):
        params = {
            "id": id,
            "name": name,
            "reversible": reversible,
            "kinetic_law": kinetic_law,
            "species": species,
            "modifiers": modifiers,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.reactions.append(Reaction(**params))

        return self.reactions[-1]

    def add_to_measurements(
        self,
        id: str,
        name: str,
        species: list[MeasurementData] = [],
        group_id: Optional[str] = None,
        ph: Optional[float] = None,
        temperature: Optional[float] = None,
        temperature_unit: Optional[UnitDefinition] = None,
        **kwargs,
    ):
        params = {
            "id": id,
            "name": name,
            "species": species,
            "group_id": group_id,
            "ph": ph,
            "temperature": temperature,
            "temperature_unit": temperature_unit,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.measurements.append(Measurement(**params))

        return self.measurements[-1]

    def add_to_equations(
        self,
        unit: UnitDefinition,
        equation_type: EquationType,
        equation: str,
        species_id: Optional[str] = None,
        variables: list[EqVariable] = [],
        parameters: list[EqParameter] = [],
        **kwargs,
    ):
        params = {
            "unit": unit,
            "equation_type": equation_type,
            "equation": equation,
            "species_id": species_id,
            "variables": variables,
            "parameters": parameters,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.equations.append(Equation(**params))

        return self.equations[-1]

    def add_to_parameters(
        self,
        id: str,
        name: str,
        value: Optional[float] = None,
        unit: Optional[UnitDefinition] = None,
        initial_value: Optional[float] = None,
        upper: Optional[float] = None,
        lower: Optional[float] = None,
        stderr: Optional[float] = None,
        constant: Optional[bool] = True,
        **kwargs,
    ):
        params = {
            "id": id,
            "name": name,
            "value": value,
            "unit": unit,
            "initial_value": initial_value,
            "upper": upper,
            "lower": lower,
            "stderr": stderr,
            "constant": constant,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.parameters.append(Parameter(**params))

        return self.parameters[-1]


class Creator(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    given_name: str
    family_name: str
    mail: str

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:Creator/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: ["enzml:Creator", "schema:person"],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "given_name": "schema:givenName",
            "family_name": "schema:familyName",
            "mail": "schema:email",
        },
    )

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Vessel(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    id: str
    name: str
    volume: float
    unit: UnitDefinition
    constant: bool = True

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:Vessel/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: ["enzml:Vessel", "OBO:OBI_0400081"],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
            "name": "schema:name",
            "volume": "OBO:OBI_0002139",
        },
    )

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Protein(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    id: str
    name: str
    constant: bool = False
    sequence: Optional[str] = Field(default=None)
    vessel_id: Optional[str] = Field(default=None)
    ecnumber: Optional[str] = Field(default=None)
    organism: Optional[str] = Field(default=None)
    organism_tax_id: Optional[str] = Field(default=None)
    references: list[str] = Field(default_factory=list)

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:Protein/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: ["enzml:Protein", "schema:Protein"],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "id": {
                "@type": "@id",
            },
            "name": "schema:name",
            "sequence": "OBO:GSSO_007262",
            "vessel_id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
            "organism": "OBO:OBI_0100026",
            "organism_tax_id": {
                "@type": "@id",
            },
            "references": {
                "@id": "schema:citation",
                "@type": "@id",
            },
        },
    )

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Complex(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    id: str
    participants: list[str] = Field(default_factory=list)

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:Complex/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:Complex",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
            "participants": {
                "@type": "@id",
            },
        },
    )

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class SmallMolecule(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    id: str
    name: str
    constant: bool = False
    vessel_id: Optional[str] = Field(default=None)
    canonical_smiles: Optional[str] = Field(default=None)
    inchikey: Optional[str] = Field(default=None)
    references: list[str] = Field(default_factory=list)

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:SmallMolecule/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:SmallMolecule",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
            "name": "schema:name",
            "vessel_id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
            "references": {
                "@id": "schema:citation",
                "@type": "@id",
            },
        },
    )

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Reaction(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    id: str
    name: str
    reversible: bool = False
    kinetic_law: Optional[Equation] = Field(default=None)
    species: list[ReactionElement] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:Reaction/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:Reaction",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
            "modifiers": {
                "@type": "@id",
            },
        },
    )

    def filter_species(self, **kwargs) -> list[ReactionElement]:
        """Filters the species attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[ReactionElement]: The filtered list of ReactionElement objects
        """

        return FilterWrapper[ReactionElement](self.species, **kwargs).filter()

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)

    def add_to_species(
        self,
        species_id: str,
        stoichiometry: float,
        **kwargs,
    ):
        params = {"species_id": species_id, "stoichiometry": stoichiometry}

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.species.append(ReactionElement(**params))

        return self.species[-1]


class ReactionElement(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    species_id: str
    stoichiometry: float

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:ReactionElement/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:ReactionElement",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "species_id": {
                "@type": "@id",
            },
        },
    )

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Equation(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    unit: UnitDefinition
    equation_type: EquationType
    equation: str
    species_id: Optional[str] = Field(default=None)
    variables: list[EqVariable] = Field(default_factory=list)
    parameters: list[EqParameter] = Field(default_factory=list)

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:Equation/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:Equation",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "species_id": {
                "@type": "@id",
            },
        },
    )

    def filter_variables(self, **kwargs) -> list[EqVariable]:
        """Filters the variables attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[EqVariable]: The filtered list of EqVariable objects
        """

        return FilterWrapper[EqVariable](self.variables, **kwargs).filter()

    def filter_parameters(self, **kwargs) -> list[EqParameter]:
        """Filters the parameters attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[EqParameter]: The filtered list of EqParameter objects
        """

        return FilterWrapper[EqParameter](self.parameters, **kwargs).filter()

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)

    def add_to_variables(
        self,
        id: str,
        name: str,
        symbol: Optional[str] = None,
        **kwargs,
    ):
        params = {"id": id, "name": name, "symbol": symbol}

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.variables.append(EqVariable(**params))

        return self.variables[-1]

    def add_to_parameters(
        self,
        id: str,
        name: str,
        symbol: Optional[str] = None,
        value: Optional[float] = None,
        **kwargs,
    ):
        params = {"id": id, "name": name, "symbol": symbol, "value": value}

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.parameters.append(EqParameter(**params))

        return self.parameters[-1]


class Parameter(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    id: str
    name: str
    value: Optional[float] = Field(default=None)
    unit: Optional[UnitDefinition] = Field(default=None)
    initial_value: Optional[float] = Field(default=None)
    upper: Optional[float] = Field(default=None)
    lower: Optional[float] = Field(default=None)
    stderr: Optional[float] = Field(default=None)
    constant: bool = True

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:Parameter/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:Parameter",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
        },
    )

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class Measurement(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    id: str
    name: str
    species: list[MeasurementData] = Field(default_factory=list)
    group_id: Optional[str] = Field(default=None)
    ph: Optional[float] = Field(default=None)
    temperature: Optional[float] = Field(default=None)
    temperature_unit: Optional[UnitDefinition] = Field(default=None)

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:Measurement/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:Measurement",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
            "group_id": {
                "@type": "@id",
            },
        },
    )

    def filter_species(self, **kwargs) -> list[MeasurementData]:
        """Filters the species attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[MeasurementData]: The filtered list of MeasurementData objects
        """

        return FilterWrapper[MeasurementData](self.species, **kwargs).filter()

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)

    def add_to_species(
        self,
        species_id: str,
        init_conc: float,
        data_type: DataTypes,
        data_unit: UnitDefinition,
        time_unit: UnitDefinition,
        time: list[float] = [],
        data: list[float] = [],
        is_calculated: bool = False,
        **kwargs,
    ):
        params = {
            "species_id": species_id,
            "init_conc": init_conc,
            "data_type": data_type,
            "data_unit": data_unit,
            "time_unit": time_unit,
            "time": time,
            "data": data,
            "is_calculated": is_calculated,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.species.append(MeasurementData(**params))

        return self.species[-1]


class MeasurementData(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    species_id: str
    init_conc: float
    data_type: DataTypes
    data_unit: UnitDefinition
    time_unit: UnitDefinition
    time: list[float] = Field(default_factory=list)
    data: list[float] = Field(default_factory=list)
    is_calculated: bool = False

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:MeasurementData/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:MeasurementData",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "species_id": {
                "@type": "@id",
            },
        },
    )

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class UnitDefinition(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    base_units: list[BaseUnit] = Field(default_factory=list)

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:UnitDefinition/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:UnitDefinition",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
        },
    )

    def filter_base_units(self, **kwargs) -> list[BaseUnit]:
        """Filters the base_units attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[BaseUnit]: The filtered list of BaseUnit objects
        """

        return FilterWrapper[BaseUnit](self.base_units, **kwargs).filter()

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)

    def add_to_base_units(
        self,
        kind: UnitType,
        exponent: int,
        multiplier: Optional[float] = None,
        scale: Optional[float] = None,
        **kwargs,
    ):
        params = {
            "kind": kind,
            "exponent": exponent,
            "multiplier": multiplier,
            "scale": scale,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.base_units.append(BaseUnit(**params))

        return self.base_units[-1]


class BaseUnit(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    kind: UnitType
    exponent: int
    multiplier: Optional[float] = Field(default=None)
    scale: Optional[float] = Field(default=None)

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:BaseUnit/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:BaseUnit",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
        },
    )

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class EqVariable(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    id: str
    name: str
    symbol: Optional[str] = Field(default=None)

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:EqVariable/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:EqVariable",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "id": {
                "@type": "@id",
            },
        },
    )

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class EqParameter(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assigment=True,
    )  # type: ignore

    id: str
    name: str
    symbol: Optional[str] = Field(default=None)
    value: Optional[float] = Field(default=None)

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:EqParameter/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:EqParameter",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "schema": "https://schema.org/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "id": {
                "@type": "@id",
            },
        },
    )

    def set_attr_term(
        self,
        attr: str,
        term: str | dict,
        prefix: str | None = None,
        iri: str | None = None,
    ):
        """Sets the term for a given attribute in the JSON-LD object

        Example:
            # Using an IRI term
            >> obj.set_attr_term("name", "http://schema.org/givenName")

            # Using a prefix and term
            >> obj.set_attr_term("name", "schema:givenName", "schema", "http://schema.org")

            # Usinng a dictionary term
            >> obj.set_attr_term("name", {"@id": "http://schema.org/givenName", "@type": "@id"})

        Args:
            attr (str): The attribute to set the term for
            term (str | dict): The term to set for the attribute

        Raises:
            AssertionError: If the attribute is not found in the model
        """

        assert (
            attr in self.model_fields
        ), f"Attribute {attr} not found in {self.__class__.__name__}"

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_context[attr] = term

    def add_type_term(
        self, term: str, prefix: str | None = None, iri: str | None = None
    ):
        """Adds a term to the @type field of the JSON-LD object

        Example:
            # Using a term
            >> obj.add_type_term("https://schema.org/Person")

            # Using a prefixed term
            >> obj.add_type_term("schema:Person", "schema", "https://schema.org/Person")

        Args:
            term (str): The term to add to the @type field
            prefix (str, optional): The prefix to use for the term. Defaults to None.
            iri (str, optional): The IRI to use for the term prefix. Defaults to None.

        Raises:
            ValueError: If prefix is provided but iri is not
            ValueError: If iri is provided but prefix is not
        """

        if prefix:
            validate_prefix(term, prefix)

        add_namespace(self, prefix, iri)
        self.ld_type.append(term)


class DataTypes(Enum):
    ABSORPTION = "abs"
    BIOMASS = "biomass"
    CONCENTRATION = "conc"
    CONVERSION = "conversion"
    FEED = "feed"
    PEAK_AREA = "peak-area"


class EquationType(Enum):
    ASSIGNMENT = "assignment"
    INITIAL_ASSIGNMENT = "initialAssignment"
    ODE = "ode"
    RATE_LAW = "rateLaw"


class UnitType(Enum):
    AMPERE = "ampere"
    AVOGADRO = "avogadro"
    BECQUEREL = "becquerel"
    CANDELA = "candela"
    CELSIUS = "celsius"
    COULOMB = "coulomb"
    DIMENSIONLESS = "dimensionless"
    FARAD = "farad"
    GRAM = "gram"
    GRAY = "gray"
    HENRY = "henry"
    HERTZ = "hertz"
    ITEM = "item"
    JOULE = "joule"
    KATAL = "katal"
    KELVIN = "kelvin"
    KILOGRAM = "kilogram"
    LITRE = "litre"
    LUMEN = "lumen"
    LUX = "lux"
    METRE = "metre"
    MOLE = "mole"
    NEWTON = "newton"
    OHM = "ohm"
    PASCAL = "pascal"
    RADIAN = "radian"
    SECOND = "second"
    SIEMENS = "siemens"
    SIEVERT = "sievert"
    STERADIAN = "steradian"
    TESLA = "tesla"
    VOLT = "volt"
    WATT = "watt"
    WEBER = "weber"
