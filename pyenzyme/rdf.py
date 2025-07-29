import rdflib
from loguru import logger


def to_rdf_xml(*objs, keep_header: bool = False):
    """Converts PyEnzyme objects to RDF/XML format.

    This function takes one or more PyEnzyme objects, converts them to JSON-LD format,
    and then transforms the JSON-LD into RDF/XML. It handles the creation of proper
    linked data identifiers and excludes properties that are references to other objects.

    Args:
        *objs: One or more PyEnzyme objects to convert to RDF/XML.
        keep_header (bool, optional): Whether to keep the XML header in the output.
            Defaults to False.

    Returns:
        str: The RDF/XML representation of the input objects.

    Example:
        >>> protein = pe.Protein(id="protein1", name="Example Protein")
        >>> rdf_xml = to_rdf_xml(protein)
        >>> print(rdf_xml)
    """
    graph = rdflib.Graph()

    for obj in objs:
        if not hasattr(obj, "ld_id"):
            logger.debug(
                f"Creating linked data ID for {obj.__class__.__name__} {obj.id}"
            )
            obj.ld_id = f"http://enzymeml.org/v2/{obj.__class__.__name__}/{obj.id}"

        # Exclude properties that are references to other objects (indicated by @id type)
        to_exclude = {
            key
            for key, value in obj.ld_context.items()
            if isinstance(value, dict) and value.get("@type", None) == "@id"
        }

        # Parse the JSON-LD representation of the object into the RDF graph
        graph.parse(
            data=obj.model_dump_json(by_alias=True, exclude=to_exclude),
            format="json-ld",
        )

    # Serialize the graph to RDF/XML format
    rdf_xml = graph.serialize(format="xml")

    # Optionally remove the XML header
    if not keep_header:
        return "\n".join(rdf_xml.split("\n")[1:])
    else:
        return rdf_xml
