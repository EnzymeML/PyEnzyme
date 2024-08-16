import rdflib
import json
import xml.etree.ElementTree as ET


def parse_sbml_rdf_annotation(sbml_obj, enzml_obj):
    """Parse the RDF annotation of an SBML object."""

    annotation = sbml_obj.getAnnotationString()

    if not annotation:
        return None

    json_ld_header = _rdf_annotation_to_json_ld(annotation)
    _map_json_ld_to_obj(enzml_obj, json_ld_header)


def _rdf_annotation_to_json_ld(annotation: str):
    """Convert an SBML annotation to JSON-LD."""

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
    """Map JSON-LD header to an object."""

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
    """Sync the context prefixes of an object."""

    inverse_prefixes = {
        value: key
        for key, value in obj.ld_context.items()
        if isinstance(value, str)
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
