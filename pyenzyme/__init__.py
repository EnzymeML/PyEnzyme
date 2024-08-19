from __future__ import annotations

import json
from pathlib import Path

from rich import print

from .model import *  # noqa: F403
from .sbml import to_sbml, read_sbml  # noqa: F401
from .tabular import to_pandas, read_csv, read_excel  # noqa: F401

__all__ = [
    "read_enzymeml",
    "write_enzymeml",
    "to_sbml",
    "to_pandas",
]


def read_enzymeml(cls, path: str) -> EnzymeMLDocument:  # noqa: F405
    with open(path) as f:
        return cls.model_validate_json(f.read())  # noqa: F405


def write_enzymeml(
    self: EnzymeMLDocument,  # noqa: F405
    path: Path | str | None = None,  # noqa: F405
):  # noqa: F405
    data = json.loads(self.model_dump_json(exclude_none=True, by_alias=True))
    data = json.dumps(sort_by_ld(data), indent=2)

    if path is None:
        return data
    elif isinstance(path, str):
        path = Path(path)

    if path.is_dir():
        path = path / "experiment.json"

    with open(path, "w") as f:
        f.write(data)

    print(f"\n  EnzymeML document written to [green][bold]{path}[/bold][/green]\n")


# Add these methods to the EnzymeMLDocument class
EnzymeMLDocument.read = classmethod(read_enzymeml)  # noqa: F405
EnzymeMLDocument.write = write_enzymeml  # noqa: F405
EnzymeMLDocument.from_sbml = classmethod(read_sbml)  # noqa: F405
EnzymeMLDocument.to_sbml = to_sbml  # noqa: F405


def sort_by_ld(d: dict) -> dict:
    keys = sorted(d.keys(), key=_pattern)
    data = {}

    for key in keys:
        value = d[key]

        if isinstance(value, dict):
            data[key] = sort_by_ld(value)
        elif isinstance(value, list) and all(isinstance(v, dict) for v in value):
            data[key] = [sort_by_ld(v) for v in value]
        else:
            data[key] = value

    return data


def _pattern(s: str):
    if s.startswith("@context"):
        return 0
    elif s.startswith("@id"):
        return 1
    elif s.startswith("@type"):
        return 2
    else:
        return 3
