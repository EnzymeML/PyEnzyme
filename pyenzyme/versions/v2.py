"""
This file contains Pydantic model definitions for data validation.

Pydantic is a data validation library that uses Python type annotations.
It allows you to define data models with type hints that are validated
at runtime while providing static type checking.

Usage example:
```python
from my_model import MyModel

# Validates data at runtime
my_model = MyModel(name="John", age=30)

# Type-safe - my_model has correct type hints
print(my_model.name)

# Will raise error if validation fails
try:
    MyModel(name="", age=30)
except ValidationError as e:
    print(e)
```

For more information see:
https://docs.pydantic.dev/

WARNING: This is an auto-generated file.
Do not edit directly - any changes will be overwritten.
"""


## This is a generated file. Do not modify it manually!

from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Generic, TypeVar
from enum import Enum
from uuid import uuid4
from mdmodels.units.annotation import UnitDefinitionAnnot

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
        validate_assignment=True,
    )  # type: ignore

    name: str = Field(
        default=...,
        description="""Title of the EnzymeML Document.""",
    )
    version: str = Field(
        default="2",
        description="""The version of the EnzymeML Document.""",
    )
    description: Optional[str] = Field(
        default=None,
        description="""Description of the EnzymeML Document.""",
    )
    created: Optional[str] = Field(
        default=None,
        description="""Date the EnzymeML Document was created.""",
    )
    modified: Optional[str] = Field(
        default=None,
        description="""Date the EnzymeML Document was modified.""",
    )
    creators: list[Creator] = Field(
        default_factory=list,
        description="""Contains descriptions of all authors that are part
        of the experiment.""",
    )
    vessels: list[Vessel] = Field(
        default_factory=list,
        description="""Contains descriptions of all vessels that are part
        of the experiment.""",
    )
    proteins: list[Protein] = Field(
        default_factory=list,
        description="""Contains descriptions of all proteins that
        are part of the experiment that may be
        referenced in reactions, measurements,
        and equations.""",
    )
    complexes: list[Complex] = Field(
        default_factory=list,
        description="""Contains descriptions of all complexes that
        are part of the experiment that may be
        referenced in reactions, measurements,
        and equations.""",
    )
    small_molecules: list[SmallMolecule] = Field(
        default_factory=list,
        description="""Contains descriptions of all reactants that
        are part of the experiment that may be
        referenced in reactions, measurements,
        and equations.""",
    )
    reactions: list[Reaction] = Field(
        default_factory=list,
        description="""Contains descriptions of all reactions that are
        part of the experiment.""",
    )
    measurements: list[Measurement] = Field(
        default_factory=list,
        description="""Contains descriptions of all measurements that are
        part of the experiment.""",
    )
    equations: list[Equation] = Field(
        default_factory=list,
        description="""Contains descriptions of all equations that are
        part of the experiment.""",
    )
    parameters: list[Parameter] = Field(
        default_factory=list,
        description="""Contains descriptions of all parameters that are
        part of the experiment and may be used
        in equations.""",
    )
    references: list[str] = Field(
        default_factory=list,
        description="""Contains references to publications, databases,
        and arbitrary links to the web.""",
    )

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
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
            "name": "schema:title",
            "created": "schema:dateCreated",
            "modified": "schema:dateModified",
            "creators": "schema:creator",
            "references": {
                "@id": "schema:citation",
                "@type": "@id",
            },
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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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
        unit: UnitDefinitionAnnot,
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
        constant: bool = True,
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
        name: str,
        constant: bool = False,
        vessel_id: Optional[str] = None,
        participants: list[str] = [],
        **kwargs,
    ):
        params = {
            "id": id,
            "name": name,
            "constant": constant,
            "vessel_id": vessel_id,
            "participants": participants,
        }

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
        inchi: Optional[str] = None,
        inchikey: Optional[str] = None,
        synonymous_names: list[str] = [],
        references: list[str] = [],
        **kwargs,
    ):
        params = {
            "id": id,
            "name": name,
            "constant": constant,
            "vessel_id": vessel_id,
            "canonical_smiles": canonical_smiles,
            "inchi": inchi,
            "inchikey": inchikey,
            "synonymous_names": synonymous_names,
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
        reactants: list[ReactionElement] = [],
        products: list[ReactionElement] = [],
        modifiers: list[ModifierElement] = [],
        **kwargs,
    ):
        params = {
            "id": id,
            "name": name,
            "reversible": reversible,
            "kinetic_law": kinetic_law,
            "reactants": reactants,
            "products": products,
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
        species_data: list[MeasurementData] = [],
        group_id: Optional[str] = None,
        ph: Optional[float] = None,
        temperature: Optional[float] = None,
        temperature_unit: Optional[UnitDefinitionAnnot] = None,
        **kwargs,
    ):
        params = {
            "id": id,
            "name": name,
            "species_data": species_data,
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
        species_id: str,
        equation: str,
        equation_type: EquationType,
        variables: list[Variable] = [],
        **kwargs,
    ):
        params = {
            "species_id": species_id,
            "equation": equation,
            "equation_type": equation_type,
            "variables": variables,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.equations.append(Equation(**params))

        return self.equations[-1]

    def add_to_parameters(
        self,
        id: str,
        name: str,
        symbol: str,
        value: Optional[float] = None,
        unit: Optional[UnitDefinitionAnnot] = None,
        initial_value: Optional[float] = None,
        upper_bound: Optional[float] = None,
        lower_bound: Optional[float] = None,
        fit: Optional[bool] = True,
        stderr: Optional[float] = None,
        constant: Optional[bool] = True,
        **kwargs,
    ):
        params = {
            "id": id,
            "name": name,
            "symbol": symbol,
            "value": value,
            "unit": unit,
            "initial_value": initial_value,
            "upper_bound": upper_bound,
            "lower_bound": lower_bound,
            "fit": fit,
            "stderr": stderr,
            "constant": constant,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.parameters.append(Parameter(**params))

        return self.parameters[-1]


class Creator(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assignment=True,
    )  # type: ignore

    given_name: str = Field(
        default=...,
        description="""Given name of the author or contributor.""",
    )
    family_name: str = Field(
        default=...,
        description="""Family name of the author or contributor.""",
    )
    mail: str = Field(
        default=...,
        description="""Email address of the author or contributor.""",
    )

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
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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
        validate_assignment=True,
    )  # type: ignore

    id: str = Field(
        default=...,
        description="""Unique identifier of the vessel.""",
    )
    name: str = Field(
        default=...,
        description="""Name of the used vessel.""",
    )
    volume: float = Field(
        default=...,
        description="""Volumetric value of the vessel.""",
    )
    unit: UnitDefinitionAnnot = Field(
        default=...,
        description="""Volumetric unit of the vessel.""",
    )
    constant: bool = Field(
        default=True,
        description="""Whether the volume of the vessel is constant or
        not. Default is True.""",
    )

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
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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
        validate_assignment=True,
    )  # type: ignore

    id: str = Field(
        default=...,
        description="""Identifier of the protein, such as a UniProt ID,
        or a custom identifier.""",
    )
    name: str = Field(
        default=...,
        description="""Name of the protein.""",
    )
    constant: bool = Field(
        default=True,
        description="""Whether the concentration of the protein is
        constant through the experiment or not.
        Default is True.""",
    )
    sequence: Optional[str] = Field(
        default=None,
        description="""Amino acid sequence of the protein""",
    )
    vessel_id: Optional[str] = Field(
        default=None,
        description="""Identifier of the vessel this protein has been
        applied to.""",
    )
    ecnumber: Optional[str] = Field(
        default=None,
        description="""EC number of the protein.""",
    )
    organism: Optional[str] = Field(
        default=None,
        description="""Expression host organism of the protein.""",
    )
    organism_tax_id: Optional[str] = Field(
        default=None,
        description="""Taxonomy identifier of the expression host.""",
    )
    references: list[str] = Field(
        default_factory=list,
        description="""List of references to publications, database
        entries, etc. that describe or reference
        the protein.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:Protein/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: ["enzml:Protein", "OBO:PR_000000001"],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
            "id": {
                "@id": "schema:identifier",
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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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
        validate_assignment=True,
    )  # type: ignore

    id: str = Field(
        default=...,
        description="""Unique identifier of the complex.""",
    )
    name: str = Field(
        default=...,
        description="""Name of the complex.""",
    )
    constant: bool = Field(
        default=False,
        description="""Whether the concentration of the complex is
        constant through the experiment or not.
        Default is False.""",
    )
    vessel_id: Optional[str] = Field(
        default=None,
        description="""Unique identifier of the vessel this complex has
        been used in.""",
    )
    participants: list[str] = Field(
        default_factory=list,
        description="""Array of IDs the complex contains""",
    )

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
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
            "id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
            "name": "schema:name",
            "vessel_id": {
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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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
        validate_assignment=True,
    )  # type: ignore

    id: str = Field(
        default=...,
        description="""Identifier of the small molecule, such as
        a Pubchem ID, ChEBI ID, or a custom
        identifier.""",
    )
    name: str = Field(
        default=...,
        description="""Name of the small molecule.""",
    )
    constant: bool = Field(
        default=False,
        description="""Whether the concentration of the small molecule
        is constant through the experiment or not.
        Default is False.""",
    )
    vessel_id: Optional[str] = Field(
        default=None,
        description="""Identifier of the vessel this small molecule has
        been used in.""",
    )
    canonical_smiles: Optional[str] = Field(
        default=None,
        description="""Canonical Simplified Molecular-Input Line-Entry
        System (SMILES) encoding of the small
        molecule.""",
    )
    inchi: Optional[str] = Field(
        default=None,
        description="""International Chemical Identifier (InChI) encoding
        of the small molecule.""",
    )
    inchikey: Optional[str] = Field(
        default=None,
        description="""Hashed International Chemical Identifier
        (InChIKey) encoding of the small molecule.""",
    )
    synonymous_names: list[str] = Field(
        default_factory=list,
        description="""List of synonymous names for the small molecule.""",
    )
    references: list[str] = Field(
        default_factory=list,
        description="""List of references to publications, database
        entries, etc. that describe or reference
        the small molecule.""",
    )

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
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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
        validate_assignment=True,
    )  # type: ignore

    id: str = Field(
        default=...,
        description="""Unique identifier of the reaction.""",
    )
    name: str = Field(
        default=...,
        description="""Name of the reaction.""",
    )
    reversible: bool = Field(
        default=False,
        description="""Whether the reaction is reversible or
        irreversible. Default is False.""",
    )
    kinetic_law: Optional[Equation] = Field(
        default=None,
        description="""Mathematical expression of the reaction.""",
    )
    reactants: list[ReactionElement] = Field(
        default_factory=list,
        description="""List of reactants that are part of the reaction.""",
    )
    products: list[ReactionElement] = Field(
        default_factory=list,
        description="""List of products that are part of the reaction.""",
    )
    modifiers: list[ModifierElement] = Field(
        default_factory=list,
        description="""List of reaction elements that are not part of the
        reaction but influence it.""",
    )

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
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
            "id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
        },
    )

    def filter_reactants(self, **kwargs) -> list[ReactionElement]:
        """Filters the reactants attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[ReactionElement]: The filtered list of ReactionElement objects
        """

        return FilterWrapper[ReactionElement](self.reactants, **kwargs).filter()

    def filter_products(self, **kwargs) -> list[ReactionElement]:
        """Filters the products attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[ReactionElement]: The filtered list of ReactionElement objects
        """

        return FilterWrapper[ReactionElement](self.products, **kwargs).filter()

    def filter_modifiers(self, **kwargs) -> list[ModifierElement]:
        """Filters the modifiers attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[ModifierElement]: The filtered list of ModifierElement objects
        """

        return FilterWrapper[ModifierElement](self.modifiers, **kwargs).filter()

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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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

    def add_to_reactants(
        self,
        species_id: str,
        stoichiometry: float = 1,
        **kwargs,
    ):
        params = {"species_id": species_id, "stoichiometry": stoichiometry}

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.reactants.append(ReactionElement(**params))

        return self.reactants[-1]

    def add_to_products(
        self,
        species_id: str,
        stoichiometry: float = 1,
        **kwargs,
    ):
        params = {"species_id": species_id, "stoichiometry": stoichiometry}

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.products.append(ReactionElement(**params))

        return self.products[-1]

    def add_to_modifiers(
        self,
        species_id: str,
        role: ModifierRole,
        **kwargs,
    ):
        params = {"species_id": species_id, "role": role}

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.modifiers.append(ModifierElement(**params))

        return self.modifiers[-1]


class ReactionElement(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assignment=True,
    )  # type: ignore

    species_id: str = Field(
        default=...,
        description="""Internal identifier to either a protein or
        reactant defined in the EnzymeML Document.""",
    )
    stoichiometry: float = Field(
        default=1,
        description="""Float number representing the associated
        stoichiometry.""",
    )

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
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
            "species_id": {
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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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


class ModifierElement(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assignment=True,
    )  # type: ignore

    species_id: str = Field(
        default=...,
        description="""Internal identifier to either a protein or
        reactant defined in the EnzymeML Document.""",
    )
    role: ModifierRole = Field(
        default=...,
        description="""Role of the modifier in the reaction.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:ModifierElement/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:ModifierElement",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
            "species_id": {
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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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
        validate_assignment=True,
    )  # type: ignore

    species_id: str = Field(
        default=...,
        description="""Identifier of a defined species (SmallMolecule,
        Protein, Complex). Represents the left
        hand side of the equation.""",
    )
    equation: str = Field(
        default=...,
        description="""Mathematical expression of the equation.
        Represents the right hand side of the
        equation.""",
    )
    equation_type: EquationType = Field(
        default=...,
        description="""Type of the equation.""",
    )
    variables: list[Variable] = Field(
        default_factory=list,
        description="""List of variables that are part of the equation""",
    )

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
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
            "species_id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
        },
    )

    def filter_variables(self, **kwargs) -> list[Variable]:
        """Filters the variables attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[Variable]: The filtered list of Variable objects
        """

        return FilterWrapper[Variable](self.variables, **kwargs).filter()

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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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
        symbol: str,
        **kwargs,
    ):
        params = {"id": id, "name": name, "symbol": symbol}

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.variables.append(Variable(**params))

        return self.variables[-1]


