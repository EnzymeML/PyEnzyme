from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
from pymetadata.omex import EntryFormat, ManifestEntry, Omex


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


def read_sbml_omex(path: Path) -> tuple[Path, Path | None]:
    """
    Read an OMEX archive and return the SBML and data file paths.

    Args:
        path (Path): The path to the OMEX archive.

    Returns:
        tuple[Path, Path | None]: The SBML file path and the data file path, if available.

    """

    omex = Omex.from_omex(path)

    # get first sbml entry in manifest
    sbml_entry = None
    for entry in omex.manifest.entries:
        if '/sbml' in entry.format:
            sbml_entry = entry.location
            if entry.master:
                break
    sbml_file = omex.get_path(sbml_entry)


    # we really need to get all of the data entries from the manifest
    # but for now just get the first one
    data_entry = None
    for entry in omex.manifest.entries:
        if '/csv' in entry.format or '/tsv' in entry.format or '/tab-separated-values' in entry.format:
            data_entry = entry.location
            break
    data = omex.get_path(data_entry)

    return sbml_file, data
