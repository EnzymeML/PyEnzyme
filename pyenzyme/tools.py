import functools as ft
import importlib.resources as pkg_resources
from enum import Enum
import json

import toml

import pyenzyme as pe


def to_dict_wo_json_ld(enzmldoc: pe.EnzymeMLDocument):
    """Serialized to dict and strips JSON-LD fields from an EnzymeMLDocument.

    Please note, this function is intended for internal use only and should not be called directly.
    For developers, if you intend to write tests and check the contents of an EnzymeMLDocument,
    it is recommended to use this method instead of `model_dump()` to avoid JSON-LD fields,
    since these contain IDs that are not deterministic and may cause tests to fail.

    Args:
        enzmldoc (EnzymeMLDocument): The EnzymeMLDocument to strip JSON-LD fields from.

    Returns:
        dict: The EnzymeMLDocument with JSON-LD fields removed.
    """

    doc = json.loads(enzmldoc.model_dump_json())
    _recursive_key_removal(doc, "ld_id")
    _recursive_key_removal(doc, "ld_type")
    _recursive_key_removal(doc, "ld_context")

    return doc


def _recursive_key_removal(obj: dict | list, key: str):
    """
    Recursively removes all occurrences of a specified key from a dictionary or list of dictionaries.

    Args:
        obj (dict | list): The dictionary or list of dictionaries to process.
        key (str): The key to remove from the dictionary or dictionaries.

    Example:
        >>> data = {'a': 1, 'b': {'a': 2, 'c': 3}, 'd': [{'a': 4}, {'e': 5}]}
        >>> _recursive_key_removal(data, 'a')
        >>> print(data)
        {'b': {'c': 3}, 'd': [{'e': 5}]}
    """
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            if key == k:
                del obj[key]
            else:
                _recursive_key_removal(obj[k], key)
    elif isinstance(obj, list):
        # Sort the list to ensure that the order of elements is preserved
        obj.sort(key=lambda x: str(x))
        for entry in obj:
            _recursive_key_removal(entry, key)


def get_all_parameters(enzmldoc):
    """Extracts all parameters from an EnzymeMLDocument.

    Args:
        enzmldoc (EnzymeMLDocument): The EnzymeMLDocument to extract parameters from.

    Returns:
        list[Parameter]: A list of all parameters in the EnzymeMLDocument.
    """
    return find_unique(enzmldoc, target=pe.Parameter)


def read_static_file(path, filename: str):
    """Reads a static file from the specified library path.

    Args:
        path (Module): Import path of the library.
        filename (str): The name of the file to read.

    Returns:
        dict: The contents of the file as a dictionary.
    """

    source = pkg_resources.files(path).joinpath(filename)
    with pkg_resources.as_file(source) as file:
        return toml.load(file)


def find_unique(obj, target):
    """Composite function that extracts all instances of a specified target type from a given object.

    Args:
        obj (Any): The object from which to extract instances of the target type.
        target (type): The target type to extract from the object.

    Returns:
        list: A list of unique instances of the target type.
    """
    if _is_basetype(obj):
        return []

    return chain(obj, ft.partial(extract, target=target), unique)


def chain(obj, *funs):
    return ft.reduce(lambda x, f: f(x), funs, obj)


def unique(args):
    """Returns a list of unique elements from a given list.

    Args:
        args (list): The list of elements to extract unique elements from.

    Returns:
        list: A list of unique elements.
    """

    unique = []
    for arg in args:
        if arg not in unique:
            unique.append(arg)

    return unique


def extract(obj, target) -> list:
    """
    Recursively extracts all instances of a specified target type from a given object's attributes.

    This function traverses through the attributes of the given object and collects all instances
    of the specified target type. It handles nested objects and lists by performing a depth-first search.

    Args:
        obj (Any): The object from which to extract instances of the target type.
        target (type): The type of the instances to extract.

    Returns:
        list: A list of instances of the target type extracted from the object.

    Example:
    >>> from dataclasses import dataclass, field
    >>> @dataclass
    >>> class Example:
    >>>     a: int
    >>>     b: list = field(default_factory=list)
    >>>
    >>> obj = Example(1, [Example(2), Example(3, [Example(4), 5])])
    >>> target_type = int
    >>> extracted = extract_type(obj, target_type)
    >>> print(extracted)
    [1, 2, 3, 4, 5]
    """

    result = []

    if isinstance(obj, target) or _is_subclass(obj, target):
        result.append(obj)

    for name, value in obj.__dict__.items():
        if not _is_basetype(value) and not isinstance(value, Enum):
            result += extract(value, target)
        elif isinstance(value, list) and not all(_is_basetype(item) for item in value):
            for item in value:
                result += extract(item, target)

    return result


def _is_subclass(obj, target):
    """Checks if an object is a subclass of a target type."""

    if not hasattr(obj, "__class__"):
        return False

    return issubclass(obj.__class__, target)


def _is_basetype(obj):
    """Checks if an object is a basic type."""
    return isinstance(
        obj,
        (
            int,
            float,
            str,
            bool,
            bytes,
            complex,
            list,
            dict,
            type(None),
        ),
    )
