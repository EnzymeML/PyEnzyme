import rdflib
import json
import xml.etree.ElementTree as ET


def parse_sbml_rdf_annotation(sbml_obj, enzml_obj):
    """
    Parse the RDF annotation of an SBML object and map it to an EnzymeML object.

    This function extracts RDF annotations from SBML objects, converts them to JSON-LD,
    and maps the resulting data to EnzymeML objects.

    Args:
        sbml_obj: The SBML object containing RDF annotations.
        enzml_obj: The EnzymeML object to which the annotations will be mapped.

    Returns:
        None: The function modifies the enzml_obj in place.
    """
    annotation = sbml_obj.getAnnotationString()

    if not annotation:
        return None

    json_ld_header = _rdf_annotation_to_json_ld(annotation)
    _map_json_ld_to_obj(enzml_obj, json_ld_header)


def _rdf_annotation_to_json_ld(annotation: str):
    """
    Convert an SBML RDF annotation to JSON-LD format.

    This function parses an XML annotation string, extracts the RDF element,
    and converts it to JSON-LD format for easier processing.

    Args:
        annotation (str): The XML annotation string from an SBML object.

    Returns:
        list | None: A list containing the JSON-LD representation of the RDF data,
                    or None if no RDF element is found.
    """
    # Parse the RDF annotation and extract the root
    # RDF element to create an RDF graph
    root = ET.fromstring(annotation)
    rdf_element = root.find("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF")

    if rdf_element is None:
        return None

    # Create a new RDF graph and parse the annotation
    g = rdflib.Graph()
    g.parse(data=ET.tostring(rdf_element), format="xml")

    return json.loads(g.serialize(format="json-ld"))


def _map_json_ld_to_obj(obj, header: list | None):
    """
    Map JSON-LD header data to an EnzymeML object.

    This function extracts context, ID, and type information from JSON-LD data
    and assigns it to the corresponding attributes of an EnzymeML object.

    Args:
        obj: The EnzymeML object to which the JSON-LD data will be mapped.
        header (list | None): The JSON-LD data as a list, or None if no data is available.

    Returns:
        None: The function modifies the obj in place.
    """
    if header is None:
        return

    for key, value in header[0].items():
        if key == "@context":
            obj.ld_context.update(value)
        elif key == "@id":
            obj.ld_id = value
        elif key == "@type":
            obj.ld_type += value

    _sync_context_prefixes(obj)


def _sync_context_prefixes(obj):
    """
    Synchronize the context prefixes of an EnzymeML object.

    This function creates a consistent representation of IRIs and prefixes
    across the context, type, and ID attributes of an EnzymeML object.
    It replaces full IRIs with their corresponding prefixed versions.

    Args:
        obj: The EnzymeML object whose context prefixes will be synchronized.

    Returns:
        None: The function modifies the obj in place.
    """
    inverse_prefixes = {
        value: key for key, value in obj.ld_context.items() if isinstance(value, str)
    }

    # Convert context
    for key, value in obj.ld_context.items():
        if not isinstance(value, str):
            continue
        if value in inverse_prefixes:
            # Skip if the prefix is already in the context
            continue

        for iri, prefix in inverse_prefixes.items():
            value = value.replace(iri, f"{prefix}:")

    # Convert types
    for i, type_ in enumerate(obj.ld_type):
        for iri, prefix in inverse_prefixes.items():
            if type_.startswith(iri):
                obj.ld_type[i] = type_.replace(iri, f"{prefix}:")
                break

    # Unique types
    obj.ld_type = list(set(obj.ld_type))

    # Convert ID
    for iri, prefix in inverse_prefixes.items():
        obj.ld_id = obj.ld_id.replace(iri, f"{prefix}:")