class Variable(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assignment=True,
    )  # type: ignore

    id: str = Field(
        default=...,
        description="""Identifier of the variable.""",
    )
    name: str = Field(
        default=...,
        description="""Name of the variable.""",
    )
    symbol: str = Field(
        default=...,
        description="""Equation symbol of the variable.""",
    )

    # JSON-LD fields
    ld_id: str = Field(
        serialization_alias="@id",
        default_factory=lambda: "enzml:Variable/" + str(uuid4()),
    )
    ld_type: list[str] = Field(
        serialization_alias="@type",
        default_factory=lambda: [
            "enzml:Variable",
        ],
    )
    ld_context: dict[str, str | dict] = Field(
        serialization_alias="@context",
        default_factory=lambda: {
            "enzml": "http://www.enzymeml.org/v2/",
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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


class Parameter(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assignment=True,
    )  # type: ignore

    id: str = Field(
        default=...,
        description="""Identifier of the parameter.""",
    )
    name: str = Field(
        default=...,
        description="""Name of the parameter.""",
    )
    symbol: str = Field(
        default=...,
        description="""Equation symbol of the parameter.""",
    )
    value: Optional[float] = Field(
        default=None,
        description="""Numerical value of the estimated parameter.""",
    )
    unit: Optional[UnitDefinitionAnnot] = Field(
        default=None,
        description="""Unit of the estimated parameter.""",
    )
    initial_value: Optional[float] = Field(
        default=None,
        description="""Initial value that was used for the parameter
        estimation.""",
    )
    upper_bound: Optional[float] = Field(
        default=None,
        description="""Upper bound for the parameter value that was used
        for the parameter estimation""",
    )
    lower_bound: Optional[float] = Field(
        default=None,
        description="""Lower bound for the parameter value that was used
        for the parameter estimation""",
    )
    fit: Optional[bool] = Field(
        default=True,
        description="""Whether this parameter should be varied or not in
        the context of an optimization.""",
    )
    stderr: Optional[float] = Field(
        default=None,
        description="""Standard error of the estimated parameter.""",
    )
    constant: Optional[bool] = Field(
        default=True,
        description="""Specifies if this parameter is constant. Default
        is True.""",
    )

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
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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
        validate_assignment=True,
    )  # type: ignore

    id: str = Field(
        default=...,
        description="""Unique identifier of the measurement.""",
    )
    name: str = Field(
        default=...,
        description="""Name of the measurement""",
    )
    species_data: list[MeasurementData] = Field(
        default_factory=list,
        description="""Measurement data of all species that were part
        of the measurement. A species refers to a
        Protein, Complex, or SmallMolecule.""",
    )
    group_id: Optional[str] = Field(
        default=None,
        description="""User-defined group ID to signal relationships
        between measurements.""",
    )
    ph: Optional[float] = Field(
        default=None,
        description="""pH value of the measurement.""",
    )
    temperature: Optional[float] = Field(
        default=None,
        description="""Temperature of the measurement.""",
    )
    temperature_unit: Optional[UnitDefinitionAnnot] = Field(
        default=None,
        description="""Unit of the temperature of the measurement.""",
    )

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
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
            "id": {
                "@id": "schema:identifier",
                "@type": "@id",
            },
            "group_id": {
                "@type": "@id",
            },
        },
    )

    def filter_species_data(self, **kwargs) -> list[MeasurementData]:
        """Filters the species_data attribute based on the given kwargs

        Args:
            **kwargs: The attributes to filter by.

        Returns:
            list[MeasurementData]: The filtered list of MeasurementData objects
        """

        return FilterWrapper[MeasurementData](self.species_data, **kwargs).filter()

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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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

    def add_to_species_data(
        self,
        species_id: str,
        prepared: Optional[float] = None,
        initial: Optional[float] = None,
        data_unit: Optional[UnitDefinitionAnnot] = None,
        data: list[float] = [],
        time: list[float] = [],
        time_unit: Optional[UnitDefinitionAnnot] = None,
        data_type: Optional[DataTypes] = None,
        is_simulated: Optional[bool] = False,
        **kwargs,
    ):
        params = {
            "species_id": species_id,
            "prepared": prepared,
            "initial": initial,
            "data_unit": data_unit,
            "data": data,
            "time": time,
            "time_unit": time_unit,
            "data_type": data_type,
            "is_simulated": is_simulated,
        }

        if "id" in kwargs:
            params["id"] = kwargs["id"]

        self.species_data.append(MeasurementData(**params))

        return self.species_data[-1]


