from enum import Enum
import toml
import functools as ft
import importlib.resources as pkg_resources


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
