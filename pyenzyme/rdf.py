import rdflib


def to_rdf_xml(*objs, keep_header: bool = False):
    """Converts a JSON-LD string to RDF/XML format.

    Args:
        json_ld (str): The JSON-LD string to convert.
        keep_header (bool, optional): Whether to keep the XML header. Defaults to False.
    Returns:
        str: The RDF/XML string.
    """

    graph = rdflib.Graph()

    for obj in objs:
        if not hasattr(obj, "ld_id"):
            obj.ld_id = f"http://enzymeml.org/v2/{obj.__class__.__name__}/{obj.ld_id}"
        to_exclude = {
            key
            for key, value in obj.ld_context.items()
            if isinstance(value, dict) and value.get("@type", None) == "@id"
        }
        graph.parse(
            data=obj.model_dump_json(by_alias=True, exclude=to_exclude),
            format="json-ld",
        )

    rdf_xml = graph.serialize(format="xml")

    if not keep_header:
        return "\n".join(rdf_xml.split("\n")[1:])
    else:
        return rdf_xml