class MeasurementData(BaseModel):
    model_config: ConfigDict = ConfigDict(  # type: ignore
        validate_assignment=True,
    )  # type: ignore

    species_id: str = Field(
        default=...,
        description="""The identifier for the described reactant.""",
    )
    prepared: Optional[float] = Field(
        default=None,
        description="""Amount of the the species before starting the
        measurement. This field can be used
        for specifying the prepared amount
        of a species in the reaction mix. Not
        to be confused with , specifying the
        concentration of a species at the first
        data point from the array.""",
    )
    initial: Optional[float] = Field(
        default=None,
        description="""Initial amount of the measurement data. This must
        be the same as the first data point in
        the array.""",
    )
    data_unit: Optional[UnitDefinitionAnnot] = Field(
        default=None,
        description="""SI unit of the data that was measured.""",
    )
    data: list[float] = Field(
        default_factory=list,
        description="""Data that was measured.""",
    )
    time: list[float] = Field(
        default_factory=list,
        description="""Corresponding time points of the .""",
    )
    time_unit: Optional[UnitDefinitionAnnot] = Field(
        default=None,
        description="""Unit of the time points of the .""",
    )
    data_type: Optional[DataTypes] = Field(
        default=None,
        description="""Type of data that was measured (e.g.
        concentration, absorbance, etc.)""",
    )
    is_simulated: Optional[bool] = Field(
        default=False,
        description="""Whether or not the data has been generated by
        simulation. Default is False.""",
    )

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
            "OBO": "http://purl.obolibrary.org/obo/",
            "schema": "https://schema.org/",
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

        assert attr in self.model_fields, (
            f"Attribute {attr} not found in {self.__class__.__name__}"
        )

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


class ModifierRole(Enum):
    ACTIVATOR = "activator"
    ADDITIVE = "additive"
    BIOCATALYST = "biocatalyst"
    BUFFER = "buffer"
    CATALYST = "catalyst"
    INHIBITOR = "inhibitor"
    SOLVENT = "solvent"


class EquationType(Enum):
    ASSIGNMENT = "assignment"
    INITIAL_ASSIGNMENT = "initialAssignment"
    ODE = "ode"
    RATE_LAW = "rateLaw"


class DataTypes(Enum):
    ABSORBANCE = "absorbance"
    AMOUNT = "amount"
    CONCENTRATION = "concentration"
    CONVERSION = "conversion"
    FLUORESCENCE = "fluorescence"
    PEAK_AREA = "peakarea"
    TRANSMITTANCE = "transmittance"
    TURNOVER = "turnover"
    YIELD = "yield"
