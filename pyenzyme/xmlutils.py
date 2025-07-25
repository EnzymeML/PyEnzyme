import re
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from enum import Enum
from typing import Any


def map_to_xml(
    root: ET.Element,
    mappings: dict,
    namespace: str,
):
    """
    Maps a dictionary to XML elements and appends them to the root element.

    Args:
        root (ET.Element): The root element to which sub-elements are appended.
        mappings (dict): The dictionary containing the key-value mappings to convert to XML.
        namespace (str): The namespace of the XML elements.
    """

    for key, value in mappings.items():
        if value is None:
            continue
        if key.startswith("@"):
            root.attrib[key[1:]] = _convert_types(value)
            continue

        subelement = ET.Element(f"{{{namespace}}}{key}")

        if isinstance(value, dict):
            process_dict_value(subelement, value)
        elif isinstance(value, list):
            process_multiple_element(key, namespace, root, value)
        elif key.startswith("@"):
            subelement.attrib[key[1:]] = _convert_types(value)
        else:
            subelement.text = _convert_types(value)

        if not _is_empty(subelement):
            root.append(subelement)


def _convert_types(value):
    if isinstance(value, float) and value == 0.0:
        return "0.0"
    if isinstance(value, Enum):
        return str(value.name)

    return str(value)


def process_multiple_element(
    key: str,
    namespace: str,
    root: ET.Element,
    value: Any,
):
    """Processes a list value and adds it as a list of elements to the root element.

    Args:
        key (str): The key of the list element.
        namespace (str): The namespace of the list element.
        root (ET.Element): The root element to which the list elements are appended.
        value (list): The list of values to be added as elements.
    """
    for i, item in enumerate(value):
        list_element = ET.Element(f"{{{namespace}}}{key}")
        list_element.text = _convert_types(item)
        root.append(list_element)


def _is_empty(element: ET.Element):
    """Checks if an element and its sub elements are empty.

    Args:
        element (ET.Element): The element to check.

    Returns:
        bool: True if the element is empty, False otherwise.
    """

    return all(
        [
            len(element.attrib) == 0,
            element.text is None or element.text.strip() == "",
            all(_is_empty(child) for child in element),
        ]
    )


def process_dict_value(
    subelement: ET.Element,
    value: dict,
):
    """
    Processes a dictionary value and adds it as attributes or text to a subelement.

    Args:
        subelement (ET.Element): The subelement to which attributes or text are added.
        value (dict): The dictionary containing the subkey-subvalue mappings.
    """
    for subkey, subvalue in value.items():
        if not subvalue:
            continue

        if subkey.startswith("@"):
            subelement.attrib[subkey[1:]] = _convert_types(subvalue)
        else:
            subelement.text = _convert_types(subvalue)


def serialize_to_pretty_xml_string(element: ET.Element | None) -> str | None:
    """Serialize the ElementTree element to a pretty-printed byte string."""

    if element is None:
        return None

    rough_string = ET.tostring(
        element,
        encoding="unicode",
        method="xml",
        xml_declaration=False,
    )

    reparsed = minidom.parseString(rough_string)

    return "\n".join(reparsed.toprettyxml(indent="\t").split("\n")[1:]).strip()


def register_namespaces(nsmap: dict):
    for prefix, uri in nsmap.items():
        ET.register_namespace(prefix, uri)


def extract_namespaces(xml_string: str | None) -> set[str]:
    """Extract all namespaces from an ElementTree element.

    Args:
        xml_string (str | None): The XML string to extract namespaces from.

    Returns:
        set[str]: A set of namespace URIs.
    """

    if xml_string is None or xml_string == "":
        raise ValueError("No XML string provided")

    pattern = r"\{(.*)\}"
    namespaces = set()

    root = ET.fromstring(xml_string)

    for child in root.iter():
        if match := re.match(pattern, child.tag):
            uri = match.group(1)
            namespaces.add(uri)

    return namespaces
