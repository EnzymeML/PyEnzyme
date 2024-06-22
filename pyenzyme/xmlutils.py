import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom


def map_to_xml(root: ET.Element, mappings: dict, namespace: str):
    """
    Maps a dictionary to XML elements and appends them to the root element.

    Args:
        root (ET.Element): The root element to which sub-elements are appended.
        mappings (dict): The dictionary containing the key-value mappings to convert to XML.
    """

    for key, value in mappings.items():
        if value is None:
            continue
        if key.startswith("@"):
            root.attrib[key[1:]] = str(value)
            continue

        subelement = ET.Element(f"{{{namespace}}}{key}")

        if isinstance(value, dict):
            process_dict_value(subelement, value)
        elif key.startswith("@"):
            subelement.attrib[key[1:]] = str(value)
        else:
            subelement.text = str(value)

        if not _is_empty(subelement):
            root.append(subelement)


def _is_empty(element: ET.Element):
    """Checks if an element and its sub elements are empty."""

    return all(
        [
            len(element.attrib) == 0,
            element.text is None or element.text.strip() == "",
            all(_is_empty(child) for child in element),
        ]
    )


def process_dict_value(subelement: ET.Element, value: dict):
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
            subelement.attrib[subkey[1:]] = str(subvalue)
        else:
            subelement.text = str(subvalue)


def serialize_to_pretty_xml_string(element: ET.Element | None) -> str | None:
    """Serialize the ElementTree element to a pretty-printed byte string."""

    if element is None:
        return None

    rough_string = ET.tostring(element, "utf-8", xml_declaration=False)
    reparsed = minidom.parseString(rough_string)

    return "\n".join(reparsed.toprettyxml(indent="\t").split("\n")[1:]).strip()


def register_namespaces(nsmap: dict):
    for prefix, uri in nsmap.items():
        ET.register_namespace(prefix, uri)
