from __future__ import annotations

import enum
import tempfile
from pathlib import Path
from typing import TextIO

import pandas as pd
from pymetadata.omex import EntryFormat, ManifestEntry, Omex

SBML_URI = "http://identifiers.org/combine.specifications/sbml"


class FileURI(enum.Enum):
    """
    Enum representing supported file URIs for data files.

    Attributes:
        CSV (str): URI for CSV files.
        TSV (str): URI for TSV files.
    """

    CSV = "http://purl.org/NET/mediatypes/text/csv"
    TSV = "https://purl.org/NET/mediatypes/text/tab-separated-values"

    @classmethod
    def from_uri(cls, uri: str):
        """
        Returns the corresponding FileURI enum member for a given URI.

        Args:
            uri (str): The URI to match.

        Returns:
            FileURI: The corresponding FileURI enum member.

        Raises:
            ValueError: If the URI is not supported.
        """
        match uri:
            case cls.CSV.value:
                return cls.CSV
            case cls.TSV.value:
                return cls.TSV
            case _:
                raise ValueError(f"Unsupported file URI: {uri}")

    @classmethod
    def is_supported(cls, uri):
        """
        Checks if a given URI is supported.

        Args:
            uri (str): The URI to check.

        Returns:
            bool: True if the URI is supported, False otherwise.
        """
        return uri in [e.value for e in cls]

    def to_dataframe(self, path):
        """
        Converts the file at the given path to a pandas DataFrame based on the file format.

        Args:
            path (str): The path to the file.

        Returns:
            pd.DataFrame: The file content as a pandas DataFrame.

        Raises:
            ValueError: If the file format is not supported.
        """
        match self:
            case self.CSV:
                # Legacy format has no headers
                return pd.read_csv(path, header=None)
            case self.TSV:
                # V2 format has headers
                return pd.read_csv(path, sep="\t")
            case _:
                raise ValueError(f"Unsupported file format: {self}")


def create_sbml_omex(
    sbml_doc: str,
    data: pd.DataFrame | None,
    out: Path,
) -> None:
    """
    Create an OMEX archive with the given SBML and data files.

    Args:
        sbml_doc (str): The SBML document to include in the archive.
        data (pd.DataFrame | None): The data to include in the archive.
        out (Path): The path to save the OMEX archive.

    Returns:
        Omex: The created OMEX archive

    """

    with tempfile.TemporaryDirectory() as temp_dir:
        omex = Omex()

        sbml_path = f"{temp_dir}/model.xml"
        with open(sbml_path, "w") as f:
            f.write(sbml_doc)
            omex.add_entry(
                entry_path=Path(sbml_path),
                entry=ManifestEntry(
                    location="./model.xml",
                    format=EntryFormat.SBML,
                    master=True,
                ),
            )

        if data is not None:
            data_path = f"{temp_dir}/data.tsv"
            data.to_csv(data_path, sep="\t", index=False)
            omex.add_entry(
                entry_path=Path(data_path),
                entry=ManifestEntry(
                    location="./data.tsv",
                    format=EntryFormat.TSV,
                ),
            )

        omex.to_omex(out)


def read_sbml_omex(path: Path) -> tuple[TextIO, dict[str, pd.DataFrame]]:
    """
    Reads an OMEX archive and extracts the SBML document and associated data files.

    Args:
        path (Path): The path to the OMEX archive.

    Returns:
        tuple[str, dict[str, pd.DataFrame]]: A tuple containing the SBML document as a string and a dictionary
                                             where keys are file locations and values are dataframes of the data files.
    """
    omex = Omex.from_omex(path)

    try:
        master_file = next(part for part in omex.manifest.entries if part.master)
    except StopIteration:
        raise ValueError("No master file found in OMEX archive")

    assert master_file.format == SBML_URI, "Master file is not SBML"

    meas_data = dict()

    for entry in omex.manifest.entries:
        if not FileURI.is_supported(entry.format):
            continue

        file_uri = FileURI.from_uri(entry.format)
        df = file_uri.to_dataframe(omex.get_path(entry.location))

        meas_data[entry.location] = df

    return open(omex.get_path(master_file.location)), meas_data
