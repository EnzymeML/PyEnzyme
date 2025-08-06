import functools as ft
import json
from enum import Enum
from typing import Literal

from pydantic import BaseModel

from pyenzyme.versions.v2 import EnzymeMLDocument, Measurement


def to_dict_wo_json_ld(obj: BaseModel):
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

    doc = json.loads(obj.model_dump_json())
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


def group_measurements(
    enzymemldoc: EnzymeMLDocument,
    attribute: Literal["initial", "prepared"] = "initial",
    tolerance: float = 0.0,
) -> EnzymeMLDocument:
    """
    Groups measurements by their conditions and assigns for each unique set of conditions
    a `group_id` attribute.

    Args:
        enzymemldoc (EnzymeMLDocument): The EnzymeMLDocument to group measurements from.
        attribute (Literal["initial", "prepared"]): Which concentration attribute to use for grouping.
        tolerance (float): Percentage tolerance for numerical comparison (e.g., 0.05 for 5%) for matching groups.

    Returns:
        EnzymeMLDocument: The EnzymeMLDocument with grouped measurements.
    """

    # Create a mapping from conditions to group_id
    conditions_to_group: dict[tuple, str] = {}
    group_counter = 0

    for measurement in enzymemldoc.measurements:
        # Get conditions as a hashable representation
        conditions = _get_measurement_conditions(measurement, attribute)

        # Find matching group with tolerance
        matching_group = _find_matching_group(
            conditions, conditions_to_group, tolerance
        )

        if matching_group is None:
            # Create new group
            group_id = f"group_{group_counter}"
            conditions_hash = _conditions_to_hashable(conditions)
            conditions_to_group[conditions_hash] = group_id
            group_counter += 1
            measurement.group_id = group_id
        else:
            measurement.group_id = matching_group

    return enzymemldoc


def _get_measurement_conditions(
    measurement: Measurement,
    attribute: Literal["initial", "prepared"] = "initial",
) -> dict:
    """
    Extract measurement conditions as a dictionary, including pH and temperature.
    Does not account for variation in units.

    Args:
        measurement: The measurement to extract conditions from
        attribute: Which concentration attribute to use ("initial" or "prepared")

    Returns:
        dict: Conditions dictionary with species concentrations and environmental conditions
    """
    conditions = {}

    # Add species conditions using the specified attribute
    for species_data in measurement.species_data:
        value = getattr(species_data, attribute)
        if value is not None:
            conditions[species_data.species_id] = value

    # Add environmental conditions
    if measurement.ph is not None:
        conditions["ph"] = measurement.ph
    if measurement.temperature is not None:
        conditions["temperature"] = measurement.temperature

    return conditions


def _find_matching_group(
    conditions: dict,
    conditions_to_group: dict,
    tolerance: float,
) -> str | None:
    """
    Find a matching group for given conditions within tolerance.

    Args:
        conditions: Current measurement conditions
        conditions_to_group: Mapping of condition hashes to group IDs
        tolerance: Percentage tolerance for numerical comparison

    Returns:
        str | None: Group ID if match found, None otherwise
    """
    # Exact matching
    if tolerance == 0.0:
        conditions_hash = _conditions_to_hashable(conditions)
        return conditions_to_group.get(conditions_hash)

    # Tolerance-based matching
    for existing_conditions_hash, group_id in conditions_to_group.items():
        existing_conditions = dict(existing_conditions_hash)

        if _conditions_match_with_tolerance(conditions, existing_conditions, tolerance):
            return group_id

    return None


def _conditions_match_with_tolerance(
    conditions1: dict,
    conditions2: dict,
    tolerance: float,
) -> bool:
    """
    Check if two condition dictionaries match within tolerance.

    Args:
        conditions1: First conditions dictionary
        conditions2: Second conditions dictionary
        tolerance: Percentage tolerance for numerical comparison

    Returns:
        bool: True if conditions match within tolerance
    """
    # Must have same keys
    if set(conditions1.keys()) != set(conditions2.keys()):
        return False

    # Check each value
    for key in conditions1:
        val1, val2 = conditions1[key], conditions2[key]

        # Handle None values
        if val1 is None or val2 is None:
            if val1 != val2:
                return False
            continue

        # Check tolerance
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            if not _values_match_with_tolerance(val1, val2, tolerance):
                return False

    return True


def _values_match_with_tolerance(
    val1: float,
    val2: float,
    tolerance: float,
) -> bool:
    """
    Check if two numerical values match within percentage tolerance.

    Args:
        val1: First value
        val2: Second value
        tolerance: Percentage tolerance (e.g., 0.05 for 5%)

    Returns:
        bool: True if values match within tolerance
    """
    if val1 == 0 and val2 == 0:
        return True

    if val1 == 0 or val2 == 0:
        return abs(val1 - val2) <= tolerance

    # Percentage difference
    relative_diff = abs(val1 - val2) / max(abs(val1), abs(val2))
    return relative_diff <= tolerance


def _conditions_to_hashable(conditions: dict) -> tuple:
    """
    Convert conditions dictionary to a hashable tuple for comparison.

    Args:
        conditions: Dictionary of conditions

    Returns:
        tuple: Sorted tuple of (key, value) pairs.
    """
    return tuple(sorted(conditions.items()))


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
