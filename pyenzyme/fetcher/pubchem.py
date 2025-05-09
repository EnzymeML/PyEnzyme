from typing import ClassVar, Optional
from pydantic import BaseModel, Field, field_validator
import requests

from pyenzyme.fetcher.chebi import process_id
from pyenzyme.versions import v2


class PCUrn(BaseModel):
    """
    Represents a PubChem URN (Uniform Resource Name) with a label and optional name.
    """

    label: str
    name: Optional[str] = Field(default=None)


class PCProp(BaseModel):
    """
    Represents a PubChem property with a value and URN.

    The value can be of different types (float, int, str, or None) and is extracted
    from one of the available fields in the PubChem JSON response.
    """

    value: float | int | str | None = Field(default=None)
    urn: PCUrn

    AVAILABLE_FIELDS: ClassVar[list[str]] = ["ival", "sval", "fval", "bval"]

    @field_validator("value", mode="before")
    def validate_value(cls, v):
        """
        Extracts the actual value from the PubChem property structure.

        PubChem properties can have different value types (ival, sval, fval, bval),
        and this validator extracts the appropriate value.

        Args:
            v: The raw value dictionary from PubChem

        Returns:
            The extracted value or None if no valid field is found
        """
        for field in cls.AVAILABLE_FIELDS:
            if field in v:
                return v[field]
        return None


class PCCompound(BaseModel):
    """
    Represents a PubChem compound with a list of properties.
    """

    props: list[PCProp]


class PubChemQuery(BaseModel):
    """
    Represents a PubChem query response containing a list of compounds.
    """

    pc_compounds: list[PCCompound] = Field(alias="PC_Compounds", default_factory=list)


class PubChemClient(BaseModel):
    """
    Client for interacting with the PubChem REST API.

    Provides methods to fetch compound data by CID and extract specific properties.
    """

    BASE_CID_URL: ClassVar[str] = (
        "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{0}/record/JSON"
    )

    @staticmethod
    def from_cid(cid: int) -> PubChemQuery:
        """
        Fetches compound data from PubChem by CID.

        Args:
            cid: The PubChem Compound ID

        Returns:
            A PubChemQuery object containing the compound data

        Raises:
            ValueError: If the PubChem API request fails
        """
        url = PubChemClient.BASE_CID_URL.format(cid)
        response = requests.get(url)

        if response.status_code != 200:
            raise ValueError(f"Failed to fetch PubChem data for CID {cid}")

        return PubChemQuery(**response.json())

    @staticmethod
    def extract_value(
        query: PCCompound,
        label: str,
        name: Optional[str] = None,
    ) -> float | int | str | None:
        """
        Extracts a specific property value from a PubChem compound.

        Args:
            query: The PubChem compound
            label: The property label to search for
            name: Optional property name to further filter the search

        Returns:
            The property value if found, or None otherwise
        """
        for prop in query.props:
            if name:
                if prop.urn.name == name and prop.urn.label == label:
                    return prop.value
            elif prop.urn.label == label:
                return prop.value
        return None

    @staticmethod
    def extract_by_preference(
        query: PCCompound, label: str, names: list[str]
    ) -> float | int | str | None:
        """
        Extracts a property value by trying a list of names in order of preference.

        Args:
            query: The PubChem compound
            label: The property label to search for
            names: A list of property names to try in order of preference

        Returns:
            The first non-None property value found, or None if none are found
        """
        for name in names:
            value = PubChemClient.extract_value(query, label, name)
            if value:
                return value
        return None


def fetch_pubchem(
    cid: str,
    smallmol_id: Optional[str] = None,
    vessel_id: Optional[str] = None,
) -> v2.SmallMolecule:
    """
    Fetches a compound from PubChem by CID and converts it to a SmallMolecule object.

    Args:
        cid: The PubChem Compound ID
        smallmol_id: Optional custom ID for the small molecule
        vessel_id: Optional vessel ID for the small molecule

    Returns:
        A SmallMolecule object with data from PubChem

    Raises:
        ValueError: If the PubChem API request fails or required data is missing
    """
    # Allow prefixing with 'CID:'
    if cid.lower().startswith("pubchem:"):
        cid = cid.split(":", 1)[-1]

    query = PubChemClient.from_cid(int(cid))
    pc_compound = query.pc_compounds[0]
    name = _extract_name(pc_compound, int(cid))

    if not smallmol_id:
        smallmol_id = process_id(name)

    smallmol = v2.SmallMolecule(
        id=smallmol_id,
        name=name,
        inchi=_extract_inchi(pc_compound),
        inchikey=_extract_inchikey(pc_compound),
        canonical_smiles=_extract_canonical_smiles(pc_compound),
        constant=False,
        vessel_id=vessel_id,
    )

    smallmol.add_type_term(
        term=f"pubchem:CID{cid}",
        prefix="pubchem",
        iri="http://rdf.ncbi.nlm.nih.gov/pubchem/compound/",
    )

    smallmol.ld_id = f"pubchem:CID{cid}"

    return smallmol


def _extract_name(query: PCCompound, cid: int) -> str:
    """
    Extracts the name of a compound from PubChem data.

    Tries different IUPAC name types in order of preference.

    Args:
        query: The PubChem compound
        cid: The PubChem Compound ID (used for error reporting)

    Returns:
        The compound name as a string

    Raises:
        ValueError: If no name is found
    """
    names = ["Preferred", "Systematic", "Allowed", "CAS-like Style", "Markup"]
    name = PubChemClient.extract_by_preference(
        query=query,
        label="IUPAC Name",
        names=names,
    )

    if not name:
        raise ValueError(f"No name found for CID {cid}")
    else:
        return str(name)


def _extract_inchi(query: PCCompound) -> str | None:
    """
    Extracts the InChI string from PubChem data.

    Args:
        query: The PubChem compound

    Returns:
        The InChI string or None if not found
    """
    inchi = PubChemClient.extract_value(query, "InChI")
    if not inchi:
        return None
    else:
        return str(inchi)


def _extract_inchikey(query: PCCompound) -> str | None:
    """
    Extracts the InChIKey from PubChem data.

    Args:
        query: The PubChem compound

    Returns:
        The InChIKey string or None if not found
    """
    inchikey = PubChemClient.extract_value(query, "InChIKey")
    if not inchikey:
        return None
    else:
        return str(inchikey)


def _extract_canonical_smiles(query: PCCompound) -> str | None:
    """
    Extracts the canonical SMILES string from PubChem data.

    Args:
        query: The PubChem compound

    Returns:
        The canonical SMILES string or None if not found
    """
    smiles = PubChemClient.extract_value(query, "SMILES")
    if not smiles:
        return None
    else:
        return str(smiles)
